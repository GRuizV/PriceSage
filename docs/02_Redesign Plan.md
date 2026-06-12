# PriceSage — Redesign Plan (v2)

*Created 2026-06-11. This is the working plan; it supersedes `00_Project Overview.md`.*

## What PriceSage is now

A personal tool that tracks **finasteride prices** (multiple brands, multiple Colombian pharmacies) daily, keeps the full price history, and **emails me when buy conditions are met**.

Guiding filter for every decision: **free, stable, useful, and provably mine** (CV-showcaseable as "I built and maintain something solving a real need"). Anything that doesn't serve that gets cut.

## Locked decisions

| Concern | Decision |
|---|---|
| Scope | Finasteride only (Levothyroxine dropped). Config-driven, so adding a product later = edit one file |
| Runtime | GitHub Actions scheduled workflow (public repo = free forever). Fallback: AWS Lambda, only if runner IPs are blocked |
| Storage | Neon free Postgres (normalized) + raw JSON snapshots committed to repo. Raw layer is provisional — drop if deadweight |
| Alerts | Plain email (Gmail SMTP + app password). No Telegram/Twilio |
| Auth (Cruz Verde) | Only `connect.sid` (anonymous session) is required — verified 2026-06-11. Must self-bootstrap per run, nothing hardcoded |
| Parked | Dashboard, ML, Docker — not until the collector has run unattended for months |

## Architecture

```
config/products.yml          # SKUs per vendor, store zone, alert thresholds
src/pricesage/
  models.py                  # PriceObservation (normalized record)
  adapters/                  # one module per vendor, all return list[PriceObservation]
    base.py
    cruz_verde.py
  storage/
    raw.py                   # append raw API JSON → data/raw/ (committed)
    db.py                    # write observations → Neon Postgres
  alerts.py                  # buy-condition rules → email
  main.py                    # CLI orchestrator; one vendor failing never kills the run
data/raw/                    # bronze layer, JSONL per vendor
.github/workflows/collect.yml
tests/
```

DB schema (minimal): `listings` (vendor, sku, brand, name) + `observations` (listing_id, scraped_at, full_price, disc_price, pum, stock). Extend only when a real need appears.

## Phases

### Phase 0 — Decisions & redesign docs ✅ (2026-06-11)
- [x] Stack decisions locked (table above)
- [x] This plan written; README rewritten

### Phase 1 — Spikes (de-risk before building)
- [ ] **S1: Session bootstrap.** Find the endpoint that mints `connect.sid` (fresh incognito + DevTools, watch for first `Set-Cookie`). Deliverable: a function that returns a fresh session cookie.
  - Request Shape:
  ```python
    import requests

    cookies = {
        '_ga': 'GA1.3.1852395052.1781278795',
        '_gid': 'GA1.3.914356628.1781278795',
        '_gat': '1',
        '_gcl_au': '1.1.987109452.1781278796',
        '_fbp': 'fb.1.1781278795825.1506076338',
        '_ga': 'GA1.1.1852395052.1781278795',
        '_ga_CVCO': 'GS2.1.s1781278796$o1$g0$t1781278796$j60$l0$h1302745312',
    }

    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'es-ES,es;q=0.9',
        'cache-control': 'no-cache',
        # Already added when you pass json=
        # 'content-type': 'application/json',
        'dnt': '1',
        'origin': 'https://www.cruzverde.com.co',
        'pragma': 'no-cache',
        'priority': 'u=1, i',
        'referer': 'https://www.cruzverde.com.co/',
        'sec-ch-ua': '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
    }

    json_data = {}

    response = requests.post('https://api.cruzverde.com.co/customer-service/login', cookies=cookies, headers=headers, json=json_data)
  ```

- [ ] **S2: Runner IP test.** Minimal script hitting the Cruz Verde API from a GitHub Actions runner. Pass → GH Actions confirmed; fail → evaluate Lambda.

### Phase 2 — Core build (local, collects real history from day one)
- [ ] Package scaffold + `config/products.yml` (finasteride SKUs, `COCV_zona14` as config)
- [ ] `PriceObservation` model
- [ ] Cruz Verde adapter (self-bootstrapping session; fix inverted %-off; drop dead cookies)
- [ ] Raw layer: append JSONL per run
- [ ] Orchestrator CLI + per-vendor failure isolation
- [ ] Micro-test each step; small pytest suite for parsing/normalization

### Phase 3 — Neon Postgres
- [ ] Create Neon project, define schema, connection via env var
- [ ] DB writer + idempotency (re-running a day must not duplicate rows)
- [ ] Backfill anything collected during Phase 2

### Phase 4 — PROD scheduling
- [ ] `collect.yml`: daily cron, secrets (DB URL, SMTP), commit raw data back to repo
- [ ] Failure visibility: GitHub's failure email + a clear job summary. A silently-dead cron is the #1 project killer
- [ ] Let it run unattended ≥1 week before building anything else

### Phase 5 — Buy alerts
- [ ] Threshold rules in `products.yml` (e.g., disc_price below X, or % off above Y, and stock > 0)
- [ ] Email sender + "already alerted" suppression (don't re-mail daily for the same price)

### Phase 6 — Second provider
- [ ] Scout candidates (Farmatodo, La Rebaja, Locatel, Colsubsidio…) — classify by tier (API / HTML / browser-gated)
- [ ] Build adapter for the easiest one → proves the adapter pattern

### Parked (revisit only with months of data and a stable collector)
- Streamlit dashboard · price prediction · Docker

## Constraints
- `00 tests & notes.ipynb` + `01 formatted_comparison.md` stay untouched and working — they're the manual runner until PROD replaces them.
- Historical daily entries exist outside the repo; they'll be migrated in when dashboard/ML phases arrive.

## Known issues being fixed in Phase 2
- Hardcoded browser cookies (rot + tied to personal session) → self-bootstrap
- "% Off" math inverted (shows 95% for a 5% discount)
- No history persisted (output overwritten each run)
- Duplicate `_ga` key in cookies dict
