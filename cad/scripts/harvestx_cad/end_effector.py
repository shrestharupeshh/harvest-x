"""Concept 3 end effector: under-canopy cradle fork with pivoting slicing blade.

Layout: a low-profile fork head (about 10 mm tall) on a flat boom. The vertical shank,
the blade actuator and the tool flange sit at the rear end of the boom, outside the
maximum canopy radius, so only the thin head and boom travel under the leaves. The
blade is driven through a pull rod along the boom.

Tool frame (mm): origin on the channel top surface at the centre of the stem seat,
+x = approach direction (the fork advances towards +x, the stem enters between the
tine tips and seats at the origin), +z up.
"""

from __future__ import annotations

import math

import cadquery as cq

MM = 1000.0
RGB = {'silver': (0.75, 0.75, 0.78), 'white': (0.95, 0.95, 0.95), 'gray': (0.45, 0.45, 0.48), 'orange': (1.0, 0.55, 0.1), 'lightgray': (0.8, 0.8, 0.82), 'blue': (0.2, 0.4, 0.9), 'green': (0.2, 0.7, 0.3), 'steelblue': (0.27, 0.51, 0.71), 'tan': (0.82, 0.71, 0.55)}


def dims(p: dict) -> dict:
    e = p["end_effector"]
    d = {k: v * MM for k, v in e.items() if isinstance(v, float) and k.endswith("_m")}
    d["shank_b"], d["shank_h"], d["shank_t"] = (x * MM for x in e["shank_tube_m"])
    d["back"] = 60.0  # head length behind the seat
    d["x_shank"] = -(d["back"] + d["boom_length_m"] - 30.0)
    d["pivot"] = (-20.0, d["plate_width_m"] / 2 - 17.0)
    d["z_plate"] = d["skid_thickness_m"]
    d["z_blade"] = d["z_plate"] + d["plate_thickness_m"]
    d["flange_d"], d["flange_t"], d["flange_pcd"] = 63.0, 8.0, 50.0
    d["blade_sweep_deg"] = 85.0
    return d


def fork_plate(d: dict) -> cq.Workplane:
    W, L, back = d["plate_width_m"], d["tine_length_m"], d["back"]
    hs, he, T = d["slot_width_m"] / 2, d["throat_entry_width_m"] / 2, d["plate_thickness_m"]
    x_v = 30.0  # where the parallel slot ends and the V starts
    z = d["z_plate"]
    plate = cq.Workplane("XY").workplane(offset=z).center((L - back) / 2, 0).rect(L + back, W) \
        .extrude(T)
    throat = cq.Workplane("XY").workplane(offset=z - 1).polyline(
        [(0, -hs), (x_v, -hs), (L + 1, -he), (L + 1, he), (x_v, hs), (0, hs)]).close() \
        .extrude(T + 2).union(cq.Workplane("XY").workplane(offset=z - 1).circle(hs).extrude(T + 2))
    plate = plate.cut(throat)
    boom = cq.Workplane("XY").workplane(offset=z).center(-back - d["boom_length_m"] / 2, 0) \
        .rect(d["boom_length_m"], d["boom_width_m"]).extrude(T)
    plate = plate.union(boom)
    for sy in (-1, 1):  # chamfered outer tine corners
        corner = cq.Workplane("XY").workplane(offset=z - 1).polyline(
            [(L - 12, sy * W / 2), (L + 1, sy * W / 2), (L + 1, sy * (W / 2 - 13))]).close() \
            .extrude(T + 2)
        plate = plate.cut(corner)
    # light path for the stem-seated break-beam sensor, through the plate across the seat
    beam = cq.Workplane("XZ").workplane(offset=-W / 2 - 1).center(-4.0, d["z_plate"] + T / 2) \
        .circle(1.5).extrude(-(W + 2))
    plate = plate.cut(beam)
    # blade pivot hole and shank bracket holes
    px, py = d["pivot"]
    plate = plate.faces(">Z").workplane(origin=(0, 0, 0)).pushPoints(
        [(px, py)] + _foot_holes(d)
    ).hole(5.3)
    return plate


def _foot_holes(d: dict) -> list[tuple[float, float]]:
    x = d["x_shank"]
    return [(x - 22, -16), (x - 22, 16), (x + 22, -16), (x + 22, 16)]


def skids(d: dict) -> cq.Workplane:
    """Two UHMW-PE wear pads under the tines; they ride on the channel top surface."""
    L, W, tw = d["tine_length_m"], d["plate_width_m"], d["tine_width_m"]
    pad = cq.Workplane("XY").box(L - 20, tw - 4, d["skid_thickness_m"], centered=(False, True, False))
    y = W / 2 - tw / 2 - 2
    return pad.translate((5, -y, 0)).union(pad.translate((5, y, 0)))


def blade(d: dict, angle_deg: float = 0.0) -> cq.Workplane:
    """Flat blade; angle 0 = parked along +x over the +y tine, negative = closing."""
    px, py = d["pivot"]
    b = cq.Workplane("XY").workplane(offset=d["z_blade"]).center(0, 0) \
        .rect(d["blade_length_m"] + 10, d["blade_width_m"], centered=(False, True)) \
        .extrude(d["blade_thickness_m"]).translate((-10, 0, 0))
    b = b.faces(">Z").workplane(origin=(0, 0, 0)).hole(5.3)
    return b.rotate((0, 0, 0), (0, 0, 1), angle_deg).translate((px, py, 0))


def blade_guard(d: dict) -> cq.Workplane:
    """Cover over the parked blade so no edge is exposed outside the cutting stroke."""
    px, py = d["pivot"]
    z0 = d["z_blade"] + d["blade_thickness_m"] + 0.6
    return cq.Workplane("XY").workplane(offset=z0).center(px + d["blade_length_m"] / 2 - 5, py) \
        .rect(d["blade_length_m"] + 14, d["blade_width_m"] + 8).extrude(1.5)


def actuator_envelope(d: dict) -> cq.Workplane:
    """Space reserved for the sealed blade gearmotor (not a specific product).

    Mounted on the boom in front of the shank, outside the maximum canopy radius.
    """
    x = d["x_shank"] + 50
    return cq.Workplane("XY").workplane(offset=d["z_blade"]).center(x, 0).rect(40, 30).extrude(52)


def pull_rod(d: dict) -> cq.Workplane:
    """Rod from the actuator crank to the blade tail (drawn for the blade-open position)."""
    px, py = d["pivot"]
    x0, x1 = d["x_shank"] + 72, px - 12
    z = d["z_blade"] + d["blade_thickness_m"] + 1.0
    length = math.hypot(x1 - x0, py - 14)
    ang = math.degrees(math.atan2(py - 14, x1 - x0))
    return cq.Workplane("XY").workplane(offset=z).rect(length, 4, centered=(False, True)).extrude(4) \
        .rotate((0, 0, 0), (0, 0, 1), ang).translate((x0, 14, 0))


def shank(d: dict) -> cq.Workplane:
    b, h, t, Ls = d["shank_b"], d["shank_h"], d["shank_t"], d["shank_length_m"]
    z0, x = d["z_blade"], d["x_shank"]
    tube = cq.Workplane("XY").workplane(offset=z0).center(x, 0).rect(b, h).extrude(Ls) \
        .cut(cq.Workplane("XY").workplane(offset=z0).center(x, 0).rect(b - 2 * t, h - 2 * t).extrude(Ls))
    foot = cq.Workplane("XY").workplane(offset=z0).center(x, 0).rect(58, 46).extrude(6)
    foot = foot.faces(">Z").workplane(origin=(0, 0, 0)).pushPoints(_foot_holes(d)).hole(5.3)
    return tube.union(foot)


def flange(d: dict) -> cq.Workplane:
    """Tool-side adapter with 4 x M6 clearance holes on a 50 mm pitch circle."""
    z0 = d["z_blade"] + d["shank_length_m"]
    x = d["x_shank"]
    f = cq.Workplane("XY").workplane(offset=z0).center(x, 0).circle(d["flange_d"] / 2) \
        .extrude(d["flange_t"])
    return f.faces(">Z").workplane(origin=(x, 0, 0)).polarArray(d["flange_pcd"] / 2, 45, 360, 4) \
        .hole(6.6)


def camera_envelope(d: dict) -> cq.Workplane:
    """Space for a low-profile wrist camera on the boom, looking along +x at the stem."""
    return cq.Workplane("XY").workplane(offset=d["z_blade"]).center(-d["back"] - 25, 0).rect(30, 14) \
        .extrude(14)


def head_height(d: dict) -> float:
    """Height of everything that travels under the canopy (head + boom + camera) [mm]."""
    return d["z_blade"] + 14.0


PARTS = {
    # name: (builder, material key or None for envelopes, colour)
    "fork_plate": (fork_plate, "ss304", "silver"),
    "skids": (skids, "uhmw", "white"),
    "blade": (blade, "ss304", "gray"),
    "blade_guard": (blade_guard, "ss304", "orange"),
    "shank": (shank, "al6061_t6", "lightgray"),
    "flange": (flange, "al6061_t6", "lightgray"),
    "pull_rod": (pull_rod, "ss304", "gray"),
    "actuator_envelope": (actuator_envelope, None, "blue"),
    "camera_envelope": (camera_envelope, None, "green"),
}
ENVELOPE_MASS_KG = {"actuator_envelope": 0.25, "camera_envelope": 0.08}  # assumed allowances


def build(p: dict) -> dict[str, cq.Workplane]:
    d = dims(p)
    return {name: fn(d) for name, (fn, _, _) in PARTS.items()}


def assembly(parts: dict[str, cq.Workplane]) -> cq.Assembly:
    a = cq.Assembly(name="end_effector_concept3")
    for name, shape in parts.items():
        a.add(shape, name=name, color=cq.Color(*RGB[PARTS[name][2]]))
    return a


def masses(p: dict, parts: dict[str, cq.Workplane]) -> dict[str, float]:
    out = {}
    for name, shape in parts.items():
        mat = PARTS[name][1]
        if mat is None:
            out[name] = ENVELOPE_MASS_KG[name]
        else:
            out[name] = shape.val().Volume() * 1e-9 * p["materials"][mat]["density"]
    return out


def blade_reaches_stem(d: dict) -> bool:
    """Geometric check: the closing stroke passes fully through a max-diameter seated stem."""
    px, py = d["pivot"]
    r_stem = d["slot_width_m"] / 2 - 1.0
    cx = -d["slot_width_m"] / 2 + r_stem  # stem pushed against the back of the seat
    far = (cx, -r_stem)
    ang = math.degrees(math.atan2(far[1] - py, far[0] - px))
    dist = math.hypot(far[0] - px, far[1] - py)
    return -d["blade_sweep_deg"] <= ang <= 0 and dist <= d["blade_length_m"]


def interference_volumes(parts: dict[str, cq.Workplane], tol: float = 1.0) -> dict[str, float]:
    """Pairwise solid-solid intersection volumes [mm^3] larger than ``tol``."""
    names, out = list(parts), {}
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            v = parts[a].intersect(parts[b]).val()
            vol = v.Volume() if v is not None and hasattr(v, "Volume") else 0.0
            if vol > tol:
                out[f"{a}/{b}"] = vol
    return out
