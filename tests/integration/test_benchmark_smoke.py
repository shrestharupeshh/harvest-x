"""End-to-end smoke test of the synthetic benchmark (generation -> report)."""
import json

import pytest
from harvestx_perception import benchmark


@pytest.mark.slow
def test_benchmark_end_to_end(tmp_path):
    benchmark.main(["--out", str(tmp_path), "--trays", "15", "--views", "2", "--seed", "7"])
    res = json.loads((tmp_path / "results.json").read_text())
    assert res["data_kind"] == "SYNTHETIC"
    assert res["split_counts"] == {"train": 9, "val": 3, "test": 3}
    for f in ("REPORT.md", "qualitative.png", "stem_error_cdf.png", "maturity_confusion.png"):
        assert (tmp_path / f).stat().st_size > 0
    assert "SYNTHETIC" in (tmp_path / "REPORT.md").read_text().splitlines()[0]
    # sanity bounds only: these guard against regressions, they are not performance claims
    assert res["segmentation"]["fusion/sites"]["f1"] > 0.9
    assert res["localization"]["site_prior"]["mean_mm"] < 15
    assert res["localization"]["fusion"]["mean_mm"] < 15
    assert 0 <= res["uncertainty"]["coverage95"] <= 1


def test_split_is_grouped_by_tray():
    ids = [f"T{i:03d}" for i in range(50) for _ in range(3)]
    split = benchmark.split_trays(ids, seed=1)
    assert len(split) == 50
    assert sorted(set(split.values())) == ["test", "train", "val"]
