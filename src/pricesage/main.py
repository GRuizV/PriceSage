"""Orchestrator: run every configured vendor, isolate failures, store results.

Entry point for `python -m pricesage`.
"""

from __future__ import annotations

import argparse
import sys

from loguru import logger

from pricesage.config import load_config
from pricesage.errors import VendorError
from pricesage.models import PriceObservation, VendorRun
from pricesage.retry import DEFAULT_ATTEMPTS, DEFAULT_COOLDOWN, call_with_retry
from pricesage.storage import db
from pricesage.storage.raw import append_observations
from pricesage.adapters.cruz_verde import CruzVerdeAdapter


def configure_logging(level: str = "INFO") -> None:
    """Route loguru to stderr with a fully traceable format (color auto-off in CI).

    Format: timestamp | LEVEL | module:function:line - message
    """
    logger.remove()
    logger.add(
        sys.stderr,
        level=level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
    )


def _build_cruz_verde(block: dict) -> CruzVerdeAdapter:
    return CruzVerdeAdapter(
        inventory_id=block["inventory_id"],
        listings=block["listings"],
    )


# vendor key -> builder taking that vendor's config block and returning an adapter
ADAPTER_BUILDERS = {
    "cruz_verde": _build_cruz_verde,
}


def _run_vendor(vendor, adapter, attempts, cooldown) -> tuple[list[PriceObservation], VendorRun]:
    """Collect one vendor with retry. Returns (observations, run-status row)."""
    attempts_used = 0

    def _attempt():
        nonlocal attempts_used
        attempts_used += 1
        return adapter.collect()

    try:
        obs = call_with_retry(
            _attempt, label=f"vendor '{vendor}'", attempts=attempts, cooldown=cooldown
        )
    except VendorError as exc:
        # Failed every attempt — expected, tracked; skip this vendor.
        logger.error("vendor '{}' failed after {} attempt(s); skipping", vendor, attempts_used)
        run = VendorRun(
            vendor=vendor,
            status=exc.kind,
            attempts=attempts_used,
            observations=0,
            error_type=f"HTTP {exc.status}" if exc.status is not None else exc.kind,
            error_detail=exc.message,
        )
        return [], run

    logger.info("vendor '{}': {} observation(s)", vendor, len(obs))
    run = VendorRun(vendor=vendor, status="ok", attempts=attempts_used, observations=len(obs))
    return obs, run


def collect_all(
    config: dict,
    only: str | None = None,
    attempts: int = DEFAULT_ATTEMPTS,
    cooldown: float = DEFAULT_COOLDOWN,
) -> tuple[list[PriceObservation], list[VendorRun]]:
    
    """Run each configured vendor with retry. One vendor failing never stops the others.

    Returns (observations, runs) — a run-status row is produced for every vendor
    actually attempted (success or failure).
    """

    observations: list[PriceObservation] = []
    runs: list[VendorRun] = []

    for vendor, block in config.items():

        if only and vendor != only:
            continue

        builder = ADAPTER_BUILDERS.get(vendor)

        if builder is None:
            logger.warning("no adapter for vendor '{}'; skipping", vendor)
            continue
        
        obs, run = _run_vendor(vendor, builder(block), attempts, cooldown)
        observations.extend(obs)
        runs.append(run)

    return observations, runs


def run(
    config_path=None,
    only=None,
    store=True,
    use_db=True,
    attempts=DEFAULT_ATTEMPTS,
    cooldown=DEFAULT_COOLDOWN,
) -> list[PriceObservation]:

    config = load_config(config_path)
    observations, runs = collect_all(config, only=only, attempts=attempts, cooldown=cooldown)

    if not store:
        logger.info("--no-store: {} observation(s) collected, not written", len(observations))
        return observations

    if observations:
        counts = append_observations(observations)
        for vendor, n in counts.items():
            logger.info("stored {} observation(s) -> data/raw/{}.jsonl", n, vendor)

    if use_db:
        url = db.get_database_url()
        if url:
            if observations:
                n = db.store(observations, url)
                logger.info("stored {} observation(s) -> Postgres", n)
            if runs:
                db.record_runs(runs, url)
                logger.info("recorded {} run-status row(s) -> Postgres", len(runs))
        else:
            logger.info("no DATABASE_URL set; skipping Postgres")

    return observations


def main() -> None:
    parser = argparse.ArgumentParser(prog="pricesage", description="Collect finasteride prices.")
    parser.add_argument("--config", help="path to products.yml (default: bundled config)")
    parser.add_argument("--vendor", help="run only this vendor key")
    parser.add_argument("--no-store", action="store_true", help="collect but don't write anywhere")
    parser.add_argument("--no-db", action="store_true", help="write JSONL but skip Postgres")
    parser.add_argument("--attempts", type=int, default=DEFAULT_ATTEMPTS, help="retry attempts per vendor")
    parser.add_argument(
        "--retry-cooldown", type=float, default=DEFAULT_COOLDOWN,
        help="seconds between retry attempts", dest="retry_cooldown",
    )
    args = parser.parse_args()

    configure_logging()
    observations = run(
        config_path=args.config,
        only=args.vendor,
        store=not args.no_store,
        use_db=not args.no_db,
        attempts=args.attempts,
        cooldown=args.retry_cooldown,
    )
    logger.info("done: {} observation(s) total", len(observations))


if __name__ == "__main__":
    main()
