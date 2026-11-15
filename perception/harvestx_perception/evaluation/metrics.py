"""Evaluation metrics: instance matching, detection PR/AP, calibration, cluster bootstrap."""

from __future__ import annotations

from collections.abc import Callable, Sequence

import numpy as np
from scipy.optimize import linear_sum_assignment


def iou_matrix(gt: np.ndarray, pred: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Mask IoU between all GT and predicted instances of two label images.

    Returns (iou [G x P], gt_ids, pred_ids).
    """
    g_ids = np.array([v for v in np.unique(gt) if v])
    p_ids = np.array([v for v in np.unique(pred) if v])
    iou = np.zeros((len(g_ids), len(p_ids)))
    for i, g in enumerate(g_ids):
        gm = gt == g
        ga = gm.sum()
        for j in np.unique(pred[gm]):
            if j == 0:
                continue
            jj = int(np.nonzero(p_ids == j)[0][0])
            inter = (gm & (pred == j)).sum()
            iou[i, jj] = inter / (ga + (pred == j).sum() - inter)
    return iou, g_ids, p_ids


def match_instances(iou: np.ndarray, thresh: float = 0.5) -> list[tuple[int, int, float]]:
    """One-to-one Hungarian matching; returns (gt_idx, pred_idx, iou) with iou >= thresh."""
    if iou.size == 0:
        return []
    r, c = linear_sum_assignment(-iou)
    return [(int(i), int(j), float(iou[i, j])) for i, j in zip(r, c) if iou[i, j] >= thresh]


def prf(tp: int, fp: int, fn: int) -> dict[str, float]:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return {"precision": p, "recall": r, "f1": f}


def average_precision(scores: Sequence[float], is_tp: Sequence[bool], n_gt: int) -> float:
    """All-point interpolated AP (PASCAL VOC 2010+ / COCO style) for one class."""
    if n_gt == 0 or len(scores) == 0:
        return 0.0
    order = np.argsort(-np.asarray(scores))
    tp = np.asarray(is_tp, float)[order]
    ctp, cfp = np.cumsum(tp), np.cumsum(1 - tp)
    rec = np.concatenate([[0.0], ctp / n_gt, [1.0]])
    prec = np.concatenate([[1.0], ctp / np.maximum(ctp + cfp, 1e-12), [0.0]])
    prec = np.maximum.accumulate(prec[::-1])[::-1]
    idx = np.nonzero(rec[1:] != rec[:-1])[0]
    return float(((rec[idx + 1] - rec[idx]) * prec[idx + 1]).sum())


def expected_calibration_error(conf: np.ndarray, correct: np.ndarray, n_bins: int = 10) -> float:
    conf, correct = np.asarray(conf, float), np.asarray(correct, float)
    if len(conf) == 0:
        return float("nan")
    bins = np.minimum((conf * n_bins).astype(int), n_bins - 1)
    ece = 0.0
    for b in range(n_bins):
        m = bins == b
        if m.any():
            ece += m.mean() * abs(correct[m].mean() - conf[m].mean())
    return float(ece)


def cluster_bootstrap_ci(
    groups: np.ndarray,
    stat: Callable[[np.ndarray], float],
    n_boot: int = 1000,
    alpha: float = 0.05,
    seed: int = 0,
) -> tuple[float, float]:
    """Percentile CI of ``stat(row_indices)`` resampling whole groups with replacement.

    Rows that share a group (same tray / same physical plants imaged repeatedly) are
    not independent, so the resampling unit is the group, not the row.
    """
    groups = np.asarray(groups)
    uniq = np.unique(groups)
    idx_by = {g: np.nonzero(groups == g)[0] for g in uniq}
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_boot):
        pick = rng.choice(uniq, len(uniq), replace=True)
        vals.append(stat(np.concatenate([idx_by[g] for g in pick])))
    lo, hi = np.nanpercentile(vals, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(lo), float(hi)
