# SC-30 through SC-42 — Sprint 2 Complete

**Date:** 2026-03-14
**Status:** All 13 tickets delivered and merged

## Sprint 2a — Data Foundation
- SC-30: Coffee metadata parser (origin, process, variety, roast, tasting notes)
- SC-31: Wired into crawl pipeline + backfilled 596/910 products (origin: 509, process: 87, variety: 84)
- SC-32: Auto-generated quality profiles for all 16 merchants
- SC-33: Crawl scheduler (A=6h, B=24h, C=7d) with dashboard banner

## Sprint 2b — Feedback Loop
- SC-34: Purchase history CRUD + logging form
- SC-35: Brew feedback form (shot style, rating, difficulty, rebuy)
- SC-36: Purchase history viewer with stats + inline feedback

## Sprint 2c — Catalog + Polish
- SC-37: Products page with debounced search + card grid
- SC-38: Product detail with variants, "best value" highlight, price chart
- SC-39: Toast notifications (Sonner) on all mutations
- SC-40: Responsive mobile layout (collapsible sidebar, horizontal scroll tables)

## Sprint 2d — Engineering
- SC-41: Error boundaries (React + TanStack Query)
- SC-42: Code-splitting — 889KB → 249KB (72% reduction!)

## Stats
- 33 total commits on main
- 64 frontend TypeScript files
- 32 backend Python files
- Bundle: 249KB initial (gzipped ~75KB)
- Ruff clean, TypeScript clean
