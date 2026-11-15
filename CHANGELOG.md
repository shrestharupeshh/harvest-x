# Changelog

All notable changes are recorded here. Format follows Keep a Changelog; versions follow SemVer.

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
