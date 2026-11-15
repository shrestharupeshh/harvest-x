"""Reference fixture: extrusion frame, NFT channels, gantry envelope, tray (simplified).

Rack frame (mm): origin on the floor at the frame's front-left corner, +x along the
channels, +y across them, +z up. Geometry is envelope-level: extrusions are plain
bars, linear guides and motors are not modelled.
"""

from __future__ import annotations

import cadquery as cq

MM = 1000.0
RGB = {'silver': (0.75, 0.75, 0.78), 'white': (0.95, 0.95, 0.95), 'gray': (0.45, 0.45, 0.48), 'orange': (1.0, 0.55, 0.1), 'lightgray': (0.8, 0.8, 0.82), 'blue': (0.2, 0.4, 0.9), 'green': (0.2, 0.7, 0.3), 'steelblue': (0.27, 0.51, 0.71), 'tan': (0.82, 0.71, 0.55)}
FRAME = dict(x=1300.0, y=1300.0, z=1250.0, bar=40.0)
CHANNEL_TOP_Z = 600.0


def _bar(dx, dy, dz, at):
    return cq.Workplane("XY").box(dx, dy, dz, centered=False).translate(at)


def frame() -> cq.Workplane:
    X, Y, Z, b = FRAME["x"], FRAME["y"], FRAME["z"], FRAME["bar"]
    f = None
    for x in (0, X - b):
        for y in (0, Y - b):
            post = _bar(b, b, Z, (x, y, 0))
            f = post if f is None else f.union(post)
    for z in (100, CHANNEL_TOP_Z - 90, Z - b):
        for y in (0, Y - b):
            f = f.union(_bar(X - 2 * b, b, b, (b, y, z)))
        for x in (0, X - b):
            f = f.union(_bar(b, Y - 2 * b, b, (x, b, z)))
    for x in (300.0, 980.0):  # cross members that carry the channels
        f = f.union(_bar(b, Y - 2 * b, b, (x, b, CHANNEL_TOP_Z - 90)))
    return f


def channel_positions(p: dict):
    r = p["rack"]
    ys = [FRAME["y"] / 2 + (i - (r["n_channels"] - 1) / 2) * r["pitch_across_m"] * MM
          for i in range(r["n_channels"])]
    x0 = 420.0  # first site; leaves a tray/park zone at low x
    xs = [x0 + j * r["pitch_along_m"] * MM for j in range(r["sites_per_channel"])]
    return xs, ys


def channels(p: dict) -> cq.Workplane:
    r = p["rack"]
    w, h, t = r["channel_width_m"] * MM, r["channel_height_m"] * MM, 3.0
    xs, ys = channel_positions(p)
    length = xs[-1] - xs[0] + 300
    out = None
    for y in ys:
        c = cq.Workplane("XY").box(length, w, h, centered=(False, True, False))
        c = c.cut(cq.Workplane("XY").box(length - 2 * t, w - 2 * t, h - 2 * t,
                                         centered=(False, True, False)).translate((t, 0, t)))
        c = c.translate((xs[0] - 150, y, CHANNEL_TOP_Z - h))
        for x in xs:
            c = c.cut(cq.Workplane("XY").workplane(offset=CHANNEL_TOP_Z - t - 1).center(x, y)
                      .circle(r["net_pot_diameter_m"] * MM / 2).extrude(t + 2))
        out = c if out is None else out.union(c)
    return out


def gantry_envelope(p: dict) -> cq.Workplane:
    """X rails on the top frame, Y bridge and Z ram at a representative position."""
    X, Y, Z, b = FRAME["x"], FRAME["y"], FRAME["z"], FRAME["bar"]
    g = p["gantry"]
    bb, hb, _ = (v * MM for v in g["bridge_tube_m"])
    rb, _, _ = (v * MM for v in g["z_ram_tube_m"])
    rails = _bar(X - 2 * b, 20, 20, (b, 10, Z)).union(_bar(X - 2 * b, 20, 20, (b, Y - 30, Z)))
    xs, ys = channel_positions(p)
    xb = xs[1]
    bridge = _bar(bb, Y, hb, (xb - bb / 2, 0, Z + 20))
    y_ram = ys[0] - 420  # over the plant-free flank used for side entry
    ram = _bar(rb, rb, 520, (xb + bb / 2 + 5, y_ram - rb / 2, Z - 380))
    return rails.union(bridge).union(ram)


def tray(p: dict) -> cq.Workplane:
    outer = cq.Workplane("XY").box(260, 400, 80, centered=(False, True, False))
    inner = cq.Workplane("XY").box(254, 394, 78, centered=(False, True, False)).translate((3, 0, 3))
    return outer.cut(inner).translate((70, FRAME["y"] / 2, CHANNEL_TOP_Z - 120))


def camera_bridge() -> cq.Workplane:
    X, Y, Z, b = FRAME["x"], FRAME["y"], FRAME["z"], FRAME["bar"]
    return _bar(20, Y - 2 * b, 20, (X - b - 20, b, Z - b - 30))


def build(p: dict) -> dict[str, cq.Workplane]:
    return {"frame": frame(), "channels": channels(p), "gantry_envelope": gantry_envelope(p),
            "collection_tray": tray(p), "camera_bridge": camera_bridge()}


COLORS = {"frame": "lightgray", "channels": "white", "gantry_envelope": "steelblue",
          "collection_tray": "tan", "camera_bridge": "gray"}


def assembly(parts: dict[str, cq.Workplane]) -> cq.Assembly:
    a = cq.Assembly(name="rack_fixture")
    for name, shape in parts.items():
        a.add(shape, name=name, color=cq.Color(*RGB[COLORS[name]]))
    return a
