import numpy as np
import pytest

from biomass.features import B4, B8, ndvi, tabular


def test_ndvi_known_value_and_zero_division():
    X = np.zeros((1, 2, 2, 10), dtype=np.float32)
    X[0, 0, 0, B8], X[0, 0, 0, B4] = 0.5, 0.1
    n = ndvi(X)
    assert n[0, 0, 0] == pytest.approx((0.5 - 0.1) / (0.5 + 0.1), rel=1e-6)
    assert n[0, 1, 1] == 0


def test_tabular_shape():
    f = tabular(np.random.default_rng(0).random((3, 4, 4, 10), dtype=np.float32), np.array(["a", "b", "c"]))
    assert f.shape == (3, 22) and list(f.index) == ["a", "b", "c"]
