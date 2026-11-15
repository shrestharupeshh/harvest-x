# Engineering decision log

Each entry: decision, alternatives, reasoning, consequences, date. Status is one of
**Accepted**, **Provisional** (accepted until named evidence arrives) or **Pending**.

## D-001 Repository and software layout — Accepted (2026-11-15)
- **Decision:** One monorepo. Algorithms live in ROS-independent Python libraries (first:
  `perception/harvestx_perception`); ROS 2 packages under `ros2_ws/src` will be thin wrappers.
- **Alternatives:** ROS-only packages; separate repositories per subsystem.
- **Reasoning:** Libraries can be unit-tested and benchmarked in plain CI without a ROS
  install; a single repo keeps CAD, firmware, software and protocols versioned together, which
  matters for reproducing an experiment.
- **Consequences:** Message types must mirror library dataclasses; some glue code.

## D-002 Licensing — Accepted (2026-11-15)
- **Decision:** Apache-2.0 (software), CERN-OHL-P-2.0 (hardware), CC-BY-4.0 (documentation).
- **Alternatives:** MIT/BSD; GPL-3.0 + CERN-OHL-S (reciprocal); single licence for everything.
- **Reasoning:** Permissive terms with explicit patent grants maximise reuse by labs and
  growers; hardware and documents need licences written for them. Details in `LICENSING.md`.
- **Consequences:** Derivatives may be closed. Full CERN-OHL/CC texts still to be vendored.

## D-003 Initial system architecture — Accepted (2026-11-15)
- **Decision:** Architecture A (fixed arm beside one rack section), built "rail-ready" so it
  can become architecture C (rail-mounted) by adding one prismatic axis.
- **Alternatives:** B mobile manipulator; C rail-mounted from the start.
- **Reasoning:** Weighted trade study (`docs/architecture/architecture_trade_study.md`): A 3.98,
  C 3.74, B 2.48 for the research-prototype profile; A ranks first in 70 % of perturbed
  trials. C wins clearly for production scaling. B is dominated and its re-registration error
  works against millimetre-level cutting.
- **Consequences:** v1 throughput is not representative of a production system. Frames, URDF
  and plant addressing must include the (currently fixed) rail joint from day one.

## D-004 Perception strategy: baselines and fixture prior first — Accepted (2026-11-15)
- **Decision:** Implement and measure training-free baselines (ExG/depth segmentation,
  site-seeded watershed, geometric stem estimators, the fixture prior, a size rule for
  maturity) before any deep model. Every learned model must beat them on held-out plants.
- **Alternatives:** Start with YOLO-seg / Mask R-CNN.
- **Reasoning:** No real images exist yet; a structured rack gives strong priors; baselines
  expose which sub-problems are actually hard (stem localisation) and which are not
  (segmentation with depth and known sites). Avoids black-box results without a reference.
- **Consequences:** Deep models are deferred to Phase 1b, after real or photorealistic data.

## D-005 Procedural simulator instead of Blender for the first dataset — Provisional (2026-11-15)
- **Decision:** A NumPy ray-caster with planar elliptical leaves generates RGB-D, masks and
  3D ground truth.
- **Alternatives:** Blender scenes (not installable in the build environment); public datasets
  (none has stem ground truth or neighbouring plants).
- **Reasoning:** Fast, dependency-free, exact ground truth, runs in CI.
- **Consequences:** Appearance is unrealistic; conclusions are limited to software
  verification and baseline ranking. Superseded when the Blender pipeline or real data exist.

## D-006 Target contract and uncertainty model — Accepted (2026-11-15)
- **Decision:** Every cutting target carries a covariance, a confidence (probability that the
  in-plane error is within the capture tolerance) and a status. Top-view perception may emit
  only `PLAUSIBLE` or `LOW_CONFIDENCE`; `VERIFIED` is reserved for a direct stem observation.
  Uncertainty is an empirical per-method sigma fitted on training plants from the same rig
  (robust, median-based), so that it absorbs calibration error.
- **Alternatives:** Analytic propagation of pixel/depth/extrinsic noise only; no uncertainty.
- **Reasoning:** The analytic model was tried first and over-covered (100 % for a nominal
  95 % region) because modelling error dominates sensor noise. The empirical model gave
  near-nominal coverage on synthetic test trays.
- **Consequences:** Sigma must be re-fitted for every rig, cultivar and calibration; it is
  isotropic and Gaussian, which real errors may not be.

## D-007 Site occupancy comes from the plant registry — Accepted (2026-11-15)
- **Decision:** Perception receives the list of planted sites from the registry and uses
  compact, site-seeded watershed for instances.
- **Alternatives:** Infer occupancy from the image; unconstrained instance segmentation.
- **Reasoning:** Without it, an overgrown plant overhanging a neighbouring site was assigned
  to the wrong site (errors > 200 mm) in the synthetic benchmark. The farm already knows where
  it planted.
- **Consequences:** Registry errors propagate into perception; an unregistered plant is
  ignored. An occupancy cross-check from the image is a planned safeguard.

## D-008 Capture-tolerance design goal ± 10 mm — Provisional (2026-11-15)
- **Decision:** Use ± 10 mm in-plane as the working cutting-target tolerance.
- **Alternatives:** ± 5 mm (precision blade), ± 15–20 mm (wide funnel/guide).
- **Reasoning:** Placeholder between assumed stem diameter and net-pot radius; needed so that
  confidence is defined. Not derived from measurements.
- **Consequences:** With the assumed 6 mm stem scatter, top-view-only targets fall short of
  this tolerance in simulation, which motivates a self-centring end-effector geometry and a
  verification view. To be replaced by measured stem scatter and end-effector tests.

## D-009 Primary research direction — Provisional (2026-11-15)
- **Decision:** Lead with contribution C1 (uncertainty-aware cutting-target localisation
  benchmarked against the fixture prior, with gated closed-loop verification), supported by C2
  (end-effector comparison). See `research/research_gap_analysis.md`.
- **Alternatives:** Platform paper first; maturity estimation; mobile manipulation.
- **Reasoning:** Most distinctive gap found, measurable with tens of plants, and useful
  whichever way the result falls.
- **Consequences:** The first physical measurement must be stem scatter relative to the net
  pot. To be re-confirmed after a systematic database search.

## D-010 Arm kinematics — Pending (Phase 2)
- **Question:** 4-DOF (XYZ + yaw; gantry or SCARA-type) versus 5/6-DOF articulated arm.
- **Evidence needed:** approach-direction study under the canopy, workspace, joint torque,
  blade-tip deflection and cost for each option.

## D-011 ROS 2 distribution — Pending verification
- **Leaning:** an LTS distribution (Jazzy Jalisco on Ubuntu 24.04 at the time of writing).
- **Evidence needed:** confirm, on an actual machine, binary availability and compatibility
  of MoveIt 2, ros2_control, the Gazebo bridge and the camera driver for the chosen
  computer. Not checked yet because ROS 2 is not installable in the current build environment.

## D-012 Compute, MCU, drivers, communication protocol — Pending (Phase 4)
