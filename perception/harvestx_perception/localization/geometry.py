"""Plane fitting, ray-plane intersection and covariance helpers (camera frame)."""

from __future__ import annotations

import numpy as np

from ..camera import CameraIntrinsics


def depth_to_points(depth: np.ndarray, intr: CameraIntrinsics) -> np.ndarray:
    """HxW depth -> HxWx3 camera-frame points (invalid pixels become NaN)."""
    rays = intr.ray_grid()
    d = np.where(depth > 0, depth, np.nan)
    return rays * d[..., None]


def fit_plane_ransac(
    pts: np.ndarray,
    rng: np.random.Generator | None = None,
    n_iter: int = 200,
    inlier_tol: float = 0.004,
    max_points: int = 6000,
) -> tuple[np.ndarray, float, float]:
    """Fit dominant plane ``n·p + d = 0`` to Nx3 points.

    Returns (n, d, inlier_fraction). The normal is oriented towards the camera origin
    so that ``n·p + d`` is the height of a point above the plane (towards the camera).
    """
    rng = rng or np.random.default_rng(0)
    pts = pts[np.isfinite(pts).all(axis=1)]
    if len(pts) < 50:
        raise ValueError("not enough valid depth points to fit a plane")
    if len(pts) > max_points:
        pts = pts[rng.choice(len(pts), max_points, replace=False)]
    best_inl, best = 0, None
    for _ in range(n_iter):
        a, b, c = pts[rng.choice(len(pts), 3, replace=False)]
        n = np.cross(b - a, c - a)
        nn = np.linalg.norm(n)
        if nn < 1e-12:
            continue
        n /= nn
        inl = np.abs((pts - a) @ n) < inlier_tol
        if inl.sum() > best_inl:
            best_inl, best = int(inl.sum()), inl
    if best is None:
        raise ValueError("plane RANSAC failed")
    sel = pts[best]
    centroid = sel.mean(axis=0)
    _, _, vt = np.linalg.svd(sel - centroid, full_matrices=False)
    n = vt[-1]
    d = -float(n @ centroid)
    if d < 0:  # camera origin must be on the positive side
        n, d = -n, -d
    return n, d, best_inl / len(pts)


def ray_plane_intersection(
    uv: np.ndarray, intr: CameraIntrinsics, n: np.ndarray, d: float, offset: float = 0.0
) -> np.ndarray:
    """Intersect pixel rays with the plane shifted ``offset`` metres towards the camera."""
    uv = np.atleast_2d(uv)
    rays = np.stack(
        [(uv[:, 0] - intr.cx) / intr.fx, (uv[:, 1] - intr.cy) / intr.fy, np.ones(len(uv))], axis=1
    )
    t = -(d - offset) / (rays @ n)
    return rays * t[:, None]


def project_to_plane(p: np.ndarray, n: np.ndarray, d: float, offset: float = 0.0) -> np.ndarray:
    """Orthogonally project points onto the plane shifted by ``offset`` towards the camera."""
    p = np.atleast_2d(p)
    h = p @ n + d - offset
    return p - h[:, None] * n[None, :]


def in_plane_covariance(sigma: float, n: np.ndarray, sigma_normal: float = 0.0) -> np.ndarray:
    """Isotropic in-plane Gaussian covariance (3x3) with optional normal component."""
    P = np.eye(3) - np.outer(n, n)
    return sigma**2 * P + sigma_normal**2 * np.outer(n, n)


def extrinsic_covariance(p_cam: np.ndarray, sigma_t: float, sigma_rot: float) -> np.ndarray:
    """First-order covariance added by camera-to-base calibration uncertainty.

    ``sigma_t`` [m] isotropic translation std, ``sigma_rot`` [rad] isotropic small-angle
    rotation std. Expressed in the camera frame (rotate with R_base_cam afterwards).
    """
    r2 = float(p_cam @ p_cam)
    return sigma_t**2 * np.eye(3) + sigma_rot**2 * (r2 * np.eye(3) - np.outer(p_cam, p_cam))
