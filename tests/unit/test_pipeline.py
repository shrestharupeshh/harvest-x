import numpy as np
import pytest
from harvestx_perception import decision as dec
from harvestx_perception.evaluation.metrics import iou_matrix, match_instances
from harvestx_perception.maturity.models import FeatureModel, SizeRuleBaseline
from harvestx_perception.pipeline import (
    LOW_CONFIDENCE,
    PLAUSIBLE,
    VERIFIED,
    PipelineConfig,
    process_frame,
)
from harvestx_perception.segmentation.classical import instance_segmentation, semantic_mask
from harvestx_perception.synthetic.growth import MATURITY_CLASSES
from harvestx_perception.synthetic.scene import SceneConfig, render_scene, sample_tray


@pytest.fixture(scope="module")
def scene():
    cfg = SceneConfig(cultivars=("butterhead",), cultivar_probs=(1.0,), age_range_days=(18, 24),
                      empty_site_prob=0.0)
    plants = sample_tray(cfg, np.random.default_rng(11))
    return render_scene(cfg, np.random.default_rng(12), "UNIT", plants)


def _run(s, **kw):
    r = s.rack
    return process_frame(s.rgb, s.depth, s.intrinsics, s.T_base_cam, r.sites(), r.plane_z,
                         r.cut_height, PipelineConfig(**kw))


@pytest.mark.parametrize("sem", ["exg", "depth", "fusion"])
@pytest.mark.parametrize("markers", ["auto", "sites"])
def test_instances_found(scene, sem, markers):
    res = _run(scene, seg_method=sem, markers=markers)
    iou, g, _ = iou_matrix(scene.instances.astype(np.int32), res.labels)
    assert len(match_instances(iou, 0.5)) >= len(g) - 1


def test_observation_contract(scene):
    res = _run(scene)
    assert res.plane_source == "depth_ransac"
    assert len(res.observations) == len(scene.plants)
    truth = {p.site_index: p for p in scene.plants}
    for o in res.observations:
        assert o.target_status in (PLAUSIBLE, LOW_CONFIDENCE)
        assert o.target_status != VERIFIED  # perception from above must never claim this
        assert 0.0 <= o.confidence <= 1.0
        assert o.cut_target_cov_base.shape == (3, 3)
        assert np.linalg.eigvalsh(o.cut_target_cov_base).min() > 0
        gt = np.array(truth[o.site_index].cut_target)
        assert np.linalg.norm(o.cut_target_base - gt) < 0.03
        # cutting target lies on the cutting plane
        assert abs(o.cut_target_base[2] - gt[2]) < 0.004
        assert set(o.stem_candidates) >= {"centroid", "centroid_3d", "site_prior", "fusion"}
        d = o.to_dict()
        assert d["target_status"] == o.target_status


def test_rgb_only_falls_back_to_calibrated_plane(scene):
    r = scene.rack
    res = process_frame(scene.rgb, None, scene.intrinsics, scene.T_base_cam, r.sites(),
                        r.plane_z, r.cut_height, PipelineConfig())
    assert res.plane_source == "calibration"
    assert len(res.observations) >= len(scene.plants) - 1
    assert all("height_apex" not in o.stem_candidates for o in res.observations)


def test_segmentation_empty_image():
    rgb = np.full((120, 160, 3), 128, np.uint8)
    m = semantic_mask(rgb, None, "exg")
    assert not m.any()
    assert instance_segmentation(m).max() == 0
    with pytest.raises(ValueError):
        semantic_mask(rgb, None, "depth")


def test_size_rule_baseline_is_monotone():
    x = np.r_[np.full(20, 0.05), np.full(20, 0.12), np.full(20, 0.18), np.full(20, 0.24),
              np.full(20, 0.30)]
    y = np.repeat(MATURITY_CLASSES, 20)
    m = SizeRuleBaseline("eq_diameter_m").fit(x[:, None], y)
    assert np.all(np.diff(m.thresholds_) > 0)
    assert (m.predict(x[:, None]) == y).all()
    assert np.allclose(m.predict_proba(x[:, None]).sum(axis=1), 1)


def test_feature_model_and_decision(scene):
    rng = np.random.default_rng(0)
    X = rng.normal(size=(200, 3))
    y = np.where(X[:, 0] > 0, "harvest_ready", "developing")
    model = FeatureModel("logreg", ["area_px", "solidity", "extent"]).fit(X, y)
    assert (model.predict(X) == y).mean() > 0.95

    o = _run(scene).observations[0]
    assert dec.decide(o).action == dec.RESCAN  # no maturity estimate
    o.maturity, o.maturity_probs = "developing", {"harvest_ready": 0.1}
    assert dec.decide(o).action == dec.DEFER
    o.maturity, o.maturity_probs = "overgrown", {"harvest_ready": 0.2}
    assert dec.decide(o).action == dec.REJECT
    o.maturity, o.maturity_probs = "harvest_ready", {"harvest_ready": 0.9}
    o.features["truncated"], o.confidence = 0.0, 0.95
    assert dec.decide(o).action == dec.HARVEST
    o.confidence = 0.2
    d = dec.decide(o)
    assert d.action == dec.RESCAN and "confidence" in d.reasons[0]
