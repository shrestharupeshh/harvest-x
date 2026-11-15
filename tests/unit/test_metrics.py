import numpy as np
from harvestx_perception.evaluation.metrics import (
    average_precision,
    cluster_bootstrap_ci,
    expected_calibration_error,
    iou_matrix,
    match_instances,
    prf,
)


def _labels():
    gt = np.zeros((20, 20), int)
    gt[2:8, 2:8] = 1
    gt[12:18, 12:18] = 2
    return gt


def test_iou_and_matching():
    gt = _labels()
    pred = np.zeros_like(gt)
    pred[2:8, 2:8] = 7  # perfect
    pred[12:18, 15:20] = 9  # partial: inter 18, union 36+30-18
    iou, g, p = iou_matrix(gt, pred)
    assert iou.shape == (2, 2)
    assert np.isclose(iou[0, 0], 1.0)
    assert np.isclose(iou[1, 1], 18 / 48)
    assert len(match_instances(iou, 0.5)) == 1
    assert len(match_instances(iou, 0.3)) == 2
    assert match_instances(np.zeros((0, 3))) == []


def test_prf_and_ap():
    assert np.allclose(list(prf(8, 2, 2).values()), 0.8)
    assert prf(0, 0, 0)["f1"] == 0.0
    assert np.isclose(average_precision([0.9, 0.8, 0.7], [True, True, True], 3), 1.0)
    # one FP ranked first: precision envelope 2/3 over the full recall range
    assert np.isclose(average_precision([0.9, 0.8, 0.7], [False, True, True], 2), 2 / 3)
    assert average_precision([], [], 3) == 0.0


def test_ece():
    assert np.isclose(expected_calibration_error(np.full(100, 0.8), np.r_[np.ones(80), np.zeros(20)]), 0)
    assert np.isclose(expected_calibration_error(np.ones(10), np.zeros(10)), 1.0)


def test_cluster_bootstrap_is_wider_than_naive():
    rng = np.random.default_rng(0)
    groups = np.repeat(np.arange(10), 50)
    x = np.repeat(rng.normal(0, 1, 10), 50) + rng.normal(0, 0.05, 500)  # strong clustering
    lo, hi = cluster_bootstrap_ci(groups, lambda i: float(x[i].mean()), 400)
    naive = 2 * 1.96 * x.std() / np.sqrt(len(x))
    assert lo < x.mean() < hi
    assert (hi - lo) > 3 * naive
