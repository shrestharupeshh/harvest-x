# Perception

Status: **Implemented, tested on synthetic data only.** No real image has been processed.

`harvestx_perception` is a ROS-independent Python library that turns an overhead RGB-D frame of
a rack section into per-plant observations in the robot base frame.

```
RGB-D frame ─► tray-plane fit ─► plant mask ─► instances ─► features ─► maturity
                                   │                           │
                    fixture geometry + plant registry          └─► stem estimators ─► fusion
                                                                     └─► cut target, covariance,
                                                                         confidence, status
```

## Modules

| Module | Purpose |
|---|---|
| `camera.py` | Pinhole model, SE(3) helpers, frame conventions |
| `synthetic/growth.py` | Latent growth model (assumed parameters) and mass-based maturity labels |
| `synthetic/scene.py` | Ray-cast RGB-D renderer with instance masks and 3D stem ground truth |
| `segmentation/classical.py` | ExG / depth / fusion masks; automatic or site-seeded (compact) watershed |
| `features.py` | Per-plant shape, colour and metric features |
| `maturity/models.py` | Size-rule baseline, logistic regression, random forest, mass regressor |
| `localization/geometry.py` | Plane RANSAC, ray–plane intersection, covariance helpers |
| `localization/stem.py` | `centroid`, `dt_peak`, `centroid_3d`, `height_apex`, `site_prior`, `fusion` |
| `pipeline.py` | `process_frame()` → `PlantObservation` list |
| `decision.py` | Rule-based HARVEST / DEFER / RESCAN / REJECT baseline |
| `evaluation/metrics.py` | Mask IoU matching, PR/AP, ECE, cluster bootstrap |
| `benchmark.py` | End-to-end synthetic benchmark and report writer |

## Use

```python
from harvestx_perception.pipeline import PipelineConfig, process_frame

result = process_frame(rgb, depth, intrinsics, T_base_cam, sites_base, plane_z_base,
                       cut_height, PipelineConfig(), maturity_model, site_occupied)
for obs in result.observations:
    print(obs.site_index, obs.maturity, obs.cut_target_base, obs.confidence, obs.target_status)
```

`target_status` is `PLAUSIBLE` or `LOW_CONFIDENCE`. `VERIFIED` is reserved for a close-range
observation of the stem, which is not implemented.

## Reproduce the benchmark

```bash
pip install -e ".[dev]"
```

```bash
python -m harvestx_perception.benchmark --out perception/results/synthetic_v0
```

About six minutes on four CPU cores. Output: `results.json`, `REPORT.md` and three figures in
[`results/synthetic_v0/`](results/synthetic_v0/REPORT.md). Results are deterministic for a
given seed and library versions.

## What the synthetic benchmark does and does not show

It shows that the software works end to end, that the evaluation respects plant-level
independence, and how the baselines rank inside an idealised simulator. It does **not** show
how any method performs on real lettuce: appearance is not realistic and several parameters
that drive the results are assumptions (see `KNOWN_LIMITATIONS.md`).
