"""Shared contract for every vendor adapter."""

from __future__ import annotations

from abc import ABC, abstractmethod

from pricesage.models import PriceObservation


class VendorAdapter(ABC):
    """One adapter per pharmacy. `collect()` returns normalized observations.

    Adapters must not raise on a single bad listing — skip it and keep going so
    one missing product never loses the rest of the vendor's data. They may
    raise on a total failure (e.g. session bootstrap fails); the orchestrator
    isolates that so one dead vendor never kills the whole run.
    """

    vendor: str  # short stable key, must match the config block name

    @abstractmethod
    def collect(self) -> list[PriceObservation]:
        ...
