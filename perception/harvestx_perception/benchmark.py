"""Reproducible perception benchmark on procedurally generated (SYNTHETIC) scenes.

Usage::

    python -m harvestx_perception.benchmark --out perception/results/synthetic_v0

Everything reported by this script is a SYNTHETIC result. It measures how the
algorithms behave on an idealised geometric simulator and is used to (a) verify the
software end to end and (b) rank baselines before real data exist. It is not evidence
of real-world performance.

Statistical design
------------------
* The experimental unit is the *tray* (a set of physical plants). Each tray is imaged
  ``n_views`` times; those images are repeated measures, not independent samples.
* Train / validation / test splits are made at tray level, so no plant appears in two
  splits. Confidence intervals use a cluster bootstrap over trays.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np
from sklearn.metrics import confusion_matrix, f1_score

from . import decision as dec
from .camera import make_T, rot_x, rot_y, rot_z
from .evaluation.metrics import (
    average_precision,
    cluster_bootstrap_ci,
    expected_calibration_error,
    iou_matrix,
    match_instances,
    prf,
)
from .features import RGB_FEATURES, RGBD_FEATURES
from .localization.stem import METHODS, SIZE_SCALED, VISION_METHODS, fuse
from .maturity.models import FeatureModel, SizeRuleBaseline, mass_regressor
from .pipeline import PipelineConfig, process_frame
from .synthetic.growth import CULTIVARS, MATURITY_CLASSES
from .synthetic.scene import SceneConfig, SceneSample, render_scene, sample_tray

CHI2_2DOF_95 = 5.991
# Assumed calibration quality injected into the simulator (1-sigma). The perception
# code never sees the true camera pose or the true rack position.
CAM_SIGMA_T = 0.002  # camera-to-base translation [m]
CAM_SIGMA_ROT = float(np.deg2rad(0.3))  # camera-to-base rotation [rad]
RACK_SIGMA = 0.002  # rack-to-base registration, in-plane [m]


def generate(cfg: SceneConfig, n_trays: int, n_views: int, seed: int) -> list[SceneSample]:
    samples = []
    for t in range(n_trays):
        tray_id = f"T{t:04d}"
        plants = sample_tray(cfg, np.random.default_rng([seed, t, 0]))
        cal = np.random.default_rng([seed, t, 999])
        rack_shift = np.append(cal.normal(0, RACK_SIGMA, 2), 0.0)
        for v in range(n_views):
            s = render_scene(cfg, np.random.default_rng([seed, t, v + 1]), tray_id, plants)
            a = cal.normal(0, CAM_SIGMA_ROT, 3)
            dT = make_T(rot_x(a[0]) @ rot_y(a[1]) @ rot_z(a[2]), cal.normal(0, CAM_SIGMA_T, 3))
            s.meta.update(view=v, T_base_cam_est=s.T_base_cam @ dT,
                          sites_est=s.rack.sites() + rack_shift)
            samples.append(s)
    return samples


def split_trays(tray_ids: list[str], seed: int, frac=(0.6, 0.2, 0.2)) -> dict[str, str]:
    ids = sorted(set(tray_ids))
    np.random.default_rng(seed).shuffle(ids)
    n_tr, n_va = int(frac[0] * len(ids)), int(frac[1] * len(ids))
    return {t: ("train" if i < n_tr else "val" if i < n_tr + n_va else "test")
            for i, t in enumerate(ids)}


def run(s: SceneSample, cfg: PipelineConfig, model=None):
    r = s.rack
    # Site occupancy is taken from the plant registry (which sites were planted); it is
    # operational knowledge, not something perception has to infer.
    occupied = np.zeros(len(s.meta["sites_est"]), bool)
    occupied[[p.site_index for p in s.plants]] = True
    return process_frame(s.rgb, s.depth, s.intrinsics, s.meta["T_base_cam_est"],
                         s.meta["sites_est"], r.plane_z, r.cut_height, cfg, model, occupied)


def eval_segmentation(samples: list[SceneSample], cfg: PipelineConfig) -> dict:
    thresholds = np.arange(0.5, 0.96, 0.05)
    scores, tps = [], defaultdict(list)
    n_gt, ious = 0, []
    miss_by_cult, gt_by_cult = Counter(), Counter()
    for s in samples:
        res = run(s, cfg)
        gt_lab = s.instances.astype(np.int32)
        for p in s.plants:
            if p.visible_px < cfg.min_area_px:
                gt_lab[gt_lab == p.instance_id] = 0  # too small to be a fair target
        iou, g_ids, p_ids = iou_matrix(gt_lab, res.labels)
        n_gt += len(g_ids)
        by_label = {o.label: o for o in res.observations}
        cult = {p.instance_id: p.cultivar for p in s.plants}
        for th in thresholds:
            matched = {j for _, j, _ in match_instances(iou, th)}
            tps[round(float(th), 2)].extend(j in matched for j in range(len(p_ids)))
        m50 = match_instances(iou, 0.5)
        ious.extend(v for _, _, v in m50)
        hit = {int(g_ids[i]) for i, _, _ in m50}
        for g in g_ids:
            gt_by_cult[cult[int(g)]] += 1
            miss_by_cult[cult[int(g)]] += int(g) not in hit
        scores.extend(by_label[int(j)].score for j in p_ids)
    tp = int(np.sum(tps[0.5]))
    out = prf(tp, len(scores) - tp, n_gt - tp)
    out.update(
        ap50=average_precision(scores, tps[0.5], n_gt),
        ap50_95=float(np.mean([average_precision(scores, tps[round(float(t), 2)], n_gt)
                               for t in thresholds])),
        mean_iou_matched=float(np.mean(ious)) if ious else 0.0,
        n_gt=n_gt, n_pred=len(scores),
        recall_by_cultivar={c: 1 - miss_by_cult[c] / gt_by_cult[c] for c in sorted(gt_by_cult)},
    )
    return out


def collect_rows(samples, split, cfg: PipelineConfig, model=None) -> list[dict]:
    rows = []
    for s in samples:
        res = run(s, cfg, model)
        iou, g_ids, p_ids = iou_matrix(s.instances.astype(np.int32), res.labels)
        by_label = {o.label: o for o in res.observations}
        truth = {p.instance_id: p for p in s.plants}
        for i, j, v in match_instances(iou, 0.5):
            o, p = by_label[int(p_ids[j])], truth[int(g_ids[i])]
            gt = np.array(p.cut_target)
            row = dict(tray=s.meta["tray_id"], view=s.meta["view"],
                       split=split[s.meta["tray_id"]], plant_id=p.plant_id, iou=v,
                       cultivar=p.cultivar, age_days=p.age_days, mass=p.fresh_mass_g,
                       maturity=p.maturity, r_eq=o.features["eq_diameter_m"] / 2, gt_cut=p.cut_target,
                       obs=o, **o.features)
            for meth, est in o.stem_candidates.items():
                row[f"err_{meth}"] = float(np.linalg.norm(est - gt))
            if o.cut_target_base is not None:
                row["err_selected"] = float(np.linalg.norm(o.cut_target_base - gt))
            rows.append(row)
    return rows


def col(rows, key, default=np.nan):
    return np.array([r.get(key, default) for r in rows], dtype=float)


def calibrate_sigma(train_rows) -> dict[str, float]:
    """Fit the per-method sigma model on training trays.

    Robust estimator: for an isotropic 2D Gaussian the radial error is Rayleigh
    distributed with median = sigma * sqrt(2 ln 2), so sigma = median / 1.1774. The
    median is used instead of the RMS so that rare gross errors (wrong association)
    do not inflate sigma for every plant.
    """
    out = {}
    for m in (*VISION_METHODS, "site_prior"):
        e, r = col(train_rows, f"err_{m}"), col(train_rows, "r_eq")
        ok = np.isfinite(e) & np.isfinite(r) & (r > 0)
        z = e[ok] / r[ok] if m in SIZE_SCALED else e[ok]
        out[m] = float(np.median(z) / np.sqrt(2 * np.log(2)))
    return out


def select_fusion_method(val_rows, sigma: dict[str, float]) -> tuple[str, dict[str, float]]:
    """Pick the vision estimate to fuse with the site prior, on VALIDATION trays only."""
    scores = {}
    for m in VISION_METHODS:
        errs = []
        for r in val_rows:
            c = r["obs"].stem_candidates
            if m in c and "site_prior" in c:
                est, _ = fuse([(c[m], sigma[m] * r["r_eq"]), (c["site_prior"], sigma["site_prior"])])
                errs.append(np.linalg.norm(est - np.array(r["gt_cut"])))
        scores[m] = float(np.mean(errs)) * 1000 if errs else float("inf")
    return min(scores, key=scores.get), scores


def eval_localization(test_rows, tol: float) -> dict:
    groups = np.array([r["tray"] for r in test_rows])
    out = {}
    for m in METHODS:
        e = col(test_rows, f"err_{m}") * 1000
        ok = np.isfinite(e)
        lo, hi = cluster_bootstrap_ci(groups, lambda idx, e=e: float(np.nanmean(e[idx])), 500)
        out[m] = dict(n=int(ok.sum()), mean_mm=float(np.nanmean(e)),
                      median_mm=float(np.nanmedian(e)), p95_mm=float(np.nanpercentile(e, 95)),
                      mean_ci95_mm=[lo, hi],
                      within_tol=float(np.mean(e[ok] <= tol * 1000)))
    return out


def feature_matrix(rows, names):
    X = np.array([[r.get(n, np.nan) for n in names] for r in rows], float)
    return X


def add_metadata(rows):
    for r in rows:
        for c in CULTIVARS:
            r[f"cult_{c}"] = float(r["cultivar"] == c)


def eval_maturity(rows) -> tuple[dict, object, np.ndarray, np.ndarray]:
    add_metadata(rows)
    tr = [r for r in rows if r["split"] == "train"]
    va = [r for r in rows if r["split"] == "val"]
    te = [r for r in rows if r["split"] == "test"]
    y = lambda rs: np.array([r["maturity"] for r in rs])  # noqa: E731
    g_te = np.array([r["tray"] for r in te])
    meta = ["age_days"] + [f"cult_{c}" for c in CULTIVARS]
    variants = {
        "rule_diameter_px (RGB)": ("rule", ["eq_diameter_px"]),
        "rule_diameter_m (RGB-D)": ("rule", ["eq_diameter_m"]),
        "ml_rgb": ("ml", RGB_FEATURES),
        "ml_rgbd": ("ml", RGB_FEATURES + RGBD_FEATURES),
        "ml_rgbd+metadata": ("ml", RGB_FEATURES + RGBD_FEATURES + meta),
    }
    out, best = {}, (None, -1.0, None, None)
    for name, (kind, feats) in variants.items():
        Xtr, Xva, Xte = (feature_matrix(rs, feats) for rs in (tr, va, te))
        if kind == "rule":
            model, chosen = SizeRuleBaseline(feats[0]).fit(Xtr, y(tr)), "thresholds"
        else:
            cands = {}
            for k in ("logreg", "rf"):
                mdl = FeatureModel(k, feats).fit(Xtr, y(tr))
                cands[k] = (f1_score(y(va), mdl.predict(Xva), average="macro"), mdl)
            chosen = max(cands, key=lambda k: cands[k][0])
            model = cands[chosen][1]
        proba = model.predict_proba(Xte)
        pred = np.asarray(model.classes_)[proba.argmax(axis=1)]
        correct = pred == y(te)
        f1 = lambda idx, pred=pred: f1_score(y(te)[idx], pred[idx], average="macro")  # noqa: E731
        ready_t, ready_p = y(te) == "harvest_ready", pred == "harvest_ready"
        out[name] = dict(
            model=chosen, n_features=len(feats), n_test=len(te),
            accuracy=float(correct.mean()),
            accuracy_ci95=list(cluster_bootstrap_ci(g_te, lambda i, c=correct: float(c[i].mean()), 500)),
            macro_f1=float(f1(np.arange(len(te)))),
            macro_f1_ci95=list(cluster_bootstrap_ci(g_te, f1, 500)),
            ece=expected_calibration_error(proba.max(axis=1), correct),
            harvest_ready=prf(int((ready_t & ready_p).sum()), int((~ready_t & ready_p).sum()),
                              int((ready_t & ~ready_p).sum())),
        )
        if name == "ml_rgbd":  # deployable without plant records -> used downstream
            best = (model, out[name]["macro_f1"], pred, y(te))
    return out, best[0], best[2], best[3]


def eval_mass(rows) -> dict:
    tr = [r for r in rows if r["split"] in ("train", "val")]
    te = [r for r in rows if r["split"] == "test"]
    out = {}
    for name, feats in (("rgb", RGB_FEATURES), ("rgbd", RGB_FEATURES + RGBD_FEATURES)):
        mdl = mass_regressor().fit(feature_matrix(tr, feats), col(tr, "mass"))
        pred, true = mdl.predict(feature_matrix(te, feats)), col(te, "mass")
        ss_res, ss_tot = np.sum((true - pred) ** 2), np.sum((true - true.mean()) ** 2)
        out[name] = dict(mae_g=float(np.mean(np.abs(true - pred))),
                         mape=float(np.mean(np.abs(true - pred) / true)),
                         r2=float(1 - ss_res / ss_tot))
    return out


def eval_decisions(test_rows, tol: float, conf_grid=(0.5, 0.6, 0.7, 0.8)) -> dict:
    """Outcome of harvest decisions assuming an ideal manipulator (perception-only bound).

    The confidence threshold is swept so that the precision/recall trade-off of refusing
    uncertain targets is visible, instead of reporting one hand-picked operating point.
    """
    n_ready = sum(r["maturity"] == "harvest_ready" for r in test_rows)

    def tally(rows):
        n = len(rows)
        ok = sum(r["maturity"] == "harvest_ready" and r.get("err_selected", 9) <= tol for r in rows)
        return dict(n_harvest=n, correct=ok,
                    wrong_maturity=sum(r["maturity"] != "harvest_ready" for r in rows),
                    mislocalised=sum(r["maturity"] == "harvest_ready"
                                     and r.get("err_selected", 9) > tol for r in rows),
                    precision=ok / n if n else float("nan"),
                    recall_of_ready=ok / n_ready if n_ready else float("nan"))

    policies = {"naive: harvest if predicted ready": tally(
        [r for r in test_rows if r["obs"].maturity == "harvest_ready"])}
    actions = {}
    for c in conf_grid:
        cfg = dec.DecisionConfig(confidence_min=c)
        acts = Counter(dec.decide(r["obs"], cfg).action for r in test_rows)
        actions[f"{c:.1f}"] = dict(acts)
        policies[f"rule + refusal, confidence >= {c:.1f}"] = tally(
            [r for r in test_rows if dec.decide(r["obs"], cfg).action == dec.HARVEST])
    return dict(n_truly_ready=n_ready, actions_by_confidence_min=actions, policies=policies)


# ------------------------------------------------------------------ figures ----
def fig_qualitative(samples, cfg, model, path: Path):
    tiles = []
    for s in samples:
        res = run(s, cfg, model)
        img = s.rgb[..., ::-1].copy()
        for o in res.observations:
            cnts, _ = cv2.findContours((res.labels == o.label).astype(np.uint8),
                                       cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(img, cnts, -1, (255, 200, 0), 1)
            if o.stem_px:
                c = (int(o.stem_px[0]), int(o.stem_px[1]))
                cv2.drawMarker(img, c, (0, 0, 255), cv2.MARKER_CROSS, 12, 2)
            txt = f"{(o.maturity or '?')[:9]} c={o.confidence:.2f}"
            cv2.putText(img, txt, (o.bbox[0], max(o.bbox[1] - 3, 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 255, 255), 1, cv2.LINE_AA)
        for p in s.plants:
            cv2.circle(img, (int(p.stem_px[0]), int(p.stem_px[1])), 4, (255, 0, 255), 1)
        cv2.putText(img, "SYNTHETIC", (6, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        tiles.append(img)
    cv2.imwrite(str(path), np.hstack(tiles))


def fig_plots(test_rows, pred, true, out: Path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(5.5, 3.8))
    for m in METHODS:
        e = np.sort(col(test_rows, f"err_{m}")[np.isfinite(col(test_rows, f"err_{m}"))]) * 1000
        ax.plot(e, np.linspace(0, 1, len(e)), label=m)
    ax.axvline(10, color="k", ls=":", lw=0.8)
    ax.set(xlabel="cutting-target error [mm]", ylabel="cumulative fraction", xlim=(0, 60),
           title="Stem localisation error CDF (SYNTHETIC, test trays)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out / "stem_error_cdf.png", dpi=140)
    plt.close(fig)

    cm = confusion_matrix(true, pred, labels=MATURITY_CLASSES)
    fig, ax = plt.subplots(figsize=(5.2, 4.4))
    ax.imshow(cm, cmap="Greens")
    ax.set_xticks(range(5), MATURITY_CLASSES, rotation=35, ha="right", fontsize=8)
    ax.set_yticks(range(5), MATURITY_CLASSES, fontsize=8)
    for i in range(5):
        for j in range(5):
            ax.text(j, i, cm[i, j], ha="center", va="center", fontsize=8)
    ax.set(xlabel="predicted", ylabel="true (from latent fresh mass)",
           title="Maturity, ml_rgbd (SYNTHETIC, test trays)")
    fig.tight_layout()
    fig.savefig(out / "maturity_confusion.png", dpi=140)
    plt.close(fig)


# ------------------------------------------------------------------- report ----
def write_report(res: dict, out: Path):
    L = ["# Perception benchmark report — SYNTHETIC DATA ONLY", "",
         "> **All numbers below come from the procedural simulator** "
         "(`harvestx_perception.synthetic`). They verify the software and rank baselines; "
         "they are **not** evidence of real-world performance. No real plant was imaged.", "",
         f"- Generated by `python -m harvestx_perception.benchmark` at commit `{res['git']}`",
         f"- Seed {res['seed']}, {res['n_trays']} trays x {res['n_views']} views "
         f"({res['n_images']} images, {res['n_gt_plants']} plant instances); tray-level split "
         f"train/val/test = {res['split_counts']}",
         "- Confidence intervals: 95 % cluster bootstrap over test trays.", "",
         "## 1. Detection / instance segmentation (test trays, IoU 0.5)", "",
         "| semantic | markers | P | R | F1 | AP50 | AP50:95 | mIoU (matched) | red-leaf recall |",
         "|---|---|---|---|---|---|---|---|---|"]
    for k, v in res["segmentation"].items():
        sem, mk = k.split("/")
        red = v["recall_by_cultivar"].get("red_leaf", float("nan"))
        L.append(f"| {sem} | {mk} | {v['precision']:.3f} | {v['recall']:.3f} | {v['f1']:.3f} | "
                 f"{v['ap50']:.3f} | {v['ap50_95']:.3f} | {v['mean_iou_matched']:.3f} | {red:.2f} |")
    L += ["", "## 2. Cutting-target localisation (test trays, matched plants only)", "",
          f"Tolerance {res['tolerance_mm']:.0f} mm (assumed blade capture tolerance).", "",
          "| method | modality | n | mean [mm] (95 % CI) | median | p95 | within tol |",
          "|---|---|---|---|---|---|---|"]
    mod = dict(centroid="RGB + plane", dt_peak="RGB + plane", centroid_3d="RGB-D",
               height_apex="RGB-D", site_prior="fixture geometry only",
               fusion=f"{res['uncertainty']['fusion_vision_method']} + fixture")
    for m, v in res["localization"].items():
        L.append(f"| {m} | {mod[m]} | {v['n']} | {v['mean_mm']:.1f} "
                 f"({v['mean_ci95_mm'][0]:.1f}–{v['mean_ci95_mm'][1]:.1f}) | {v['median_mm']:.1f} | "
                 f"{v['p95_mm']:.1f} | {v['within_tol']:.2f} |")
    u = res["uncertainty"]
    L += ["", "Injected calibration error (1-sigma, assumed): camera-to-base "
          f"{res['calibration_error']['cam_sigma_t_mm']:.0f} mm / "
          f"{res['calibration_error']['cam_sigma_rot_deg']:.1f} deg, rack-to-base "
          f"{res['calibration_error']['rack_sigma_mm']:.0f} mm; stem scatter inside the net pot "
          f"{res['calibration_error']['stem_offset_sigma_mm']:.0f} mm per axis.", "",
          f"Calibrated sigma model (fit on training trays): `{u['sigma_scale']}`. Vision method "
          f"fused with the site prior, selected on validation trays: "
          f"`{u['fusion_vision_method']}` (validation mean error mm: {u['fusion_val_scores_mm']}).",
          f"Selected method `{u['method']}`: empirical coverage of the nominal 95 % region = "
          f"**{u['coverage95']:.3f}**; confidence ECE = {u['confidence_ece']:.3f}.", "",
          "## 3. Maturity classification (5 classes, test trays)", "",
          "Labels are defined from latent fresh mass, not from appearance.", "",
          "| variant | model | acc (95 % CI) | macro-F1 (95 % CI) | ECE | ready P / R |",
          "|---|---|---|---|---|---|"]
    for k, v in res["maturity"].items():
        h = v["harvest_ready"]
        L.append(f"| {k} | {v['model']} | {v['accuracy']:.3f} ({v['accuracy_ci95'][0]:.2f}–"
                 f"{v['accuracy_ci95'][1]:.2f}) | {v['macro_f1']:.3f} ({v['macro_f1_ci95'][0]:.2f}–"
                 f"{v['macro_f1_ci95'][1]:.2f}) | {v['ece']:.3f} | {h['precision']:.2f} / "
                 f"{h['recall']:.2f} |")
    L += ["", "## 4. Fresh-mass regression (random forest, test trays)", "",
          "| features | MAE [g] | MAPE | R² |", "|---|---|---|---|"]
    for k, v in res["mass"].items():
        L.append(f"| {k} | {v['mae_g']:.1f} | {v['mape']:.3f} | {v['r2']:.3f} |")
    d = res["decision"]
    L += ["", "## 5. Harvest decision (perception-only upper bound, ideal manipulator)", "",
          f"Truly harvest-ready plants among test detections: {d['n_truly_ready']}. A harvest "
          "counts as correct only if the plant is truly harvest-ready AND the target error is "
          "within tolerance. P(harvest_ready) threshold fixed at 0.6.", "",
          "| policy | harvest attempts | correct | wrong maturity | mislocalised | precision | "
          "recall of ready |", "|---|---|---|---|---|---|---|"]
    for k, v in d["policies"].items():
        L.append(f"| {k} | {v['n_harvest']} | {v['correct']} | {v['wrong_maturity']} | "
                 f"{v['mislocalised']} | {v['precision']:.2f} | {v['recall_of_ready']:.2f} |")
    L += ["", f"Actions by confidence threshold: `{d['actions_by_confidence_min']}`."]
    L += ["", "## 6. Runtime", "",
          f"Full pipeline: {res['runtime_ms_per_image']:.0f} ms per 640x480 frame "
          f"(single CPU thread of the CI container; not an embedded-target measurement).", "",
          "## Figures", "", "![qualitative](qualitative.png)", "",
          "![stem error](stem_error_cdf.png)", "", "![confusion](maturity_confusion.png)", ""]
    (out / "REPORT.md").write_text("\n".join(L))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=Path, default=Path("perception/results/synthetic_v0"))
    ap.add_argument("--trays", type=int, default=150)
    ap.add_argument("--views", type=int, default=2)
    ap.add_argument("--seed", type=int, default=20261115)
    args = ap.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)

    scfg = SceneConfig()
    samples = generate(scfg, args.trays, args.views, args.seed)
    split = split_trays([s.meta["tray_id"] for s in samples], args.seed)
    test = [s for s in samples if split[s.meta["tray_id"]] == "test"]

    seg = {}
    for sem in ("exg", "depth", "fusion"):
        for mk in ("auto", "sites"):
            seg[f"{sem}/{mk}"] = eval_segmentation(test, PipelineConfig(seg_method=sem, markers=mk))

    base = PipelineConfig()
    rows = collect_rows(samples, split, base)
    sigma = calibrate_sigma([r for r in rows if r["split"] == "train"])
    mat, model, pred, true = eval_maturity(rows)
    mass = eval_mass(rows)

    fus_m, fus_scores = select_fusion_method([r for r in rows if r["split"] == "val"], sigma)
    final = PipelineConfig(sigma_scale=sigma, fusion_vision_method=fus_m)
    t0 = time.perf_counter()
    for s in test:
        run(s, final, model)
    runtime = (time.perf_counter() - t0) / len(test) * 1000
    test_rows = collect_rows(test, split, final, model)
    loc = eval_localization(test_rows, final.cut_tolerance)

    e = col(test_rows, "err_selected")
    sig = np.array([r["obs"].sigma_plane for r in test_rows], float)
    conf = np.array([r["obs"].confidence for r in test_rows], float)
    unc = dict(method=final.stem_method, fusion_vision_method=fus_m,
               fusion_val_scores_mm={k: round(v, 1) for k, v in fus_scores.items()},
               sigma_scale={k: round(v, 4) for k, v in sigma.items()},
               coverage95=float(np.mean(e**2 <= CHI2_2DOF_95 * sig**2)),
               confidence_ece=expected_calibration_error(conf, e <= final.cut_tolerance))

    try:
        git = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True,
                             text=True, check=True).stdout.strip()
    except Exception:
        git = "uncommitted"
    res = dict(
        data_kind="SYNTHETIC", git=git, seed=args.seed, n_trays=args.trays, n_views=args.views,
        n_images=len(samples), n_gt_plants=sum(len(s.plants) for s in samples),
        split_counts=dict(Counter(split.values())), tolerance_mm=final.cut_tolerance * 1000,
        calibration_error=dict(cam_sigma_t_mm=CAM_SIGMA_T * 1000,
                               cam_sigma_rot_deg=float(np.rad2deg(CAM_SIGMA_ROT)),
                               rack_sigma_mm=RACK_SIGMA * 1000,
                               stem_offset_sigma_mm=scfg.stem_offset_sigma * 1000),
        segmentation=seg, localization=loc, uncertainty=unc, maturity=mat, mass=mass,
        decision=eval_decisions(test_rows, final.cut_tolerance), runtime_ms_per_image=runtime,
    )
    (args.out / "results.json").write_text(json.dumps(res, indent=2))
    fig_qualitative(test[:2], final, model, args.out / "qualitative.png")
    fig_plots(test_rows, pred, true, args.out)
    write_report(res, args.out)
    print((args.out / "REPORT.md").read_text())


if __name__ == "__main__":
    main()
