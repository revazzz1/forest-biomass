"""Chip-level train / validation / test split, saved to data/cache/split.json."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from biomass import CACHE
from biomass.load import load_patches


def split_chips(ids: list[str], seed: int = 0, fractions: tuple[float, float, float] = (0.7, 0.15, 0.15)) -> dict[str, list[str]]:
    """Shuffle chip ids with a fixed seed and cut them into three disjoint lists."""
    order = np.random.default_rng(seed).permutation(sorted(ids))
    n_train, n_val = (round(len(ids) * f) for f in fractions[:2])
    return {"train": order[:n_train].tolist(), "val": order[n_train:n_train + n_val].tolist(),
            "test": order[n_train + n_val:].tolist()}


def load_split(cache: Path = CACHE) -> dict[str, list[str]]:
    return json.loads((cache / "split.json").read_text())


def main() -> None:
    split = split_chips(load_patches()["ids"].tolist())
    (CACHE / "split.json").write_text(json.dumps(split, indent=1))
    print({k: len(v) for k, v in split.items()})


if __name__ == "__main__":
    main()
