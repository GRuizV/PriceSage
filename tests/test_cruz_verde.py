from pricesage.adapters.cruz_verde import CruzVerdeAdapter
from pricesage.errors import VendorError


def _adapter():
    return CruzVerdeAdapter(
        inventory_id="COCV_zona14",
        listings=[{"sku": "COCV_95278", "brand": "Lafrancol", "units_per_box": 28}],
    )


def test_parse_maps_a_good_payload():
    payload = {
        "COCV_95278": {
            "name": "Finasterida 1Mg Caja X 28",
            "prices": {"price-list-col": 140200, "price-sale-col": 119170},
            "stock": 39,
            "brand": "LAFRANCOL",
            "pageURL": "finasterida-1mg-caja-x-28",
        }
    }
    listing = {"sku": "COCV_95278", "brand": "Lafrancol", "units_per_box": 28}
    obs = _adapter()._parse(payload, listing)
    assert obs.disc_price == 119170
    assert obs.price_source == "price-sale-col"
    assert obs.brand == "Lafrancol"  # config brand wins over API's noisy legal name
    assert obs.url.endswith("/finasterida-1mg-caja-x-28/COCV_95278.html")


def test_parse_returns_none_when_sku_absent():
    listing = {"sku": "COCV_95278", "brand": "Lafrancol", "units_per_box": 28}
    assert _adapter()._parse({}, listing) is None


def test_parse_returns_none_when_no_list_price():
    payload = {"COCV_95278": {"name": "x", "prices": {}, "stock": 0}}
    listing = {"sku": "COCV_95278", "brand": "Lafrancol", "units_per_box": 28}
    assert _adapter()._parse(payload, listing) is None


def test_vendor_error_carries_response():
    err = VendorError("cruz_verde", "boom", status=403, body="<html>blocked</html>")
    assert err.vendor == "cruz_verde"
    assert err.status == 403
    assert err.body == "<html>blocked</html>"
    assert err.kind == "error"  # default
    assert "cruz_verde" in str(err) and "HTTP 403" in str(err)


def test_vendor_error_kind_can_be_empty():
    err = VendorError("cruz_verde", "nothing", status=200, kind="empty")
    assert err.kind == "empty"
