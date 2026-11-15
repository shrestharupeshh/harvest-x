import numpy as np
import pytest
from harvestx_perception.camera import (
    CameraIntrinsics,
    invert_T,
    look_down_pose,
    plane_base_to_cam,
    transform_points,
)
from harvestx_perception.localization.geometry import (
    extrinsic_covariance,
    fit_plane_ransac,
    in_plane_covariance,
    project_to_plane,
    ray_plane_intersection,
)
from harvestx_perception.localization.stem import capture_confidence, fuse

INTR = CameraIntrinsics(600, 600, 319.5, 239.5, 640, 480)


def test_project_backproject_roundtrip():
    rng = np.random.default_rng(0)
    pts = np.column_stack([rng.uniform(-0.3, 0.3, 50), rng.uniform(-0.2, 0.2, 50),
                           rng.uniform(0.4, 1.0, 50)])
    uv, z = INTR.project(pts)
    assert np.allclose(INTR.backproject(uv, z), pts, atol=1e-12)


def test_ray_grid_matches_backproject():
    rays = INTR.ray_grid()
    assert rays.shape == (480, 640, 3)
    assert np.allclose(rays[100, 200] * 0.7, INTR.backproject(np.array([[200, 100]]), 0.7)[0])


def test_transform_inverse_and_look_down():
    T = look_down_pose([0.4, 0.1, 0.9], 0.05, -0.03, 0.2)
    assert np.allclose(T @ invert_T(T), np.eye(4), atol=1e-12)
    assert np.isclose(np.linalg.det(T[:3, :3]), 1.0)
    # optical axis points (mostly) down in the base frame
    assert T[:3, :3][2, 2] < -0.99
    p = transform_points(T, np.array([[0, 0, 0.5]]))[0]
    assert p[2] < 0.9 - 0.49


def test_plane_base_to_cam_consistent():
    T = look_down_pose([0.4, 0.0, 0.85], 0.04, 0.02)
    n, d = plane_base_to_cam(T, np.array([0, 0, 1.0]), -0.10)
    pts_base = np.array([[0.3, 0.1, 0.10], [0.5, -0.2, 0.10]])
    pts_cam = transform_points(invert_T(T), pts_base)
    assert np.allclose(pts_cam @ n + d, 0, atol=1e-12)
    assert d > 0  # camera is above the plane


def test_plane_ransac_recovers_plane_with_outliers():
    rng = np.random.default_rng(1)
    n_true = np.array([0.05, -0.03, -1.0])
    n_true /= np.linalg.norm(n_true)
    xy = rng.uniform(-0.3, 0.3, (4000, 2))
    z = (-0.75 - n_true[0] * xy[:, 0] - n_true[1] * xy[:, 1]) / n_true[2]
    pts = np.column_stack([xy, z + rng.normal(0, 0.001, 4000)])
    pts[:1200, 2] -= rng.uniform(0.02, 0.12, 1200)  # "plants" above the plane
    n, d, frac = fit_plane_ransac(pts, rng)
    assert abs(n @ n_true) > 0.9995
    assert frac > 0.6
    heights = pts @ n + d
    assert np.median(heights[:1200]) > 0.02  # outliers are above (towards camera)
    assert abs(np.median(heights[1200:])) < 0.001


def test_plane_ransac_rejects_too_few_points():
    with pytest.raises(ValueError):
        fit_plane_ransac(np.zeros((10, 3)))


def test_ray_plane_and_projection():
    n, d = np.array([0, 0, -1.0]), 0.75
    p = ray_plane_intersection(np.array([[319.5, 239.5], [619.5, 239.5]]), INTR, n, d)
    assert np.allclose(p[0], [0, 0, 0.75])
    assert np.allclose(p[1], [0.375, 0, 0.75])
    p_off = ray_plane_intersection(np.array([[319.5, 239.5]]), INTR, n, d, offset=0.01)
    assert np.isclose(p_off[0, 2], 0.74)
    q = project_to_plane(np.array([[0.1, 0.2, 0.6]]), n, d, offset=0.01)
    assert np.allclose(q[0], [0.1, 0.2, 0.74])


def test_covariances_are_symmetric_psd():
    n = np.array([0, 0, -1.0])
    C = in_plane_covariance(0.005, n, 0.001)
    assert np.allclose(np.diag(C), [25e-6, 25e-6, 1e-6])
    E = extrinsic_covariance(np.array([0.1, 0.0, 0.75]), 0.002, np.deg2rad(0.3))
    assert np.allclose(E, E.T)
    assert np.linalg.eigvalsh(E).min() > 0


def test_fusion_and_confidence():
    a, b = np.array([0.0, 0, 0]), np.array([0.01, 0, 0])
    p, s = fuse([(a, 0.005), (b, 0.005)])
    assert np.allclose(p, [0.005, 0, 0])
    assert np.isclose(s, 0.005 / np.sqrt(2))
    p2, _ = fuse([(a, 0.001), (b, 0.01)])
    assert p2[0] < 0.001
    assert capture_confidence(0.002, 0.01) > capture_confidence(0.01, 0.01)
    assert np.isclose(capture_confidence(0.01, 0.01), 1 - np.exp(-0.5))
