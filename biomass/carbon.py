"""Biomass to stored carbon dioxide, with every assumption as an explicit parameter."""

CO2_PER_C = 44 / 12  # molar mass ratio CO2 : C


def tco2_per_patch(agb_t_per_ha: float, carbon_fraction: float = 0.47, area_ha: float = 655.36,
                   root_to_shoot: float = 0.0) -> float:
    """Tonnes of CO2 stored in one patch given its mean above-ground biomass.

    Default is above-ground only (root_to_shoot=0). IPCC's default carbon
    fraction of dry biomass is 0.47; a 2.56 km square is 655.36 ha.
    """
    return agb_t_per_ha * (1 + root_to_shoot) * carbon_fraction * CO2_PER_C * area_ha
