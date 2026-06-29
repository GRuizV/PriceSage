"""Orchestrator: run every configured vendor, isolate failures, store results.

Entry point for `python -m pricesage`.
"""

from __future__ import annotations

import argparse
import logging

from pricesage.config import load_config
from pricesage.models import PriceObservation
from pricesage.adapters.cruz_verde import CruzVerdeAdapter
from pricesage.storage.raw import append_observations

log = logging.getLogger("pricesage")


def _build_cruz_verde(block: dict) -> CruzVerdeAdapter:
    return CruzVerdeAdapter(
        inventory_id=block["inventory_id"],
        listings=block["listings"],
    )


# vendor key -> builder taking that vendor's config block and returning an adapter
ADAPTER_BUILDERS = {
    "cruz_verde": _build_cruz_verde,
}


def collect_all(config: dict, only: str | None = None) -> list[PriceObservation]:
    """Run each configured vendor. One vendor failing never stops the others."""
    observations: list[PriceObservation] = []
    for vendor, block in config.items():
        if only and vendor != only:
            continue
        builder = ADAPTER_BUILDERS.get(vendor)
        if builder is None:
            log.warning("no adapter for vendor '%s'; skipping", vendor)
            continue
        try:
            vendor_obs = builder(block).collect()
        except Exception:
            log.exception("vendor '%s' failed entirely; skipping", vendor)
            continue
        log.info("vendor '%s': %d observation(s)", vendor, len(vendor_obs))
        observations.extend(vendor_obs)
    return observations


def run(config_path=None, only=None, store=True, use_db=True) -> list[PriceObservation]:
    config = load_config(config_path)
    observations = collect_all(config, only=only)

    if not store:
        log.info("--no-store: %d observation(s) collected, not written", len(observations))
        return observations
    if not observations:
        return observations

    counts = append_observations(observations)
    for vendor, n in counts.items():
        log.info("stored %d observation(s) -> data/raw/%s.jsonl", n, vendor)

    if use_db:
        from pricesage.storage import db

        url = db.get_database_url()
        if url:
            n = db.store(observations, url)
            log.info("stored %d observation(s) -> Postgres", n)
        else:
            log.info("no DATABASE_URL set; skipping Postgres")

    return observations


def main() -> None:
    parser = argparse.ArgumentParser(prog="pricesage", description="Collect finasteride prices.")
    parser.add_argument("--config", help="path to products.yml (default: bundled config)")
    parser.add_argument("--vendor", help="run only this vendor key")
    parser.add_argument("--no-store", action="store_true", help="collect but don't write anywhere")
    parser.add_argument("--no-db", action="store_true", help="write JSONL but skip Postgres")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    observations = run(
        config_path=args.config,
        only=args.vendor,
        store=not args.no_store,
        use_db=not args.no_db,
    )
    log.info("done: %d observation(s) total", len(observations))


if __name__ == "__main__":
    main()
