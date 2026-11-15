# Task list

Ordered by priority within each block. IDs are stable.

## Now (next session)
- [ ] T-012 AGC lettuce dataset: download locally, write loader, plant-level split, run the
      feature/maturity/mass baselines on real RGB-D (first non-synthetic numbers)
- [ ] T-013 Arm kinematics study for D-010: workspace + static torque + deflection scripts for
      gantry, SCARA-type and articulated options, with tests
- [ ] T-014 End-effector concept sheets (three concepts) with force estimates from literature
- [ ] T-015 Check which CAD kernel installs in CI (CadQuery/OCP vs. FreeCAD) and record D-0xx
- [ ] T-016 `research/experimental_protocol.md` and `research/research_proposal.md`

## Soon
- [ ] T-020 Calibration scripts (intrinsics, extrinsics, hand-eye) + synthetic validation
- [ ] T-021 Oblique-view simulator and stem verification estimator (`VERIFIED` status)
- [ ] T-022 Image-based occupancy cross-check against the registry
- [ ] T-023 Plant registry / experiment database schema (SQLite) with validation tests
- [ ] T-024 Rack and fixture CAD; BOM skeleton with verified supplier data only
- [ ] T-025 URDF/Xacro with rail joint; ROS 2 distribution verification (D-011)

## Research hygiene
- [ ] T-030 Verify all 19 [R] and 14 [V*] bibliography entries against publisher pages
- [ ] T-031 Systematic database search with query log; read top-10 papers in full; re-extract
      Vegebot figures from the full text
- [ ] T-032 Locate the two unconfirmed lettuce papers noted in `literature_review.md` §9
- [ ] T-033 Vendor CERN-OHL-P-2.0 and CC-BY-4.0 texts under `LICENSES/`

## Done
- [x] T-001 Tooling inventory and repository conventions
- [x] T-002 Literature review first pass, comparison table, gap analysis, research questions
- [x] T-003 Architecture trade study, requirements, diagrams
- [x] T-004 Synthetic RGB-D generator
- [x] T-005 Segmentation, features, maturity, stem localisation, decision baseline
- [x] T-006 Benchmark + report + tests + CI
- [x] T-007 Dataset registry and data-collection protocol draft
