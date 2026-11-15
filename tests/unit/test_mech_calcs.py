import math

import pytest

from harvestx_mech import calcs as c
from harvestx_mech.params import load_params
from harvestx_mech.report import design_case, write_markdown


def test_section_properties():
    assert math.isclose(c.rect_I(0.02, 0.01), 0.02 * 0.01**3 / 12)
    solid = c.rect_I(0.04, 0.08)
    assert c.rect_tube_I(0.04, 0.08, 0.003) < solid
    assert math.isclose(c.rect_tube_I(0.04, 0.08, 0.02), solid)  # walls meet -> solid
    # thin-wall square tube: J -> b^3 t for t << b
    assert math.isclose(c.square_tube_J(0.1, 1e-4), 0.1**3 * 1e-4, rel_tol=0.01)


def test_beam_formulas_against_hand_values():
    # steel cantilever 1 m, I = 1e-6 m^4, 1 kN: 1000 / (3 * 200e9 * 1e-6) = 1.667 mm
    assert math.isclose(c.cantilever_tip_deflection(1000, 1.0, 200e9, 1e-6), 1.6667e-3, rel_tol=1e-4)
    assert math.isclose(c.simply_supported_center_deflection(1000, 1.0, 200e9, 1e-6),
                        1000 / (48 * 200e9 * 1e-6))
    assert math.isclose(c.bending_stress(100, 0.01, 1e-8), 1e8)


def test_cutting_force_scales_with_area_and_slicing():
    f = c.stem_cut_force(0.02, 0.35e6)
    assert math.isclose(f, 0.35e6 * math.pi * 1e-4, rel_tol=1e-9)
    assert math.isclose(c.stem_cut_force(0.01, 0.35e6), f / 4)
    assert c.stem_cut_force(0.02, 0.35e6, 0.3) < f


def test_axis_requirements():
    belt = dict(type="belt", pulley_radius_m=0.015, efficiency=1.0)
    h = c.axis_requirements(10, 2.0, 0.5, False, 0.0, belt, 1.0)
    assert math.isclose(h.thrust_n, 20) and math.isclose(h.torque_nm, 0.3)
    assert h.holding_torque_nm == 0
    screw = dict(type="screw", lead_m=0.01, efficiency=1.0)
    v = c.axis_requirements(10, 0.0, 0.25, True, 0.0, screw, 2.0)
    assert math.isclose(v.thrust_n, 10 * c.G)
    assert math.isclose(v.torque_nm, 2 * 10 * c.G * 0.01 / (2 * math.pi))
    assert math.isclose(v.motor_rpm, 1500)
    assert v.holding_torque_nm > 0
    with pytest.raises(ValueError):
        c.axis_requirements(1, 1, 1, False, 0, dict(type="rack"), 1)


def test_trapezoid_time():
    assert c.trapezoid_time(0, 1, 1) == 0
    assert math.isclose(c.trapezoid_time(0.25, 1.0, 1.0), 1.0)  # triangular: 2*sqrt(d/a)
    assert math.isclose(c.trapezoid_time(2.0, 1.0, 1.0), 3.0)  # d/v + v/a


def test_bolts_and_capture():
    t = c.bolt_circle_max_tension(10.0, 0.0, 4, 0.05)
    assert math.isclose(t, 2 * 10 / (4 * 0.025))
    assert c.bolt_safety_factor(t, "M6", 450e6) > c.bolt_safety_factor(t, "M4", 450e6)
    assert math.isclose(c.capture_probability(0.01, 0.01), math.erf(1 / math.sqrt(2)))
    assert c.capture_probability(0.025, 0.006) > 0.999


def test_design_case_meets_declared_safety_factors():
    p = load_params()
    r = design_case(p)
    sf = p["safety_factors"]["structure_yield"]
    for key in ("blade", "tine", "boom", "bridge", "tool_stiffness"):
        assert r[key]["fos_yield"] >= sf, key
    assert r["flange_bolts"]["fos_proof"] >= sf
    assert r["axes"]["z"]["holding_torque_nm"] > 0
    assert 5 < r["cycle"]["total_s"] < 30
    md = write_markdown(p, r, "test")
    assert "ESTIMATED" in md.splitlines()[1]


def test_params_coerce_scientific_notation():
    p = load_params()
    assert isinstance(p["materials"]["al6061_t6"]["E_pa"], float)
    assert p["crop"]["cultivar_type"] == "butterhead"
