from pathlib import Path

import numpy as np
import yaml

import trade_study as ts

CFG = Path(__file__).resolve().parents[2] / "docs/architecture/trade_study.yaml"


def test_weighted_scores_normalises_weights():
    s = np.array([[5, 1], [1, 5]])
    assert np.allclose(ts.weighted_scores(s, [1, 1]), [3, 3])
    assert np.allclose(ts.weighted_scores(s, [30, 10]), [4, 2])


def test_sensitivity_sums_to_one_and_prefers_dominant_option():
    s = np.array([[5, 1], [5, 1], [5, 2]])
    win = ts.sensitivity(s, [1, 1, 1], n=500)
    assert np.isclose(win.sum(), 1)
    assert win[0] > 0.99


def test_project_config_is_well_formed_and_report_builds():
    cfg = yaml.safe_load(CFG.read_text())
    n = len(cfg["architectures"])
    assert n == 3
    for c, v in cfg["criteria"].items():
        assert len(v) == n and all(1 <= x <= 5 for x in v), c
    for prof in cfg["profiles"].values():
        assert set(prof) == set(cfg["criteria"])
    report = ts.build_report(cfg)
    assert "research_prototype" in report and "production_scaling" in report
