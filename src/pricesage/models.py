"""Normalized data model shared by every vendor adapter.

A `PriceObservation` is one product's price at one point in time from one
vendor. Adapters are responsible for mapping their vendor's raw response onto
this shape; everything downstream (storage, alerts, dashboard) only ever sees
this.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class PriceObservation:
    """One price reading for one product from one vendor.

    Prices are whole Colombian pesos (COP has no practical cents). Boxes differ
    in size across brands (x28 Lafrancol/AG vs x30 Mk/Finhet), so comparisons
    must use `price_per_unit`, never the raw box price.
    """

    vendor: str                 # short stable key, e.g. "cruz_verde"
    sku: str                    # vendor's own product id / reference
    name: str                   # product name as the vendor lists it
    brand: str
    full_price: int             # list / undiscounted price (COP)
    disc_price: int             # effective price paid today (COP)
    units_per_box: int          # tablets per box (for per-unit normalization)
    stock: int
    price_source: str           # which field disc_price came from (audit trail)
    currency: str = "COP"
    url: str | None = None
    scraped_at: datetime = field(default_factory=_utcnow)

    @property
    def price_per_unit(self) -> Decimal:
        """Effective price per tablet — the only fair cross-brand comparison."""
        if self.units_per_box <= 0:
            raise ValueError(f"units_per_box must be > 0, got {self.units_per_box}")
        cents = Decimal(self.disc_price) / Decimal(self.units_per_box)
        return cents.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def discount_pct(self) -> int:
        """Percent off the list price (0 when there's no discount)."""
        if self.full_price <= 0:
            return 0
        off = (1 - self.disc_price / self.full_price) * 100
        return round(off)

    def to_dict(self) -> dict:
        """Flat, JSON-serializable dict including the computed fields."""
        d = asdict(self)
        d["scraped_at"] = self.scraped_at.isoformat()
        d["price_per_unit"] = str(self.price_per_unit)
        d["discount_pct"] = self.discount_pct
        return d


@dataclass(slots=True)
class VendorRun:
    """Outcome of one vendor's collection in one run — feeds `collection_runs`.

    Recorded for every attempted vendor, success or failure, so the health of
    the pipeline is queryable and the Layer-2 persistent-failure alert has a
    source of truth.
    """

    vendor: str
    status: str                        # 'ok' | 'empty' | 'error'
    attempts: int                      # tries used (1 = succeeded first go)
    observations: int                  # how many observations were collected
    run_at: datetime = field(default_factory=_utcnow)
    error_type: str | None = None      # e.g. 'HTTP 404' (None when ok)
    error_detail: str | None = None    # short message (None when ok)
    error_body: str | None = None      # raw failure response, in-memory only (not stored in DB)
