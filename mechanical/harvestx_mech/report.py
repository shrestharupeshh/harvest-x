"""Run the reference design case and write docs/mechanical/engineering_calculations.md.

    python -m harvestx_mech.report
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from . import calcs as c
from .params import DEFAULT, load_params

ROOT = Path(__file__).resolve().parents[2]


def design_case(p: dict, ee_mass: float | None = None) -> dict:
    crop, ee, g, sf, mat = p["crop"], p["end_effector"], p["gantry"], p["safety_factors"], p["materials"]
    al, ss = mat["al6061_t6"], mat["ss304"]
    m_tool = (ee_mass if ee_mass is not None else ee["mass_estimate_kg"]) + crop["head_mass_max_kg"]
    r: dict = {"tool_plus_payload_kg": m_tool}

    # 1 cutting
    f_chop = c.stem_cut_force(crop["stem_diameter_max_m"], crop["stem_shear_strength_pa"])
    r["cut"] = dict(force_straight_n=f_chop, design_force_n=f_chop,
                    actuator_torque_nm=c.blade_torque(f_chop, ee["blade_force_radius_m"],
                                                     sf["blade_actuator"]))
    I_bl = c.rect_I(ee["blade_thickness_m"], ee["blade_width_m"])
    s_bl = c.bending_stress(f_chop * ee["blade_force_radius_m"], ee["blade_width_m"] / 2, I_bl)
    r["blade"] = dict(bending_stress_mpa=s_bl / 1e6, fos_yield=ss["yield_pa"] / s_bl)

    # 2 fork tines lifting the head (dynamic factor 2, two tines)
    f_t = crop["head_mass_max_kg"] * c.G * 2 / 2
    I_t = c.rect_I(ee["tine_width_m"], ee["plate_thickness_m"])
    s_t = c.bending_stress(f_t * ee["tine_length_m"], ee["plate_thickness_m"] / 2, I_t)
    # boom: head weight + cut head carried at the end of the flat boom (bending about weak axis)
    Lb = ee["boom_length_m"] + 0.06
    I_bm = c.rect_I(ee["boom_width_m"], ee["plate_thickness_m"])
    head_w = ss["density"] * ee["plate_width_m"] * (ee["tine_length_m"] + 0.06) * ee["plate_thickness_m"]
    F_b = (crop["head_mass_max_kg"] + head_w) * c.G * 2
    s_b = c.bending_stress(F_b * Lb, ee["plate_thickness_m"] / 2, I_bm)
    r["boom"] = dict(load_n=F_b, stress_mpa=s_b / 1e6, fos_yield=ss["yield_pa"] / s_b,
                     tip_deflection_mm=c.cantilever_tip_deflection(F_b, Lb, ss["E_pa"], I_bm) * 1e3)
    r["tine"] = dict(load_per_tine_n=f_t, stress_mpa=s_t / 1e6, fos_yield=ss["yield_pa"] / s_t,
                     tip_deflection_mm=c.cantilever_tip_deflection(
                         f_t, ee["tine_length_m"], ss["E_pa"], I_t) * 1e3)

    # 3 tool-point lateral stiffness: Z ram + shank as one cantilever (conservative: shank section)
    b, h, t = ee["shank_tube_m"]
    L = ee["shank_length_m"] + g["z_ram_overhang_m"]
    I_s = c.rect_tube_I(b, h, t)
    F = ee["lateral_contact_force_n"]
    d_s = c.cantilever_tip_deflection(F, L, al["E_pa"], I_s)
    br, hr, tr = g["z_ram_tube_m"]
    I_r = c.rect_tube_I(br, hr, tr)
    # two-segment cantilever: ram (stiffer) then shank
    Lr, Ls = g["z_ram_overhang_m"], ee["shank_length_m"]
    d_two = (F * Lr**3 / (3 * al["E_pa"] * I_r) + F * Ls * Lr**2 / (2 * al["E_pa"] * I_r)
             + (F * Lr**2 / (2 * al["E_pa"] * I_r) + F * Ls * Lr / (al["E_pa"] * I_r)) * Ls
             + F * Ls**3 / (3 * al["E_pa"] * I_s))
    # torsion: the lateral force acts at the seat, offset from the shank axis by the boom
    arm = ee["boom_length_m"] + 0.03
    G_al = al["E_pa"] / (2 * (1 + 0.33))
    twist = (c.twist_angle(F * arm, Ls, G_al, c.square_tube_J(b, t))
             + c.twist_angle(F * arm, Lr, G_al, c.square_tube_J(br, tr)))
    d_tors = twist * arm
    s_root = c.bending_stress(F * L, hr / 2, I_r)
    r["tool_stiffness"] = dict(lateral_force_n=F, deflection_uniform_shank_mm=d_s * 1e3,
                               deflection_ram_plus_shank_mm=d_two * 1e3,
                               deflection_torsion_mm=d_tors * 1e3,
                               deflection_total_mm=(d_two + d_tors) * 1e3,
                               stiffness_n_per_mm=F / ((d_two + d_tors) * 1e3),
                               ram_root_stress_mpa=s_root / 1e6,
                               fos_yield=al["yield_pa"] / s_root)

    # 4 bridge
    bb, hb, tb = g["bridge_tube_m"]
    W = (g["moving_mass_kg"]["y"] + g["moving_mass_kg"]["z"] + m_tool) * c.G
    I_b = c.rect_tube_I(bb, hb, tb)
    r["bridge"] = dict(load_n=W, deflection_mm=c.simply_supported_center_deflection(
        W, g["bridge_span_m"], al["E_pa"], I_b) * 1e3,
        stress_mpa=c.bending_stress(W * g["bridge_span_m"] / 4, hb / 2, I_b) / 1e6)
    r["bridge"]["fos_yield"] = al["yield_pa"] / (r["bridge"]["stress_mpa"] * 1e6)

    # 5 axes. Each axis carries the masses of the axes it supports.
    mm = g["moving_mass_kg"]
    carried = dict(z=mm["z"] + m_tool, y=mm["y"] + mm["z"] + m_tool,
                   x=mm["x"] + mm["y"] + mm["z"] + m_tool)
    r["axes"] = {}
    for ax in "xyz":
        a = c.axis_requirements(carried[ax], g["a_max_mps2"][ax], g["v_max_mps"][ax], ax == "z",
                                g["friction_coeff"], g["drive"][ax], sf["drive_torque"])
        r["axes"][ax] = dict(carried_mass_kg=carried[ax], **a.__dict__)
    r["power_peak_w"] = sum(v["peak_power_w"] for v in r["axes"].values())

    # 6 flange bolts: 4 x M6 on 50 mm PCD (ISO 9409-1-50-4-M6 pattern)
    M = m_tool * c.G * 2 * 0.10 + F * ee["shank_length_m"]  # 2 g dynamic at 100 mm offset + contact
    T = c.bolt_circle_max_tension(M, m_tool * c.G * 2, 4, 0.050)
    r["flange_bolts"] = dict(moment_nm=M, max_tension_n=T,
                             fos_proof=c.bolt_safety_factor(T, "M6", mat["bolt_a2_70_proof_pa"]))

    # 7 capture probability of the V-throat versus perception error
    half = ee["throat_entry_width_m"] / 2 - crop["stem_diameter_max_m"] / 2
    r["capture"] = dict(usable_half_width_mm=half * 1e3)
    for name, sig in (("fixture_prior_only", 0.0065), ("fusion", 0.0061), ("vision_only_rgbd", 0.0154)):
        r["capture"][name] = c.capture_probability(half, sig)

    # 8 cycle time
    v, a = g["v_max_mps"], g["a_max_mps2"]
    moves = [("traverse to plant (x)", c.trapezoid_time(0.45, v["x"], a["x"])),
             ("descend in the plant-free flank (z)", c.trapezoid_time(0.30, v["z"], a["z"])),
             ("flank traverse towards the channel (y)", c.trapezoid_time(0.25, v["y"], a["y"])),
             ("under-canopy approach (y, 0.15 m at 0.08 m/s)", 0.15 / 0.08),
             ("seat check + cut", 1.0),
             ("lift (z)", c.trapezoid_time(0.30, v["z"], a["z"])),
             ("traverse to tray (x)", c.trapezoid_time(0.60, v["x"], a["x"])),
             ("deposit", 1.0),
             ("perception + planning allowance", 1.0)]
    r["cycle"] = dict(moves=moves, total_s=sum(t for _, t in moves))
    r["cycle"]["plants_per_hour"] = 3600 / r["cycle"]["total_s"]
    return r


def write_markdown(p: dict, r: dict, ee_mass_src: str) -> str:
    crop, ee, g, sf = p["crop"], p["end_effector"], p["gantry"], p["safety_factors"]
    L = ["<!-- GENERATED by `python -m harvestx_mech.report` - do not edit by hand -->",
         "# Engineering calculations (analytical, ESTIMATED)", "",
         "> Closed-form first-order sizing. Inputs marked **A** in "
         "`mechanical/design_params.yaml` are assumptions. Nothing here is a measurement, and "
         "no finite-element analysis has been run. Formulas are in "
         "`mechanical/harvestx_mech/calcs.py` with unit tests.", "",
         f"Tool + payload mass used: **{r['tool_plus_payload_kg']:.2f} kg** ({ee_mass_src}).", "",
         "## 1. Cutting force and blade actuator", "",
         f"Upper bound for a straight chop: F = tau x pi d^2 / 4 with tau = "
         f"{crop['stem_shear_strength_pa'] / 1e6:.2f} MPa (**assumed placeholder**) and d = "
         f"{crop['stem_diameter_max_m'] * 1e3:.0f} mm gives **{r['cut']['force_straight_n']:.0f} N**. "
         "No reduction is credited for the slicing action, although published work on lettuce "
         "stems reports large reductions with a sliding cut.", "",
         f"- Actuator torque at {ee['blade_force_radius_m'] * 1e3:.0f} mm radius with safety factor "
         f"{sf['blade_actuator']:.0f}: **{r['cut']['actuator_torque_nm']:.1f} N·m**",
         f"- Blade in-plane bending stress {r['blade']['bending_stress_mpa']:.0f} MPa, factor of "
         f"safety on yield {r['blade']['fos_yield']:.1f} (annealed 304; a hardened blade steel "
         "is stronger). Lateral buckling and edge loading are not analysed.",
         "- The blade closes against the fork edge, so the cutting force is internal to the end "
         "effector and is not transmitted to the gantry.", "",
         "## 2. Fork tines carrying the cut head", "",
         f"- Load per tine (2x dynamic factor): {r['tine']['load_per_tine_n']:.1f} N at the tip",
         f"- Bending stress {r['tine']['stress_mpa']:.0f} MPa, factor of safety "
         f"{r['tine']['fos_yield']:.1f}; tip deflection {r['tine']['tip_deflection_mm']:.2f} mm", "",
         "## 2b. Flat boom (weak-axis bending)", "",
         f"- Load {r['boom']['load_n']:.1f} N (cut head + fork head, 2x dynamic) at the boom end: "
         f"stress {r['boom']['stress_mpa']:.0f} MPa, factor of safety {r['boom']['fos_yield']:.1f}; "
         f"free-air tip sag **{r['boom']['tip_deflection_mm']:.1f} mm** when lifted clear of the "
         "channel", "",
         "## 3. Tool-point lateral stiffness", "",
         f"Z ram ({g['z_ram_overhang_m'] * 1e3:.0f} mm overhang) plus shank "
         f"({ee['shank_length_m'] * 1e3:.0f} mm) as a stepped cantilever under "
         f"{r['tool_stiffness']['lateral_force_n']:.0f} N lateral contact force (assumed):", "",
         f"- Bending {r['tool_stiffness']['deflection_ram_plus_shank_mm']:.2f} mm + torsion of the "
         f"tubes acting over the boom offset {r['tool_stiffness']['deflection_torsion_mm']:.2f} mm = "
         f"**{r['tool_stiffness']['deflection_total_mm']:.2f} mm** at the stem seat (stiffness "
         f"{r['tool_stiffness']['stiffness_n_per_mm']:.1f} N/mm); joint and guide compliance are "
         "not included, so the real value will be larger. This is small against the 25 mm "
         "capture half-width, and the fork is located vertically by the channel, not by the ram.",
         f"- Ram root stress {r['tool_stiffness']['ram_root_stress_mpa']:.1f} MPa, factor of safety "
         f"{r['tool_stiffness']['fos_yield']:.0f}", "",
         "## 4. Y bridge", "",
         f"- Central load {r['bridge']['load_n']:.0f} N on a {g['bridge_span_m'] * 1e3:.0f} mm span: "
         f"deflection {r['bridge']['deflection_mm']:.3f} mm, stress {r['bridge']['stress_mpa']:.1f} "
         f"MPa, factor of safety {r['bridge']['fos_yield']:.0f}",
         "- Section is a hollow-rectangle idealisation; replace with the extrusion "
         "manufacturer's section properties when the profile is selected.", "",
         "## 5. Axis drive requirements", "",
         f"Torque includes safety factor {sf['drive_torque']:.0f}.", "",
         "| axis | drive | carried mass [kg] | thrust [N] | motor torque [N·m] | speed [rpm] | "
         "peak power [W] | gravity holding torque [N·m] |", "|---|---|---|---|---|---|---|---|"]
    for ax, v in r["axes"].items():
        L.append(f"| {ax.upper()} | {g['drive'][ax]['type']} | {v['carried_mass_kg']:.1f} | "
                 f"{v['thrust_n']:.0f} | {v['torque_nm']:.2f} | {v['motor_rpm']:.0f} | "
                 f"{v['peak_power_w']:.0f} | {v['holding_torque_nm']:.3f} |")
    L += ["", f"Sum of peak mechanical power {r['power_peak_w']:.0f} W (axes never peak together; "
          "electrical sizing in Phase 4 adds driver efficiency, logic, lighting and compute). "
          "The Z axis needs a brake or a self-locking drive: gravity holding torque is non-zero.", "",
          "## 6. Tool-flange bolts (4 x M6 on 50 mm pitch circle)", "",
          f"- Moment {r['flange_bolts']['moment_nm']:.1f} N·m, max bolt tension "
          f"{r['flange_bolts']['max_tension_n']:.0f} N, factor of safety on A2-70 proof load "
          f"**{r['flange_bolts']['fos_proof']:.0f}** (preload and fatigue not analysed)", "",
          "## 7. Stem capture by the V-throat", "",
          f"Usable half-width (entry half-width minus stem radius): "
          f"{r['capture']['usable_half_width_mm']:.0f} mm. Probability that the lateral error is "
          "inside it, using the 1-sigma errors from the **synthetic** perception benchmark:", "",
          "| target source | sigma [mm] | P(captured) |", "|---|---|---|",
          f"| fixture prior only | 6.5 | {r['capture']['fixture_prior_only']:.5f} |",
          f"| RGB-D + fixture fusion | 6.1 | {r['capture']['fusion']:.5f} |",
          f"| RGB-D vision only | 15.4 | {r['capture']['vision_only_rgbd']:.4f} |", "",
          "Gaussian tails are optimistic; gross errors (wrong plant, leaning stem outside the net "
          "pot) are not covered and are the reason for the stem-seated sensor.", "",
          "## 8. Cycle-time estimate", "", "| step | time [s] |", "|---|---|"]
    L += [f"| {n} | {t:.2f} |" for n, t in r["cycle"]["moves"]]
    L += [f"| **total** | **{r['cycle']['total_s']:.1f}** |", "",
          f"About {r['cycle']['plants_per_hour']:.0f} plants per hour for one tool on one rack "
          "section, **estimated** from kinematic limits only. Not a throughput claim.", ""]
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", type=Path, default=DEFAULT)
    ap.add_argument("--out", type=Path, default=ROOT / "docs/mechanical/engineering_calculations.md")
    a = ap.parse_args(argv)
    p = load_params(a.params)
    mass_file = ROOT / "cad/exports/mass_properties.json"
    ee_mass, src = None, "assumed value from design_params.yaml"
    if mass_file.exists():
        ee_mass = json.loads(mass_file.read_text())["end_effector_total_kg"]
        src = "end-effector mass from the CAD model + maximum head mass"
    r = design_case(p, ee_mass)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(write_markdown(p, r, src))
    print(a.out.read_text())
    assert math.isfinite(r["cycle"]["total_s"])


if __name__ == "__main__":
    main()
