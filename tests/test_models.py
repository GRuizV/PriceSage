from datetime import datetime, timezone
from decimal import Decimal

from pricesage.models import PriceObservation


def _obs(**overrides):
    base = dict(
        vendor="cruz_verde",
        sku="COCV_95278",
        name="Finasterida Tabletas Recubiertas 1Mg Caja X 28",
        brand="Lafrancol",
        full_price=140200,
        disc_price=119170,
        units_per_box=28,
        stock=39,
        price_source="price-sale-col",
    )
    base.update(overrides)
    return PriceObservation(**base)


def test_price_per_unit_rounds_half_up():
    # 119170 / 28 = 4256.0714... -> 4256.07
    assert _obs().price_per_unit == Decimal("4256.07")


def test_discount_pct():
    # 1 - 119170/140200 = 15.0%
    assert _obs().discount_pct == 15


def test_discount_pct_zero_when_no_discount():
    assert _obs(full_price=120600, disc_price=120600).discount_pct == 0


def test_units_per_box_must_be_positive():
    obs = _obs(units_per_box=0)
    try:
        _ = obs.price_per_unit
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_to_dict_is_json_friendly():
    obs = _obs(scraped_at=datetime(2026, 6, 12, 10, 0, tzinfo=timezone.utc))
    d = obs.to_dict()
    assert d["scraped_at"] == "2026-06-12T10:00:00+00:00"
    assert d["price_per_unit"] == "4256.07"
    assert d["discount_pct"] == 15
    assert d["vendor"] == "cruz_verde"


def test_default_scraped_at_is_utc_aware():
    assert _obs().scraped_at.tzinfo is not None
