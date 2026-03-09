# SzimplaCoffee Comprehensive Build Plan

This document turns the north star into an actionable build plan for a solo developer using agentic engineering.

## Consensus Packet

### Problem statement

Build a local-first web application that helps us decide where to buy coffee right now, based on espresso intent, quality bar, merchant trust, bag size, delivery timing, promotions, and total landed cost.

The product must support:

- broad merchant coverage across U.S. coffee roasters and online coffee shops
- a strong quality bar
- espresso-specific recommendation logic
- personalized learning from our own buying history
- bulk-buy decisions such as 12 to 18 oz versus 2 lb or 5 lb
- automation for merchant discovery, offer refreshes, and promo tracking

### Domain and risk tier

- Domain: software
- Risk tier: medium

### Team composition used for synthesis

- Framer: product-owner-task-planner
- Analysts: technical-analyst, server-expert, coffee-brewing-expert
- Architects: software-architect, server-expert, ux-expert
- Critic: verifier
- Synthesizer: product-owner-task-planner

### Summary of votes and disagreements

- Strong agreement that this should be a local-first web application, not a CLI-only tool.
- Strong agreement that SQLite should be the initial source of truth, not CSV or Notion.
- Strong agreement that crawling should be adapter-first, not browser-first.
- Mild disagreement on frontend complexity:
  - Option A: React / SPA for richer interactivity
  - Option B: server-rendered UI with HTMX for faster solo-dev velocity
  - Resolution: choose server-rendered UI with HTMX for v1
- Mild disagreement on worker system:
  - Option A: simple in-process scheduling
  - Option B: full external queue system
  - Resolution: use APScheduler plus CLI job execution in v1, reserve external queue for later

### Recommendation

Build SzimplaCoffee as a Python local-first web app with:

- FastAPI
- server-rendered Jinja templates
- HTMX for progressive interactivity
- SQLite in WAL mode with FTS5 and JSON support
- SQLAlchemy 2 plus Alembic
- Crawlee for Python as the crawler framework
- adapter-first merchant extraction, with full browser automation only as fallback
- APScheduler for recurring jobs
- direct LLM usage with structured outputs for low-confidence extraction and note normalization
- a repo-local markdown-based second brain that the agent and developer can both use

### Risks

- Merchant discovery can grow faster than review capacity.
- Browser-first crawling would become slow, brittle, and expensive.
- Promo data can be inconsistent or partially personalized.
- Too much frontend complexity would slow a solo developer.
- Too much documentation entropy would hurt continuity across agent sessions.

### Confidence

- Confidence: high

### Confidence rationale

- The crawler choice is grounded in current official docs for Crawlee, Playwright, SQLite, FastAPI, APScheduler, and Notion limits.
- The product and data constraints are clear from the north star and the existing Bean Database patterns.
- The recommended stack minimizes moving parts while preserving a clean growth path.
- The rejected alternatives are valid, but they add complexity too early for this stage.

### Assumptions

- This remains a single-user or single-household tool in its first phase.
- The app runs locally on one machine for daily use and scheduled crawls.
- Most high-value merchants will expose parseable HTML, Shopify endpoints, WooCommerce Store API endpoints, or other structured data.
- We can manually review low-confidence merchants rather than demand perfect autonomous coverage.

### Unknowns

- How much of promo value comes from public sale signals versus personalized wallet signals.
- How quickly merchant count will grow after discovery is automated.
- Whether we eventually want multi-device sync or remote hosting.

## Initial Recommendation

There is a clear initial answer.

Build:

- a local-first web application
- with a companion CLI
- using SQLite as the operational store
- using adapter-first crawlers
- with a markdown-based second brain inside the repo

Do not build:

- a CLI-only tool
- a React-heavy SPA in v1
- a CSV-backed catalog
- a Notion-first operational system
- a browser-first crawler architecture

## Why this stack wins

### Why a local-first web app

The product is not just a recommendation API. It is also an operator console.

We need to:

- browse merchants
- inspect product and price snapshots
- review crawl health
- edit trust tiers
- override bad parses
- inspect why a recommendation was made

That is web-UI work, not CLI-only work.

### Why not a React-first SPA in v1

For a solo developer, a full SPA adds complexity in:

- state management
- API boundaries
- frontend build tooling
- testing surface area
- agent maintenance burden

A server-rendered interface with HTMX gives enough interactivity for admin-style workflows while keeping complexity low.

HTMX’s current documentation states that it expects HTML fragment responses and allows modern browser interactions directly from HTML, which is aligned with a low-complexity local admin app. [Source](https://htmx.org/docs/)

### Why SQLite

SQLite is the right first database because it is optimized for application-local storage and low-to-medium traffic workloads.

SQLite explicitly documents:

- it is commonly used as an application file format
- it works well for most low to medium traffic websites
- WAL mode allows readers and writers to proceed concurrently
- there can still only be one writer at a time

Those are good tradeoffs for a single-user local app with queued writes. [Sources](https://www.sqlite.org/whentouse.html) [WAL](https://www.sqlite.org/wal.html) [FTS5](https://www.sqlite.org/fts5.html)

### Why not Notion as the primary database

Notion is useful as an input source and report surface, but not as the operational store for crawling, snapshots, and recommendation data.

Notion’s official docs state that the average rate limit is three requests per second per integration, with 429 handling required. That is the wrong foundation for crawler-heavy data operations. [Source](https://developers.notion.com/reference/request-limits)

### Why Crawlee for Python plus Playwright

The crawler system needs:

- request queues
- retries
- deep crawl support
- HTTP crawlers for simple sites
- browser crawlers for dynamic sites
- a path to adaptive crawling

Crawlee for Python provides:

- `BeautifulSoupCrawler`
- `PlaywrightCrawler`
- `AdaptivePlaywrightCrawler`
- `RequestQueue`

Its docs specifically describe `AdaptivePlaywrightCrawler` as a combination of Playwright and an HTTP-based crawler, falling back to browser automation only when needed. That is exactly the efficiency pattern we want. [Sources](https://crawlee.dev/python/docs/quick-start) [Adaptive Playwright](https://crawlee.dev/python/docs/guides/adaptive-playwright-crawler) [RequestQueue](https://crawlee.dev/python/api/class/RequestQueue)

### Why FastAPI

FastAPI is a good local-first application server for APIs, templates, background-triggered endpoints, and CLI coordination.

Its background task docs are useful, but they also explicitly note that heavier background computation may benefit from bigger tools such as Celery. That reinforces the decision to keep heavy crawling outside request handlers and execute scheduled crawl jobs via CLI or worker entrypoints. [Source](https://fastapi.tiangolo.com/tutorial/background-tasks/)

### Why APScheduler for v1

We need recurring jobs, but we do not need a distributed worker fleet yet.

APScheduler gives:

- triggers
- job stores
- executors
- schedulers

That is enough for local recurring refreshes and periodic crawl orchestration. [Source](https://apscheduler.readthedocs.io/en/stable/userguide.html)

## Chosen Tech Stack

### Runtime and packaging

- Python 3.12+
- `uv` for environment and package management
- `ruff` for linting and formatting
- `pytest` for tests

### Web application

- FastAPI
- Jinja2 templates
- HTMX 2.x
- small amounts of plain JavaScript only where HTMX is not enough
- simple CSS system first, no frontend framework build pipeline in v1

### Data layer

- SQLite
- WAL mode enabled
- FTS5 for search over merchants, tasting notes, products, and notes
- JSON columns for flexible merchant metadata where needed
- SQLAlchemy 2
- Alembic for migrations

### Crawling and extraction

- Crawlee for Python
- BeautifulSoupCrawler for static HTTP extraction
- AdaptivePlaywrightCrawler for mixed sites
- PlaywrightCrawler only when JavaScript is truly required
- Playwright browsers installed locally

### Scheduling and jobs

- APScheduler
- CLI job entrypoints executed on schedules
- app-triggered jobs recorded in database as runs, but not executed inline in request handlers

### LLM and agent layer

- direct SDK usage with structured outputs
- no LangChain, no heavy graph orchestration in v1
- use LLMs only for:
  - normalization of tasting notes and merchant metadata
  - fallback extraction for messy unstructured content
  - merchant classification
  - recommendation explanation generation

### Testing

- unit tests for scoring and normalization
- adapter tests using captured merchant fixtures
- Playwright UI tests only for critical flows

## Architecture Overview

### Primary app surfaces

The web application should have six initial pages:

1. Dashboard
2. Merchants
3. Products and offers
4. Recommendation console
5. Jobs and crawl health
6. Notes and feedback

### CLI surfaces

The CLI should support:

- `szimpla merchant add <url>`
- `szimpla merchant discover`
- `szimpla crawl merchant <merchant_id>`
- `szimpla crawl promos`
- `szimpla recommend`
- `szimpla sync notion`
- `szimpla brain capture`

## Data Model

Start with explicit relational tables.

### Core tables

- `merchants`
- `merchant_sources`
- `merchant_quality_profiles`
- `merchant_personal_profiles`
- `merchant_promo_profiles`
- `products`
- `product_variants`
- `offer_snapshots`
- `shipping_policies`
- `job_runs`
- `crawl_events`
- `user_preferences`
- `recommendation_runs`
- `purchase_history`
- `brew_feedback`

### Search tables

- `merchant_search_fts`
- `product_search_fts`
- `notes_search_fts`

### Important design rule

Keep historical snapshots.

Do not overwrite the current truth without preserving:

- observed prices
- availability
- promotions
- shipping thresholds
- recommendation inputs and outputs

This tool becomes more valuable as it learns time-series behavior.

## Crawler Strategy

This is the most important engineering decision in the plan.

### Principle

Do not crawl every site with a browser.

Start with the cheapest reliable extraction path and only escalate when needed.

### Merchant pipeline

1. Merchant intake
2. Platform detection
3. Adapter selection
4. Catalog extraction
5. Offer extraction
6. Shipping and promo extraction
7. Confidence scoring
8. Human review if needed

### Adapter order

#### 1. Shopify adapter

Check for:

- `products.json`
- product `.js` endpoints
- structured theme metadata

Use direct HTTP when available.

#### 2. WooCommerce adapter

Check for:

- `wp-json/wc/store/v1/products`
- category and product endpoints
- structured schema in HTML

Use direct HTTP when available.

#### 3. Static HTML adapter

Use Crawlee HTTP crawlers to parse:

- merchant pages
- product pages
- FAQ and shipping pages
- sale banners
- subscription pages

#### 4. Adaptive browser adapter

Use `AdaptivePlaywrightCrawler` when:

- some pages are static and others are dynamic
- we need selector-based detection with uncertain rendering needs
- site behavior varies across merchant pages

#### 5. Full browser adapter

Use `PlaywrightCrawler` only when:

- content requires client-side rendering
- promo data exists only after page execution
- the site blocks or obscures direct extraction

### Why this is efficient

Most coffee merchants will fall into one of these buckets:

- Shopify with public endpoints
- WooCommerce with Store API
- static-ish HTML with parseable content
- true dynamic edge cases

That means the browser should be the exception, not the default.

### Discovery strategy

Use three discovery paths:

1. Manual add by URL
2. Seeded imports from curated roaster lists
3. Web discovery crawler

The discovery crawler should:

- search for U.S. coffee roasters and coffee subscriptions
- extract domains
- detect commerce capability
- queue merchant candidates
- classify whether the merchant is worth tracking

### Merchant crawl tiers

- Tier A: trusted and high-value merchants, refresh every 4 to 6 hours
- Tier B: strong candidates, refresh daily
- Tier C: long-tail merchants, refresh weekly
- Tier D: excluded or very low-trust merchants, refresh rarely or on demand

This keeps coverage broad without paying the same attention to every merchant.

### Promo and shipping extraction strategy

Store promo and shipping data separately from product data.

Track:

- announcement bars
- compare-at prices
- coupon codes
- free shipping thresholds
- subscription discounts
- “ships free” size variants
- sale timing patterns

### Personalized wallet value

Public crawlers cannot be trusted to know personal wallet credits consistently.

Treat Shop Cash and similar value as a separate ingestion stream:

- email parsing later
- manual entry initially
- possible authenticated integration later

## Recommendation Engine

### Inputs

- shot style
- quantity goal
- delivery deadline
- bulk allowed or not
- ferment tolerance
- roaster trust
- merchant trust
- delivery estimate
- landed price
- current promos
- personal wallet credits

### Initial scoring dimensions

- `merchant_trust_score`
- `coffee_fit_score`
- `espresso_style_fit_score`
- `freshness_confidence_score`
- `delivery_confidence_score`
- `deal_score`
- `inventory_fit_score`
- `personal_history_score`

### Important scoring rules

- A cheaper coffee from a low-trust merchant should not beat a better coffee from a trusted merchant unless the value difference is meaningful.
- Bulk sizes should only rank highly when the user allows them.
- The system should be allowed to return “wait”.
- Recommendation output must be explainable.

### Recommendation output contract

Every recommendation should include:

- top choice
- two alternatives
- wait recommendation if appropriate
- why each option ranked where it did
- confidence

## Second Brain System

This project must have a second brain from day one because it is a solo dev, agentic engineering effort.

The second brain should live inside the repo so both the human and the agent can use it directly.

### Goals of the second brain

- preserve decisions across sessions
- reduce repeated analysis
- keep merchant intelligence reusable
- capture assumptions and invalidations
- provide continuity for future implementation agents

### Recommended structure

Create and maintain:

- `SzimplaCoffee/north-star.md`
- `SzimplaCoffee/comprehensive-plan.md`
- `SzimplaCoffee/brain/index.md`
- `SzimplaCoffee/brain/decisions/`
- `SzimplaCoffee/brain/research/`
- `SzimplaCoffee/brain/merchant-intel/`
- `SzimplaCoffee/brain/experiments/`
- `SzimplaCoffee/brain/worklog/`
- `SzimplaCoffee/brain/backlog/`

### Document types

#### Decisions

Use ADR-style records for:

- stack decisions
- crawler decisions
- scoring decisions
- schema changes

#### Merchant intel

One file per high-value merchant with:

- trust notes
- crawl strategy
- promo habits
- shipping quirks
- extraction approach

#### Experiments

Track:

- scoring experiments
- espresso profile tuning
- merchant ranking changes
- crawl heuristics

#### Worklog

Session-based notes:

- what changed
- why it changed
- blockers
- follow-up work

#### Backlog

A prioritized backlog of:

- current slice
- next slice
- later slice

### Second-brain operating rules

- update decisions when architecture changes
- write merchant intel only for merchants that matter
- keep notes short and durable
- prefer markdown over external tools
- keep Notion as an optional mirror, not the working memory

## Build Phases

### Phase 0: foundation

Build:

- project skeleton
- FastAPI app
- SQLite schema
- migrations
- basic templates
- CLI shell
- second-brain folders

Done when:

- app starts locally
- database migrations run
- homepage and merchant list page render
- CLI can run a stub command

### Phase 1: merchant registry

Build:

- manual merchant add flow
- platform detection
- merchant list and merchant detail views
- trust-tier editing

Done when:

- we can add merchants by URL
- the system can classify Shopify, WooCommerce, or unknown
- merchants can be reviewed in the UI

### Phase 2: crawler adapters

Build:

- Shopify adapter
- WooCommerce adapter
- static HTML adapter
- browser fallback adapter

Done when:

- we can crawl Olympia-like and Camber-like sites reliably
- products, variants, and offers are stored
- crawl confidence is visible

### Phase 3: shipping and promo intelligence

Build:

- shipping threshold extraction
- promo extraction
- offer snapshot history
- tiered crawl scheduling

Done when:

- the system can show true landed price better than a manual spreadsheet

### Phase 4: personalized recommendation loop

Build:

- Notion import for Bean Database
- user preferences
- espresso-mode selection
- recommendation engine
- recommendation UI and CLI output

Done when:

- we can ask “what should I buy right now?” and get a useful, explainable answer

### Phase 5: second-brain maturity

Build:

- ADR cadence
- merchant-intel notes
- experiment tracking
- session worklog habits

Done when:

- future sessions no longer require re-deriving major decisions

### Phase 6: automation and refinement

Build:

- recurring merchant refreshes
- recurring promo crawls
- discovery runs
- recommendation notification workflow if desired

Done when:

- the system stays current without constant manual maintenance

## Risks and Mitigations

### Risk: long-tail crawl bloat

Mitigation:

- keep the tier system strict
- only elevate merchants that show quality and extractability

### Risk: bad promo data

Mitigation:

- separate public promos from personal wallet credits
- store confidence on every extracted promo

### Risk: too much browser usage

Mitigation:

- default to adapters and HTTP crawling
- measure browser crawl rate explicitly
- treat browser fallback as a failure signal to improve adapters

### Risk: overbuilding the UI

Mitigation:

- admin-tool aesthetics, not consumer-app aesthetics
- HTMX and templates first

### Risk: agent memory loss across sessions

Mitigation:

- keep the second brain inside the repo
- make updating it part of the normal workflow

## Immediate next actions

1. Create the app skeleton and second-brain folder structure.
2. Define the initial SQLite schema and migrations.
3. Implement merchant intake plus platform detection.
4. Build Shopify and WooCommerce adapters before any browser fallback work.
5. Add the merchant registry and merchant detail pages.
6. Import the existing Bean Database as the first personalization source.

## Final recommendation

The most effective and efficient way to build SzimplaCoffee is:

- Python local-first web app
- FastAPI plus Jinja plus HTMX
- SQLite plus SQLAlchemy
- Crawlee for Python with adapter-first crawling
- Playwright only as fallback
- APScheduler for local recurring jobs
- direct structured LLM calls for selective enrichment
- repo-local markdown second brain as a first-class system

This gives us the best balance of speed, clarity, and extensibility for a solo developer project.
