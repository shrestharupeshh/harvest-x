from harvestx_mech import approach_study as a
from harvestx_mech.params import load_params


def test_inside_boxes():
    import numpy as np

    pts = np.array([[0, 0, 0.01], [0.2, 0, 0.01], [0, 0, 0.5]])
    assert a.inside(pts, [(-0.1, 0.1, -0.1, 0.1, 0, 0.02)]).tolist() == [True, False, False]


def test_side_entry_spares_the_heart():
    res = a.run(load_params(), n_plants=25, seed=1)
    assert res["data_kind"] == "SIMULATED"
    r = {k[:2]: v for k, v in res["results"].items()}
    assert r["S3"]["target_inner"]["mean"] < 0.05
    assert r["S3"]["target"]["mean"] < r["S1"]["target"]["mean"]
    assert "SIMULATED" in a.to_markdown(res)
