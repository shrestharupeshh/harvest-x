import numpy as np
import pytest

from harvestx_harvest.machine import (
    HarvestConfig,
    HarvestMachine,
    Outcome,
    SimGantry,
    SimTool,
)

SITE = np.array([0.45, -0.12, 0.10])


def run(cfg, target=SITE, stem=SITE, channel_y=-0.12, estop=False):
    m = HarvestMachine(cfg, SimGantry(cfg), SimTool(cfg))
    m.estop = estop
    return m.harvest("P1", target, stem, channel_y, 0.10), m


def test_default_is_dry_run_and_never_cuts():
    rec, _ = run(HarvestConfig())
    assert rec.outcome is Outcome.DRY_RUN
    assert "CUT" not in rec.states and rec.verified


def test_armed_harvest_sequence_and_duration():
    rec, m = run(HarvestConfig(cut_armed=True))
    assert rec.outcome is Outcome.HARVESTED
    assert rec.states == ["PLAN", "APPROACH", "SEAT", "VERIFY_TARGET", "CUT", "VERIFY", "COLLECT",
                          "LOG"]
    assert 5 < rec.duration_s < 30
    assert not m.tool.holding  # released at the tray


def test_lateral_error_inside_throat_is_captured_outside_is_not():
    cfg = HarvestConfig(cut_armed=True, max_seat_attempts=1)
    ok, _ = run(cfg, stem=SITE + [0.020, 0, 0])
    assert ok.outcome is Outcome.HARVESTED
    miss, _ = run(cfg, stem=SITE + [0.040, 0, 0])
    assert miss.outcome is Outcome.MISSED and "CUT" not in miss.states


def test_retry_with_lateral_offset_recovers_a_miss():
    cfg = HarvestConfig(cut_armed=True, max_seat_attempts=3)
    rec, _ = run(cfg, stem=SITE + [0.040, 0, 0])
    assert rec.outcome is Outcome.HARVESTED and rec.seat_attempts == 2


def test_without_sensor_gate_a_miss_becomes_a_blind_cut():
    cfg = HarvestConfig(cut_armed=True, sensor_gate=False)
    rec, _ = run(cfg, stem=SITE + [0.060, 0, 0])
    assert rec.outcome is Outcome.BLIND_CUT and not rec.verified


def test_estop_aborts_before_any_motion():
    rec, m = run(HarvestConfig(cut_armed=True), estop=True)
    assert rec.outcome is Outcome.FAULT and rec.states == ["PLAN", "FAULT"]
    assert np.allclose(m.gantry.pos, [0, 0, 0.40])


def test_unreachable_target_is_refused():
    rec, _ = run(HarvestConfig(cut_armed=True), target=SITE + [2.0, 0, 0], stem=SITE + [2.0, 0, 0])
    assert rec.outcome is Outcome.UNREACHABLE


def test_second_channel_is_approached_from_the_other_flank():
    cfg = HarvestConfig(cut_armed=True)
    site = np.array([0.45, 0.12, 0.10])
    rec, m = run(cfg, target=site, stem=site, channel_y=0.12)
    assert rec.outcome is Outcome.HARVESTED
    assert np.isclose(m.gantry.yaw, np.pi)


def test_gantry_limits():
    cfg = HarvestConfig()
    g = SimGantry(cfg)
    assert g.move([0.5, 0.0, 0.40]) > 0
    with pytest.raises(ValueError):
        g.move([5.0, 0, 0.4])
