# Research questions, hypotheses and metrics

Status: draft v0.1 (2026-11-15). Hypotheses will be frozen (pre-registered in
`research/experimental_protocol.md`, not yet written) before physical data collection.

Experimental unit throughout: the **individual plant**. Repeated images or repeated cut
attempts on one plant are repeated measures. Results are always labelled *simulated*,
*estimated* (analytical) or *measured* (physical).

## RQ-A Visual maturity estimation

*Can harvest readiness be predicted from RGB / RGB-D images, and how much do non-visual records
(age, cultivar, environment) add?*

- Ground truth: fresh shoot mass at destructive harvest (primary); grower's readiness label
  (secondary, with inter-rater agreement).
- Compared methods: single-feature size rule → classical ML on hand features → CNN → multimodal
  (image + plant record).
- H-A1: RGB-D features reduce fresh-mass MAE relative to RGB-only features.
- H-A2: Adding plant age and cultivar improves 5-class macro-F1 over image-only models.
- Metrics: macro-F1, per-class P/R, MAE/MAPE of mass, expected calibration error (ECE).
- Design constraints: plant-level (better: sowing-batch-level) train/val/test split; final test
  on plants never imaged during development.

## RQ-B 3D localisation of the cutting target

*How accurately can the cutting target be located when the stem is occluded, and is the reported
uncertainty honest?*

- Ground truth: stem position at the cutting plane measured after canopy removal with a
  calibrated probe or fiducial, in the robot base frame.
- Compared methods: fixture prior (no vision) → RGB centroid → RGB-D canopy geometry → fusion →
  close-range verification view.
- H-B1: Vision-plus-prior fusion has lower mean in-plane error than the fixture prior alone.
- H-B2: A close-range oblique view that sees the stem reduces error below the end-effector
  capture tolerance for ≥ 95 % of plants.
- H-B3: Nominal 95 % uncertainty regions contain the true target in 90–98 % of cases.
- Metrics: in-plane error (mm; mean, median, 95th percentile), fraction within tolerance,
  coverage of uncertainty regions, ECE of the confidence score.
- Output contract: every target is tagged `PLAUSIBLE`, `LOW_CONFIDENCE` or `VERIFIED`; only a
  direct observation of the stem may set `VERIFIED`.

## RQ-C Harvesting mechanics

*Which end-effector concept gives the highest clean-cut rate with the least damage?*

- Concepts: (1) scissor/guillotine, (2) enclosing gripper with integrated blade, (3) compliant
  stabiliser with separate slicing blade.
- Factors: concept, approach direction, cut height, blade speed/sliding angle.
- Metrics: complete-cut rate, cut-height error, damage score (predeclared rubric, blinded
  rating), peak cutting force and energy, cycle time, cleaning time.
- H-C1: A slicing cut requires lower peak force than a straight chop (motivated by
  `cui2021cutter`).
- H-C2: Stabilising at the base damages fewer marketable leaves than enclosing the head.

## RQ-D Adaptive, closed-loop harvesting

*Does uncertainty-gated behaviour (re-observe, re-plan, reject) outperform a fixed sequence?*

- Conditions: open-loop fixed trajectory to the fixture prior; open-loop to the perception
  target; closed-loop with verification view and gating.
- Metrics: harvest success, damage, cycle time, number of refusals and their correctness.
- H-D1: Closed-loop gating reduces failed + damaging cuts at a cycle-time cost; the trade-off
  curve is reported, not a single operating point.
- Baseline rule (implemented in `harvestx_perception.decision`) must be beaten by any learned
  policy.

## RQ-E System-level performance

Harvest success rate, cut accuracy, damage rate, cycle time, energy per harvest, repeatability,
recovery rate, throughput, reported per configuration with confidence intervals, using the
definitions of Bac et al. where applicable. Failures and negative results are reported.

## Current evidence level

| RQ | Simulated | Estimated | Measured |
|---|---|---|---|
| A | First synthetic benchmark | – | none |
| B | First synthetic benchmark | – | none |
| C | – | – | none |
| D | Rule baseline evaluated on synthetic detections | – | none |
| E | – | – | none |
