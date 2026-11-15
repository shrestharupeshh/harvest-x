"""Procedural RGB-D lettuce-tray scene generator (perspective ray caster).

Each plant is a rosette of planar elliptical leaves attached to a hidden stem that
emerges from a net-pot hole in an NFT channel. Leaves are ray-cast with a z-buffer
through a pinhole camera at an arbitrary pose, so RGB, depth, instance masks and
3D ground truth (stem base, cutting target) are mutually consistent.

This is a deliberately simple *geometry-level* simulator. Known gaps versus real
imagery (flat leaves, no leaf curl/ruffle, no specular highlights, no true cast
shadows, no roots/algae/water films, idealised depth noise) are listed in
``KNOWN_LIMITATIONS.md``. Results on these data are SYNTHETIC and say nothing about
real-world accuracy.
"""

from __future__ import annotations

import zlib
from dataclasses import asdict, dataclass, field

import cv2
import numpy as np

from ..camera import CameraIntrinsics, invert_T, look_down_pose, transform_points
from .growth import CULTIVARS, PlantState, sample_plant

GOLDEN_ANGLE = np.deg2rad(137.5)


@dataclass
class RackLayout:
    """Known fixture geometry, expressed in the robot base frame."""

    tray_center: tuple[float, float, float] = (0.45, 0.0, 0.10)
    n_cols: int = 3  # along base x
    n_rows: int = 2  # along base y (one NFT channel per row)
    pitch_x: float = 0.22
    pitch_y: float = 0.24
    channel_width: float = 0.10
    hole_radius: float = 0.025
    cut_height: float = 0.008  # cutting plane height above channel top surface

    def sites(self) -> np.ndarray:
        cx, cy, cz = self.tray_center
        xs = (np.arange(self.n_cols) - (self.n_cols - 1) / 2) * self.pitch_x + cx
        ys = (np.arange(self.n_rows) - (self.n_rows - 1) / 2) * self.pitch_y + cy
        return np.array([[x, y, cz] for y in ys for x in xs])

    @property
    def plane_z(self) -> float:
        return self.tray_center[2]


@dataclass
class SceneConfig:
    intrinsics: CameraIntrinsics = field(
        default_factory=lambda: CameraIntrinsics(600.0, 600.0, 319.5, 239.5, 640, 480)
    )
    rack: RackLayout = field(default_factory=RackLayout)
    camera_height: float = 0.75  # above tray plane
    camera_xy_jitter: float = 0.03
    camera_tilt_max_deg: float = 6.0
    cultivars: tuple[str, ...] = ("butterhead", "green_oakleaf", "romaine", "red_leaf")
    cultivar_probs: tuple[float, ...] = (0.4, 0.25, 0.2, 0.15)
    age_range_days: tuple[float, float] = (4.0, 48.0)
    tray_age_spread_days: float = 5.0  # plants in one tray are similar but not identical age
    empty_site_prob: float = 0.08
    stem_offset_sigma: float = 0.006  # stem position scatter inside the net pot
    lean_max: float = 0.35  # max fractional leaf-length asymmetry
    depth_noise_coeff: float = 0.002  # sigma_z = coeff * z^2  [m]
    depth_edge_dropout: float = 0.6
    rgb_noise_sigma: float = 0.012


@dataclass
class PlantTruth:
    plant_id: str
    site_index: int
    instance_id: int  # value in the instance mask
    cultivar: str
    age_days: float
    fresh_mass_g: float
    diameter_m: float
    height_m: float
    leaf_count: int
    bolting: bool
    maturity: str
    stem_base: list[float]  # base frame, on channel surface
    cut_target: list[float]  # base frame
    stem_px: list[float]  # projection of the cut target into the image
    visible_px: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SceneSample:
    rgb: np.ndarray  # HxWx3 uint8 (RGB order)
    depth: np.ndarray  # HxW float32 metres along optical axis, 0 = invalid
    instances: np.ndarray  # HxW uint8, 0 = background
    plants: list[PlantTruth]
    intrinsics: CameraIntrinsics
    T_base_cam: np.ndarray
    rack: RackLayout
    meta: dict


def _plant_leaves(
    rng: np.random.Generator, state: PlantState, stem_base: np.ndarray, lean_max: float
):
    """Return list of leaf dicts (centre C, axes u/v, semi-axes, colour mix)."""
    c = CULTIVARS[state.cultivar]
    n = state.leaf_count
    R = state.diameter_m / 2
    lean_dir = rng.uniform(0, 2 * np.pi)
    lean = rng.uniform(0, 1) ** 1.5  # most plants lean a little, a few a lot
    leaves = []
    phi0 = rng.uniform(0, 2 * np.pi)
    for i in range(n):
        f = i / max(n - 1, 1)  # 0 = outermost/oldest, 1 = innermost/youngest
        phi = phi0 + i * GOLDEN_ANGLE + rng.normal(0, 0.12)
        elev = np.deg2rad(8 + 60 * f**1.2 + c.elev_offset_deg + rng.normal(0, 4))
        elev = np.clip(elev, np.deg2rad(3), np.deg2rad(85))
        length = R * (1.0 - 0.72 * f) * rng.normal(1.0, 0.08)
        length *= 1.0 + lean * lean_max * np.cos(phi - lean_dir)
        if state.bolting:
            elev = min(elev + np.deg2rad(12), np.deg2rad(85))
        length = max(length, 0.006)
        width = c.width_ratio * length * rng.normal(1.0, 0.08)
        attach = stem_base + np.array([0, 0, 0.004 + f * 0.30 * state.nominal_height_m])
        if state.bolting:
            attach[2] += f * 0.5 * state.nominal_height_m
        u = np.array([np.cos(elev) * np.cos(phi), np.cos(elev) * np.sin(phi), np.sin(elev)])
        v = np.array([-np.sin(phi), np.cos(phi), 0.0])
        leaves.append(
            dict(C=attach + u * length / 2, u=u, v=v, a=length / 2, b=width / 2, f=f,
                 tex=rng.uniform(0.9, 1.1))
        )
    return leaves


def _tray_color(P: np.ndarray, rack: RackLayout, rng: np.random.Generator) -> np.ndarray:
    """Colour of tray-plane points P (...,3) in base frame."""
    cy = rack.tray_center[1]
    ys = (np.arange(rack.n_rows) - (rack.n_rows - 1) / 2) * rack.pitch_y + cy
    dy = np.min(np.abs(P[..., 1, None] - ys[None, None, :]), axis=-1)
    on_channel = dy < rack.channel_width / 2
    col = np.where(on_channel[..., None], np.array([0.86, 0.86, 0.84]), np.array([0.20, 0.21, 0.23]))
    col = col.astype(np.float32)
    for s in rack.sites():
        d = np.hypot(P[..., 0] - s[0], P[..., 1] - s[1])
        col[d < rack.hole_radius] = np.array([0.10, 0.09, 0.08])
    # subtle procedural texture so the background is not perfectly uniform
    tex = 1.0 + 0.04 * np.sin(P[..., 0] * 180.0) * np.cos(P[..., 1] * 140.0)
    return col * tex[..., None]


def render_scene(
    cfg: SceneConfig,
    rng: np.random.Generator,
    tray_id: str = "tray",
    plants_state: list[tuple[int, PlantState, np.ndarray]] | None = None,
) -> SceneSample:
    """Render one RGB-D view.

    ``plants_state`` lets the caller re-image the *same* physical plants from another
    viewpoint/lighting (list of (site_index, PlantState, stem_base)). When ``None`` a
    new tray population is sampled.
    """
    rack, intr = cfg.rack, cfg.intrinsics
    if plants_state is None:
        plants_state = sample_tray(cfg, rng)

    # Camera pose
    tilt = np.deg2rad(cfg.camera_tilt_max_deg)
    cam_pos = np.array(rack.tray_center) + np.array(
        [rng.uniform(-1, 1) * cfg.camera_xy_jitter, rng.uniform(-1, 1) * cfg.camera_xy_jitter,
         cfg.camera_height * rng.uniform(0.95, 1.05)]
    )
    T_base_cam = look_down_pose(
        cam_pos, rng.uniform(-tilt, tilt), rng.uniform(-tilt, tilt), rng.uniform(-0.05, 0.05)
    )
    T_cam_base = invert_T(T_base_cam)
    R_bc = T_base_cam[:3, :3]
    rays_cam = intr.ray_grid()  # HxWx3, z = 1
    rays_base = rays_cam @ R_bc.T
    origin = T_base_cam[:3, 3]

    H, W = intr.height, intr.width
    # Tray plane
    t_plane = (rack.plane_z - origin[2]) / rays_base[..., 2]
    depth = t_plane.astype(np.float32)
    P_plane = origin + rays_base * t_plane[..., None]
    rgb = _tray_color(P_plane, rack, rng)
    inst = np.zeros((H, W), np.uint8)

    light = np.array([rng.uniform(-0.4, 0.4), rng.uniform(-0.4, 0.4), 1.0])
    light /= np.linalg.norm(light)

    truths: list[PlantTruth] = []
    for k, (site_idx, state, stem_base) in enumerate(plants_state, start=1):
        cult = CULTIVARS[state.cultivar]
        leaf_rng = np.random.default_rng(zlib.crc32(f"{tray_id}/{site_idx}".encode()))
        leaves = _plant_leaves(leaf_rng, state, stem_base, cfg.lean_max)
        top = max(leaf["C"][2] + leaf["u"][2] * leaf["a"] for leaf in leaves)
        for leaf in leaves:
            C, u, v, a, b = leaf["C"], leaf["u"], leaf["v"], leaf["a"], leaf["b"]
            n = np.cross(u, v)
            uvc, zc = intr.project(transform_points(T_cam_base, C[None]))
            r_px = intr.fx * max(a, b) / max(zc[0], 0.05) * 1.25 + 2
            x0, x1 = int(max(uvc[0, 0] - r_px, 0)), int(min(uvc[0, 0] + r_px + 1, W))
            y0, y1 = int(max(uvc[0, 1] - r_px, 0)), int(min(uvc[0, 1] + r_px + 1, H))
            if x0 >= x1 or y0 >= y1:
                continue
            d = rays_base[y0:y1, x0:x1]
            denom = d @ n
            denom = np.where(np.abs(denom) < 1e-9, 1e-9, denom)
            t = ((C - origin) @ n) / denom
            q = origin + d * t[..., None] - C
            qa, qb = (q @ u) / a, (q @ v) / b
            # tapered leaf outline: narrower at the base (qa -> -1)
            hit = (qa**2 + (qb / (0.55 + 0.45 * np.clip(qa + 1, 0, 1))) ** 2 <= 1) & (t > 0.02)
            hit &= t < depth[y0:y1, x0:x1]
            if not hit.any():
                continue
            lambert = 0.55 + 0.45 * abs(float(n @ light))
            base = np.array(cult.base_rgb) * (1 - leaf["f"]) + np.array(cult.inner_rgb) * leaf["f"]
            shade = lambert * leaf["tex"] * (0.82 + 0.18 * np.clip(qa, -1, 1))
            col = base[None, None, :] * shade[..., None]
            midrib = np.abs(qb) < 0.07
            col = np.where(midrib[..., None], col * 1.18 + 0.03, col)
            sub_rgb, sub_d, sub_i = rgb[y0:y1, x0:x1], depth[y0:y1, x0:x1], inst[y0:y1, x0:x1]
            sub_rgb[hit] = col[hit]
            sub_d[hit] = t[hit]
            sub_i[hit] = k
        cut = stem_base + np.array([0, 0, rack.cut_height])
        stem_px, _ = intr.project(transform_points(T_cam_base, cut[None]))
        truths.append(
            PlantTruth(
                plant_id=f"{tray_id}-S{site_idx:02d}", site_index=int(site_idx), instance_id=k,
                cultivar=state.cultivar, age_days=state.age_days,
                fresh_mass_g=state.fresh_mass_g, diameter_m=state.diameter_m,
                height_m=float(top - rack.plane_z), leaf_count=state.leaf_count,
                bolting=state.bolting, maturity=state.maturity,
                stem_base=stem_base.tolist(), cut_target=cut.tolist(),
                stem_px=stem_px[0].tolist(),
            )
        )

    for tr in truths:
        tr.visible_px = int((inst == tr.instance_id).sum())

    # ---- photometric effects -------------------------------------------------
    plant_mask = (inst > 0).astype(np.float32)
    shift = (light[:2] * -18).astype(int)
    shadow = cv2.GaussianBlur(np.roll(plant_mask, (shift[1], shift[0]), axis=(0, 1)), (0, 0), 9)
    rgb = rgb * (1 - 0.45 * shadow * (1 - plant_mask))[..., None]
    gain = rng.uniform(0.65, 1.2)
    tint = np.array([rng.uniform(0.9, 1.12), rng.uniform(0.92, 1.05), rng.uniform(0.9, 1.12)])
    yy, xx = np.mgrid[0:H, 0:W]
    vign = 1 - 0.18 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    rgb = rgb * gain * tint[None, None, :] * vign[..., None]
    rgb = rgb + rng.normal(0, cfg.rgb_noise_sigma, rgb.shape)
    rgb8 = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)

    # ---- depth sensor model ---------------------------------------------------
    clean = depth.copy()
    noisy = clean + rng.normal(0, 1, clean.shape).astype(np.float32) * cfg.depth_noise_coeff * clean**2
    gx = cv2.Sobel(clean, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(clean, cv2.CV_32F, 0, 1, ksize=3)
    edges = (np.hypot(gx, gy) > 0.06) & (rng.random(clean.shape) < cfg.depth_edge_dropout)
    holes = rng.random(clean.shape) < 0.004
    noisy[edges | holes] = 0.0

    meta = dict(tray_id=tray_id, gain=float(gain), tint=tint.tolist(), light=light.tolist(),
                synthetic=True, generator="harvestx_perception.synthetic.scene/v0")
    return SceneSample(rgb8, noisy.astype(np.float32), inst, truths, intr, T_base_cam, rack, meta)


def sample_tray(cfg: SceneConfig, rng: np.random.Generator):
    """Sample the physical plant population of one tray (independent of imaging)."""
    sites = cfg.rack.sites()
    tray_age = rng.uniform(*cfg.age_range_days)
    cultivar = str(rng.choice(cfg.cultivars, p=np.array(cfg.cultivar_probs)))
    plants = []
    for i, s in enumerate(sites):
        if rng.random() < cfg.empty_site_prob:
            continue
        age = float(np.clip(tray_age + rng.normal(0, cfg.tray_age_spread_days / 2), 2, 60))
        state = sample_plant(rng, cultivar, age)
        off = rng.normal(0, cfg.stem_offset_sigma, 2)
        nrm = np.linalg.norm(off)
        if nrm > cfg.rack.hole_radius * 0.7:
            off *= cfg.rack.hole_radius * 0.7 / nrm
        plants.append((i, state, s + np.array([off[0], off[1], 0.0])))
    return plants
