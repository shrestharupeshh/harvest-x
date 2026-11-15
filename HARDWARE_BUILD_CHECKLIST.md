# Hardware build and physical-work checklist

Nothing on this list has been done. Items are ordered so that early, cheap measurements
de-risk later purchases. An item is ticked only with a dated log entry and evidence (photo,
data file, calibration report) referenced beside it.

## A. Before buying robot hardware (cheap, high information)
- [ ] A1 Grow one batch (≥ 12 plants) of the chosen cultivar in the intended NFT channel and
      net pots; follow `data/data_collection_protocol.md`.
- [ ] A2 Measure stem position relative to net-pot centre at the cutting plane for every
      plant (decides whether top-view stem localisation is needed at all; D-008/D-009).
- [ ] A3 Measure stem diameter, canopy diameter/height and fresh mass at harvest.
- [ ] A4 Capture overhead RGB-D images through the growth cycle with the candidate camera.
- [ ] A5 Hand-held fork-and-blade trials (parts from `cad/exports/`): does the stem seat,
      does the head stay on the fork, are low leaves trapped, does the plate clear the
      net-pot lip, cutting force with a spring scale or load cell, cut quality.
- [ ] A6 Measure net-pot lip height and plug height above the channel.

## B. Fixture and growing system
- [ ] B1 Frame, channels, reservoir, pump, lighting assembled and leak-tested
- [ ] B2 Environment sensors installed and logging
- [ ] B3 Plant ID tags and registry in use

## C. Fabrication and assembly (after Phase 2/6 packages exist)
- [ ] C1 Printed/machined parts inspected against critical dimensions
- [ ] C2 Arm assembled; fasteners torqued and marked
- [ ] C3 End effector assembled with blade guard fitted before any blade is installed

## D. Electrical inspection (power off, then current-limited)
- [ ] D1 Continuity, polarity, insulation and fuse ratings checked against the wiring diagram
- [ ] D2 E-stop chain test: motors and blade lose power with the main computer unplugged
- [ ] D3 Logic rails verified before connecting controllers

## E. Motion commissioning (no blade installed)
- [ ] E1 Each motor jogged at reduced current; direction and encoder sign verified
- [ ] E2 Limit switches, homing and soft limits verified
- [ ] E3 Watchdog and communication-loss stop verified

## F. Calibration
- [ ] F1 Camera intrinsics with reprojection-error report
- [ ] F2 Camera-to-rack and rack-to-base extrinsics with independent check points
- [ ] F3 Arm repeatability test at the cutting plane
- [ ] F4 Load cell calibration with reference masses

## G. Safety validation (before any powered cut)
- [ ] G1 Guarding and interlock inspection
- [ ] G2 Written manual-intervention procedure rehearsed
- [ ] G3 Blade actuator tests on surrogate stems with the operator outside the guard
- [ ] G4 "Cut armed" defaults to off after every power cycle (tested)

## H. Controlled harvesting trials
- [ ] H1 Pre-registered protocol frozen
- [ ] H2 Supervised single-plant harvest cycle demonstrated repeatedly
- [ ] H3 Experiments 3–6 executed and logged; failures recorded

## Requires the project owner
Purchases, access to a workspace with mains power and water, growing plants, all assembly and
measurement work, and every safety sign-off.
