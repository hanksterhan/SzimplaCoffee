# SzimplaCoffee Execution Plan

## Goal

Build a local-first web application that answers:

**What coffee should I order right now, from which merchant, in what size, and why?**

The system must optimize for:

- espresso fit
- merchant trust
- freshness confidence
- delivered cost
- bag-size fit
- promo and bulk value

## Product Cut

### In scope for v1

- local web app for operating the system
- merchant registry with trust tiers
- manual merchant add
- Shopify and WooCommerce crawling
- product, variant, offer, and promo snapshots
- shipping threshold tracking
- Notion import for purchase history
- recommendation flow for espresso-oriented buying
- support for `12-18 oz`, `2 lb`, and `5 lb` decisions

### Out of scope for v1

- multi-user auth
- cloud hosting
- browser-first crawling
- generic marketplace features
- social or review features
- full automation of personalized wallet credits

## Core Decisions

| Decision | Choice | Rationale |
| --- | --- | --- |
| App shape | Local-first web app plus CLI | We need an operator console, not just commands |
| Backend | Python 3.12 + FastAPI | Fast to build, good typing, easy CLI and web integration |
| UI | Jinja templates + HTMX | Lower complexity than a SPA, enough interactivity for admin workflows |
| DB | SQLite + WAL + FTS5 | Best fit for single-user local app with search and history |
| ORM | SQLAlchemy 2 + Alembic | Stable schema management and migrations |
| Crawler framework | Crawlee for Python | Gives queues, retries, HTTP crawlers, and browser fallback |
| Browser automation | Playwright fallback only | Browser crawling is slow and brittle; use only when needed |
| Scheduler | APScheduler | Enough for local recurring jobs without a queue platform |
| LLM use | Direct structured calls only | Use only for enrichment and low-confidence extraction, not orchestration magic |
| Second brain | Repo-local markdown system | Durable, diffable, easy for both human and agent to use |

## Architecture

### Runtime components

1. Web app
2. CLI
3. Scheduler
4. Crawl workers
5. Recommendation engine
6. Importers
7. Second brain

### Request and job boundaries

- Web requests should read data, trigger jobs, and render results.
- Heavy crawling should run outside request handlers.
- Scheduled jobs should execute via CLI entrypoints or worker functions.
- All crawler and recommendation runs should write structured run records.

### High-level flow

1. Add or discover merchant
2. Detect platform
3. Select crawler adapter
4. Extract products, offers, promos, and policies
5. Store time-series snapshots
6. Import personal purchase history
7. Score candidate coffees against current buying intent
8. Return recommendation with explanation

## Tech Stack

### Application

- Python 3.12+
- FastAPI
- Jinja2
- HTMX
- small plain JavaScript only where needed

### Data

- SQLite
- SQLAlchemy 2
- Alembic

### Crawling

- Crawlee for Python
- BeautifulSoupCrawler
- AdaptivePlaywrightCrawler
- PlaywrightCrawler only for true fallback cases

### Tooling

- `uv`
- `ruff`
- `pytest`

## Crawler Architecture

### Design rule

Do not default to a browser.

Use the cheapest reliable extractor in this order:

1. direct platform API
2. static HTML parse
3. adaptive browser crawl
4. full browser crawl

### Adapter registry

The crawler layer should be adapter-driven.

Each adapter should expose:

- `detect(url) -> confidence`
- `discover_entrypoints(merchant)`
- `crawl_catalog(merchant)`
- `crawl_promos(merchant)`
- `crawl_shipping(merchant)`
- `normalize(payload) -> records + confidence`

### Initial adapters

#### Shopify adapter

Primary paths:

- `/products.json`
- product `.js` endpoints
- HTML fallback for banners, shipping pages, and promo pages

Why first:

- many specialty roasters use Shopify
- product and variant data is often publicly structured

#### WooCommerce adapter

Primary paths:

- `/wp-json/wc/store/v1/products`
- category endpoints
- HTML fallback for policies and promos

Why first:

- Camber-like stores are already relevant to the target user
- store API is structured enough for v1

#### Static HTML adapter

Use when:

- no useful platform API is available
- pages still expose parseable product and policy content

#### Browser fallback adapter

Use only when:

- client-side rendering blocks extraction
- promo data appears only after execution
- selectors cannot be resolved from static HTML

### Merchant discovery

Support three ingestion paths:

1. Manual add by URL
2. Seed imports from curated roaster lists
3. Discovery crawl for U.S. coffee roasters

Discovery output should go into a candidate queue, not directly into trusted merchants.

### Crawl tiers

| Tier | Meaning | Frequency |
| --- | --- | --- |
| A | Trusted or high-value merchants | Every 4 to 6 hours |
| B | Good candidates with strong fit | Daily |
| C | Long tail merchants | Weekly |
| D | Excluded or low-value merchants | Rare or on-demand |

### Crawl run outputs

Each crawl run should persist:

- adapter used
- started_at
- finished_at
- status
- confidence
- pages touched
- records written
- errors

## Data Shape

The database should be explicit and historical. Do not overwrite current state without retaining snapshots.

### `merchants`

Purpose:

- canonical merchant record

Core fields:

- `id`
- `name`
- `canonical_domain`
- `homepage_url`
- `platform_type`
- `country_code`
- `is_active`
- `crawl_tier`
- `trust_tier`
- `created_at`
- `updated_at`

Indexes:

- unique `canonical_domain`
- index on `crawl_tier`
- index on `trust_tier`

### `merchant_sources`

Purpose:

- record how a merchant entered the system

Core fields:

- `id`
- `merchant_id`
- `source_type` (`manual`, `seed`, `discovery`)
- `source_value`
- `discovered_at`
- `confidence`

### `merchant_quality_profiles`

Purpose:

- objective merchant quality signals

Core fields:

- `merchant_id`
- `freshness_transparency_score`
- `shipping_clarity_score`
- `metadata_quality_score`
- `espresso_relevance_score`
- `service_confidence_score`
- `overall_quality_score`
- `last_reviewed_at`

### `merchant_personal_profiles`

Purpose:

- user-specific trust and experience

Core fields:

- `merchant_id`
- `has_order_history`
- `would_reorder`
- `personal_trust_score`
- `average_rating`
- `notes`
- `last_ordered_at`

### `shipping_policies`

Purpose:

- normalized shipping policy state

Core fields:

- `id`
- `merchant_id`
- `free_shipping_threshold_cents`
- `shipping_notes`
- `estimated_roast_to_ship_days`
- `estimated_delivery_days`
- `source_url`
- `observed_at`
- `confidence`

### `products`

Purpose:

- canonical coffee product record

Core fields:

- `id`
- `merchant_id`
- `external_product_id`
- `name`
- `product_url`
- `origin_text`
- `process_text`
- `variety_text`
- `roast_cues`
- `tasting_notes_text`
- `is_single_origin`
- `is_espresso_recommended`
- `is_active`
- `first_seen_at`
- `last_seen_at`

Indexes:

- unique `(merchant_id, external_product_id)`
- full-text search on `name`, `origin_text`, `process_text`, `tasting_notes_text`

### `product_variants`

Purpose:

- size-level and option-level purchasable variants

Core fields:

- `id`
- `product_id`
- `external_variant_id`
- `label`
- `weight_grams`
- `is_whole_bean`
- `is_available`
- `first_seen_at`
- `last_seen_at`

Indexes:

- unique `(product_id, external_variant_id)`
- index on `weight_grams`

### `offer_snapshots`

Purpose:

- time-series price and availability tracking

Core fields:

- `id`
- `variant_id`
- `observed_at`
- `price_cents`
- `compare_at_price_cents`
- `is_on_sale`
- `subscription_price_cents`
- `is_available`
- `source_url`

Indexes:

- index on `(variant_id, observed_at desc)`

### `promo_snapshots`

Purpose:

- merchant-level promo capture

Core fields:

- `id`
- `merchant_id`
- `observed_at`
- `promo_type`
- `title`
- `details`
- `code`
- `estimated_value_cents`
- `source_url`
- `confidence`

### `purchase_history`

Purpose:

- imported and native purchase record

Core fields:

- `id`
- `merchant_id`
- `product_name`
- `origin_text`
- `process_text`
- `price_cents`
- `weight_grams`
- `purchased_at`
- `source_system`
- `source_ref`

### `brew_feedback`

Purpose:

- connect coffee outcomes to actual espresso use

Core fields:

- `id`
- `purchase_id`
- `shot_style`
- `grinder`
- `basket`
- `rating`
- `would_rebuy`
- `difficulty_score`
- `notes`

### `recommendation_runs`

Purpose:

- reproducibility and learning

Core fields:

- `id`
- `run_at`
- `request_json`
- `top_result_json`
- `alternatives_json`
- `wait_recommendation`
- `model_version`

### `crawl_runs`

Purpose:

- crawl observability

Core fields:

- `id`
- `merchant_id`
- `run_type`
- `adapter_name`
- `started_at`
- `finished_at`
- `status`
- `confidence`
- `records_written`
- `error_summary`

## Recommendation Engine

### Input contract

The recommendation request should accept:

- `shot_style`
- `quantity_mode`
- `max_inventory_grams`
- `delivery_by`
- `bulk_allowed`
- `ferment_tolerance`
- `preferred_roasters`
- `avoid_roasters`

### First scoring model

Use weighted scoring with explicit subscores:

- `merchant_trust_score`
- `personal_history_score`
- `coffee_fit_score`
- `espresso_style_fit_score`
- `freshness_confidence_score`
- `delivery_confidence_score`
- `deal_score`
- `inventory_fit_score`

### Decision rules

- Low-trust merchants should not win on price alone.
- Bulk variants should only rank highly when the user allows bulk.
- The engine should be able to return `wait`.
- Every output should include a short rationale tied to the subscores.

## Web Application Shape

### Initial pages

1. Dashboard
2. Merchant list
3. Merchant detail
4. Product and offer explorer
5. Recommendation console
6. Job and crawl health

### UI rule

This is an operator tool first. Prefer fast, inspectable screens over polished consumer UX.

## CLI Shape

Initial commands:

- `szimpla merchant add <url>`
- `szimpla merchant discover`
- `szimpla crawl merchant <merchant_id>`
- `szimpla crawl promos <merchant_id>`
- `szimpla recommend`
- `szimpla sync notion`
- `szimpla brain capture`

## Second Brain System

The second brain should support continuity, not narrative.

### Required structure

- `SzimplaCoffee/north-star.md`
- `SzimplaCoffee/comprehensive-plan.md`
- `SzimplaCoffee/brain/index.md`
- `SzimplaCoffee/brain/decisions/`
- `SzimplaCoffee/brain/research/`
- `SzimplaCoffee/brain/merchant-intel/`
- `SzimplaCoffee/brain/worklog/`
- `SzimplaCoffee/brain/backlog/`

### Rules

- Architecture changes require a short decision record.
- High-value merchants get one merchant-intel file.
- Each work session updates the worklog and backlog.
- Long analysis should be converted into durable decisions or deleted.

## Execution Phases

### Phase 0: Repo and foundation

Build:

- app skeleton
- SQLite setup
- Alembic migrations
- FastAPI app shell
- Jinja layout
- CLI shell
- second brain folders

Acceptance:

- app boots
- migration runs
- base page renders
- CLI command executes

### Phase 1: Merchant registry

Build:

- merchant schema
- manual add form
- platform detection
- merchant list and detail pages
- trust-tier editing

Acceptance:

- can add merchant by URL
- can classify Shopify, WooCommerce, or unknown
- can inspect merchant status in UI

### Phase 2: Structured crawlers

Build:

- Shopify adapter
- WooCommerce adapter
- crawl run persistence
- product and variant persistence
- offer snapshot persistence

Acceptance:

- Olympia-like and Camber-like merchants crawl successfully
- price and size snapshots persist
- crawl confidence is visible

### Phase 3: Policies and promos

Build:

- shipping policy extraction
- promo extraction
- compare-at and subscription handling
- tiered scheduling

Acceptance:

- landed price is visible
- free-shipping thresholds are tracked
- promos are visible per merchant

### Phase 4: Personalization and recommendations

Build:

- Notion import
- purchase history model
- brew feedback model
- recommendation scoring
- recommendation page and CLI output

Acceptance:

- can issue a recommendation request
- output includes top pick, alternatives, and rationale

### Phase 5: Discovery and maintenance

Build:

- candidate merchant discovery
- candidate review workflow
- long-tail tiering
- second-brain discipline

Acceptance:

- new merchants can be discovered, reviewed, and promoted into active crawl tiers

## What we are intentionally not doing yet

- Postgres
- Celery or distributed workers
- React SPA
- cloud deployment
- automated wallet-credit ingestion
- universal browser crawling

These are valid future upgrades, but they are not the best use of time for v1.

## Immediate Next Step

Start implementation with:

1. app skeleton
2. migration setup
3. merchant schema
4. manual merchant add flow
5. platform detection

That sequence unlocks the crawler work without forcing premature UI or infra complexity.
