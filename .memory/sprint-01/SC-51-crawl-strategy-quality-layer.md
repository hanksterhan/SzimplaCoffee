# SC-51 Delivery Memory: Crawl Strategy Quality Layer

## What Changed

- Added `STRATEGY_FEED`, `STRATEGY_STRUCTURED`, `STRATEGY_DOM`, `STRATEGY_AGENTIC`, `STRATEGY_NONE` constants to `services/crawlers.py`
- Extended `CrawlSummary` dataclass with `catalog_strategy`, `promo_strategy`, `shipping_strategy`, `metadata_strategy` fields and a computed `crawl_quality_score` property
- All 4 crawl functions now return explicit strategy metadata:
  - `_crawl_shopify` → `catalog: feed`, `metadata: structured`
  - `_crawl_woocommerce` → `catalog: feed`, `metadata: dom`
  - `_crawl_agentic_catalog` → `catalog: agentic`, `metadata: structured`
  - `_crawl_generic` → delegates to agentic
- `crawl_merchant()` writes strategy + quality score to `CrawlRun` model
- Added 5 new fields to `CrawlRun` model: `catalog_strategy`, `promo_strategy`, `shipping_strategy`, `metadata_strategy`, `crawl_quality_score`
- Updated `CrawlRunSchema` to expose all 5 new fields
- Added `/api/v1/merchants/{id}/crawl-quality` endpoint (SC-51 AC-3)
- Added `/api/v1/merchants/low-confidence` endpoint for review queue (feeds SC-52)
- 9 new tests in `tests/test_crawl_quality.py`

## Quality Score Formula

`crawl_quality_score = 0.60 × composite + 0.40 × confidence`

Where composite = `0.50 × catalog + 0.30 × metadata + 0.10 × promo + 0.10 × shipping`

Layer values: feed=1.0, structured=0.85, dom=0.70, agentic=0.55, none=0.0

## Why It Changed

The old system had no way to know whether a merchant's data came from a reliable JSON feed or a fragile agentic scrape. Low-confidence merchants were invisible. The strategy layer system makes this explicit and measurable.

## Surprises / Notes

- `CrawlSummary` used `@dataclass` so `crawl_quality_score` is a `@property`, not a field — SQLAlchemy models must still store the value explicitly via `run.crawl_quality_score = summary.crawl_quality_score`
- The `low-confidence` endpoint is a list endpoint — must be ordered before `/{merchant_id}` route or FastAPI will try to match "low-confidence" as an integer ID. Added it before the parameterized route.

## Follow-ups

- SC-52 should wire the low-confidence endpoint to a Review Queue UI component
- Future: track rolling success_rate per merchant across runs
