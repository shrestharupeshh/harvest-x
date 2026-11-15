"""CAD regression checks. Skipped when CadQuery is not installed."""
import pytest

cq = pytest.importorskip("cadquery")

from harvestx_cad import end_effector as ee  # noqa: E402
from harvestx_cad import rack  # noqa: E402
from harvestx_mech.params import load_params  # noqa: E402


@pytest.fixture(scope="module")
def model():
    p = load_params()
    return p, ee.dims(p), ee.build(p)


def test_all_parts_are_valid_solids(model):
    _, _, parts = model
    assert set(parts) == set(ee.PARTS)
    for name, s in parts.items():
        assert s.val().isValid(), name
        assert s.val().Volume() > 0, name


def test_no_interference_open_or_closed(model):
    _, d, parts = model
    assert ee.interference_volumes(parts) == {}
    closed = {k: v for k, v in parts.items() if k != "pull_rod"}
    closed["blade"] = ee.blade(d, -d["blade_sweep_deg"])
    assert ee.interference_volumes(closed) == {}


def test_functional_geometry(model):
    p, d, parts = model
    assert ee.blade_reaches_stem(d)
    # slot admits the largest stem; throat is wider than the slot
    assert d["slot_width_m"] >= p["crop"]["stem_diameter_max_m"] * 1000
    assert d["throat_entry_width_m"] > 2 * d["slot_width_m"]
    # everything that goes under the canopy is low; shank and actuator stay outside it
    assert ee.head_height(d) <= 25
    r_canopy = p["crop"]["canopy_diameter_max_m"] * 1000 / 2
    for name in ("shank", "flange", "actuator_envelope"):
        assert parts[name].val().BoundingBox().xmax <= -r_canopy, name
    # skids define the lowest surface (they ride on the channel)
    assert abs(parts["skids"].val().BoundingBox().zmin) < 1e-6
    # blade plane = cut height above the channel
    assert 5 <= d["z_blade"] <= 12


def test_mass_budget(model):
    p, _, parts = model
    m = ee.masses(p, parts)
    assert 0.5 < sum(m.values()) < 3.0
    assert m["fork_plate"] > m["blade"]


def test_rack_layout():
    p = load_params()
    parts = rack.build(p)
    for name, s in parts.items():
        assert s.val().Volume() > 0, name
    xs, ys = rack.channel_positions(p)
    assert len(xs) == p["rack"]["sites_per_channel"] and len(ys) == p["rack"]["n_channels"]
    # plant-free flank beside each outer channel for side entry
    r_canopy = p["crop"]["canopy_diameter_max_m"] * 1000 / 2
    need = r_canopy + p["rack"]["flank_clear_m"] * 1000
    assert ys[0] - rack.FRAME["bar"] >= need
    assert rack.FRAME["y"] - rack.FRAME["bar"] - ys[-1] >= need
    # channel top is the datum height
    assert abs(parts["channels"].val().BoundingBox().zmax - rack.CHANNEL_TOP_Z) < 1e-6
