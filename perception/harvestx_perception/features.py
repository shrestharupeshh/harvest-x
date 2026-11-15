"""Per-plant morphological and colour features for maturity/biomass estimation."""

from __future__ import annotations

import cv2
import numpy as np

from .segmentation.classical import excess_green

RGB_FEATURES = [
    "area_px", "eq_diameter_px", "feret_px", "solidity", "extent", "aspect",
    "h_mean", "s_mean", "v_mean", "h_std", "s_std", "v_std", "exg_mean",
    "contact_frac", "truncated",
]
# Metric features that need either depth or a calibrated tray plane.
RGBD_FEATURES = [
    "area_m2", "eq_diameter_m", "feret_m", "height_p95_m", "height_mean_m", "volume_m3",
    "depth_valid_frac",
]
ALL_FEATURES = RGB_FEATURES + RGBD_FEATURES


def instance_features(
    rgb: np.ndarray,
    labels: np.ndarray,
    label: int,
    height: np.ndarray | None = None,
    px_area_m2: np.ndarray | None = None,
    hsv: np.ndarray | None = None,
    exg: np.ndarray | None = None,
) -> dict[str, float]:
    """Compute features of one instance.

    ``px_area_m2`` is the HxW metric footprint of each pixel on the tray plane (from
    depth/plane geometry); ``height`` is height above the tray plane.
    """
    m = labels == label
    H, W = m.shape
    ys, xs = np.nonzero(m)
    area = float(len(xs))
    f: dict[str, float] = {k: float("nan") for k in ALL_FEATURES}
    if area == 0:
        return f
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV) if hsv is None else hsv
    exg = excess_green(rgb) if exg is None else exg
    cnts, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cnt = max(cnts, key=cv2.contourArea)
    hull = cv2.convexHull(cnt)
    hull_area = max(cv2.contourArea(hull), 1.0)
    (_, _), (w_r, h_r), _ = cv2.minAreaRect(cnt)
    feret = float(max(w_r, h_r))
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    f.update(
        area_px=area,
        eq_diameter_px=float(2 * np.sqrt(area / np.pi)),
        feret_px=feret,
        solidity=float(min(area / hull_area, 1.0)),
        extent=float(area / ((x1 - x0 + 1) * (y1 - y0 + 1))),
        aspect=float(min(w_r, h_r) / max(feret, 1.0)),
        exg_mean=float(exg[m].mean()),
        truncated=float(x0 <= 1 or y0 <= 1 or x1 >= W - 2 or y1 >= H - 2),
    )
    px = hsv[m].astype(np.float32)
    for i, ch in enumerate("hsv"):
        f[f"{ch}_mean"] = float(px[:, i].mean())
        f[f"{ch}_std"] = float(px[:, i].std())
    # fraction of the instance boundary that touches another plant (occlusion proxy)
    dil = cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool) & ~m
    ring = labels[dil]
    f["contact_frac"] = float((ring > 0).mean()) if ring.size else 0.0

    if px_area_m2 is not None:
        a_m2 = float(np.nansum(px_area_m2[m]))
        scale = np.sqrt(a_m2 / area)  # metres per pixel at this plant
        f.update(area_m2=a_m2, eq_diameter_m=float(2 * np.sqrt(a_m2 / np.pi)),
                 feret_m=float(feret * scale))
    if height is not None:
        h = height[m]
        valid = np.isfinite(h)
        f["depth_valid_frac"] = float(valid.mean())
        if valid.sum() > 10:
            hv = np.clip(h[valid], 0, None)
            f["height_p95_m"] = float(np.percentile(hv, 95))
            f["height_mean_m"] = float(hv.mean())
            if px_area_m2 is not None:
                f["volume_m3"] = float(np.nansum(np.clip(h, 0, None) * px_area_m2[m]))
    return f
