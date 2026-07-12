from datetime import date

from pricesage.alerts import find_persistent_failures

TODAY = date(2026, 7, 12)


def _health():
    return [
        {"vendor": "ok_today", "last_ok": date(2026, 7, 12), "last_run": date(2026, 7, 12)},
        {"vendor": "ok_1d", "last_ok": date(2026, 7, 11), "last_run": date(2026, 7, 12)},
        {"vendor": "stale_3d", "last_ok": date(2026, 7, 9), "last_run": date(2026, 7, 12)},
        {"vendor": "never", "last_ok": None, "last_run": date(2026, 7, 12)},
    ]


def test_flags_stale_and_never_succeeded():
    stale = find_persistent_failures(TODAY, health=_health(), alert_after_days=3)
    assert {s["vendor"] for s in stale} == {"stale_3d", "never"}


def test_never_succeeded_has_none_days():
    stale = find_persistent_failures(TODAY, health=_health(), alert_after_days=3)
    never = next(s for s in stale if s["vendor"] == "never")
    assert never["days_since_ok"] is None


def test_threshold_is_inclusive_at_boundary():
    health = [{"vendor": "v", "last_ok": date(2026, 7, 9), "last_run": TODAY}]  # exactly 3 days
    assert find_persistent_failures(TODAY, health=health, alert_after_days=3)  # alerts
    assert not find_persistent_failures(TODAY, health=health, alert_after_days=4)  # not yet


def test_healthy_vendors_never_flagged():
    health = [{"vendor": "v", "last_ok": TODAY, "last_run": TODAY}]
    assert find_persistent_failures(TODAY, health=health, alert_after_days=3) == []
