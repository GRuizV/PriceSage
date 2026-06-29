"""Append normalized observations to per-vendor JSONL files.

This is the committed history layer: one append-only `data/raw/{vendor}.jsonl`
per vendor, one JSON object per line. Append-only means re-runs never rewrite
past data — they only add. The queryable layer (Postgres) comes later; this
file stays as the human-readable, version-controlled record.
"""

from __future__ import annotations

import json
from pathlib import Path

from pricesage.models import PriceObservation

# src/pricesage/storage/raw.py -> project root
DEFAULT_RAW_DIR = Path(__file__).resolve().parents[3] / "data" / "raw"


def append_observations(
    observations: list[PriceObservation],
    raw_dir: str | Path | None = None,
) -> dict[str, int]:
    """Append observations to per-vendor JSONL files. Returns {vendor: count}."""
    target_dir = Path(raw_dir) if raw_dir else DEFAULT_RAW_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    by_vendor: dict[str, list[PriceObservation]] = {}
    for obs in observations:
        by_vendor.setdefault(obs.vendor, []).append(obs)

    counts: dict[str, int] = {}
    for vendor, items in by_vendor.items():
        path = target_dir / f"{vendor}.jsonl"
        with path.open("a", encoding="utf-8") as f:
            for obs in items:
                f.write(json.dumps(obs.to_dict(), ensure_ascii=False) + "\n")
        counts[vendor] = len(items)
    return counts
