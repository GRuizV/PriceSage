"""Layer-2 persistent-failure detection.

A single bad day is transient (Layer-1 retry handles the flakes). But a vendor
whose last *successful* collection is several days old is genuinely broken and
worth a human's attention. This module finds those vendors from the
`collection_runs` history and logs the alert.

Phase 4 detects and logs; Phase 5 will wire the same signal to email.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from loguru import logger

from pricesage.storage import db

# Alert once a vendor's last success is this many days old (or it never succeeded).
# 3 days x 3 attempts/day is a strong enough signal that it's not just flakiness.
DEFAULT_ALERT_AFTER_DAYS = 3


def _colombia_today() -> date:
    return db.observation_date(datetime.now(timezone.utc))


def find_persistent_failures(
    today: date,
    health: list[dict] | None = None,
    alert_after_days: int = DEFAULT_ALERT_AFTER_DAYS,
    database_url: str | None = None,
) -> list[dict]:
    """Vendors whose last success is >= alert_after_days old (or never).

    `today` and `health` are injectable so this is testable without a clock or a
    DB. Returns [{vendor, last_ok, days_since_ok}] (days_since_ok is None if the
    vendor has never succeeded).
    """
    rows = health if health is not None else db.vendor_health(database_url)
    stale = []
    for row in rows:
        last_ok = row.get("last_ok")
        days_since_ok = (today - last_ok).days if last_ok else None
        if last_ok is None or days_since_ok >= alert_after_days:
            stale.append(
                {"vendor": row["vendor"], "last_ok": last_ok, "days_since_ok": days_since_ok}
            )
    return stale


def check_and_log(
    today: date | None = None,
    alert_after_days: int = DEFAULT_ALERT_AFTER_DAYS,
    database_url: str | None = None,
) -> list[dict]:
    """Detect persistent failures and log each as an ALERT. Returns them."""
    today = today or _colombia_today()
    failures = find_persistent_failures(
        today, alert_after_days=alert_after_days, database_url=database_url
    )
    for f in failures:
        if f["last_ok"] is None:
            logger.error("ALERT: vendor '{}' has never succeeded", f["vendor"])
        else:
            logger.error(
                "ALERT: vendor '{}' last succeeded {} ({} day(s) ago)",
                f["vendor"], f["last_ok"], f["days_since_ok"],
            )
    return failures
