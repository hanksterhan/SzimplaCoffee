# 002 — React Migration Tech Stack

**Date:** 2026-03-14
**Status:** accepted

## Context

SzimplaCoffee v1 was built with Python/FastAPI/Jinja2/HTMX. While functional, the frontend is basic — no interactivity beyond HTMX partials, no client-side state management, no responsive design. The owner wants a modern, visually appealing React frontend while preserving the working Python backend.

## Data Reality (from actual SQLite DB, 2026-03-14)

- 16 merchants (14 Shopify, 1 WooCommerce, 1 agentic catalog)
- 910 products, 3207 variants, 9352 offer snapshots
- 37 merchant promos, 321 shipping policies
- Offer prices: $0–$1,732.80, avg $80
- Weight distribution: 340g (12oz) and 2268g (5lb) most common
- Product note parsing not yet wired in (origin/process/tasting mostly empty)
- Only 2 trusted merchants (Olympia, Camber), rest are candidates
- All offer data from single crawl day (2026-03-09)

## Options Considered

### Frontend
1. **Next.js** — SSR/SSG overkill for local-first personal tool. Two-server problem.
2. **Vite + React SPA + TanStack Router** — simplest, zero SSR overhead, type-safe routing. ✅
3. **Remix** — SSR-oriented, same two-server problem as Next.js.

### State Management
1. **Redux Toolkit** — too heavy for this scope.
2. **TanStack Query + component state** — almost all state is server state. Perfect fit. ✅
3. **Zustand** — reserve for later if prop-drilling becomes painful.

### UI Library
1. **MUI** — heavy, enterprise aesthetic.
2. **shadcn/ui + Tailwind CSS v4** — own the components, gorgeous defaults, coffee-warm theme. ✅
3. **Mantine** — good but opinionated styling conflicts.

### Backend
1. **Rewrite in Rust/Hono/tRPC** — months of work, lose Python crawlers.
2. **Keep FastAPI, add JSON API routes** — zero rewrite of working code. ✅

### Type Safety
1. **tRPC** — requires same runtime on both sides.
2. **openapi-typescript + openapi-fetch** — generates TS types from FastAPI's OpenAPI spec. ✅

## Decision

**Frontend:** Vite + React + TanStack Router + TanStack Query
**UI:** shadcn/ui + Tailwind CSS v4 + Recharts
**Backend:** Keep FastAPI with new `/api/v1/` JSON routes + Pydantic schemas
**Data:** Keep SQLAlchemy + SQLite
**Type Safety:** openapi-typescript + openapi-fetch

Monorepo structure: `backend/` (Python) + `frontend/` (React SPA)

## Consequences

**Gains:**
- Modern, responsive, visually appealing UI
- Client-side state management with caching and optimistic updates
- Type-safe API boundary without tRPC coupling
- All Python backend code preserved (crawlers, models, recommendations)
- Single-port deployment in production (FastAPI serves built React)

**Costs:**
- Two dev servers during development (Vite :5173, FastAPI :8000)
- Need to build Pydantic response schemas for all 15 models
- Frontend build step required for production
- Larger dependency footprint (node_modules)

**Risks:**
- OpenAPI type generation may need manual tweaks for complex nested models
- Vite proxy config needs to handle WebSocket if we add real-time later
