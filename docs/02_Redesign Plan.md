# PriceSage — Redesign Plan (v2)

*Created 2026-06-11, updated 2026-06-29. This is the working plan; it supersedes `00_Project Overview.md`.*

**Progress:** Phases 0–4 DONE — autonomous daily collection is LIVE (verified green cloud run 2026-07-12: Cruz Verde → JSONL + Neon, commit-back, health log). 32 tests. **Next: Phase 4 checkpoint cleanup sweep, then Phase 5 (email).**

*(older progress note below)* Collector runs end to end (`python -m pricesage` → live Cruz Verde → JSONL + Neon), loguru logging, **23 tests passing**. Done in P4: structured `VendorError` (raise-with-body), Layer-1 retry, `collection_runs` health log (verified in Neon). S2 spike passed (runtime = GitHub Actions). Provider scouting (6a) done early. **Next in P4: `debug.py` failure-body capture → persistent-failure detection → secure logging → `collect.yml`.**

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
  errors.py                  # [done] VendorError(vendor, message, status, body) — structured, carries raw response
  adapters/
    base.py                  # [done] VendorAdapter contract (raise VendorError incl. unexpected-empty)
    cruz_verde.py            # [done] connect.sid session; raises VendorError on failure/empty, carries body
  storage/
    raw.py                   # [done] append normalized observations → data/raw/{vendor}.jsonl
    db.py                    # [done] observations → Neon + collection_runs health rows; [todo] health query
    debug.py                 # [todo] dump raw failure bodies → data/debug/ (uploaded as CI artifact, not committed)
  retry.py                   # [done] orchestrator-level retry wrapper (attempts/cooldown), generic per vendor
  alerts.py                  # [todo] persistent-failure detection [P4] + email sending [P5]
  main.py / __main__.py      # [done] CLI orchestrator: retry per vendor, records VendorRun per vendor; flags --attempts/--retry-cooldown
data/raw/                    # [done] committed history, JSONL per vendor
data/debug/                  # [todo] failure bodies, gitignored, CI-artifact only
.github/workflows/collect.yml  # [todo]
tests/                       # [done] 23 tests (model/storage/db/adapter/errors/retry/orchestrator), offline
```

**Storage layering decision (2026-06-29):** `raw.py` stores *normalized observations* as JSONL, not raw API JSON. Raw API bodies are captured **only on failure** (debug.py → CI artifacts), never for successful runs — no daily-bronze bloat.

**Resilience model (2026-06-29):** two layers, kept separate.
- *Layer 1 — transient retry (within a run):* orchestrator wraps each vendor's `collect()`; on failure wait `cooldown` (60s) and retry, up to `attempts` (3) total. A fresh attempt re-mints the session. Lives in the orchestrator so every adapter gets it free — adapters stay dumb.
- *Layer 2 — persistent-failure alert (across runs):* `collection_runs` table is the source of truth. Alert when a vendor's latest `'ok'` run is > `alert_after_days` (3) old. Detection in P4, email delivery in P5.
- *Adapter contract:* success returns observations (partial = still success); **any failure, including unexpected-empty, raises `VendorError` carrying status + raw body.** Orchestrator catches it → retries → on final failure dumps the body (debug.py) + records the run row. Dumb adapter, smart orchestrator.
- *Visibility split:* GitHub run red/green = did the job run (red only on a real crash). Empty-after-retries is a tracked condition, stays green + logged. Email = the Layer-2 persistence signal. Avoids alert fatigue.
- *Config (global to start, per-vendor override later if needed):* `attempts=3`, `cooldown=60s`, `alert_after_days=3`.

DB schema: `listings` (vendor, sku, brand, name, units_per_box, url) + `observations` (listing_id, obs_date, scraped_at, full_price, disc_price, price_source, stock) + **`collection_runs`** (vendor, run_at, run_date, status `ok|empty|error`, attempts, observations, error_type, error_detail) — one appended row per vendor per run; feeds health dashboard (later) + Layer-2 alert. Extend only when a real need appears.

## Phases

### Phase 0 — Decisions & redesign docs ✅ (2026-06-11)
- [x] Stack decisions locked (table above)
- [x] This plan written; README rewritten

### Phase 1 — Spikes (de-risk before building)
- [x] **S1: Session bootstrap.** ✅ (2026-06-29) `POST https://api.cruzverde.com.co/customer-service/login` with empty body `{}` → 201, `authType: guest`, sets `connect.sid`. No copied cookies needed. Implemented in `cruz_verde.py:_new_session()`.
- [x] **S2: Runner IP test.** Minimal script/workflow hitting the Cruz Verde API from a GitHub Actions runner. Pass → GH Actions confirmed; fail → evaluate Lambda. **← gates the runtime decision; do before investing in scheduling.**

### Phase 2 — Core build ✅ (2026-06-29) — collects real history from day one
- [x] Package scaffold (uv + src layout) + `config/products.yml` (finasteride SKUs, `COCV_zona14` as config)
- [x] `PriceObservation` model (computed `price_per_unit` + `discount_pct`, `price_source` audit field)
- [x] Cruz Verde adapter (self-bootstrapping session; fixed inverted %-off; dropped dead cookies)
- [x] Raw layer: append-only JSONL per vendor
- [x] Orchestrator CLI (`python -m pricesage`, flags `--config/--vendor/--no-store`) + per-vendor failure isolation
- [x] pytest suite: 9 tests (model + storage), all offline

### Phase 3 — Neon Postgres ✅ (2026-06-29)
- [x] Neon project created (free tier); schema in `storage/schema.sql` (listings + observations + `observation_details` view), connection via `DATABASE_URL` (.env, dotenv)
- [x] DB writer with idempotent upsert on `(listing_id, obs_date)`; obs_date is Colombia-local. Verified real round-trip.
- [ ] Backfill: optional, revisit (manual history lives outside repo; not blocking)

### Phase 4 — PROD scheduling + resilience
Decisions locked (2026-06-30): run time **13:00 UTC = 08:00 COT**; **commit raw JSONL back** (in-repo history + keepalive); visibility split = **green-on-transient, email-on-persistence** (retires the old "exit non-zero on 0 obs" idea).

Build order:
- [x] **Structured errors:** `errors.py` with `VendorError(vendor, message, status, body)`. Adapter contract: failure (incl. unexpected-empty) raises it carrying the raw body; success returns observations (partial = success).
- [x] **Cruz Verde adapter** raises `VendorError` on failure/empty instead of returning `[]` or logging-and-skipping.
- [x] **Retry (Layer 1):** `retry.py::call_with_retry` — orchestrator wraps each vendor `collect()`, `attempts=3`, `cooldown=60s`, fresh session per attempt, retries only on `VendorError` (real bugs propagate). CLI `--attempts`/`--retry-cooldown` for tuning/fast tests. Generic; adapters untouched.
- [x] **Run status (Layer 2 source):** `collection_runs` table + index + `db.record_runs`; orchestrator records one `VendorRun` per vendor per run (`ok|empty|error`, attempts, count, error_type/detail) — even on total failure. Verified in Neon (ok/1/2 and error/3/HTTP 404 rows).
- [ ] **Failure body capture:** `debug.py` dumps `VendorError.body` → `data/debug/` (gitignored); workflow uploads it as an artifact **only when failures occurred**.
- [ ] **Persistent-failure detection:** health query "latest `ok` per vendor older than `alert_after_days` (3)"; log the alert condition (email wiring is P5).
- [x] **Secure logging:** `configure_logging(diagnose=None)` auto-detects CI (`in_ci()`) and disables `backtrace`/`diagnose` there (secret-leak guard); rich locally.
- [x] **`collect.yml`:** daily cron (13:00 UTC) + `workflow_dispatch`; `DATABASE_URL` secret; runs collector; commits `data/raw/*.jsonl` back (`contents: write`); uploads `data/debug/` artifact only on failure. Green-on-transient. **Verified: full green cloud run 2026-07-12 — obs→JSONL+Neon, run-status row, data commit pushed, artifact correctly skipped.**
- [x] Delete obsolete `ip-probe.yml`.
- [ ] Let it run unattended ≥1 week before building anything else (probe phase; data cleared at real kick-off).
- [x] **Cron reliability — WON'T CHANGE (2026-07-13):** GitHub's `:00` scheduler is best-effort and delayed, but observed to fire reliably every day (~2h late: 13:00 UTC slot lands ~10:00 COT). Leaving `0 13 * * *` as-is to avoid churn — the delay is harmless for daily prices.
- [ ] **CI test workflow `tests.yml`:** on push + PR, run `uv sync --extra dev` then `pytest` (offline suite, no secrets). Add a passing-tests badge to the README. NOT branch protection / required checks yet — we push directly to `main` (+ bot data commits), so required-PR checks would fight that; revisit only if a PR flow is adopted.

**Phase Checkpoint and clean-up**
- [ ] Make sure everything built up until now is self-documenting, clear, has in-line comments, docstrings on main functions and at module level where needed. Include README + CHANGELOG coherence.


### Phase 5 — Buy alerts + outage emails
- [ ] Email sender (Gmail SMTP + app password); shared by both alert types below.
- [ ] **Outage email:** deliver the Layer-2 persistent-failure signal detected in P4.
- [ ] **Buy alert:** threshold rules in `products.yml` (e.g. price_per_unit below X, or % off above Y, and stock > 0).
- [ ] "Already alerted" suppression for both (don't re-mail daily for the same condition; re-arm on recovery/change).

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
