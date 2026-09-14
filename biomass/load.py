"""Chip selection, download, and the patch cache (data/cache/patches.npz)."""
from __future__ import annotations

import os
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile

from biomass import CACHE, RAW
from biomass.fetch import BASE, archive_index, download

BANDS = ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12"]  # band 11 is cloud probability
SUMMER = ["June", "July", "August"]  # month index 09, 10, 11 in the filenames


def tracker(raw: Path = RAW) -> pd.DataFrame:
    """Sentinel-2 rows of the mirror's chip tracker (downloaded once, ~110 MB)."""
    path = raw / "biomassters_chip_tracker.csv"
    if not path.exists():
        urllib.request.urlretrieve(BASE + path.name, path)
    cols = ["filename", "chip_id", "satellite", "split", "month", "cloud_percentage", "corrupt_values", "red_mean"]
    t = pd.read_csv(path, usecols=cols)
    return t[t.satellite == "S2"].drop(columns="satellite")


def select_chips(t: pd.DataFrame, n: int, seed: int = 0, max_cloud: float = 5.0, max_red: float = 1000.0) -> pd.DataFrame:
    """Pick `n` training chips with a clean summer image; one image per chip.

    A chip is eligible if some June-August image is uncorrupted, has at most
    `max_cloud` percent cloudy pixels, and a plausible red-band mean (zero means
    an empty image, very high means snow or a failed atmospheric correction).
    Among a chip's eligible images the one with the fewest clouds wins, ties
    broken by the lowest red mean (thin haze brightens the red band).
    """
    ok = t[t.month.isin(SUMMER) & (t.split == "train") & ~t.corrupt_values
           & (t.cloud_percentage <= max_cloud) & (t.red_mean > 0) & (t.red_mean <= max_red)]
    best = ok.sort_values(["cloud_percentage", "red_mean"]).drop_duplicates("chip_id")
    picked = best.sample(n, random_state=seed).sort_values("chip_id")
    return picked.assign(label=picked.chip_id + "_agbm.tif")[["chip_id", "filename", "month", "label"]]


def read_s2(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Reflectance in [0, 1] as (256, 256, 10) float32, plus the (256, 256) cloud-probability band."""
    img = tifffile.imread(path)
    return img[..., :10].astype(np.float32) / 10_000, img[..., 10]


def read_label(path: Path) -> np.ndarray:
    """Above-ground biomass in t/ha per 10 m pixel, (256, 256) float32."""
    return tifffile.imread(path).astype(np.float32)


def patch_mean(label: np.ndarray, nodata: float | None = None) -> float:
    """Mean biomass over the patch. BioMassters labels have no nodata value: zero is real (water, rock, clearcut)."""
    values = label if nodata is None else label[label != nodata]
    return float(values.mean())


def block_mean(img: np.ndarray, size: int) -> np.ndarray:
    """Downsample an (H, W, ...) image to (size, size, ...) by averaging square blocks."""
    h, w = img.shape[:2]
    f = h // size
    assert f * size == h == w, f"{img.shape[:2]} is not a square multiple of {size}"
    return img.reshape(size, f, size, f, *img.shape[2:]).mean(axis=(1, 3)).astype(np.float32)


def build_patches(selection: pd.DataFrame, raw: Path, size: int) -> dict[str, np.ndarray]:
    X = np.stack([block_mean(read_s2(raw / f)[0], size) for f in selection.filename])
    y = np.array([patch_mean(read_label(raw / f)) for f in selection.label], dtype=np.float32)
    return {"X": X, "y": y, "ids": selection.chip_id.to_numpy().astype(str)}


def load_patches(cache: Path = CACHE) -> dict[str, np.ndarray]:
    with np.load(cache / "patches.npz", allow_pickle=False) as z:
        return {k: z[k] for k in z}


def main() -> None:
    n, size = int(os.environ.get("N", 1500)), int(os.environ.get("SIZE", 64))
    selection = select_chips(tracker(), n)
    selection.to_csv(CACHE / "selection.csv", index=False)
    download([*selection.filename, *selection.label], archive_index(CACHE), RAW)
    np.savez(CACHE / "patches.npz", **build_patches(selection, RAW, size))
    print(f"{n} chips, patches {size}x{size}, cached in {CACHE}")


if __name__ == "__main__":
    main()
