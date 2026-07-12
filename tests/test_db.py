from datetime import datetime, timezone

from pricesage.storage.db import SCHEMA_PATH, _split_statements, observation_date


def test_schema_splits_into_clean_statements():
    statements = _split_statements(SCHEMA_PATH.read_text(encoding="utf-8"))
    # listings, observations, collection_runs, its index, and the view
    assert len(statements) == 5
    # no comment markers leaked in, and every statement's parens are balanced
    for stmt in statements:
        assert "--" not in stmt
        assert stmt.count("(") == stmt.count(")")
    assert statements[1].lower().startswith("create table if not exists observations")
    assert any("collection_runs" in s for s in statements)


def test_observation_date_uses_colombia_local_day():
    # 02:00 UTC on Jun 30 is 21:00 (prev day) in Bogota (UTC-5) -> Jun 29.
    dt = datetime(2026, 6, 30, 2, 0, tzinfo=timezone.utc)
    assert observation_date(dt).isoformat() == "2026-06-29"


def test_observation_date_same_day_when_afternoon_utc():
    dt = datetime(2026, 6, 29, 21, 30, tzinfo=timezone.utc)  # 16:30 Bogota
    assert observation_date(dt).isoformat() == "2026-06-29"
