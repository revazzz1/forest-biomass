"""Tabular features for the baselines, one row per chip (data/cache/features.parquet)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from biomass import CACHE
from biomass.load import BANDS, load_patches

B4, B8, B11 = BANDS.index("B4"), BANDS.index("B8"), BANDS.index("B11")


def normalized_difference(X: np.ndarray, a: int, b: int) -> np.ndarray:
    """(band a - band b) / (band a + band b) per pixel; 0 where both bands are 0."""
    num, den = X[..., a] - X[..., b], X[..., a] + X[..., b]
    return np.divide(num, den, out=np.zeros_like(num), where=den != 0)


def ndvi(X: np.ndarray) -> np.ndarray:
    return normalized_difference(X, B8, B4)


def ndmi(X: np.ndarray) -> np.ndarray:
    return normalized_difference(X, B8, B11)


def tabular(X: np.ndarray, ids: np.ndarray) -> pd.DataFrame:
    """Per-band mean and standard deviation plus mean NDVI and NDMI of each patch."""
    cols = {f"mean_{b}": X[..., i].mean(axis=(1, 2)) for i, b in enumerate(BANDS)}
    cols |= {f"std_{b}": X[..., i].std(axis=(1, 2)) for i, b in enumerate(BANDS)}
    cols |= {"ndvi": ndvi(X).mean(axis=(1, 2)), "ndmi": ndmi(X).mean(axis=(1, 2))}
    return pd.DataFrame(cols, index=pd.Index(ids, name="chip_id"))


def load_features(cache: Path = CACHE) -> pd.DataFrame:
    return pd.read_parquet(cache / "features.parquet")


def main() -> None:
    p = load_patches()
    tabular(p["X"], p["ids"]).to_parquet(CACHE / "features.parquet")
    print(f"features for {len(p['ids'])} chips")


if __name__ == "__main__":
    main()
