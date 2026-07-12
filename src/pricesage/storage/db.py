"""Postgres (Neon) storage — the queryable layer.

Writes are idempotent: one observation row per (product, Colombia-local day).
Re-running the collector on the same day updates that day's row instead of
duplicating it, so the cron is safe to fire more than once.
"""

from __future__ import annotations

import os
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import psycopg
from dotenv import load_dotenv

from pricesage.models import PriceObservation, VendorRun

SCHEMA_PATH = Path(__file__).with_name("schema.sql")
_BOGOTA = ZoneInfo("America/Bogota")


def get_database_url() -> str | None:
    """Read DATABASE_URL from the environment (loading a local .env if present)."""
    load_dotenv()
    return os.getenv("DATABASE_URL")


def observation_date(scraped_at: datetime) -> date:
    """The Colombia-local calendar date of a reading (prices are a COP/Colombia thing)."""
    return scraped_at.astimezone(_BOGOTA).date()


def _split_statements(sql: str) -> list[str]:
    """Split a SQL script into statements, ignoring `--` line comments.

    Comments are stripped first so a semicolon inside a comment can't cut a
    statement in half. (Our DDL has no `--` inside string literals.)
    """
    no_comments = "\n".join(line.split("--", 1)[0] for line in sql.splitlines())
    return [stmt.strip() for stmt in no_comments.split(";") if stmt.strip()]


def ensure_schema(conn: psycopg.Connection) -> None:
    statements = _split_statements(SCHEMA_PATH.read_text(encoding="utf-8"))
    with conn.cursor() as cur:
        for statement in statements:
            cur.execute(statement)


def store(observations: list[PriceObservation], database_url: str | None = None) -> int:
    """Upsert observations into Postgres. Returns the number written."""
    url = database_url or get_database_url()
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    with psycopg.connect(url) as conn:
        ensure_schema(conn)
        with conn.cursor() as cur:
            for obs in observations:
                listing_id = _upsert_listing(cur, obs)
                _upsert_observation(cur, listing_id, obs)
        conn.commit()
    return len(observations)


def record_runs(runs: list[VendorRun], database_url: str | None = None) -> int:
    """Append one health row per vendor run. Returns the number written."""
    if not runs:
        return 0
    url = database_url or get_database_url()
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    with psycopg.connect(url) as conn:
        ensure_schema(conn)
        with conn.cursor() as cur:
            for r in runs:
                cur.execute(
                    """
                    INSERT INTO collection_runs
                        (vendor, run_at, run_date, status, attempts, observations,
                         error_type, error_detail)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        r.vendor,
                        r.run_at,
                        observation_date(r.run_at),
                        r.status,
                        r.attempts,
                        r.observations,
                        r.error_type,
                        r.error_detail,
                    ),
                )
        conn.commit()
    return len(runs)


def _upsert_listing(cur: psycopg.Cursor, obs: PriceObservation) -> int:
    cur.execute(
        """
        INSERT INTO listings (vendor, sku, brand, name, units_per_box, url)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (vendor, sku) DO UPDATE SET
            brand = EXCLUDED.brand,
            name = EXCLUDED.name,
            units_per_box = EXCLUDED.units_per_box,
            url = EXCLUDED.url
        RETURNING id
        """,
        (obs.vendor, obs.sku, obs.brand, obs.name, obs.units_per_box, obs.url),
    )
    return cur.fetchone()[0]


def _upsert_observation(cur: psycopg.Cursor, listing_id: int, obs: PriceObservation) -> None:
    cur.execute(
        """
        INSERT INTO observations
            (listing_id, obs_date, scraped_at, full_price, disc_price, price_source, stock, currency)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (listing_id, obs_date) DO UPDATE SET
            scraped_at = EXCLUDED.scraped_at,
            full_price = EXCLUDED.full_price,
            disc_price = EXCLUDED.disc_price,
            price_source = EXCLUDED.price_source,
            stock = EXCLUDED.stock,
            currency = EXCLUDED.currency
        """,
        (
            listing_id,
            observation_date(obs.scraped_at),
            obs.scraped_at,
            obs.full_price,
            obs.disc_price,
            obs.price_source,
            obs.stock,
            obs.currency,
        ),
    )
