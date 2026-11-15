# Known limitations

Last updated 2026-11-15. This file is deliberately blunt.

## Project-level
- **No hardware exists.** No electronics, firmware, ROS 2 code, robot simulation or dashboard
  has been produced yet. The perception library, the research and architecture documents,
  first-iteration CAD of one end effector and analytical calculations exist.
- **No real data.** Not a single real image or measurement has been used. Every number in
  the repository is *simulated*.
- **Toolchain gaps in the build environment:** FreeCAD, Blender, ROS 2, Gazebo, KiCad and
  LaTeX were not available, and DOI/publisher and dataset hosts were not reachable. Work that needs them
  is planned, not done.

## Literature review
- Web-search based, abstract-level, English-biased; 19 bibliography entries are recalled and
  not machine-verified ([R]); several quantitative figures come from secondary summaries.
- "Not found" statements describe this search, not the state of the art.

## Synthetic data generator
- Leaves are flat, tapered ellipses with Lambert shading. No curl, ruffles, translucency,
  specular highlights, water, roots, algae, tip burn or true cast shadows.
- Growth model parameters (mass curve, diameter and leaf-count allometry, class thresholds,
  bolting probability) are **assumed**, not fitted to plants.
- Stem scatter in the net pot (6 mm per axis), plant lean, depth noise model and calibration
  error (2 mm / 0.3 deg camera, 2 mm rack) are **assumed**. The headline localisation result
  depends directly on these numbers.
- One cultivar per tray, one top-down camera pose family, one rack layout.
- Python's process is deterministic for a given seed, but results can differ slightly across
  NumPy/OpenCV versions.

## Perception pipeline
- Stem estimators infer a hidden stem from the canopy. They cannot be better than the
  canopy–stem relationship allows; nothing here observes the stem.
- `VERIFIED` targets are not implemented (needs a wrist/oblique view).
- The uncertainty model is isotropic, Gaussian and fitted per rig; it reports average
  behaviour and will be wrong for unusual plants.
- Site-seeded segmentation needs correct site occupancy from the registry. A plain watershed
  let a tall plant absorb a shorter neighbour (site errors > 200 mm in ~1–2 % of plants of
  overgrown trays); compact watershed removed this in simulation. The compactness value was
  chosen on a sample that overlapped the test trays, which is acceptable for a smoke
  benchmark but would be a protocol violation with real data.
- ExG segmentation fails on red-leaf cultivars by construction; depth is required for them.
- Maturity models are trained on synthetic features only and are not transferable.
- Runtime was measured on a cloud CPU, not on an embedded target.

## Mechanical design
- The end effector is a first-iteration concept that has never been made or tried on a plant.
  Its key premises (a stem seats in a V-throat, a head stays on the fork, low leaves tolerate
  a 25 mm tall tool sliding under them) are untested.
- Cutting force uses a placeholder shear strength (0.35 MPa); crop dimensions, net-pot lip
  height and stem scatter are assumptions.
- Calculations are closed-form and first-order: no FEA, fatigue, bearing life, bolt preload,
  blade buckling or dynamics. Gantry moving masses are guesses until modules are selected.
- The approach study treats leaves as rigid and fixed; it bounds contact, not damage.
- The rack and gantry CAD is envelope-level (plain bars); the purchased gearmotor and camera
  are space reservations with assumed masses. No dimensioned drawings exist.
- Trade-study scores are engineering judgement.

## Decision baseline
- Evaluated as a perception-only upper bound with an ideal manipulator; no reachability,
  collision or cutting model yet. With the provisional 10 mm tolerance it refuses most ready
  plants, which reflects the tolerance/uncertainty mismatch rather than a tuned policy.

## Safety and compliance
- No safety function has been designed in detail, built or tested. No food-contact,
  machinery or electrical compliance is claimed anywhere.
