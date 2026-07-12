"""Shared error types.

`VendorError` is the single failure signal every adapter raises. It carries the
raw response (status + body) so the orchestrator can dump it for post-mortem
(debug.py) and record the failure mode (collection_runs), without each adapter
reimplementing any of that.
"""

from __future__ import annotations


class VendorError(Exception):
    """A vendor collection failed. Carries the raw response for diagnosis.

    Raised on ANY failure — transport/session errors AND unexpected-empty (a
    configured vendor that returns no observations). A partial result (some
    listings missing) is NOT a failure; the adapter returns what it got.
    """

    def __init__(
        self,
        vendor: str,
        message: str,
        *,
        status: int | None = None,
        body: str | None = None,
    ):
        self.vendor = vendor
        self.message = message
        self.status = status
        self.body = body
        detail = f" (HTTP {status})" if status is not None else ""
        super().__init__(f"[{vendor}] {message}{detail}")
