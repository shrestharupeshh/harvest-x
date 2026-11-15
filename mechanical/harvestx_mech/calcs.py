"""Closed-form engineering calculations. SI units. Every result is an ESTIMATE."""

from __future__ import annotations

import math
from dataclasses import dataclass

G = 9.80665


# ------------------------------------------------------------------ sections / beams
def rect_tube_I(b: float, h: float, t: float) -> float:
    """Second moment of area of a hollow rectangle about the axis parallel to b."""
    return (b * h**3 - (b - 2 * t) * (h - 2 * t) ** 3) / 12.0


def rect_I(b: float, h: float) -> float:
    return b * h**3 / 12.0


def cantilever_tip_deflection(F: float, L: float, E: float, I: float) -> float:
    return F * L**3 / (3 * E * I)


def simply_supported_center_deflection(F: float, L: float, E: float, I: float) -> float:
    return F * L**3 / (48 * E * I)


def bending_stress(M: float, c: float, I: float) -> float:
    return M * c / I


def square_tube_J(b: float, t: float) -> float:
    """Torsion constant of a thin-walled square tube (Bredt): 4 A_m^2 t / perimeter."""
    bm = b - t
    return 4 * (bm * bm) ** 2 * t / (4 * bm)


def twist_angle(T: float, L: float, G_mod: float, J: float) -> float:
    return T * L / (G_mod * J)


# ------------------------------------------------------------------ cutting
def stem_cut_force(d_stem: float, tau: float, slicing_factor: float = 1.0) -> float:
    """Upper-bound blade force to shear a round stem: tau * area * slicing_factor.

    ``slicing_factor`` < 1 models the reduction obtained with a drawn (sliding) cut.
    """
    return tau * math.pi * d_stem**2 / 4 * slicing_factor


def blade_torque(F_cut: float, radius: float, sf: float) -> float:
    return F_cut * radius * sf


# ------------------------------------------------------------------ linear axes
@dataclass
class AxisResult:
    thrust_n: float
    torque_nm: float
    motor_rpm: float
    peak_power_w: float
    holding_torque_nm: float


def axis_requirements(mass: float, a: float, v: float, vertical: bool, mu: float, drive: dict,
                      sf: float) -> AxisResult:
    """Thrust, motor torque (incl. safety factor), speed and peak mechanical power."""
    grav = mass * G if vertical else 0.0
    thrust = mass * a + grav + mu * mass * G * (0.0 if vertical else 1.0)
    if drive["type"] == "belt":
        r = drive["pulley_radius_m"]
        torque, rpm, hold = thrust * r / drive["efficiency"], v / r * 60 / (2 * math.pi), grav * r
    elif drive["type"] == "screw":
        lead = drive["lead_m"]
        torque = thrust * lead / (2 * math.pi * drive["efficiency"])
        rpm, hold = v / lead * 60, grav * lead / (2 * math.pi)
    else:
        raise ValueError(drive["type"])
    return AxisResult(thrust, torque * sf, rpm, thrust * v, hold)


def trapezoid_time(dist: float, v: float, a: float) -> float:
    """Duration of a rest-to-rest move with trapezoidal (or triangular) velocity profile."""
    dist = abs(dist)
    if dist <= 0:
        return 0.0
    d_acc = v**2 / a
    if dist < d_acc:
        return 2 * math.sqrt(dist / a)
    return dist / v + v / a


# ------------------------------------------------------------------ fasteners
STRESS_AREA_M2 = {"M4": 8.78e-6, "M5": 14.2e-6, "M6": 20.1e-6, "M8": 36.6e-6}  # ISO 898-1


def bolt_circle_max_tension(M: float, F_axial: float, n: int, pcd: float) -> float:
    """Max bolt tension for n bolts on a pitch circle under moment M and axial pull.

    Conservative rigid-flange model pivoting about the circle centre:
    T_max = F/n + 2 M / (n * r).
    """
    return F_axial / n + 2 * M / (n * (pcd / 2))


def bolt_safety_factor(tension: float, size: str, proof: float) -> float:
    return proof * STRESS_AREA_M2[size] / tension if tension > 0 else math.inf


# ------------------------------------------------------------------ capture probability
def capture_probability(half_width: float, sigma: float) -> float:
    """P(|lateral error| < half_width) for a zero-mean Gaussian lateral error."""
    return math.erf(half_width / (sigma * math.sqrt(2)))
