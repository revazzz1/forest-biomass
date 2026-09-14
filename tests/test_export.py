import numpy as np
import pytest

from biomass.export import check_export, to_colormap, to_rgb, write_export

SUMMARY = {"dataset": {"n_chips": 2, "patch_size": 64, "splits": {"train": 1, "val": 0, "test": 1}},
           "models": {"ridge": {"test": {"mae": 1, "rmse": 2, "r2": 0.5, "rmse_tco2_per_patch": 3}}},
           "scales": {"ndvi": [0, 0.9], "agb": [0, 250], "rgb": [0.01, 0.3]}, "carbon": {"carbon_fraction": 0.47}}
RECORD = {"id": "abc", "split": "test", "agb_true": 10.0, "ndvi": 0.5, "tco2_true": 1.0,
          "pred": {"ridge": 12.0}, "tco2_pred": {"ridge": 1.2}}


def images(chip):
    refl = np.random.default_rng(0).random((8, 8, 10), dtype=np.float32)
    return {chip: {"rgb": to_rgb(refl, 0.0, 1.0), "ndvi": to_colormap(refl[..., 0], (0, 1), "YlGn"),
                   "agb": to_colormap(refl[..., 1] * 100, (0, 250), "viridis")}}


def test_export_roundtrip_validates(tmp_path):
    write_export(SUMMARY, [RECORD], images("abc"), tmp_path)
    check_export(tmp_path)
    assert (tmp_path / "patches" / "abc_rgb.png").stat().st_size > 0


def test_missing_png_is_caught(tmp_path):
    write_export(SUMMARY, [RECORD], {}, tmp_path)
    with pytest.raises(AssertionError, match="abc_rgb.png"):
        check_export(tmp_path)


def test_rgb_stretch_clips_to_uint8():
    refl = np.array([[[0.0] * 10, [1.0] * 10]], dtype=np.float32)
    out = to_rgb(refl, 0.1, 0.5)
    assert out.dtype == np.uint8 and out[0, 0].tolist() == [0, 0, 0] and out[0, 1].tolist() == [255, 255, 255]
