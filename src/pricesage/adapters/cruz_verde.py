"""Cruz Verde adapter.

Cruz Verde's product API is gated by a single `connect.sid` cookie tied to an
anonymous ("guest") session. We mint a fresh one per run via the login
endpoint, so nothing copied from a browser can rot.
"""

from __future__ import annotations

import requests
from loguru import logger

from pricesage.adapters.base import VendorAdapter
from pricesage.errors import VendorError
from pricesage.models import PriceObservation


_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
)


def _response_parts(resp: requests.Response | None) -> tuple[int | None, str | None]:

    """Pull (status, body) off a response for VendorError, tolerating None."""
    if resp is None:
        return None, None
    
    return resp.status_code, resp.text


class CruzVerdeAdapter(VendorAdapter):

    vendor = "cruz_verde"

    API = "https://api.cruzverde.com.co"
    SITE = "https://www.cruzverde.com.co"
    # Only the fields we actually map — far smaller than the browser's request.
    FIELDS = ("name", "prices", "stock", "brand", "pageURL")
    # disc_price preference order; the chosen key is recorded as price_source.
    DISCOUNT_KEYS = ("price-club-col", "price-sale-col")
    LIST_KEY = "price-list-col"

    def __init__(self, inventory_id: str, listings: list[dict], timeout: int = 15):
        self.inventory_id = inventory_id
        self.listings = listings
        self.timeout = timeout

    def collect(self) -> list[PriceObservation]:
        """Return observations. Raise VendorError on total failure or empty.

        A single listing missing/erroring is tolerated (partial result); only a
        run that yields *zero* observations raises — carrying the last response
        seen, so the orchestrator can dump it for diagnosis.
        """
        session = self._new_session()

        observations: list[PriceObservation] = []
        last_status: int | None = None
        last_body: str | None = None

        for listing in self.listings:
            sku = listing.get("sku")
            try:
                resp = session.get(self._summary_url(sku), timeout=self.timeout)
                last_status, last_body = resp.status_code, resp.text
                resp.raise_for_status()
                obs = self._parse(resp.json(), listing)
            except requests.RequestException as exc:
                last_status, last_body = _response_parts(exc.response)
                logger.warning("cruz_verde: request failed for {}: {}", sku, exc)
                continue

            if obs is None:
                logger.warning("cruz_verde: no usable data for {}", sku)
                continue
            observations.append(obs)

        if not observations:
            raise VendorError(
                self.vendor,
                "no observations (all listings missing or failing)",
                status=last_status,
                body=last_body,
            )
        return observations

    def _new_session(self) -> requests.Session:
        """Mint a fresh anonymous session; the login response sets connect.sid."""
        session = requests.Session()
        session.headers.update(
            {
                "accept": "application/json, text/plain, */*",
                "accept-language": "es-ES,es;q=0.9",
                "origin": self.SITE,
                "referer": f"{self.SITE}/",
                "user-agent": _USER_AGENT,
            }
        )
        try:
            resp = session.post(f"{self.API}/customer-service/login", json={}, timeout=self.timeout)
            resp.raise_for_status()
        except requests.RequestException as exc:
            status, body = _response_parts(exc.response)
            raise VendorError(
                self.vendor, "session bootstrap failed", status=status, body=body
            ) from exc
        if "connect.sid" not in session.cookies:
            raise VendorError(self.vendor, "login did not set connect.sid")
        return session

    def _summary_url(self, sku: str) -> str:
        fields = "".join(f"&fields={f}" for f in self.FIELDS)
        return (
            f"{self.API}/product-service/products/product-summary"
            f"?ids[]={sku}{fields}&inventoryId={self.inventory_id}"
        )

    def _parse(self, payload: dict, listing: dict) -> PriceObservation | None:
        sku = listing["sku"]
        node = payload.get(sku)
        if not node:
            return None

        prices = node.get("prices") or {}
        full_price = prices.get(self.LIST_KEY)
        if full_price is None:
            logger.warning("cruz_verde: {} has no {}", sku, self.LIST_KEY)
            return None

        disc_price, price_source = full_price, self.LIST_KEY
        for key in self.DISCOUNT_KEYS:
            if prices.get(key) is not None:
                disc_price, price_source = prices[key], key
                break

        slug = node.get("pageURL")
        url = f"{self.SITE}/{slug}/{sku}.html" if slug else None

        return PriceObservation(
            vendor=self.vendor,
            sku=sku,
            name=node.get("name", ""),
            brand=listing.get("brand") or node.get("brand", ""),
            full_price=int(full_price),
            disc_price=int(disc_price),
            units_per_box=int(listing["units_per_box"]),
            stock=int(node.get("stock", 0)),
            price_source=price_source,
            url=url,
        )
