import numpy as np
import pytest

from biomass.load import block_mean, patch_mean


def test_patch_mean_ignores_nodata_but_keeps_zero():
    raster = np.array([[10, 20, -1, 0], [30, 40, -1, 0], [-1, -1, -1, 0], [0, 0, 0, 0]], dtype=np.float32)
    assert patch_mean(raster, nodata=-1) == pytest.approx((10 + 20 + 30 + 40) / 11)
    assert patch_mean(raster) == pytest.approx(raster.mean())


def test_block_mean_shape_and_values():
    img = np.arange(4 * 4 * 2, dtype=np.float32).reshape(4, 4, 2)
    out = block_mean(img, 2)
    assert out.shape == (2, 2, 2) and out.dtype == np.float32
    assert out[0, 0, 0] == img[:2, :2, 0].mean()
    assert out[1, 1, 1] == img[2:, 2:, 1].mean()
    assert block_mean(img[..., 0], 2).shape == (2, 2)
