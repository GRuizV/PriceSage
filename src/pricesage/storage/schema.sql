-- PriceSage schema. Idempotent: safe to run on every collection.
-- Two tables: stable product identity (listings) + time-varying prices (observations).

CREATE TABLE IF NOT EXISTS listings (
    id            SERIAL PRIMARY KEY,
    vendor        TEXT    NOT NULL,
    sku           TEXT    NOT NULL,
    brand         TEXT    NOT NULL,
    name          TEXT    NOT NULL,
    units_per_box INTEGER NOT NULL,
    url           TEXT,
    UNIQUE (vendor, sku)
);

CREATE TABLE IF NOT EXISTS observations (
    id           SERIAL      PRIMARY KEY,
    listing_id   INTEGER     NOT NULL REFERENCES listings (id),
    obs_date     DATE        NOT NULL,        -- Colombia-local date of the reading
    scraped_at   TIMESTAMPTZ NOT NULL,        -- exact UTC instant
    full_price   INTEGER     NOT NULL,
    disc_price   INTEGER     NOT NULL,
    price_source TEXT        NOT NULL,
    stock        INTEGER     NOT NULL,
    currency     TEXT        NOT NULL DEFAULT 'COP',
    UNIQUE (listing_id, obs_date)             -- one row per product per day; re-runs upsert
);

-- Health log: one appended row per vendor per run (success or failure).
-- Source of truth for the persistent-failure alert and a future health dashboard.
CREATE TABLE IF NOT EXISTS collection_runs (
    id           SERIAL      PRIMARY KEY,
    vendor       TEXT        NOT NULL,
    run_at       TIMESTAMPTZ NOT NULL,        -- exact UTC instant of the run
    run_date     DATE        NOT NULL,        -- Colombia-local day
    status       TEXT        NOT NULL,        -- ok | empty | error
    attempts     INTEGER     NOT NULL,        -- tries used before resolving
    observations INTEGER     NOT NULL DEFAULT 0,
    error_type   TEXT,                        -- e.g. HTTP 404 (null when ok)
    error_detail TEXT                         -- short message (null when ok)
);

CREATE INDEX IF NOT EXISTS idx_collection_runs_vendor_run_at
    ON collection_runs (vendor, run_at DESC);

-- Convenience view: joins identity + adds the derived per-unit price and % off,
-- so dashboard/alert queries don't recompute them.
CREATE OR REPLACE VIEW observation_details AS
SELECT
    o.id,
    l.vendor,
    l.sku,
    l.brand,
    l.name,
    l.units_per_box,
    o.obs_date,
    o.scraped_at,
    o.full_price,
    o.disc_price,
    o.price_source,
    o.stock,
    o.currency,
    round(o.disc_price::numeric / l.units_per_box, 2) AS price_per_unit,
    CASE WHEN o.full_price > 0
         THEN round((1 - o.disc_price::numeric / o.full_price) * 100)
         ELSE 0 END AS discount_pct,
    l.url
FROM observations o
JOIN listings l ON l.id = o.listing_id;
