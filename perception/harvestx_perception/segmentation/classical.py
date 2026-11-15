"""Classical (training-free) plant segmentation baselines.

Semantic step (plant vs background)
    ``exg``    Excess-green index + Otsu threshold (RGB only).
    ``depth``  Height above the fitted tray plane (depth only).
    ``fusion`` Union of both, i.e. "green OR raised".

Instance step
    Marker-controlled watershed. Markers are either found automatically from the
    distance transform (and height map when available) or seeded from the *known*
    plant-site positions of the growing fixture (``site_px``).

These are the measurable baselines against which learned detectors/segmenters
(YOLO-seg, Mask R-CNN, ...) must later be compared.
"""

from __future__ import annotations

import cv2
import numpy as np
from scipy import ndimage as ndi
from skimage.feature import peak_local_max
from skimage.segmentation import watershed


def excess_green(rgb: np.ndarray) -> np.ndarray:
    f = rgb.astype(np.float32)
    s = f.sum(axis=2) + 1e-6
    r, g, b = f[..., 0] / s, f[..., 1] / s, f[..., 2] / s
    return 2 * g - r - b


def _clean(mask: np.ndarray, min_area: int) -> np.ndarray:
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    m = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_OPEN, k)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    keep = np.zeros(n, bool)
    keep[1:] = stats[1:, cv2.CC_STAT_AREA] >= min_area
    return keep[lab]


def semantic_mask(
    rgb: np.ndarray,
    height: np.ndarray | None = None,
    method: str = "fusion",
    min_area: int = 150,
    height_thresh: float = 0.007,
    exg_floor: float = 0.05,
) -> np.ndarray:
    """Binary plant mask. ``height`` is HxW height above the tray plane (NaN = invalid)."""
    masks = []
    if method in ("exg", "fusion"):
        exg = excess_green(rgb)
        scaled = np.uint8(np.clip((exg + 1) / 3 * 255, 0, 255))
        thr, _ = cv2.threshold(scaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        thr = max(thr / 255 * 3 - 1, exg_floor)  # never accept "not green at all"
        masks.append(exg > thr)
    if method in ("depth", "fusion"):
        if height is None:
            if method == "depth":
                raise ValueError("depth segmentation needs a height map")
        else:
            h = np.nan_to_num(height, nan=0.0)
            masks.append(cv2.medianBlur(h.astype(np.float32), 5) > height_thresh)
    if not masks:
        raise ValueError(f"unknown method {method!r}")
    m = masks[0]
    for other in masks[1:]:
        m = m | other
    return _clean(m, min_area)


def instance_segmentation(
    mask: np.ndarray,
    height: np.ndarray | None = None,
    site_px: np.ndarray | None = None,
    min_distance: int = 28,
    min_area: int = 150,
) -> np.ndarray:
    """Split a binary plant mask into instances. Returns int32 label image (0 = bg).

    With ``site_px`` (Nx2 pixel positions of known plant sites) the label value of a
    plant equals ``site index + 1``; otherwise labels are arbitrary.
    """
    if not mask.any():
        return np.zeros(mask.shape, np.int32)
    dist = ndi.distance_transform_edt(mask)
    land = cv2.GaussianBlur(dist.astype(np.float32), (0, 0), 3)
    if height is not None:
        h = cv2.GaussianBlur(np.nan_to_num(height, nan=0.0).astype(np.float32), (0, 0), 4)
        if h.max() > 0 and land.max() > 0:
            # canopy domes: combine "far from edge" and "high above tray"
            land = land / land.max() + h / h.max()
    markers = np.zeros(mask.shape, np.int32)
    if site_px is not None:
        H, W = mask.shape
        for i, (u, v) in enumerate(np.asarray(site_px)):
            ui, vi = int(round(u)), int(round(v))
            if 0 <= ui < W and 0 <= vi < H:
                cv2.circle(markers, (ui, vi), 6, i + 1, -1)
        markers[~mask] = 0
        # sites whose marker fell entirely on background are empty sites
    else:
        peaks = peak_local_max(land, min_distance=min_distance, labels=mask.astype(int),
                               exclude_border=False)
        for i, (r, c) in enumerate(peaks, start=1):
            markers[r, c] = i
    if markers.max() == 0:
        return np.zeros(mask.shape, np.int32)
    labels = watershed(-land, markers, mask=mask).astype(np.int32)
    for lab in np.unique(labels):
        if lab and (labels == lab).sum() < min_area:
            labels[labels == lab] = 0
    return labels
