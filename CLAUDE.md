# CLAUDE.md — SzimplaCoffee Agent Instructions

## What This Is

SzimplaCoffee is a local-first coffee sourcing and recommendation platform. It answers: **"What coffee should I order right now, from which merchant, in what size, and why?"**

Read `north-star.md` for product vision. Read `comprehensive-plan.md` for architecture and execution plan.

## Tech Stack

- **Backend:** Python 3.12+ / FastAPI / Jinja2 / HTMX
- **Data:** SQLite + WAL + FTS5 / SQLAlchemy 2 / Alembic
- **Crawling:** Crawlee for Python (BeautifulSoup → Adaptive Playwright → full browser fallback)
- **Scheduling:** APScheduler
- **Tooling:** uv, ruff, pytest
- **CLI:** `szimpla` entrypoint via `src/szimplacoffee/cli.py`

## Project Layout

```
src/szimplacoffee/       # Application source
  main.py                # FastAPI app + routes
  cli.py                 # CLI entrypoint
  config.py              # Configuration
  db.py                  # SQLAlchemy engine/session
  models.py              # SQLAlchemy models
  bootstrap.py           # Seed data
  services/
    crawlers.py           # Adapter-based crawling
    discovery.py          # Merchant discovery
    platforms.py          # Platform detection
    recommendations.py   # Scoring engine
  templates/             # Jinja2 templates
  static/                # CSS/JS
tests/                   # pytest tests
SzimplaCoffee/brain/     # Second brain (see below)
north-star.md            # Product vision (read-only reference)
comprehensive-plan.md    # Architecture plan (read-only reference)
```

## Conventions

- **Crawler order:** API → static HTML → adaptive browser → full browser. Never default to browser.
- **Snapshots over overwrites:** Price/promo data is append-only time-series. Don't mutate offer_snapshots.
- **Quality > price:** Recommendations optimize for best buy above a quality threshold, not lowest price.
- **Espresso-aware:** Shot style (58mm modern, 49mm lever, turbo, experimental) changes recommendation ranking.
- **Bag size matters:** 12-18oz vs 2lb vs 5lb is a first-class recommendation dimension.

## Commands

```bash
# Run the web app
uvicorn szimplacoffee.main:app --reload

# Run CLI
szimpla merchant add <url>
szimpla crawl merchant <id>
szimpla recommend

# Tests
pytest tests/

# Lint
ruff check src/ tests/
```

## Brain Protocol

After any meaningful work session:
1. Update `SzimplaCoffee/brain/worklog/YYYY-MM-DD-<slug>.md`
2. Update `SzimplaCoffee/brain/backlog/now-next-later.md`
3. If an architecture decision was made, create `SzimplaCoffee/brain/decisions/NNN-<title>.md`
4. If merchant-specific intel was gathered, update `SzimplaCoffee/brain/merchant-intel/<merchant>.md`

## Current State (as of 2026-03-08)

- 5 merchants, 111 products, 351 variants, 1451 offer snapshots
- Shopify + WooCommerce adapters working
- Recommendation engine functional with weighted scoring
- Web UI renders dashboard, merchant detail, discovery, recommendations
- Notion import is seeded, not fully integrated
- Browser fallback not wired up yet
- Promo false-positive suppression needs improvement
