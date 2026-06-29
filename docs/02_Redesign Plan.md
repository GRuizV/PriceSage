# PriceSage — Redesign Plan (v2)

*Created 2026-06-11, updated 2026-06-29. This is the working plan; it supersedes `00_Project Overview.md`.*

**Progress:** Phases 0–2 done (core collector works end to end: `python -m pricesage` → live Cruz Verde data → `data/raw/cruz_verde.jsonl`, 9 tests passing). Provider scouting (Phase 6a) done early. **Next decision: S2 runner-IP spike vs Phase 3 Neon.**

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
config/products.yml          # [done] vendor blocks: store zone + listings (sku, brand, units_per_box)
src/pricesage/
  config.py                  # [done] load products.yml
  models.py                  # [done] PriceObservation (normalized record + per-unit/%off)
  adapters/
    base.py                  # [done] VendorAdapter contract (per-listing resilient)
    cruz_verde.py            # [done] self-bootstrapping connect.sid session
  storage/
    raw.py                   # [done] append normalized observations → data/raw/{vendor}.jsonl
    db.py                    # [todo] write observations → Neon Postgres
  alerts.py                  # [todo] buy-condition rules → email
  main.py / __main__.py      # [done] CLI orchestrator; one vendor failing never kills the run
data/raw/                    # [done] committed history, JSONL per vendor
.github/workflows/collect.yml  # [todo]
tests/                       # [done] 9 tests (model + storage), offline
```

**Storage layering decision (2026-06-29):** `raw.py` stores *normalized observations* as JSONL (immediately useful, testable history), not raw API JSON. When Postgres lands, decide whether `data/raw` becomes true raw-API bronze or retires — it's marked provisional, so no raw-capture machinery built yet.

DB schema (minimal): `listings` (vendor, sku, brand, name) + `observations` (listing_id, scraped_at, full_price, disc_price, price_source, units_per_box, stock). Extend only when a real need appears.

## Phases

### Phase 0 — Decisions & redesign docs ✅ (2026-06-11)
- [x] Stack decisions locked (table above)
- [x] This plan written; README rewritten

### Phase 1 — Spikes (de-risk before building)
- [x] **S1: Session bootstrap.** ✅ (2026-06-29) `POST https://api.cruzverde.com.co/customer-service/login` with empty body `{}` → 201, `authType: guest`, sets `connect.sid`. No copied cookies needed. Implemented in `cruz_verde.py:_new_session()`.
- [ ] **S2: Runner IP test.** Minimal script/workflow hitting the Cruz Verde API from a GitHub Actions runner. Pass → GH Actions confirmed; fail → evaluate Lambda. **← gates the runtime decision; do before investing in scheduling.**

### Phase 2 — Core build ✅ (2026-06-29) — collects real history from day one
- [x] Package scaffold (uv + src layout) + `config/products.yml` (finasteride SKUs, `COCV_zona14` as config)
- [x] `PriceObservation` model (computed `price_per_unit` + `discount_pct`, `price_source` audit field)
- [x] Cruz Verde adapter (self-bootstrapping session; fixed inverted %-off; dropped dead cookies)
- [x] Raw layer: append-only JSONL per vendor
- [x] Orchestrator CLI (`python -m pricesage`, flags `--config/--vendor/--no-store`) + per-vendor failure isolation
- [x] pytest suite: 9 tests (model + storage), all offline

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
- [x] **6a: Scout candidates** ✅ (2026-06-12) — all 9 sources are Tier 1 (plain HTTP, no browser). 4 adapter families cover everything: CruzVerde / VTEX×4 / WooCommerce / ld+json HTML×3. Full request shapes in `99 manual collection/02 providers guide.md`.
- [ ] **6b: Build adapter for the easiest one** → VTEX (covers FarmaExpress, Colsubsidio, La Rebaja, tudrogueriavirtual at once) → proves the adapter pattern

### Parked (revisit only with months of data and a stable collector)
- Streamlit dashboard · price prediction · Docker

## Constraints
- `00 tests & notes.ipynb` + `01 formatted_comparison.md` stay untouched and working — they're the manual runner until PROD replaces them.
- Historical daily entries exist outside the repo; they'll be migrated in when dashboard/ML phases arrive.

## Known issues — all fixed in Phase 2 ✅
- [x] Hardcoded browser cookies (rot + tied to personal session) → self-bootstrap per run
- [x] "% Off" math inverted (showed 95% for a 5% discount) → correct now
- [x] No history persisted (output overwritten each run) → append-only JSONL
- [x] Duplicate `_ga` key in cookies dict → cookie jar gone entirely
