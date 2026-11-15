"""End-to-end perception: RGB(-D) frame -> per-plant observations in the base frame."""

from __future__ import annotations

from dataclasses import dataclass, field

import cv2
import numpy as np

from .camera import CameraIntrinsics, invert_T, plane_base_to_cam, transform_points
from .features import ALL_FEATURES, instance_features
from .localization import stem as stem_mod
from .localization.geometry import (
    depth_to_points,
    fit_plane_ransac,
    in_plane_covariance,
    ray_plane_intersection,
)
from .segmentation.classical import excess_green, instance_segmentation, semantic_mask

# Target status vocabulary. VERIFIED is intentionally never produced by this module.
PLAUSIBLE = "PLAUSIBLE"
LOW_CONFIDENCE = "LOW_CONFIDENCE"
VERIFIED = "VERIFIED"  # reserved for a close-range stem confirmation step (not implemented)


@dataclass
class PipelineConfig:
    seg_method: str = "fusion"  # exg | depth | fusion
    markers: str = "sites"  # sites | auto
    stem_method: str = "fusion"  # see localization.stem.METHODS
    fusion_vision_method: str = "centroid_3d"  # vision estimate fused with the site prior
    use_depth: bool = True
    cut_tolerance: float = 0.010  # allowable in-plane cut error [m] (assumed, see DECISIONS)
    confidence_min: float = 0.5
    # Empirical sigma model in the base frame: vision methods use sigma = k * r_eq
    # (r_eq = equivalent canopy radius), the site prior uses sigma = k  [m]. The scale
    # factors must be fitted on training data from the SAME rig, so that they absorb
    # camera-to-base and rack-to-base calibration error. Defaults are uncalibrated guesses.
    sigma_scale: dict = field(
        default_factory=lambda: {"centroid": 0.15, "dt_peak": 0.15, "centroid_3d": 0.12,
                                 "height_apex": 0.20, "site_prior": 0.007}
    )
    min_area_px: int = 150


@dataclass
class PlantObservation:
    label: int
    site_index: int | None
    bbox: tuple[int, int, int, int]  # x0, y0, x1, y1 (inclusive)
    score: float
    center_px: tuple[float, float]
    center_base: np.ndarray
    stem_px: tuple[float, float] | None
    cut_target_base: np.ndarray | None
    cut_target_cov_base: np.ndarray | None
    sigma_plane: float | None  # 1-sigma in-plane std from the empirical sigma model [m]
    confidence: float  # P(in-plane error < cut_tolerance) under the sigma model
    target_status: str
    stem_candidates: dict  # method -> (3,) base-frame estimate (for evaluation)
    features: dict
    maturity_probs: dict | None = None
    maturity: str | None = None

    def to_dict(self) -> dict:
        def arr(a):
            return None if a is None else np.asarray(a).round(5).tolist()

        return dict(
            label=self.label, site_index=self.site_index, bbox=list(self.bbox), score=self.score,
            center_px=list(self.center_px), center_base=arr(self.center_base),
            stem_px=None if self.stem_px is None else list(self.stem_px),
            cut_target_base=arr(self.cut_target_base),
            cut_target_cov_base=arr(self.cut_target_cov_base), sigma_plane=self.sigma_plane,
            confidence=self.confidence, target_status=self.target_status,
            maturity=self.maturity, maturity_probs=self.maturity_probs,
        )


@dataclass
class FrameResult:
    observations: list[PlantObservation]
    labels: np.ndarray
    plane: tuple[np.ndarray, float]
    plane_source: str


def process_frame(
    rgb: np.ndarray,
    depth: np.ndarray | None,
    intr: CameraIntrinsics,
    T_base_cam: np.ndarray,
    sites_base: np.ndarray,
    plane_z_base: float,
    cut_height: float,
    cfg: PipelineConfig | None = None,
    maturity_model=None,
) -> FrameResult:
    cfg = cfg or PipelineConfig()
    T_cam_base = invert_T(T_base_cam)
    use_depth = cfg.use_depth and depth is not None

    # --- tray plane -----------------------------------------------------------
    n_cal, d_cal = plane_base_to_cam(T_base_cam, np.array([0.0, 0.0, 1.0]), -plane_z_base)
    n, d, source = n_cal, d_cal, "calibration"
    points = height = None
    if use_depth:
        points = depth_to_points(depth, intr)
        try:
            n_fit, d_fit, frac = fit_plane_ransac(points.reshape(-1, 3))
            # accept the fitted plane only if it is supported and close to calibration
            if frac > 0.15 and n_fit @ n_cal > 0.98 and abs(d_fit - d_cal) < 0.03:
                n, d, source = n_fit, d_fit, "depth_ransac"
        except ValueError:
            pass
        height = points @ n + d

    rays = intr.ray_grid()
    t_plane = -d / (rays @ n)
    z_eff = np.where(np.isfinite(height), points[..., 2], t_plane) if use_depth else t_plane
    px_area = z_eff**2 / (intr.fx * intr.fy)

    # --- segmentation ---------------------------------------------------------
    seg_method = cfg.seg_method if use_depth else "exg"
    mask = semantic_mask(rgb, height, seg_method, cfg.min_area_px)
    sites_cam = transform_points(T_cam_base, sites_base)
    site_px, _ = intr.project(sites_cam)
    labels = instance_segmentation(
        mask, height, site_px if cfg.markers == "sites" else None, min_area=cfg.min_area_px
    )

    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    exg = excess_green(rgb)
    R_bc = T_base_cam[:3, :3]
    obs: list[PlantObservation] = []
    for lab in [int(v) for v in np.unique(labels) if v]:
        m = labels == lab
        ys, xs = np.nonzero(m)
        feats = instance_features(rgb, labels, lab, height, px_area, hsv, exg)
        c_px = (float(xs.mean()), float(ys.mean()))
        c_cam = ray_plane_intersection(np.array([c_px]), intr, n, d, cut_height)[0]
        if cfg.markers == "sites":
            site_idx: int | None = lab - 1
        else:
            dists = np.linalg.norm(sites_cam - c_cam, axis=1)
            site_idx = int(np.argmin(dists)) if dists.min() < 0.12 else None
        site_cam = sites_cam[site_idx] if site_idx is not None else None

        r_eq = feats["eq_diameter_m"] / 2
        cands: dict[str, tuple[np.ndarray, float]] = {}
        for meth in (*stem_mod.VISION_METHODS, "site_prior"):
            p = stem_mod.estimate_stem(meth, m, intr, n, d, cut_height, points, height, site_cam)
            if p is not None:
                k = cfg.sigma_scale[meth]
                cands[meth] = (p, k * r_eq if meth in stem_mod.SIZE_SCALED else k)
        fus = [cands[k] for k in (cfg.fusion_vision_method, "site_prior") if k in cands]
        if fus:
            cands["fusion"] = stem_mod.fuse(fus)

        chosen = cands.get(cfg.stem_method)
        if chosen is None:
            stem_px = cut_base = cov_base = sigma_tot = None
            conf, status = 0.0, LOW_CONFIDENCE
        else:
            p_cam, sigma = chosen
            cov_base = R_bc @ in_plane_covariance(sigma, n, 0.001) @ R_bc.T
            sigma_tot = float(sigma)
            conf = stem_mod.capture_confidence(sigma_tot, cfg.cut_tolerance)
            status = PLAUSIBLE if conf >= cfg.confidence_min else LOW_CONFIDENCE
            cut_base = transform_points(T_base_cam, p_cam[None])[0]
            uv, _ = intr.project(p_cam[None])
            stem_px = (float(uv[0, 0]), float(uv[0, 1]))

        o = PlantObservation(
            label=lab, site_index=site_idx,
            bbox=(int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())),
            score=float(feats["solidity"] * min(1.0, feats["area_px"] / 800.0)),
            center_px=c_px, center_base=transform_points(T_base_cam, c_cam[None])[0],
            stem_px=stem_px, cut_target_base=cut_base, cut_target_cov_base=cov_base,
            sigma_plane=sigma_tot, confidence=conf, target_status=status,
            stem_candidates={k: transform_points(T_base_cam, p[None])[0]
                             for k, (p, _) in cands.items()},
            features=feats,
        )
        obs.append(o)
    if maturity_model is not None and obs:
        X = np.array([[o.features[k] for k in maturity_model.feature_names] for o in obs])
        for o, pr in zip(obs, maturity_model.predict_proba(X)):
            o.maturity_probs = {c: float(p) for c, p in zip(maturity_model.classes_, pr)}
            o.maturity = str(maturity_model.classes_[int(np.argmax(pr))])
    return FrameResult(obs, labels, (n, d), source)


__all__ = ["PipelineConfig", "PlantObservation", "FrameResult", "process_frame", "ALL_FEATURES"]
