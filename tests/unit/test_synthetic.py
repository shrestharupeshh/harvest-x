import numpy as np
from harvestx_perception.camera import invert_T, transform_points
from harvestx_perception.synthetic.growth import (
    MATURITY_CLASSES,
    maturity_from_mass,
    sample_plant,
)
from harvestx_perception.synthetic.scene import SceneConfig, render_scene, sample_tray


def _scene(seed=3):
    cfg = SceneConfig()
    plants = sample_tray(cfg, np.random.default_rng(seed))
    return cfg, plants, render_scene(cfg, np.random.default_rng(seed + 1), "TEST", plants)


def test_maturity_labels_follow_mass():
    assert maturity_from_mass(5) == "early"
    assert maturity_from_mass(150) == "harvest_ready"
    assert maturity_from_mass(150, bolting=True) == "overgrown"
    assert maturity_from_mass(500) == "overgrown"
    rng = np.random.default_rng(0)
    young = np.mean([sample_plant(rng, "butterhead", 8).fresh_mass_g for _ in range(50)])
    old = np.mean([sample_plant(rng, "butterhead", 40).fresh_mass_g for _ in range(50)])
    assert old > 5 * young
    assert sample_plant(rng, "romaine", 20).maturity in MATURITY_CLASSES


def test_render_is_deterministic():
    _, _, a = _scene()
    _, _, b = _scene()
    assert np.array_equal(a.rgb, b.rgb)
    assert np.array_equal(a.depth, b.depth)
    assert np.array_equal(a.instances, b.instances)


def test_shapes_and_instances_consistent():
    cfg, plants, s = _scene()
    H, W = cfg.intrinsics.height, cfg.intrinsics.width
    assert s.rgb.shape == (H, W, 3) and s.rgb.dtype == np.uint8
    assert s.depth.shape == (H, W) and s.instances.shape == (H, W)
    assert len(s.plants) == len(plants)
    ids = {p.instance_id for p in s.plants}
    assert set(np.unique(s.instances)) - {0} <= ids
    assert len({p.plant_id for p in s.plants}) == len(s.plants)
    assert s.meta["synthetic"] is True


def test_depth_is_metrically_consistent_with_ground_truth():
    cfg, _, s = _scene()
    # background pixels back-project onto the tray plane in the base frame
    bg = (s.instances == 0) & (s.depth > 0)
    vs, us = np.nonzero(bg)
    sel = np.random.default_rng(0).choice(len(us), 2000, replace=False)
    uv = np.column_stack([us[sel], vs[sel]])
    pts = transform_points(s.T_base_cam, cfg.intrinsics.backproject(uv, s.depth[vs[sel], us[sel]]))
    assert abs(np.median(pts[:, 2]) - cfg.rack.plane_z) < 5e-4
    assert np.std(pts[:, 2]) < 0.004
    # plant pixels are above the tray, and never higher than the tallest plant
    vs, us = np.nonzero((s.instances > 0) & (s.depth > 0))
    pts = transform_points(s.T_base_cam, cfg.intrinsics.backproject(
        np.column_stack([us, vs]), s.depth[vs, us]))
    h = pts[:, 2] - cfg.rack.plane_z
    assert np.percentile(h, 1) > -0.005
    assert np.percentile(h, 99.5) < max(p.height_m for p in s.plants) + 0.01


def test_stem_ground_truth_projection():
    cfg, _, s = _scene()
    T_cam_base = invert_T(s.T_base_cam)
    for p in s.plants:
        uv, _ = cfg.intrinsics.project(transform_points(T_cam_base, np.array([p.cut_target])))
        assert np.allclose(uv[0], p.stem_px)
        assert np.isclose(p.cut_target[2] - p.stem_base[2], cfg.rack.cut_height)
        site = cfg.rack.sites()[p.site_index]
        assert np.hypot(*(np.array(p.stem_base[:2]) - site[:2])) <= cfg.rack.hole_radius


def test_same_plants_reimaged_keep_identity():
    cfg = SceneConfig()
    plants = sample_tray(cfg, np.random.default_rng(5))
    a = render_scene(cfg, np.random.default_rng(1), "T", plants)
    b = render_scene(cfg, np.random.default_rng(2), "T", plants)
    assert [p.plant_id for p in a.plants] == [p.plant_id for p in b.plants]
    assert [p.stem_base for p in a.plants] == [p.stem_base for p in b.plants]
    assert not np.array_equal(a.rgb, b.rgb)  # different view / lighting
