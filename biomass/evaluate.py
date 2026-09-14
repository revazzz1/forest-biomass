"""Test-set metrics in t/ha and tCO2 per patch, residuals by biomass bin, and the two figures per model."""
from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from biomass import FIGURES, MODELS
from biomass.carbon import tco2_per_patch
from biomass.models import inputs, load_model
from biomass.split import load_split

MODEL_NAMES = {"ridge": "Ridge", "rf": "Random forest", "cnn": "CNN"}
BINS = [0, 50, 100, 150, np.inf]
BIN_LABELS = ["0–50", "50–100", "100–150", "150+"]
COLORS = {"ridge": "#7fa86f", "rf": "#2f5d3a", "cnn": "#1f3d34"}  # same series colours as the UI


def metrics(y: np.ndarray, yhat: np.ndarray) -> dict[str, float]:
    err = yhat - y
    rmse = float(np.sqrt(np.mean(err**2)))
    return {"mae": float(np.mean(np.abs(err))), "rmse": rmse,
            "r2": float(1 - np.sum(err**2) / np.sum((y - y.mean()) ** 2)),
            "rmse_tco2_per_patch": tco2_per_patch(rmse), "mae_tco2_per_patch": tco2_per_patch(float(np.mean(np.abs(err))))}


def residuals_by_bin(y: np.ndarray, yhat: np.ndarray) -> pd.DataFrame:
    """Mean residual (prediction minus truth) and MAE per true-biomass bin; negative means under-prediction."""
    df = pd.DataFrame({"bin": pd.cut(y, BINS, labels=BIN_LABELS, right=False), "res": yhat - y})
    g = df.groupby("bin", observed=False).res
    return pd.DataFrame({"n": g.size(), "mean_residual": g.mean(), "mae": g.apply(lambda r: r.abs().mean())}).fillna(0)


def predict(name: str, d: dict) -> np.ndarray:
    m = load_model(name)
    return m.predict(d["X"] if name == "cnn" else d["F"]).astype(np.float32)


def scatter(y: np.ndarray, preds: dict[str, np.ndarray], path) -> None:
    fig, axes = plt.subplots(1, len(preds), figsize=(4 * len(preds), 4), sharex=True, sharey=True)
    lim = max(float(y.max()), *(float(p.max()) for p in preds.values())) * 1.05
    for ax, (name, p) in zip(np.atleast_1d(axes), preds.items()):
        ax.plot([0, lim], [0, lim], color="#999", lw=1)
        ax.scatter(y, p, s=8, alpha=0.6, color=COLORS[name])
        ax.set(title=MODEL_NAMES[name], xlabel="LiDAR biomass (t/ha)", xlim=(0, lim), ylim=(0, lim), aspect="equal")
    np.atleast_1d(axes)[0].set_ylabel("Predicted biomass (t/ha)")
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def residual_plot(y: np.ndarray, preds: dict[str, np.ndarray], path) -> None:
    fig, ax = plt.subplots(figsize=(6, 4))
    width = 0.8 / len(preds)
    for i, (name, p) in enumerate(preds.items()):
        r = residuals_by_bin(y, p)
        ax.bar(np.arange(len(r)) + i * width, r.mean_residual, width, label=MODEL_NAMES[name], color=COLORS[name])
    ax.axhline(0, color="#333", lw=1)
    ax.set(xticks=np.arange(len(BIN_LABELS)) + width, xticklabels=BIN_LABELS, xlabel="LiDAR biomass (t/ha)",
           ylabel="Mean residual, predicted − true (t/ha)")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def main() -> None:
    test = inputs(load_split())["test"]
    names = [n for n in MODEL_NAMES if (MODELS / f"{n}_settings.json").exists()]
    preds = {n: predict(n, test) for n in names}
    for n, p in preds.items():
        (MODELS / f"{n}_metrics.json").write_text(json.dumps(
            {"test": metrics(test["y"], p), "residuals_by_bin": residuals_by_bin(test["y"], p).to_dict("index")}, indent=1))
    FIGURES.mkdir(exist_ok=True)
    scatter(test["y"], preds, FIGURES / "scatter.png")
    residual_plot(test["y"], preds, FIGURES / "residuals.png")
    print(pd.DataFrame({n: metrics(test["y"], p) for n, p in preds.items()}).T.round(2))


if __name__ == "__main__":
    main()
