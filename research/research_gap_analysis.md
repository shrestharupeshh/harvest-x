# Research gap analysis and candidate contribution

Status: first pass (2026-11-15), based on [`literature_review.md`](literature_review.md) and its
stated limits. Gaps are phrased as "not found in this search", never as "does not exist".

## 1. Gaps

| ID | Gap | Evidence | Confidence the gap is real |
|---|---|---|---|
| G1 | No open, integrated, peer-reviewed robot for **hydroponic** lettuce harvesting; existing work is either field iceberg (Vegebot) or isolated component studies (cutter mechanics, gripper damage, phenotyping). | Lit. review §2 | Medium (non-English literature under-searched) |
| G2 | Lettuce vision work estimates traits (fresh weight, growth stage); few studies turn this into a **harvest decision with calibrated confidence and the option to refuse**. | §3 | Medium–high |
| G3 | The **stem is occluded** in top views of rosette lettuce. No study found reports cutting-target error in millimetres for hydroponic lettuce or distinguishes a plausible target from a verified one. | §4 | Medium |
| G4 | In structured CEA the plant site is known from fixture geometry. Papers do not report whether vision **beats the fixture prior**, so the value added by perception is unquantified. | §4 | High (methodological, easy to check per paper) |
| G5 | Perception uncertainty is rarely propagated into the manipulation decision (approach, re-observe, reject). Closed-loop vs. open-loop harvesting is seldom compared under a controlled protocol. | §1, §6 | Medium |
| G6 | End-effector studies for lettuce are bench tests of one mechanism; there is no controlled **comparison of several cutting/stabilising concepts on the same plants** with damage as an outcome. | §2, §5 | Medium |
| G7 | Performance reporting is inconsistent (success, damage, cycle time defined per paper), and plant-level independence is often ignored in ML evaluation. | §1, §3; Bac et al. | High |
| G8 | No public **RGB-D dataset with stem / cutting-point ground truth** for lettuce on a growing fixture; the AGC dataset shows isolated plants only. | §3, §7 | Medium–high |

## 2. What HARVEST-X can credibly contribute

The overall idea (a robot that harvests lettuce) is not novel. Candidate contributions, ranked
by the ratio of expected scientific value to what a single-investigator prototype can deliver:

**C1 — Uncertainty-aware cutting-target localisation under full stem occlusion, benchmarked
against the fixture prior (addresses G3, G4, G5, G8).**
Question: on a growing fixture with known plant sites, how much does RGB / RGB-D perception
reduce cutting-target error relative to the fixture prior alone, is the reported uncertainty
calibrated, and does gating the cut on that uncertainty (re-observe / reject) reduce failed or
damaging cuts? This is measurable in millimetres with a simple ground-truth rig, needs tens of
plants rather than thousands, and yields a reusable dataset. It is the recommended primary
contribution (maps to candidate Paper 2, merged with the adaptive element of Paper 3).

**C2 — Controlled comparison of three end-effector concepts on identical fixtures (G6).**
Bench-level experiment (cut success, cut-height error, damage score, force/energy) that can run
before the arm exists, using a manual or single-axis positioning rig. Lower risk than a full
robot and directly publishable as an engineering study (candidate Paper 4).

**C3 — Open, reproducible platform and protocol (G1, G7).**
CAD, firmware, software, simulator, data schema and predeclared metrics released together. On
its own this is a systems/"resource" contribution whose value depends on physical validation;
it becomes credible once C1 or C2 results exist (candidate Paper 1).

**C4 — Harvest-readiness decision with refusal (G2).** Worth doing as part of the platform, but
as a stand-alone paper it competes with a crowded phenotyping literature and needs destructive
ground truth from many plants. Treated as a secondary analysis.

Mobile manipulation is not a contribution candidate at this stage: none of the gaps depends on
mobility.

## 3. Early evidence from our own synthetic benchmark

The first synthetic benchmark ([`perception/results/synthetic_v0/REPORT.md`](../perception/results/synthetic_v0/REPORT.md))
was built specifically around G3/G4. In that simulator the fixture prior alone is more accurate
than any canopy-based vision estimate, and fusing vision with the prior gives only a small
improvement. **This is a property of an idealised simulator with assumed parameters (stem
scatter in the net pot, plant lean, calibration error), not a finding about real plants.** Its
value is that it turns G4 into a concrete, falsifiable experimental question and shows which
physical quantities must be measured first:

1. the real distribution of stem position relative to the net-pot centre;
2. the real relationship between canopy centroid and stem position (lean, asymmetry);
3. the capture tolerance of each end-effector concept.

If (1) is small compared with (3), top-view stem localisation is unnecessary and the research
emphasis should shift to C2 and to close-range verification; if not, C1 is the core problem.
Either outcome is reportable.

## 4. Risks to the contribution

| Risk | Mitigation |
|---|---|
| A closer prior system exists in literature not yet searched | Systematic database search before writing any novelty statement (TASKS.md) |
| Synthetic-to-real gap makes simulator conclusions misleading | Simulator results are never reported as performance; first real images are top priority |
| Too few plants for statistical power | Predeclare effect sizes and sample sizes; plant is the experimental unit; staggered sowing |
| Cultivar dependence | Fix one cultivar for the primary experiment, replicate on a second |
