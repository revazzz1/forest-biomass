import pytest

from biomass.carbon import tco2_per_patch


def test_known_value_above_ground_only():
    assert tco2_per_patch(100) == pytest.approx(100 * 0.47 * 44 / 12 * 655.36)
    assert tco2_per_patch(100) == pytest.approx(112_950, rel=1e-3)


def test_root_to_shoot_scales_linearly():
    assert tco2_per_patch(100, root_to_shoot=0.25) == pytest.approx(1.25 * tco2_per_patch(100))


def test_zero_biomass_is_zero_carbon():
    assert tco2_per_patch(0) == 0
