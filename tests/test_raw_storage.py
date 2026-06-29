import json

from pricesage.models import PriceObservation
from pricesage.storage.raw import append_observations


def _obs(vendor="cruz_verde", sku="COCV_95278", disc_price=119170):
    return PriceObservation(
        vendor=vendor,
        sku=sku,
        name="Finasterida 1Mg Caja X 28",
        brand="Lafrancol",
        full_price=140200,
        disc_price=disc_price,
        units_per_box=28,
        stock=39,
        price_source="price-sale-col",
    )


def test_appends_one_line_per_observation(tmp_path):
    counts = append_observations([_obs(), _obs(sku="COCV_55507")], raw_dir=tmp_path)
    assert counts == {"cruz_verde": 2}
    lines = (tmp_path / "cruz_verde.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["sku"] == "COCV_95278"


def test_append_is_additive_across_runs(tmp_path):
    append_observations([_obs()], raw_dir=tmp_path)
    append_observations([_obs(disc_price=133190)], raw_dir=tmp_path)
    lines = (tmp_path / "cruz_verde.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2  # second run added, didn't overwrite


def test_splits_files_by_vendor(tmp_path):
    counts = append_observations([_obs(), _obs(vendor="farma_express")], raw_dir=tmp_path)
    assert counts == {"cruz_verde": 1, "farma_express": 1}
    assert (tmp_path / "cruz_verde.jsonl").exists()
    assert (tmp_path / "farma_express.jsonl").exists()
