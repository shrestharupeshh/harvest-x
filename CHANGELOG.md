# Changelog

All notable changes are recorded here. Format follows Keep a Changelog; versions follow SemVer.

## [0.2.0] - 2026-11-15

Phase 2 (mechanical design), first iteration.

### Added
- `mechanical/`: design parameters with assumption tags, `harvestx_mech` calculation library,
  generated calculation report, simulated approach-direction study.
- `cad/`: parametric CadQuery models of the C3 cradle-fork end effector and an envelope-level
  rack fixture; STEP/STL/SVG exports, renders, parts list, mass properties.
- Trade studies for manipulator kinematics and end-effector concept; decisions D-010 and
  D-013 to D-017.
- 25 new tests (calculations, approach study, CAD validity/interference/geometry, state
  machine, integrated study); CI job that
  installs the CAD kernel and regenerates the models.

- `harvesting/`: harvest state machine with simulated gantry and fork (dry-run default,
  e-stop abort, sensor gate, lateral retry) and an integrated perception-to-harvest study.

### Changed
- "Arm" is now a 4-axis Cartesian gantry; no custom articulated arm will be designed.
- Rack layout widened for side entry.

### Still not included
- Hardware, real data, gantry detail design, drawings, BOM, electronics, firmware, ROS 2.

## [0.1.0] - 2026-11-15

Phase 0 (research foundation) and first slice of Phase 1 (perception).

### Added
- Repository governance: licences, contribution rules, status / roadmap / decision records.
- Research foundation: literature review (first pass), gap analysis, comparison table of 25
  works, research questions, bibliography with per-entry verification flags.
- Architecture: three-way trade study with reproducible weighted matrix and sensitivity
  analysis; system requirements; system, mechanical, electrical, software, data-flow,
  control-flow and frame diagrams (Mermaid).
- `harvestx_perception` Python library: procedural RGB-D lettuce-rack simulator with 3D ground
  truth; classical semantic/instance segmentation (ExG, depth, fusion; automatic or
  site-seeded watershed); per-plant features; maturity baselines (size rule, logistic
  regression, random forest) and fresh-mass regression; five cutting-target estimators with
  an empirical uncertainty model; rule-based harvest decision with refusal; metrics with
  cluster bootstrap; end-to-end benchmark and report generator.
- 35 automated tests; GitHub Actions CI (lint, tests, trade-study regeneration check).
- Dataset registry and data-collection protocol draft.

### Not included (see PROJECT_STATUS.md)
- No CAD, electronics, firmware, ROS 2 packages, simulation or dashboard yet.
- No real images and no physical measurements; all reported numbers are synthetic.
