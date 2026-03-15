# SC-10 through SC-29 — React Migration Sprint

**Date:** 2026-03-14
**Duration:** ~2 hours of agent delivery time
**Status:** All 20 tickets delivered and merged

## What Was Built

### Phase 0 — API Foundation (SC-10..17)
- Monorepo restructure: `backend/` + `frontend/` + `data/` + `scripts/`
- 17 Pydantic v2 response schemas with computed fields
- 28 API endpoints across 5 routers (merchants, products, recommendations, discovery, dashboard)
- OpenAPI spec → TypeScript client generation pipeline

### Phase 1 — React Scaffold (SC-18..20)
- Vite + React 19 + TypeScript + TanStack Router + TanStack Query
- shadcn/ui with coffee design tokens (espresso brown, latte foam, cream)
- App shell: sidebar nav, topbar, ⌘K command palette (cmdk)

### Phase 2 — Core Pages (SC-21..24)
- Dashboard: 6 metrics cards + merchant overview table
- Merchant list: filterable by platform/trust with bookmarkable URL params
- Merchant detail: tabbed Products/Crawl Runs/Promos with quality scores
- Add merchant: URL input with platform auto-detection

### Phase 3 — Recommendations & Discovery (SC-25..26)
- Recommendation console: shot style + bag size selectors, scored result cards
- Discovery pipeline: candidate review with promote/reject flow

### Phase 4 — Polish & Cleanup (SC-27..29)
- Recharts price history charts with coffee palette + sale dot markers
- Removed all Jinja templates and HTML routes
- Production build: FastAPI serves React static, single port

## Build Stats
- Frontend: 889KB JS (270KB gzipped), 36KB CSS
- Backend: ruff clean, all schemas typed
- TypeScript: clean, no errors

## Known Issues / Gaps
- Bundle is 889KB — should code-split with dynamic imports
- Product note parsing still not wired (origin/process/tasting mostly empty)
- Only 1 day of offer snapshot data — need recurring crawls for price trends
- Quality profiles only exist for 4 of 16 merchants
- Purchase history has only 3 seed records
- No error boundary components
- No toast notifications for mutations (crawl trigger, promote, etc.)
- No responsive/mobile layout
- No dark mode
