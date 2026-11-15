# CAD — status: Implemented (first iteration), not built

Parametric CadQuery models generated from `mechanical/design_params.yaml`.

| Path | Content |
|---|---|
| `scripts/harvestx_cad/end_effector.py` | Concept C3: cradle fork, boom, pivoting blade, guard, skids, shank, flange, pull rod, actuator and camera envelopes; interference and reach checks |
| `scripts/harvestx_cad/rack.py` | Envelope-level rack fixture with gantry envelope |
| `scripts/build_cad.py` | Regenerates everything in `exports/` and the renders in `docs/images/` |
| `exports/` | STEP assemblies, STL parts, SVG top views, custom-parts list, mass properties |

```bash
pip install -e ".[dev,cad]"
```

```bash
python cad/scripts/build_cad.py
```

CadQuery was chosen over FreeCAD scripting because it installs with `pip`, runs headless in
CI and uses the same OpenCASCADE kernel; STEP output opens in FreeCAD, SolidWorks or Fusion
(decision D-016). Design rationale: `docs/mechanical/mechanical_design.md`.

Missing: dimensioned drawings, exploded views, gantry detail design, concepts C1/C2 as CAD,
mobile base. Licence: CERN-OHL-P-2.0.
