# System requirements

Status: v0.1 (2026-11-15). Values marked **(A)** are assumptions awaiting measurement or
literature confirmation; they are tracked in `KNOWN_LIMITATIONS.md` and will be revised.
Verification methods: **T** test, **A** analysis, **I** inspection, **D** demonstration.

## Scope of prototype v1

Stationary robot (architecture A), one rack section of 2 NFT channels x 3 sites, one cultivar,
one complete supervised harvest cycle per plant.

## Functional

| ID | Requirement | Rationale | Verif. |
|---|---|---|---|
| F-01 | Detect and segment every planted site's lettuce in the rack section from the overhead camera. | Workflow steps 2, 6 | T |
| F-02 | Classify each plant into {early, developing, near harvest, harvest ready, overgrown} with a calibrated probability. | RQ-A | T |
| F-03 | Output for each plant: box, mask, centre, cutting target in `base_link`, 3x3 covariance, confidence and a status in {PLAUSIBLE, LOW_CONFIDENCE, VERIFIED}. | RQ-B | T |
| F-04 | Never report VERIFIED without a direct observation of the stem at the cutting plane. | Honesty of uncertainty | T, I |
| F-05 | Decide HARVEST / DEFER / RESCAN / REJECT per plant and be able to refuse. | RQ-D | T |
| F-06 | Plan and execute a collision-free approach to the cutting target within joint, velocity and acceleration limits. | Workflow 8–9 | T (sim), D |
| F-07 | Stabilise the plant, cut the stem at the cutting plane and transfer the head to the collection tray. | Workflow 10–12 | D |
| F-08 | Verify detachment (vision and/or tray mass) and record outcome, images, timing, forces and failures against the plant ID. | Workflow 13–14 | T |
| F-09 | Maintain a unique plant identity from transplant to harvest record. | Experimental integrity | I, T |
| F-10 | Run the same high-level software against simulated and real hardware. | Brief §7 | T |

## Performance (targets for v1, to be confirmed)

| ID | Requirement | Basis | Verif. |
|---|---|---|---|
| P-01 | Cutting-target in-plane error ≤ end-effector capture tolerance for ≥ 95 % of harvest attempts. Capture tolerance design goal: ± 10 mm **(A)**. | Synthetic benchmark shows top-view-only estimates do not meet this with the assumed stem scatter; drives the wrist-camera verification step and the end-effector capture geometry | T |
| P-02 | Cut height within ± 3 mm of commanded height above the channel **(A)**. | Product trim quality; channel clearance | T |
| P-03 | Payload at the tool flange ≥ end effector mass + 0.5 kg product **(A)**; arm sized with torque margin ≥ 2 on the worst static case. | Mature heads assumed ≤ 0.3 kg **(A)** | A, T |
| P-04 | Blade actuator sized for ≥ 5x the largest stem cutting force found in literature for hydroponic lettuce (order 10 N, to be re-read from `wang2021lettuceproperties`, `cui2021cutter`). | Margin for cultivar variation and blade wear | A, T |
| P-05 | TCP repeatability ≤ ± 1 mm at the cutting plane **(A)**. | Small against P-01 budget | T |
| P-06 | Cycle time per plant ≤ 30 s as an initial goal; measured, not optimised, in v1. | Comparable with reported systems (24–33 s, other crops) | T |
| P-07 | Perception latency ≤ 1 s per overhead frame on the selected computer. | Not the bottleneck vs. motion | T |

## Safety

| ID | Requirement | Verif. |
|---|---|---|
| S-01 | Accessible, latching, hard-wired emergency stop removes power from all motors and the blade actuator independently of software. | T, I |
| S-02 | Blade is mechanically guarded whenever it is outside the cutting pose; no exposed edge reachable during manual loading. | I |
| S-03 | Cutting requires: safety chain closed, guard closed, homed, and an operator-set "cut armed" flag that defaults to off at every power-up. | T |
| S-04 | Firmware watchdog stops motion if the main computer link is silent for > 200 ms **(A)**. | T |
| S-05 | Homing is performed at reduced speed and current limit. | T |
| S-06 | Autonomous cutting is disabled during commissioning; first cuts are performed on surrogate stems with the operator outside the guard. | Procedure |
| S-07 | A documented manual-intervention and recovery procedure exists before first power-up. | I |

## Hygiene and materials

| ID | Requirement | Verif. |
|---|---|---|
| H-01 | Product-contact parts (blade, stabiliser pads, tray) are removable without tools for cleaning. | D |
| H-02 | Contact materials are selected from grades commonly used for food contact (e.g. austenitic stainless steel blade, silicone pads). **No compliance is claimed** until the applicable regulations and supplier declarations have been checked. | I |
| H-03 | No lubricated mechanism directly above product without a shield. | I |

## Data and reproducibility

| ID | Requirement | Verif. |
|---|---|---|
| D-01 | Every result is labelled simulated, estimated or measured. | I |
| D-02 | ML splits are made at plant level or coarser; final evaluation uses unseen plants. | I, T |
| D-03 | All CAD, analyses and figures regenerate from scripts and committed configuration. | T (CI) |
| D-04 | Third-party datasets are referenced, never redistributed, unless the licence allows it. | I |
