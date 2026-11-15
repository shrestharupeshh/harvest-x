#!/usr/bin/env python3
"""Regenerate all CAD exports from mechanical/design_params.yaml.

    python cad/scripts/build_cad.py

Writes STEP assemblies, per-part STL, SVG views, a custom-parts list and mass
properties under cad/exports/. Requires CadQuery (pip install cadquery).
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "cad/scripts"), str(ROOT / "mechanical")]

import cadquery as cq  # noqa: E402

from harvestx_cad import end_effector as ee  # noqa: E402
from harvestx_cad import rack  # noqa: E402
from harvestx_mech.params import load_params  # noqa: E402

VIEWS = {"top": (0, 0, 1)}
MATERIAL_NAME = {"ss304": "304 stainless steel (grade to be confirmed for food contact)",
                 "al6061_t6": "6061-T6 aluminium", "uhmw": "UHMW-PE", None: "purchased item (envelope)"}


def render(parts: dict, path: Path, title: str, elev=25, azim=-60, tol=0.3):
    """Shaded matplotlib render of tessellated solids ({name: (shape, rgb)})."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    fig = plt.figure(figsize=(8, 6.4))
    ax = fig.add_subplot(111, projection="3d")
    light = np.array([0.3, -0.5, 0.8])
    light /= np.linalg.norm(light)
    lo, hi = np.full(3, np.inf), np.full(3, -np.inf)
    for shape, rgb in parts.values():
        verts, tris = shape.val().tessellate(tol)
        v = np.array([[p.x, p.y, p.z] for p in verts])
        t = v[np.array(tris)]
        n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
        n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
        shade = 0.45 + 0.55 * np.abs(n @ light)
        ax.add_collection3d(Poly3DCollection(t, facecolors=np.outer(shade, rgb), edgecolors="none"))
        lo, hi = np.minimum(lo, v.min(0)), np.maximum(hi, v.max(0))
    c, r = (lo + hi) / 2, (hi - lo).max() / 2
    ax.set(xlim=(c[0] - r, c[0] + r), ylim=(c[1] - r, c[1] + r), zlim=(c[2] - r, c[2] + r),
           xlabel="x [mm]", ylabel="y [mm]", zlabel="z [mm]", title=title)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=elev, azim=azim)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def svg(shape, path: Path, direction, width=900, height=600):
    cq.exporters.export(shape, str(path), opt=dict(width=width, height=height, showAxes=False,
                                                   projectionDir=direction, showHidden=False,
                                                   strokeWidth=0.6))


def main(out: Path = ROOT / "cad/exports") -> dict:
    p = load_params()
    out.mkdir(parents=True, exist_ok=True)
    (out / "stl").mkdir(exist_ok=True)

    parts = ee.build(p)
    asm = ee.assembly(parts)
    asm.export(str(out / "end_effector_concept3.step"))
    masses = ee.masses(p, parts)
    rows = []
    for name, shape in parts.items():
        cq.exporters.export(shape, str(out / "stl" / f"ee_{name}.stl"), tolerance=0.05)
        bb = shape.val().BoundingBox()
        rows.append(dict(part=f"ee_{name}", qty=1, material=MATERIAL_NAME[ee.PARTS[name][1]],
                         mass_kg=round(masses[name], 4),
                         bbox_mm=f"{bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f}",
                         source="custom" if ee.PARTS[name][1] else "allowance (assumed mass)"))
    comp = asm.toCompound()
    for v, d in VIEWS.items():
        svg(comp, out / f"end_effector_{v}.svg", d)
    closed = dict(parts)
    closed["blade"] = ee.blade(ee.dims(p), -ee.dims(p)["blade_sweep_deg"])
    closed.pop("pull_rod")  # the rod is only modelled for the blade-open position
    svg(ee.assembly({k: closed[k] for k in ("fork_plate", "blade", "skids")}).toCompound(),
        out / "end_effector_blade_closed_top.svg", (0, 0, 1))

    rparts = rack.build(p)
    rasm = rack.assembly(rparts)
    rasm.export(str(out / "rack_fixture.step"))
    svg(rasm.toCompound(), out / "rack_fixture_top.svg", (0, 0, 1), 1000, 700)
    img = ROOT / "docs/images"
    img.mkdir(parents=True, exist_ok=True)
    render({k: (v, ee.RGB[ee.PARTS[k][2]]) for k, v in parts.items()}, img / "end_effector_render.png",
           "End effector concept 3 (CAD render, blade parked)", elev=24, azim=-60)
    render({k: (v, rack.RGB[rack.COLORS[k]]) for k, v in rparts.items()}, img / "rack_fixture_render.png",
           "Rack fixture with gantry envelope (CAD render, envelope-level)", elev=20, azim=-60, tol=2.0)

    with (out / "custom_parts.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    props = dict(end_effector_total_kg=round(sum(masses.values()), 4),
                 end_effector_parts_kg={k: round(v, 4) for k, v in masses.items()},
                 head_height_under_canopy_mm=ee.head_height(ee.dims(p)),
                 blade_reaches_stem=ee.blade_reaches_stem(ee.dims(p)),
                 interference_blade_open_mm3=ee.interference_volumes(parts),
                 interference_blade_closed_mm3=ee.interference_volumes(closed),
                 note="CAD-derived masses for custom parts; purchased items are assumed allowances")
    (out / "mass_properties.json").write_text(json.dumps(props, indent=2))
    print(json.dumps(props, indent=2))
    return props


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "cad/exports")
