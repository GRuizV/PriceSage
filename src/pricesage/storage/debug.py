"""Failure-body capture.

When a vendor fails, we already carry the raw response on `VendorError.body`.
This dumps it to `data/debug/` so the CI workflow can upload it as an artifact
for post-mortem. Successful runs never write here — only failures — so there's
no daily-bronze bloat. The directory is gitignored; it exists purely to hand
files to the artifact upload step.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

# src/pricesage/storage/debug.py -> project root
DEFAULT_DEBUG_DIR = Path(__file__).resolve().parents[3] / "data" / "debug"


def _extension(body: str) -> str:
    """Best-effort file extension so the dump opens cleanly in an editor."""
    head = body.lstrip()[:100].lower()
    if head.startswith(("{", "[")):
        return ".json"
    if head.startswith("<!doctype html") or "<html" in head:
        return ".html"
    return ".txt"


def dump_failure(
    vendor: str,
    body: str | None,
    *,
    when: datetime | None = None,
    debug_dir: str | Path | None = None,
) -> Path | None:
    """Write a failure body to data/debug/. Returns the path, or None if no body.

    The body is written verbatim (no header) so it stays valid JSON/HTML;
    metadata (vendor, time) lives in the filename.
    """
    if not body:
        return None
    target_dir = Path(debug_dir) if debug_dir else DEFAULT_DEBUG_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    when = when or datetime.now(timezone.utc)
    stamp = when.strftime("%Y%m%d_%H%M%S")
    path = target_dir / f"{vendor}_{stamp}{_extension(body)}"
    path.write_text(body, encoding="utf-8", errors="replace")
    return path
