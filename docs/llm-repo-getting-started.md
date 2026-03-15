# SzimplaCoffee LLM Getting Started

## Purpose

This document is the shortest accurate path to being useful in this repository.

Read these files first:

1. `AGENTS.md`
2. `north-star.md`
3. `README.md`

When those disagree with the code, prefer the code.

## Product Reality

SzimplaCoffee is a local-first coffee sourcing and recommendation system for an experienced home espresso user. The key product question is:

**What coffee should I order right now, from which merchant, in what size, and why?**

The core optimization target is not lowest price. It is best buy above a quality threshold, with espresso style, bag size, freshness, shipping, trust, and current promotions all factored in.

The system is allowed to recommend waiting.

## Architectural Reality

- The backend is a FastAPI application in `backend/src/szimplacoffee/`.
- The frontend is a React SPA in `frontend/`.
- In production, FastAPI serves the compiled frontend from `frontend/dist`.
- In development, Vite serves the frontend and proxies API traffic to the backend.
- SQLite is the operational source of truth.

## What Exists Today

- A full React SPA — not a scaffold.
- JSON APIs under `/api/v1`.
- Merchant discovery and promotion workflow.
- Catalog browsing and product search.
- Recommendation runs and recommendation history — inventory-aware, subscription-aware, with "wait" rationale.
- Purchase logging and brew feedback.
- **APScheduler**-driven recurring crawl scheduling — tiers A/B/C/D with automatic quality scoring after each crawl.
- **Layered crawl strategy**: feed → structured page data → DOM extraction → agentic fallback.
- Per-merchant crawl quality metrics persisted in the DB.
- Persisted pricing and promo history (append-only).
- **Deal facts** (`VariantDealFact`) tracking historical biggest-sale data per variant.
- **Today view** — daily buying decision dashboard.
- **Watch view** — merchant watch list and low-confidence merchant review queue.
- **Merchant registry** with trust tiers and buying-view inclusion thresholds.
- 60-merchant specialty roaster seed list at `SzimplaCoffee/brain/merchants/top-500-seed.md`.

## Backend Surface You Should Know

Important backend areas:

- `backend/src/szimplacoffee/main.py`: app startup, API mounting, legacy form compatibility endpoints, SPA serving.
- `backend/src/szimplacoffee/api/`: route modules grouped by domain.
- `backend/src/szimplacoffee/schemas/`: response models and API contracts.
- `backend/src/szimplacoffee/services/`: crawling, discovery, parser, recommendation scoring, scheduler logic.
- `backend/src/szimplacoffee/models.py`: the primary SQLAlchemy data model surface.

Current API groups:

- `dashboard`
- `merchants`
- `products`
- `recommendations`
- `discovery`
- `crawl`
- `history`

## Frontend Surface You Should Know

Important frontend areas:

- `frontend/src/routes/`: route entry points and page-level loaders.
- `frontend/src/hooks/`: shared TanStack Query data access hooks.
- `frontend/src/components/`: reusable UI and domain components.
- `frontend/src/api/`: typed client and generated schema from the backend OpenAPI surface.

Current SPA routes:

- `/` — dashboard
- `/merchants` — merchant list
- `/merchants/new` — add merchant
- `/merchants/$merchantId` — merchant detail
- `/products` — catalog with multi-select filters
- `/products/$productId` — product detail
- `/recommend` — recommendation console
- `/discovery` — discovery pipeline
- `/purchases` — purchase history + brew feedback
- `/today` — daily buying decision view *(new)*
- `/watch` — merchant watch list and review queue *(new)*

## Data Model Reality

The current primary model surface includes **18 SQLAlchemy models**:

- `Merchant`
- `MerchantCandidate`
- `MerchantSource`
- `MerchantQualityProfile`
- `MerchantPersonalProfile`
- `ShippingPolicy`
- `MerchantFieldPattern` *(per-field extraction patterns for crawlers)*
- `ProductMetadataOverride` *(manual metadata corrections)*
- `Product`
- `ProductVariant`
- `OfferSnapshot`
- `PromoSnapshot`
- `MerchantPromo`
- `VariantDealFact` *(historical biggest-sale records per variant)*
- `PurchaseHistory`
- `BrewFeedback`
- `CrawlRun`
- `RecommendationRun`

The most important data rule: offer, promo, and deal history are **append-only observed snapshots**. Never rewrite `OfferSnapshot`, `PromoSnapshot`, or `VariantDealFact` to represent current state.

## How To Think About Changes

- Prefer small, reviewable changes.
- Preserve existing architecture unless the ticket requires a structural change.
- Extend existing routes, hooks, schemas, and services before adding new abstractions.
- Keep backend contracts and frontend generated types in sync.
- Keep recommendation behavior explainable. Avoid silent ranking changes.
- Respect the product truth that quality beats lowest price.

## Workflow Reality

For non-trivial work, this repo expects local delivery bookkeeping:

- `.tickets/` for ticket state
- `.plans/` for execution plans
- `.memory/` for delivery memory
- `SzimplaCoffee/brain/` for worklog, backlog, decisions, and merchant intel

If work crosses behavior, planning, and memory boundaries, update all relevant artifacts.

## Commands That Matter

Backend:

```bash
cd backend && uvicorn szimplacoffee.main:app --reload
cd backend && pytest tests/
cd backend && ruff check src/ tests/
```

Frontend:

```bash
cd frontend && npm run dev
cd frontend && npx tsc -b
cd frontend && npm run build
```

Full stack:

```bash
./scripts/dev.sh
```

API type regeneration:

```bash
cd frontend && npm run gen:api
```

## Common Failure Modes

- Updating backend response shapes without regenerating or adapting frontend API types.
- Treating the frontend as a scaffold when it is already the primary UI.
- Missing the purchase and brew feedback surface when changing recommendations.
- Mutating historical snapshot tables (`OfferSnapshot`, `PromoSnapshot`, `VariantDealFact`) instead of appending new observations.
- Making ranking changes that ignore espresso style, bag size, subscription pricing, or inventory state.
- Forgetting that the repo has a formal ticket, plan, and memory workflow.
- Running `tsc -b` before `npm run build` — TanStack Router regenerates `routeTree.gen.ts` during Vite build, not standalone tsc.
- Assuming the scheduler is manual — it starts automatically on app startup. Don't add redundant trigger logic.
- Adding new crawl logic that bypasses the strategy layer order (feed → structured → DOM → agentic).
- Changing recommendation scoring without preserving the quality-first intent documented in `north-star.md`.

## Source Of Truth Order

Use this order when you need to resolve uncertainty:

1. `north-star.md` for product intent
2. `AGENTS.md` for repo workflow and conventions
3. Current code in `backend/src/szimplacoffee/` and `frontend/src/`
4. `README.md` for developer setup and broad product surface
5. `.tickets/`, `.plans/`, `.memory/`, and `SzimplaCoffee/brain/` for active delivery context
