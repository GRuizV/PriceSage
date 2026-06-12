# PriceSage

**"Track. Analyze. Buy Smart."**

PriceSage tracks finasteride prices across Colombian pharmacies daily, keeps the full price history, and emails me when it's a good moment to buy.

A personal tool, built to be **free to run, stable, and genuinely useful** — and maintained solo, end to end.

## How it works

- **Collect** — one adapter per pharmacy hits the vendor's internal API and emits normalized price observations (vendor, brand, full price, discounted price, price-per-unit, stock). One vendor failing never kills the run.
- **Store** — raw API snapshots committed to the repo (audit trail) + normalized rows in a free-tier Postgres (Neon).
- **Schedule** — GitHub Actions cron runs the collector daily. No servers, no cost.
- **Alert** — email when configured buy conditions are met (price threshold + stock).

Current vendors: **Cruz Verde** (more planned — see roadmap).

## Tech

Python · requests · PostgreSQL (Neon) · GitHub Actions · pytest

## Status & roadmap

Redesigned 2026-06-11 — see [docs/02_Redesign Plan.md](docs/02_Redesign%20Plan.md) for the working plan.
Currently on: **Phase 1 — spikes** (session bootstrap, runner IP test).

## License

[MIT License](LICENSE)

## Author

Built by Gerardo Ruiz — [LinkedIn](https://www.linkedin.com/in/GRuizV/) · [GitHub](https://github.com/GRuizV)
