"""Stem / cutting-target estimators.

The stem of a rosette lettuce is hidden under the canopy when viewed from above, so
every estimator here returns a *plausible* cutting target inferred from indirect
evidence. None of them returns a *verified* target; verification requires a second,
close-range observation of the stem itself (planned: wrist camera, see
``research/research_questions.md`` RQ-B/RQ-D).

All estimators return a 3D point in the camera frame lying on the cutting plane
(tray plane shifted by ``cut_height`` towards the camera).

Methods
-------
``centroid``     Ray through the mask centroid, intersected with the cutting plane.
                 (RGB + calibrated tray plane.)
``dt_peak``      Ray through the distance-transform maximum of the mask. (RGB.)
``centroid_3d``  3D centroid of all valid canopy points, dropped along the plane
                 normal onto the cutting plane (removes the parallax bias of
                 ``centroid``). (RGB-D.)
``height_apex``  3D centroid of the highest canopy points, dropped along the plane
                 normal onto the cutting plane. (RGB-D.)
``site_prior``   Known net-pot hole position from fixture geometry. (No vision.)
``fusion``       Inverse-variance fusion of one vision estimate and ``site_prior``.
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from ..camera import CameraIntrinsics
from .geometry import project_to_plane, ray_plane_intersection

VISION_METHODS = ("centroid", "dt_peak", "centroid_3d", "height_apex")
METHODS = (*VISION_METHODS, "site_prior", "fusion")
# Methods whose error scales with canopy size; the others have a constant sigma.
SIZE_SCALED = VISION_METHODS


def estimate_stem(
    method: str,
    mask: np.ndarray,
    intr: CameraIntrinsics,
    plane_n: np.ndarray,
    plane_d: float,
    cut_height: float,
    points: np.ndarray | None = None,
    height: np.ndarray | None = None,
    site_cam: np.ndarray | None = None,
) -> np.ndarray | None:
    """Return the estimated cutting target (3,) in the camera frame, or None."""
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    if method == "centroid":
        uv = np.array([[xs.mean(), ys.mean()]])
        return ray_plane_intersection(uv, intr, plane_n, plane_d, cut_height)[0]
    if method == "dt_peak":
        y0, x0 = max(ys.min() - 1, 0), max(xs.min() - 1, 0)
        sub = np.pad(mask[y0 : ys.max() + 2, x0 : xs.max() + 2], 1)
        dist = ndi.gaussian_filter(ndi.distance_transform_edt(sub), 2.0)
        r, c = np.unravel_index(np.argmax(dist), dist.shape)
        uv = np.array([[c - 1 + x0, r - 1 + y0]], float)
        return ray_plane_intersection(uv, intr, plane_n, plane_d, cut_height)[0]
    if method == "centroid_3d":
        if points is None:
            return None
        p = points[ys, xs]
        p = p[np.isfinite(p).all(axis=1)]
        if len(p) < 20:
            return None
        return project_to_plane(p.mean(axis=0)[None], plane_n, plane_d, cut_height)[0]
    if method == "height_apex":
        if points is None or height is None:
            return None
        h = height[ys, xs]
        valid = np.isfinite(h)
        if valid.sum() < 20:
            return None
        hv = h[valid]
        top = hv >= np.percentile(hv, 85)
        p = points[ys[valid][top], xs[valid][top]]
        w = hv[top] - hv[top].min() + 1e-4
        apex = (p * w[:, None]).sum(axis=0) / w.sum()
        return project_to_plane(apex[None], plane_n, plane_d, cut_height)[0]
    if method == "site_prior":
        if site_cam is None:
            return None
        return project_to_plane(site_cam[None], plane_n, plane_d, cut_height)[0]
    raise ValueError(f"unknown stem method {method!r}")


def fuse(estimates: list[tuple[np.ndarray, float]]) -> tuple[np.ndarray, float]:
    """Inverse-variance fusion of (point, sigma) pairs with isotropic in-plane sigma."""
    w = np.array([1.0 / max(s, 1e-6) ** 2 for _, s in estimates])
    pts = np.stack([p for p, _ in estimates])
    return (pts * w[:, None]).sum(axis=0) / w.sum(), float(1.0 / np.sqrt(w.sum()))


def capture_confidence(sigma: float, tolerance: float) -> float:
    """P(|error| < tolerance) for an isotropic 2D Gaussian (Rayleigh CDF)."""
    return float(1.0 - np.exp(-(tolerance**2) / (2.0 * max(sigma, 1e-9) ** 2)))
