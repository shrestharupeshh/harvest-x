import pytest

from harvestx_harvest import study


@pytest.mark.slow
def test_integrated_harvest_study_small():
    r = study.run(n_trays=25, seed=3)
    assert r["data_kind"] == "SIMULATED" and r["attempts"] > 0
    t = r["table"]
    gated = t["25|fusion + stem sensor + lateral retry"]
    assert gated["blind_cut"] == 0  # the sensor gate makes blind cuts impossible
    assert gated["harvested"] >= t["5|fusion + stem sensor, no retry"]["harvested"]
    # wider throat never captures fewer stems
    assert t["25|fusion, open loop"]["harvested"] >= t["5|fusion, open loop"]["harvested"]
    assert "SIMULATED" in study.to_markdown(r).splitlines()[1]
