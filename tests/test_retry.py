import pytest

from pricesage.errors import VendorError
from pricesage.retry import call_with_retry


def _no_sleep(_seconds):
    pass


def test_returns_first_success_without_retrying():
    calls = []

    def fn():
        calls.append(1)
        return "ok"

    assert call_with_retry(fn, attempts=3, sleep=_no_sleep) == "ok"
    assert len(calls) == 1  # succeeded first try, no retry


def test_retries_then_succeeds():
    calls = []

    def fn():
        calls.append(1)
        if len(calls) < 3:
            raise VendorError("v", "flaky")
        return "recovered"

    assert call_with_retry(fn, attempts=3, sleep=_no_sleep) == "recovered"
    assert len(calls) == 3


def test_sleeps_between_attempts_but_not_after_last():
    sleeps = []

    def fn():
        raise VendorError("v", "always down")

    with pytest.raises(VendorError):
        call_with_retry(fn, attempts=3, cooldown=60, sleep=sleeps.append)
    # 3 attempts -> sleep only between them (after #1 and #2), not after the last
    assert sleeps == [60, 60]


def test_reraises_last_vendor_error():
    def fn():
        raise VendorError("cruz_verde", "still empty", status=404)

    with pytest.raises(VendorError) as exc:
        call_with_retry(fn, attempts=2, sleep=_no_sleep)
    assert exc.value.status == 404


def test_non_vendor_error_propagates_immediately():
    calls = []

    def fn():
        calls.append(1)
        raise ValueError("a real bug")

    with pytest.raises(ValueError):
        call_with_retry(fn, attempts=3, sleep=_no_sleep)
    assert len(calls) == 1  # not retried
