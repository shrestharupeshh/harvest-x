"""Pinhole camera model and rigid-transform helpers.

Conventions
-----------
* Units are metres and radians everywhere in the code base.
* Camera optical frame: x right, y down, z forward (OpenCV / ROS optical convention).
* Robot base frame ``B``: z up. ``T_a_b`` is the 4x4 homogeneous transform that maps
  points expressed in frame ``b`` into frame ``a`` (``p_a = T_a_b @ p_b``).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class CameraIntrinsics:
    fx: float
    fy: float
    cx: float
    cy: float
    width: int
    height: int

    @property
    def K(self) -> np.ndarray:
        return np.array([[self.fx, 0, self.cx], [0, self.fy, self.cy], [0, 0, 1.0]])

    def project(self, pts_cam: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Project Nx3 camera-frame points. Returns (Nx2 pixel coords, N depths)."""
        pts_cam = np.atleast_2d(pts_cam)
        z = pts_cam[:, 2]
        u = self.fx * pts_cam[:, 0] / z + self.cx
        v = self.fy * pts_cam[:, 1] / z + self.cy
        return np.stack([u, v], axis=1), z

    def backproject(self, uv: np.ndarray, z: np.ndarray) -> np.ndarray:
        """Back-project Nx2 pixels with depths z (along optical axis) to Nx3 points."""
        uv = np.atleast_2d(uv)
        z = np.atleast_1d(z)
        x = (uv[:, 0] - self.cx) / self.fx * z
        y = (uv[:, 1] - self.cy) / self.fy * z
        return np.stack([x, y, z], axis=1)

    def ray_grid(self) -> np.ndarray:
        """(H, W, 3) ray directions with unit z, so that ``point = depth * ray``."""
        u, v = np.meshgrid(np.arange(self.width), np.arange(self.height))
        return np.stack(
            [(u - self.cx) / self.fx, (v - self.cy) / self.fy, np.ones_like(u, dtype=float)],
            axis=-1,
        )

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in ("fx", "fy", "cx", "cy", "width", "height")}


def make_T(R: np.ndarray, t: np.ndarray) -> np.ndarray:
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = t
    return T


def invert_T(T: np.ndarray) -> np.ndarray:
    R, t = T[:3, :3], T[:3, 3]
    return make_T(R.T, -R.T @ t)


def transform_points(T: np.ndarray, pts: np.ndarray) -> np.ndarray:
    pts = np.atleast_2d(pts)
    return pts @ T[:3, :3].T + T[:3, 3]


def rot_x(a: float) -> np.ndarray:
    c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rot_y(a: float) -> np.ndarray:
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rot_z(a: float) -> np.ndarray:
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def look_down_pose(
    position: np.ndarray, tilt_x: float = 0.0, tilt_y: float = 0.0, yaw: float = 0.0
) -> np.ndarray:
    """T_base_cam for a camera at ``position`` looking along -z of the base frame.

    With zero tilt the camera x axis is aligned with base +x and camera y with base -y.
    Tilts are applied in the camera frame.
    """
    R0 = np.diag([1.0, -1.0, -1.0])
    return make_T(R0 @ rot_z(yaw) @ rot_x(tilt_x) @ rot_y(tilt_y), np.asarray(position, float))


def plane_base_to_cam(T_base_cam: np.ndarray, n_base: np.ndarray, d_base: float):
    """Express plane ``n·p + d = 0`` (base frame) in the camera frame."""
    R, t = T_base_cam[:3, :3], T_base_cam[:3, 3]
    n_cam = R.T @ n_base
    d_cam = float(n_base @ t + d_base)
    return n_cam, d_cam
