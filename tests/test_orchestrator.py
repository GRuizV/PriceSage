from pricesage import main
from pricesage.errors import VendorError
from pricesage.models import PriceObservation


def _obs(vendor="v_ok"):
    return PriceObservation(
        vendor=vendor, sku="S1", name="n", brand="b",
        full_price=100, disc_price=90, units_per_box=10, stock=5, price_source="x",
    )


class _OK:
    def collect(self):
        return [_obs()]


class _Empty:
    def collect(self):
        raise VendorError("v_empty", "nothing usable", status=200, kind="empty")


class _Flaky:
    """Fails once, then succeeds — exercises retry + attempts counting."""

    def __init__(self):
        self.n = 0

    def collect(self):
        self.n += 1
        if self.n < 2:
            raise VendorError("v_flaky", "temporary", status=500, kind="error")
        return [_obs("v_flaky")]


def test_collect_all_records_runs(monkeypatch):
    monkeypatch.setitem(main.ADAPTER_BUILDERS, "v_ok", lambda b: _OK())
    monkeypatch.setitem(main.ADAPTER_BUILDERS, "v_empty", lambda b: _Empty())
    monkeypatch.setitem(main.ADAPTER_BUILDERS, "v_flaky", lambda b: _Flaky())
    config = {"v_ok": {}, "v_empty": {}, "v_flaky": {}}

    observations, runs = main.collect_all(config, attempts=3, cooldown=0)

    by = {r.vendor: r for r in runs}
    # success first try
    assert by["v_ok"].status == "ok"
    assert by["v_ok"].attempts == 1
    assert by["v_ok"].observations == 1
    # empty after exhausting attempts, classified 'empty', carries the mode
    assert by["v_empty"].status == "empty"
    assert by["v_empty"].attempts == 3
    assert by["v_empty"].error_type == "HTTP 200"
    assert by["v_empty"].error_detail == "nothing usable"
    # flaky recovered on the 2nd try
    assert by["v_flaky"].status == "ok"
    assert by["v_flaky"].attempts == 2
    # observations = v_ok + recovered v_flaky (empty contributes none)
    assert len(observations) == 2
