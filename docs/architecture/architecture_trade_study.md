# System architecture trade study

Status: v0.1 (2026-11-15). Computed table: [`trade_study_results.md`](trade_study_results.md),
generated from [`trade_study.yaml`](trade_study.yaml) by `tools/utilities/trade_study.py`.
Scores are engineering judgement, not measurements; the sensitivity analysis exists to show how
much that matters.

## Candidates

**A — Fixed arm beside the growing rack.** The manipulator is bolted to the same aluminium
extrusion frame as a short NFT rack section (2 channels x 3 sites in the reference fixture). An
overhead RGB-D camera is fixed to the frame.

**B — Mobile manipulator.** A differential-drive base carries the arm between racks; it must
localise, navigate, dock and then register itself to the rack before manipulating.

**C — Rail-mounted arm.** The same arm as A rides a linear axis parallel to the rack, giving one
extra prismatic degree of freedom along the row.

## Score rationale

| Criterion | A fixed | B mobile | C rail | Reasoning |
|---|---|---|---|---|
| Mechanical simplicity | 5 | 2 | 3 | A adds nothing beyond arm + frame. C adds one precision axis (rail, carriage, drive, cable chain, homing). B adds a drivetrain, battery, suspension/stability and docking hardware. |
| Cost | 5 | 2 | 3 | C adds roughly one actuator plus rail; B adds a whole vehicle, battery system, LiDAR/IMU and a second compute load. Not priced yet (see procurement, planned). |
| Workspace coverage | 2 | 5 | 4 | A reaches only what the arm reaches. C covers a full row. B covers the room. |
| Reachability per plant | 3 | 3 | 4 | C can always place the arm base at the best offset for each site; A serves edge sites at worse joint configurations; B depends on docking accuracy. |
| Throughput potential | 2 | 3 | 5 | C indexes between plants in about a second with no re-registration. B pays navigation and docking time per rack. A is limited to its fixed set of sites. |
| Positioning precision | 5 | 2 | 4 | A has a single rigid camera-arm-rack chain calibrated once. C adds rail straightness and repeatability errors. B must re-register to the rack after every move, which dominates the error budget for a millimetre-level cut. |
| Low navigation burden | 5 | 1 | 4 | A needs none; C needs 1-D homing and limits; B needs SLAM/Nav2, obstacle avoidance and docking. |
| Low collision risk | 4 | 2 | 4 | A and C move in a known, guarded envelope. B shares floor space with people. |
| Maintainability | 5 | 2 | 3 | Fewer moving parts and no battery for A. |
| Scalability | 1 | 4 | 5 | A needs one arm per rack section. C scales linearly with rail length (and vertically with a lift). B scales across racks without infrastructure, at the price of everything above. |
| Experimental feasibility | 5 | 2 | 3 | The research questions (RQ-A to RQ-D) concern perception, cutting and adaptive manipulation at one plant. A lets experiments start soonest and keeps nuisance variables (base pose, rail error) out of the measurements. |

## Result

| Profile | 1st | 2nd | 3rd | Robustness |
|---|---|---|---|---|
| Research prototype | **A** 3.98 | C 3.74 | B 2.48 | A ranks first in 70 % of perturbed trials, C in 30 %, B in 0 % |
| Production scaling | **C** 4.06 | A 3.24 | B 2.92 | C ranks first in ~100 % of trials |

Interpretation:

- B is dominated for this project under both weightings. Its only wins (coverage, flexibility)
  do not serve any current research question, and its re-registration error works directly
  against cut accuracy. It stays optional and deferred (Section 11 of the brief).
- A vs. C is close for the prototype and C is clearly the scale-up answer. The two share the
  arm, end effector, camera and software; they differ by one prismatic axis.

## Decision (recorded as D-003 in `DECISIONS.md`)

Build **A (fixed arm) as prototype v1, designed "rail-ready"**:

1. The arm base mounts on a carriage plate with the bolt pattern of a standard linear-guide
   carriage, clamped to the frame for v1.
2. The kinematic model already contains a `rail_joint` between `rack_frame` and
   `arm_base`, declared as a fixed joint in configuration A and prismatic in C, so URDF,
   planning and calibration code do not change.
3. Cable management leaves service-loop length for a later cable chain.
4. Perception and the plant registry address plants by `(rack, channel, site)`, never by arm
   joint presets.

Consequences: v1 serves one rack section only; throughput figures from v1 will not represent a
production system and must not be reported as such; migrating to C is a mechanical upgrade plus
one more axis in firmware.

## Open question carried into Phase 2: arm kinematics

The cutting plane is horizontal and at a known height above the channel, and plants sit on a
planar grid. That suggests the simplest capable manipulator may be a 4-DOF arrangement (three
translations plus yaw about the vertical), realised either as a Cartesian gantry or as a
SCARA-type arm, rather than a 5/6-DOF articulated arm. The choice depends on approach direction
under the canopy, stiffness at the blade and enclosure footprint. It will be decided with a
workspace/torque/deflection analysis in Phase 2 (pending decision D-010), not by preference.
