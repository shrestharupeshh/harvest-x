# Next steps

Updated 2026-11-15. Ordered by value; IDs refer to `TASKS.md`.

## Software and research work that needs no hardware

1. **Real-data check of the maturity/biomass baselines (T-012).** Run the existing feature and
   model code on the Autonomous Greenhouse Challenge lettuce RGB-D set (CC BY 4.0, 388 pairs).
   This produces the first non-synthetic numbers and tests how much of the simulator's
   ranking survives.
2. **Arm kinematics study (T-013, decision D-010).** Scripts for workspace, static joint
   torque and blade-tip deflection for gantry, SCARA-type and articulated candidates over the
   2 x 3-site rack, so the simplest capable arm is chosen from numbers.
3. **End-effector concept sheets (T-014)** for the three concepts, sized from published stem
   cutting forces, with capture geometry driven by the stem-scatter finding.
4. **Experimental protocol and research proposal (T-016)**, including power analysis for the
   stem-localisation and end-effector experiments.
5. **Calibration scripts and oblique-view stem verification (T-020, T-021)** so that a
   `VERIFIED` target can exist.
6. **CAD kernel check and first parametric parts (T-015, T-024).**

## Decisions and actions needed from the project owner

These cannot be done from the repository:

| # | Item | Why it matters |
|---|---|---|
| 1 | Confirm the cultivar(s) and growing format (NFT channel size, net-pot size, plant pitch) | Fixes rack geometry, simulator parameters and the test crop |
| 2 | Grow a first batch and measure stem position relative to the net pot (checklist A1–A3) | Single most informative measurement: decides whether top-view stem localisation is a real problem (D-008, D-009) |
| 3 | Choose or lend an RGB-D camera for early image capture | Enables the real dataset before any robot exists |
| 4 | Approximate budget tier (low-cost / recommended / advanced) | Bounds arm and actuator choices in Phase 2 |
| 5 | Access to literature databases (university library login) or exported search results | Needed for the systematic review and to verify [R] references |
| 6 | A development environment with FreeCAD or CadQuery, ROS 2, Gazebo, KiCad and LaTeX | Current cloud environment lacks them; alternatively approve adding them to the environment setup |

## Working assumptions until the owner says otherwise

Butterhead-type lettuce on 100 mm NFT channels at 220 x 240 mm pitch, 50 mm net pots, one
overhead RGB-D camera at about 0.75 m, 10 mm capture tolerance, recommended-tier budget.
