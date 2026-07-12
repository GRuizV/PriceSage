"""Layer-1 transient retry.

Wraps a vendor's `collect()` and retries on `VendorError`. Lives in the
orchestrator layer so every adapter gets retry for free — adapters just raise
`VendorError`; they don't know retry exists. Each attempt re-runs `collect()`
from scratch (fresh session), which is what clears most transient flakes
(DNS blips, stale/blocked sessions, 5xx).
"""

from __future__ import annotations

import time
from typing import Callable, TypeVar

from loguru import logger

from pricesage.errors import VendorError

DEFAULT_ATTEMPTS = 3
DEFAULT_COOLDOWN = 60.0  # seconds between attempts

T = TypeVar("T")


def call_with_retry(
    fn: Callable[[], T],
    *,
    label: str = "",
    attempts: int = DEFAULT_ATTEMPTS,
    cooldown: float = DEFAULT_COOLDOWN,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    
    """Call `fn()`; on `VendorError`, wait `cooldown` and retry, up to `attempts`.

    Returns the first successful result. Re-raises the last `VendorError` if
    every attempt fails (so the caller can record the failure / dump the body).
    Non-`VendorError` exceptions propagate immediately — those are bugs, not
    transient vendor flakes, and should surface loudly.

    `sleep` is injectable so tests don't actually wait.
    """

    last_error: VendorError | None = None
    
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except VendorError as exc:
            last_error = exc
            if attempt < attempts:
                logger.warning(
                    "{}: attempt {}/{} failed ({}); retrying in {:.0f}s",
                    label, attempt, attempts, exc, cooldown,
                )
                sleep(cooldown)
            else:
                logger.error(
                    "{}: attempt {}/{} failed ({}); giving up",
                    label, attempt, attempts, exc,
                )
    assert last_error is not None  # loop ran >=1 time, so this is set
    raise last_error
