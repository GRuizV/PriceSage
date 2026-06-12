# Providers Guide — Recon Reference

*Recon done 2026-06-12, all via plain HTTP (no browser anywhere). Prices below are from that day, just as proof of access.*

## Cross-cutting notes

- **All 9 sources are Tier 1** — plain `requests` is enough.
- **4 adapters cover everything**: CruzVerde (custom), VTEX (×4 sites), WooCommerce (×1), PrestaShop/HTML (×2 + Farmatodo).
- **Headers**: send full browser-like headers everywhere (UA, accept, accept-language, referer/origin). Two sites rejected bare curl but accepted a browser-shaped request.
- **Normalize per tablet**: boxes are x28 (Lafrancol/AG) vs x30 (Mk, Finhet). `PriceObservation` needs `units_per_box` + computed price-per-tablet, or comparisons lie.
- **EAN codes are the cross-vendor join key** where available: Lafrancol x28 = `7706569021601`, Mk = `7702057624170` / `7702057100568` (two variants seen — verify which is the x30 box).

---

## 1. Cruz Verde — custom API (current, working)

- Already solved in the notebook. Only missing piece: session self-bootstrap via `POST https://api.cruzverde.com.co/customer-service/login` (empty JSON body) → `Set-Cookie: connect.sid`. Only that cookie is needed.
- `inventoryId=COCV_zona14` pins the store zone (prices/stock vary by zone — keep as config).

## 2. VTEX platform — Farma Express, Colsubsidio, La Rebaja, tudrogueriavirtual

One adapter, four domains. Public catalog API, **no auth, no cookies**:

```
GET https://{domain}/api/catalog_system/pub/products/search?fq=alternateIds_Ean:{EAN}
GET https://{domain}/api/catalog_system/pub/products/search?ft={free text}     # fallback search
GET https://{domain}/api/catalog_system/pub/products/search?fq=productId:{id}  # stable per site
```

- Domains: `www.farmaexpress.com`, `www.drogueriascolsubsidio.com`, `www.larebajavirtual.com`, `www.tudrogueriavirtual.com`
- Response: JSON array of products. The money is in:
  `[0].items[0].sellers[0].commertialOffer` → `.Price` (current), `.ListPrice` (full), `.AvailableQuantity` (stock). *(Yes, "commertial" is misspelled in VTEX itself.)*
- Useful identity fields: `productId`, `productName`, `brand`, `linkText` (URL slug), `productReference` (often the EAN or vendor ref).
- Note: La Rebaja's Lafrancol-equivalent is branded **"AG"** (American Generics) — same molecule, different brand. Decide whether AG counts as a tracked brand.
- `ft=` search returns multiple products — filter by brand/EAN; `fq=` queries return exact matches.
- Caveat: VTEX supports regional sellers/sales channels (`sc=` param). Defaults looked national here, but if prices ever look off, that's where to look.

Verified 2026-06-12: FarmaExpress $114,470 (stock 10) · Colsubsidio $109,600/list $137,000 (100) · La Rebaja AG $120,600 (0) · TuDV Lafrancol $124,600 (100), Finhet x30 $77,900 (10).

## 3. San Jorge — WooCommerce Store API

Public, no auth:

```
GET https://www.drogueriasanjorge.com/wp-json/wc/store/v1/products?search=finasterida
```

- Fields: `name`, `sku` (=`100014362`, same ref as FarmaExpress — likely shared distributor code), `prices.price`, `prices.regular_price`, `is_in_stock`.
- **Gotcha**: `prices.currency_minor_unit` tells you how to scale the integer price (here `0` → price is already in COP units: `98000` = $98,000).
- Verified 2026-06-12: AG x28 $98,000, out of stock.

## 4. PrestaShop sites — Comfandi, Cafam

No public JSON API; data is server-rendered in the product page HTML. Two extraction options, prefer (a):

a) **`ld+json` structured data** (Comfandi has a full `Product` block: name, sku, gtin13, brand, `offers.price`, `offers.priceCurrency`, availability).
b) **Microdata**: Cafam exposes `itemprop="price" content="151900"` (its ld+json is partial — verify which block carries availability).

- Plain GET with browser headers works on both. Parse, don't regex the whole page — pull the `<script type="application/ld+json">` blocks.
- Verified 2026-06-12: Cafam Mk x30 $151,900 · Comfandi Mk x30 listed (~$5,500/tablet in description — confirm box price from `offers` when implementing).

## 5. Farmatodo — Angular SSR + Algolia

- The **SSR HTML already contains `ld+json` with the price** (`"price":151900`) → simplest path: plain GET on the product URL + parse ld+json, same technique as PrestaShop sites.
- Deeper option if HTML proves flaky: Algolia powers their search — app id `vcojeyd2po` (host `vcojeyd2po-dsn.algolia.net` visible in page source; search-only API key retrievable from their JS bundle). Also seen: `api-transactional.farmatodo.com`. Don't bother unless needed.
- Verified 2026-06-12: Mk x30 $151,900.

---

## Suggested implementation order

1. VTEX adapter (4 vendors at once, pure JSON, easiest win)
2. WooCommerce (San Jorge — trivial, ~same shape)
3. ld+json HTML adapter (Comfandi, Cafam, Farmatodo — one parser, three sites)
4. Cruz Verde refactor (session bootstrap) — already specced in the main plan

## Open questions

- Finhet ($2,597/tablet, 34% cheaper than best Lafrancol): vendor is Seven Pharma Colombia S.A.S. — verify INVIMA registration before trusting/buying.
- Mk EAN discrepancy (`...624170` vs `...100568`) — confirm both are the same x30 box.
- Which brands count as "the product" for alerts: Lafrancol only? + AG? + Mk? + Finhet?
