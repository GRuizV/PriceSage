"""Shared contract for every vendor adapter."""

from __future__ import annotations

from abc import ABC, abstractmethod

from pricesage.models import PriceObservation


class VendorAdapter(ABC):
    
    """One adapter per pharmacy. `collect()` returns normalized observations.

    Contract:
      - Success returns >=1 observation. A single missing/erroring listing is
        tolerated (partial result) — don't lose the rest for one bad product.
      - ANY failure raises `VendorError` carrying the raw response (status +
        body), INCLUDING unexpected-empty (a configured vendor that yields
        zero observations). Never return an empty list.

    The orchestrator wraps `collect()` with retry + failure capture + run-status
    recording, so adapters stay simple and every vendor gets that for free.
    """

    vendor: str  # short stable key, must match the config block name

    @abstractmethod
    def collect(self) -> list[PriceObservation]:
        ...
