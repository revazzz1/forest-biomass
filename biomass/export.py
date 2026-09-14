"""Everything the web UI reads: web/public/data/summary.json, patches.json and three PNGs per chip."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from PIL import Image

from biomass import CACHE, MODELS, RAW, ROOT
from biomass.carbon import tco2_per_patch
from biomass.evaluate import MODEL_NAMES, predict
from biomass.features import ndvi
from biomass.load import BANDS, read_label, read_s2
from biomass.models import inputs
from biomass.split import load_split

OUT = ROOT / "web" / "public" / "data"
RGB = [BANDS.index(b) for b in ("B4", "B3", "B2")]
NDVI_SCALE = (0.0, 0.9)  # fixed colour scale limits shared by every chip
AGB_SCALE = (0.0, 250.0)  # t/ha; LiDAR maps rarely exceed this in Finland
STRETCH = (2, 98)  # percentiles of reflectance, over all exported chips, for the RGB composite
TRAIN_SAMPLE = 100


def rgb_limits(images: list[np.ndarray]) -> tuple[float, float]:
    """One reflectance stretch for all chips, so bright and dark patches stay comparable."""
    lo, hi = np.percentile(np.stack([im[..., RGB] for im in images]), STRETCH)
    return float(lo), float(hi)


def to_rgb(refl: np.ndarray, lo: float, hi: float) -> np.ndarray:
    return (np.clip((refl[..., RGB] - lo) / (hi - lo), 0, 1) * 255).astype(np.uint8)


def to_colormap(values: np.ndarray, scale: tuple[float, float], cmap: str) -> np.ndarray:
    unit = np.clip((values - scale[0]) / (scale[1] - scale[0]), 0, 1)
    return (matplotlib.colormaps[cmap](unit)[..., :3] * 255).astype(np.uint8)


def write_export(summary: dict, records: list[dict], images: dict[str, dict[str, np.ndarray]], out: Path = OUT) -> None:
    """`images` maps chip id -> {"rgb", "ndvi", "agb"} uint8 arrays. Writes the JSON and one PNG per array."""
    (out / "patches").mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=1))
    (out / "patches.json").write_text(json.dumps(records, indent=1))
    for chip, kinds in images.items():
        for kind, arr in kinds.items():
            Image.fromarray(arr).save(out / "patches" / f"{chip}_{kind}.png")


def check_export(out: Path = OUT) -> None:
    """A small schema: the keys the UI reads must exist, and every PNG a record implies must be on disk."""
    s = json.loads((out / "summary.json").read_text())
    assert {"dataset", "models", "scales", "carbon"} <= s.keys()
    assert {"n_chips", "patch_size", "splits"} <= s["dataset"].keys()
    for m in s["models"].values():
        assert {"mae", "rmse", "r2", "rmse_tco2_per_patch"} <= m["test"].keys()
    assert {"ndvi", "agb", "rgb"} <= s["scales"].keys()
    records = json.loads((out / "patches.json").read_text())
    for r in records:
        assert {"id", "split", "agb_true", "ndvi", "tco2_true", "pred", "tco2_pred"} <= r.keys()
        assert r["pred"].keys() == s["models"].keys() == r["tco2_pred"].keys()
        for kind in ("rgb", "ndvi", "agb"):
            assert (out / "patches" / f"{r['id']}_{kind}.png").exists(), f"{r['id']}_{kind}.png missing"


def main() -> None:
    split = load_split()
    d = inputs(split)
    names = [n for n in MODEL_NAMES if (MODELS / f"{n}_settings.json").exists()]
    rng = np.random.default_rng(0)
    chosen = {"test": d["test"], "train": {k: (v.iloc[i] if k == "F" else [v[j] for j in i] if k == "ids" else v[i])
                                           for i in [rng.choice(len(d["train"]["y"]), TRAIN_SAMPLE, replace=False)]
                                           for k, v in d["train"].items()}}
    files = pd.read_csv(CACHE / "selection.csv").set_index("chip_id")
    records, images, raw_rgb = [], {}, {}
    for split_name, part in chosen.items():
        preds = {n: predict(n, part) for n in names}
        for i, chip in enumerate(part["ids"]):
            refl, _ = read_s2(RAW / files.filename[chip])
            label = read_label(RAW / files.label[chip])
            raw_rgb[chip] = refl
            images[chip] = {"ndvi": to_colormap(ndvi(refl), NDVI_SCALE, "YlGn"), "agb": to_colormap(label, AGB_SCALE, "viridis")}
            records.append({"id": chip, "split": split_name, "agb_true": float(part["y"][i]),
                            "ndvi": float(part["F"].ndvi.iloc[i]), "tco2_true": tco2_per_patch(float(part["y"][i])),
                            "pred": {n: float(p[i]) for n, p in preds.items()},
                            "tco2_pred": {n: tco2_per_patch(float(p[i])) for n, p in preds.items()}})
    lo, hi = rgb_limits(list(raw_rgb.values()))
    for chip, refl in raw_rgb.items():
        images[chip]["rgb"] = to_rgb(refl, lo, hi)
    patches = np.load(CACHE / "patches.npz")
    summary = {
        "dataset": {"n_chips": int(len(patches["ids"])), "patch_size": int(patches["X"].shape[1]),
                    "splits": {k: len(v) for k, v in split.items()}, "exported": {k: len(v["ids"]) for k, v in chosen.items()},
                    "agb_mean": float(patches["y"].mean()), "agb_max": float(patches["y"].max())},
        "models": {n: json.loads((MODELS / f"{n}_metrics.json").read_text())
                   | {"settings": json.loads((MODELS / f"{n}_settings.json").read_text()), "label": MODEL_NAMES[n]} for n in names},
        "scales": {"ndvi": NDVI_SCALE, "agb": AGB_SCALE, "rgb": [lo, hi], "stretch_percentiles": STRETCH},
        "carbon": {"carbon_fraction": 0.47, "area_ha": 655.36, "root_to_shoot": 0.0, "co2_per_c": 44 / 12},
    }
    write_export(summary, records, images)
    check_export()
    print(f"exported {len(records)} patches for {names} to {OUT}")


if __name__ == "__main__":
    main()
