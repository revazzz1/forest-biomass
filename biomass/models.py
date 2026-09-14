"""The three models: ridge, random forest, CNN. Trained on `train`, selected on `val`, saved to models/."""
from __future__ import annotations

import json
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from biomass import CACHE, MODELS
from biomass.features import load_features
from biomass.load import load_patches
from biomass.split import load_split

RIDGE_ALPHAS = (0.01, 0.1, 1, 10, 100, 1000)
MAX_EPOCHS = 100


def fit_ridge(Xtr: pd.DataFrame, ytr: np.ndarray, Xva: pd.DataFrame, yva: np.ndarray) -> tuple[object, dict]:
    """Standardised ridge; alpha chosen by validation MAE."""
    fits = {a: make_pipeline(StandardScaler(), Ridge(alpha=a)).fit(Xtr, ytr) for a in RIDGE_ALPHAS}
    maes = {a: mean_absolute_error(yva, m.predict(Xva)) for a, m in fits.items()}
    best = min(maes, key=maes.get)
    return fits[best], {"alpha": best, "val_mae_by_alpha": maes}


def fit_rf(Xtr: pd.DataFrame, ytr: np.ndarray, seed: int = 0) -> tuple[object, dict]:
    """The standard forestry remote-sensing baseline, with default-ish settings."""
    rf = RandomForestRegressor(n_estimators=500, min_samples_leaf=2, n_jobs=-1, random_state=seed).fit(Xtr, ytr)
    return rf, {"n_estimators": 500, "min_samples_leaf": 2}


def build_cnn(Xtr: np.ndarray):
    """Three conv blocks -> global average pool -> dense 64 -> linear. Inputs standardised per band from `Xtr`."""
    from tensorflow import keras

    norm = keras.layers.Normalization(axis=-1)
    norm.adapt(Xtr)
    layers = [keras.Input(Xtr.shape[1:]), norm]
    for filters in (32, 64, 128):
        layers += [keras.layers.Conv2D(filters, 3, padding="same", activation="relu"), keras.layers.MaxPooling2D()]
    layers += [keras.layers.GlobalAveragePooling2D(), keras.layers.Dense(64, activation="relu"), keras.layers.Dense(1)]
    model = keras.Sequential(layers)
    model.compile(optimizer="adam", loss="mse", metrics=["mae"])
    return model


def fit_cnn(Xtr: np.ndarray, ytr: np.ndarray, Xva: np.ndarray, yva: np.ndarray, seed: int = 0) -> tuple[object, dict]:
    """Train on the standardised label with early stopping on validation MAE; the wrapper inverts the scaling."""
    from tensorflow import keras

    keras.utils.set_random_seed(seed)
    mu, sd = float(ytr.mean()), float(ytr.std())
    model = build_cnn(Xtr)
    stop = keras.callbacks.EarlyStopping(monitor="val_mae", patience=10, restore_best_weights=True)
    hist = model.fit(Xtr, (ytr - mu) / sd, validation_data=(Xva, (yva - mu) / sd), epochs=MAX_EPOCHS,
                     batch_size=32, callbacks=[stop], verbose=2)
    epochs = len(hist.history["loss"])
    return CNN(model, mu, sd), {"epochs": epochs, "best_epoch": epochs - stop.wait,
                                "val_mae_by_epoch": [float(v * sd) for v in hist.history["val_mae"]],
                                "params": int(model.count_params())}


class CNN:
    """Keras model plus the label scaling, so `predict` returns t/ha like the sklearn models."""

    def __init__(self, model, mu: float, sd: float):
        self.model, self.mu, self.sd = model, mu, sd

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(X, verbose=0).ravel() * self.sd + self.mu

    def save(self, path: Path) -> None:
        self.model.save(path.with_suffix(".keras"))
        path.with_suffix(".json").write_text(json.dumps({"mu": self.mu, "sd": self.sd}))

    @classmethod
    def load(cls, path: Path) -> "CNN":
        from tensorflow import keras

        scale = json.loads(path.with_suffix(".json").read_text())
        return cls(keras.models.load_model(path.with_suffix(".keras")), **scale)


def save_model(name: str, model: object, settings: dict, models: Path = MODELS) -> None:
    models.mkdir(exist_ok=True)
    if isinstance(model, CNN):
        model.save(models / name)
    else:
        joblib.dump(model, models / f"{name}.joblib")
    (models / f"{name}_settings.json").write_text(json.dumps(settings, indent=1))


def load_model(name: str, models: Path = MODELS) -> object:
    return CNN.load(models / name) if name == "cnn" else joblib.load(models / f"{name}.joblib")


def inputs(split: dict[str, list[str]]) -> dict[str, dict]:
    """Per split: tabular features `F`, image tensor `X`, label `y`, chip ids."""
    p, f = load_patches(), load_features()
    pos = {c: i for i, c in enumerate(p["ids"])}
    out = {}
    for name, ids in split.items():
        idx = [pos[c] for c in ids]
        out[name] = {"F": f.loc[ids], "X": p["X"][idx], "y": p["y"][idx], "ids": ids}
    return out


def main() -> None:
    d = inputs(load_split())
    tr, va = d["train"], d["val"]
    which = os.environ.get("MODELS_TO_TRAIN", "ridge,rf,cnn").split(",")
    if "ridge" in which:
        save_model("ridge", *fit_ridge(tr["F"], tr["y"], va["F"], va["y"]))
    if "rf" in which:
        save_model("rf", *fit_rf(tr["F"], tr["y"]))
    if "cnn" in which:
        save_model("cnn", *fit_cnn(tr["X"], tr["y"], va["X"], va["y"]))
    print("trained:", which)


if __name__ == "__main__":
    main()
