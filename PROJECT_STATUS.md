# Project status

Last updated: 2026-11-15 (end of session 2).

Status vocabulary: Not started → In progress → Implemented → Tested in simulation →
Tested on hardware → Experimentally validated. Levels are never skipped.

## Subsystem status

| Subsystem | Status | Evidence / note |
|---|---|---|
| Repository, licences, CI | Implemented | `ruff` + `pytest` (50 tests) pass locally; GitHub Actions green on the session-1 push; a CAD job was added in session 2 |
| Literature review | In progress | First pass, abstract level; 25-work comparison table; 19 of 42 bibliography entries still unverified ([R]), 14 partly verified ([V*]) |
| Research gap / contribution | In progress | Provisional direction D-009 |
| Research proposal, experimental protocol, manuscript | Not started | |
| System architecture and requirements | Implemented (v0.1 documents) | Trade study reproducible from YAML; requirements contain assumptions marked (A) |
| Perception: synthetic data generator | Tested in simulation | Deterministic; geometry consistency tests |
| Perception: detection / segmentation | Tested in simulation | Classical baselines only |
| Perception: maturity estimation | Tested in simulation | Rule + classical ML; synthetic labels |
| Perception: cutting-target localisation + uncertainty | Tested in simulation | No stem verification (`VERIFIED` never emitted) |
| Harvest decision | Tested in simulation | Rule baseline; negative result on gating |
| Camera / hand-eye calibration | Not started | |
| Learned perception models (YOLO, Mask R-CNN, …) | Not started | Deferred until real/photorealistic data (D-004) |
| Dataset registry / collection protocol | Implemented (documents) | No data collected |
| Manipulator (4-axis gantry) | In progress | Kinematics decided (D-010); axis requirements estimated; no module selection or detail CAD |
| End effector C3 (cradle fork + slicing blade) | Implemented (CAD + analytical estimates) | Interference-free in CAD, reach check passes; never built or tried on a plant |
| End effectors C1, C2 | Not started | Compared on paper only |
| Engineering calculations | Implemented (estimates) | Closed-form, unit-tested; no FEA |
| Growing rack / fixture | In progress | Envelope-level CAD only |
| Electronics, PCB | Not started | |
| Firmware | Not started | |
| ROS 2 packages, motion planning, state machine | Not started | State machine specified as a diagram only |
| Digital twin (Gazebo / MoveIt 2) | Not started | |
| Dashboard | Not started | |
| Procurement / BOM | Not started | |
| Mobile platform | Not started | Deferred by trade study |
| Physical prototype, experiments | Not started | Requires hardware and plants |

## Results so far (all SIMULATED)

Source: `perception/results/synthetic_v0/` at commit `9c3c893`, seed 20261115, 150 trays x 2
views, tray-level 90/30/30 split, 95 % cluster-bootstrap CIs over the 30 test trays.

| Quantity | Result |
|---|---|
| Instance segmentation, fusion + known sites | P 1.000, R 0.997, AP50:95 0.885 |
| Instance segmentation, colour only, automatic markers | F1 0.767; red-leaf recall 0.02 |
| Cut-target error, best vision-only (RGB-D 3D centroid) | mean 15.2 mm (13.6–16.8) |
| Cut-target error, fixture prior only | mean 8.1 mm (7.6–8.5) |
| Cut-target error, RGB-D + fixture fusion | mean 7.5 mm (7.0–7.9); 81 % within 10 mm |
| Uncertainty calibration (fusion) | 94.4 % coverage of nominal 95 % region; confidence ECE 0.051 |
| Maturity macro-F1: diameter rule / RGB-D ML / + age, cultivar | 0.63 / 0.75 / 0.78 |
| Fresh-mass MAE: RGB / RGB-D features | 21.7 g / 17.3 g |
| Decision precision: naive vs. rule with refusal | 0.50 (88 attempts) vs. 0.41 (29 attempts) |
| Pipeline runtime | ~0.2 s per 640x480 frame on a cloud CPU |

Negative / uncomfortable results, stated plainly:

1. Vision alone localises the stem worse than simply trusting the rack geometry.
2. The refusal policy did not raise precision; target confidence is calibrated on average but
   nearly constant across plants, so it cannot discriminate good from bad targets. Differences
   in section 5 of the report rest on small counts and are not statistically meaningful.
3. A provisional 10 mm tolerance is not met by top-view perception under the assumed stem
   scatter (19 % of fused targets miss it).

## Mechanical results so far (ESTIMATED or SIMULATED, none measured)

| Quantity | Result | Kind |
|---|---|---|
| Leaf area in tool path: top-down / beside stem / side entry | 76 % / 72 % / 29 % | Simulated, rigid leaves |
| Inner-leaf area in tool path, same order | 98 % / 79 % / 1 % | Simulated |
| Stem capture probability of the 70 mm V-throat for a 6.5 mm sigma target | > 0.999 | Estimated (Gaussian) |
| Straight-chop stem force upper bound | 110 N | Estimated from a placeholder shear strength |
| Blade actuator torque with safety factor 2 | 9.2 N·m | Estimated |
| End-effector mass | 1.77 kg | CAD volumes + assumed allowances |
| Lateral deflection at the stem seat under 10 N | 0.42 mm | Estimated, structure only |
| Kinematic cycle estimate | 11 s | Estimated from motion limits |

## Session 2 summary

**Completed**
- Owner delegated all decisions and removed the budget limit; crop/format fixed (D-013).
- Kinematics trade study: 4-axis Cartesian gantry (D-010). End-effector comparison: cradle
  fork with pivoting slicing blade (D-014). Side-entry approach and robot-accessible rack
  (D-015), supported by a simulated leaf-interference study. Verification by stem-seated
  sensor (D-017). CadQuery as CAD kernel (D-016).
- `harvestx_mech`: design parameters, calculation library, generated calculation report,
  approach study.
- `harvestx_cad`: parametric end effector and envelope-level rack; STEP, STL, SVG, renders,
  parts list, mass properties.

**Design iterations forced by the analysis (kept in the record)**
- Blade section increased after the first calculation gave a factor of safety of 1.5.
- First CAD layout had the shank foot inside the blade sweep; found by inspection, now
  guarded by an automated interference test.
- The compact tool with a vertical shank at the head was abandoned when the approach geometry
  showed it must pass through the canopy; replaced by a low head on a boom.
- Skids raised from 2 to 6 mm so the plate clears a net-pot lip.

**Tests performed**
- `ruff` clean; `pytest`: 50 passed, including CAD validity, interference (blade open and
  closed), functional geometry, mass budget, rack clearances, calculation hand-checks.
- All generated reports and CAD exports regenerated from scripts.

**Unresolved issues**
- Every mechanical premise is untested on plants (six open risks in
  `docs/mechanical/mechanical_design.md` §6).
- The public lettuce dataset host is not reachable from the build environment, so the
  planned real-data check (T-012) is blocked.
- Gantry is not detailed; no drawings, no BOM.

## Session 1 summary

**Completed**
- Tool/environment inventory; repository structure, licences, contribution rules, CI.
- Literature search and verification by web search; review, comparison table, gap analysis,
  research questions, flagged bibliography.
- Three-architecture trade study with sensitivity analysis; architecture decision; system
  requirements; seven Mermaid diagrams; interface table.
- Perception library with simulator, baselines, uncertainty model, decision baseline,
  benchmark and report; dataset registry and collection protocol.
- Decision log (12 entries), roadmap, limitations, build checklist, task list.

**Tests performed**
- `ruff check perception tools tests`: clean.
- `pytest`: 35 passed (≈ 30 s), including an end-to-end benchmark smoke test.
- Full benchmark run three times; the first two exposed defects (an over-conservative
  analytic uncertainty model; wrong site association for overgrown neighbours) that were
  diagnosed, fixed and recorded in `DECISIONS.md` (D-006, D-007) and `KNOWN_LIMITATIONS.md`.

**Unresolved issues**
- CI has not yet been seen running on GitHub.
- Bibliography: 19 entries unverified, 14 partly verified; some quantitative figures are from secondary summaries.
- Watershed compactness was chosen on a sample overlapping the test trays (disclosed).
- All simulator parameters are assumptions; no real data yet.
- FreeCAD, Blender, ROS 2, Gazebo, KiCad and LaTeX are not available in the current build
  environment, which blocks parts of Phases 2–5 and 8 until an environment with them is set up.

**Next highest-priority tasks**: see `NEXT_STEPS.md`.
