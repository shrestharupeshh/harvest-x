# Task list

Ordered by priority within each block. IDs are stable.

## Now (next session)
- [ ] T-012 (blocked: dataset host not reachable from the build environment) AGC lettuce dataset: download locally, write loader, plant-level split, run the
      feature/maturity/mass baselines on real RGB-D (first non-synthetic numbers)
- [ ] T-040 Gantry detail design: select linear modules, guides, drives and brake from
      catalogues (verified data only); workspace check; cable chain; guarding
- [ ] T-041 Hand-held bench rig of the fork + blade (STEP files exist) and test plan for the
      six open risks in `docs/mechanical/mechanical_design.md` §6
- [ ] T-042 Head-retention features (tine rails / hold-down) and boom stiffening rib
- [ ] T-043 Dimensioned drawings and exploded views from the CadQuery model
- [ ] T-045 Improve maturity-gate recall (only 28 of 96 ready plants attempted in simulation):
      threshold study, ordinal models, repeated observation over days
- [ ] T-046 Adaptive lateral search (step scaled to capture width) and larger simulated sample
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
- [x] T-013 Kinematics trade study (D-010)
- [x] T-014 End-effector concept comparison, approach study, C3 CAD and calculations
- [x] T-015 CAD kernel decision (D-016)
- [x] T-044 Stem-seated sensor gate in the harvest state machine; integrated simulation
