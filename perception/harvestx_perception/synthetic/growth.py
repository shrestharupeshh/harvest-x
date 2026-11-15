"""Latent lettuce growth model used ONLY to drive the synthetic data generator.

IMPORTANT: every numeric parameter in this file is an *assumed prior* chosen to give
plausible-looking hydroponic lettuce geometry. They are not fitted to measurements and
must be replaced by parameters estimated from real plants (see
``data/data_collection_protocol.md``) before any agronomic conclusion is drawn.

Design intent: maturity labels are defined from the latent *fresh mass* (what a grower
actually sells), not from appearance. Appearance (diameter, height, leaf count) is a
noisy function of mass, so a vision model cannot trivially recover the label.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

MATURITY_CLASSES = ["early", "developing", "near_harvest", "harvest_ready", "overgrown"]

# Fresh-mass class boundaries in grams (assumed; a real protocol sets these per cultivar).
MASS_BOUNDS_G = (15.0, 70.0, 120.0, 200.0)


@dataclass(frozen=True)
class Cultivar:
    name: str
    base_rgb: tuple[float, float, float]
    inner_rgb: tuple[float, float, float]
    width_ratio: float  # leaf width / length
    elev_offset_deg: float  # added to leaf elevation (upright types > 0)
    diameter_coeff: float  # D[mm] = coeff * mass[g]^0.33
    m_max_g: float


CULTIVARS: dict[str, Cultivar] = {
    "butterhead": Cultivar(
        "butterhead", (0.36, 0.62, 0.20), (0.62, 0.80, 0.34), 0.85, 0.0, 48.0, 230.0
    ),
    "green_oakleaf": Cultivar(
        "green_oakleaf", (0.30, 0.58, 0.16), (0.55, 0.76, 0.28), 0.60, 5.0, 52.0, 210.0
    ),
    "romaine": Cultivar("romaine", (0.22, 0.50, 0.14), (0.50, 0.72, 0.26), 0.45, 18.0, 40.0, 260.0),
    "red_leaf": Cultivar(
        "red_leaf", (0.42, 0.16, 0.20), (0.50, 0.62, 0.24), 0.70, 3.0, 50.0, 200.0
    ),
}


@dataclass
class PlantState:
    cultivar: str
    age_days: float
    fresh_mass_g: float
    diameter_m: float
    nominal_height_m: float
    leaf_count: int
    bolting: bool
    maturity: str


def maturity_from_mass(mass_g: float, bolting: bool = False) -> str:
    if bolting:
        return "overgrown"
    idx = int(np.searchsorted(MASS_BOUNDS_G, mass_g, side="right"))
    return MATURITY_CLASSES[idx]


def sample_plant(rng: np.random.Generator, cultivar: str, age_days: float) -> PlantState:
    c = CULTIVARS[cultivar]
    vigor = rng.lognormal(0.0, 0.18)  # plant-to-plant variation
    mass = vigor * c.m_max_g / (1.0 + np.exp(-0.20 * (age_days - 26.0)))
    mass = float(max(mass, 0.8))
    diameter = c.diameter_coeff * mass**0.33 * rng.normal(1.0, 0.07) / 1000.0
    bolting = bool(age_days > 40 and rng.random() < 0.25)
    height = 0.42 * diameter * rng.normal(1.0, 0.10) * (1.6 if bolting else 1.0)
    leaf_count = int(round(4 + 3.2 * mass**0.4 * rng.normal(1.0, 0.08)))
    return PlantState(
        cultivar=cultivar,
        age_days=float(age_days),
        fresh_mass_g=mass,
        diameter_m=float(max(diameter, 0.02)),
        nominal_height_m=float(max(height, 0.01)),
        leaf_count=max(leaf_count, 4),
        bolting=bolting,
        maturity=maturity_from_mass(mass, bolting),
    )
