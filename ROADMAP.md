# Roadmap

Legend: ✅ done · 🟡 in progress · ⛔ blocked · ⬜ planned. "Done" means the artefact exists,
is tested where testable, and is committed; it never implies hardware validation.

## Phase 0 — Repository initialisation and research
- ✅ Tooling inventory, repo structure, conventions, licences, CI
- ✅ Literature review, first pass (web search, abstract level)
- ✅ Gap analysis, comparison table (25 works), research questions
- ✅ Architecture trade study and selection (D-003)
- ✅ System requirements v0.1 and architecture diagrams
- 🟡 Bibliography verification (19 entries still flagged [R], 14 flagged [V*])
- ⛔ Systematic database search + full-text reading — needs access to IEEE Xplore /
  ScienceDirect / Scholar (not reachable from the build environment)
- ⬜ Research proposal and experimental protocol with pre-declared analyses

## Phase 1 — Computational foundation
- ✅ Procedural RGB-D simulator with 3D ground truth
- ✅ Classical detection / instance segmentation baselines
- ✅ Maturity baselines (rule, classical ML) and fresh-mass regression
- ✅ Cutting-target estimators, fixture prior, fusion, empirical uncertainty
- ✅ Rule-based harvest decision with refusal
- ✅ Benchmark, metrics, cluster-bootstrap CIs, report generator, tests
- ✅ Dataset registry, data-collection protocol draft
- ⬜ 1b: evaluate on the AGC lettuce dataset (download + loader + plant-level split)
- ⬜ 1b: Blender scene generator (appearance realism, oblique wrist views)
- ⬜ 1b: learned models (YOLO-seg / Mask R-CNN / keypoints) against the baselines
- ⬜ 1b: camera intrinsic/extrinsic/hand-eye calibration scripts with validation reports
- ⬜ 1b: close-range stem verification from an oblique view

## Phase 2 — Mechanical design
- ✅ Kinematics trade study → 4-axis gantry (D-010)
- ✅ End-effector concept comparison → cradle fork C3 (D-014); approach study (D-015)
- ✅ Parametric CAD of the C3 end effector with interference and reach checks; STEP/STL
- ✅ Analytical calculations with tests (cutting, blade, tines, boom, stiffness, axes, bolts, capture, cycle)
- ✅ CAD toolchain decision: CadQuery (D-016)
- 🟡 Rack / fixture CAD (envelope level only)
- ⬜ Gantry detail design with selected linear modules, guides, drives, cable chain
- ⬜ Bench validation of the fork-and-blade principle on real plants (checklist A5)
- ⬜ Concepts C1 and C2 as CAD for the comparison experiment
- ⬜ Dimensioned drawings, exploded views, BOM, FEA of fork/boom

## Phase 3 — Simulation
- ⬜ URDF/Xacro incl. rail joint; Gazebo world; MoveIt 2 config; scenario runner

## Phase 4 — Electronics and firmware
- ⬜ Component selection, schematics, PCB decision, firmware with host-side tests

## Phase 5 — Integrated robotics software
- ⬜ ROS 2 packages, state machine, experiment manager, dashboard

## Phase 6 — Prototype build package
- ⬜ Final BOM (three cost tiers), drawings, assembly, wiring, calibration and safety procedures

## Phase 7 — Physical validation (requires hardware and plants)
- ⬜ Not started. Cannot be marked complete without measured evidence.

## Phase 8 — Publication
- ⬜ Not started. Venue analysis and manuscript skeleton follow Phase 1b results.

## Optional — Mobile platform
- ⬜ Deferred; currently no research question depends on it (trade study).
