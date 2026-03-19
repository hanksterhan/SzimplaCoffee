# Discovery Completion Packet — SzimplaCoffee Phase 2 (Post SC-95)
_Generated: 2026-03-19T21:11:00Z by autopilot brainstorm refresh_

---

## Problem Statement

SzimplaCoffee has completed three foundational Phase 2 tickets (SC-93/94/95) and now has:
- **16 active merchants**, 918 products, 3,700 variant deal facts
- **Canonical normalized metadata** (origin_country, process_family, roast_level) with confidence and provenance fields on all products
- **Crawl quality signals** per merchant (crawl_quality_score, reliability signals in schedule API)
- **Serialized crawl execution** (1 merchant per 15-min APScheduler tick)
- **Stable autopilot startup** (startup-time noise eliminated in SC-93)

The remaining Phase 2 gap is: **catalog filtering, search, and availability semantics do not yet use normalized metadata truth**. The frontend still shows raw `origin_text` / `roast_cues` / `process_text` in product cards instead of canonical normalized values. The "In stock" / "Unavailable" label in the catalog list uses `is_active` (a presence flag) rather than variant-level `is_available` truth. Filtering and search work at the backend level, but the frontend metadata display and availability messaging are disconnected from the normalized fields SC-94 added.

Specific gaps:
1. **Frontend product card metadata**: `products.lazy.tsx` shows `origin_text`, `process_text`, `roast_cues` (raw free-text) instead of `origin_country`, `process_family`, `roast_level` (normalized canonical).
2. **Availability messaging**: catalog list uses `product.is_active` for "● In stock" / "● Unavailable", but `is_active` means "seen in the last crawl", not "has a purchaseable variant with a current offer". This misleads the user.
3. **Tag generation for product quick-view** (`buildTags`) uses raw text fields exclusively — it should prefer normalized fields with fallback to raw.
4. **Backend filter surface** already uses normalized fields correctly (origin_country, process_family, roast_level parameters in `/products/catalog` and `/products/search`). The back-end side of SC-96 may be smaller than planned.
5. **"unknown" metadata values**: roast_level=unknown (277 products, 30%) and process_family=unknown (458 products, 50%) are currently surfaced in filter dropdowns as valid options — they should be treated as null/absent for UX purposes, not as a filter choice.

---

## Consensus Solution

SC-96 is the right next task and it's unblocked. Scope is narrower than originally planned because the backend filtering already works correctly. Focus SC-96 on:

1. **Align frontend display to normalized fields** — prefer `origin_country`/`process_family`/`roast_level` with fallback to raw text in product cards and quick-view tags.
2. **Fix catalog availability messaging** — use backend `has_stock` (which reflects variant-level `is_available + latest_offer.is_available`) instead of `product.is_active` for "In stock" / "Unavailable" copy.
3. **Suppress "unknown" as a filter option** — when the backend returns `unknown` for roast or process, treat it as absent in the UI (do not show it as a filter button or tag).
4. **No backend changes needed** for basic filter semantics — the heavy backend query work is already correct. Minor: verify the catalog endpoint `in_stock` filter uses `has_stock` correctly (it does per code review).

After SC-96, the Phase 2 success criteria are substantially met:
- ✅ Autopilot stable (SC-93)
- ✅ Canonical metadata normalization with confidence/provenance (SC-94)
- ✅ Crawl quality observable, serialized execution (SC-95)
- ✅ SC-96: Catalog semantics aligned with normalized metadata
- ⬜ Metadata coverage and trust: origin=63%, roast/process coverage limited by "unknown" (needs observation; improving via better backfill patterns is Phase 2 extended or Phase 3)
- ✅ Backend tests pass (249 passing)

The remaining gap — improving "unknown" fill rates — depends on richer crawl data and better parser patterns. That is a Phase 2 extended or Phase 3 concern and should be captured as a future ticket, not blocker to SC-96.

---

## Task Candidates

Current open tickets: only **SC-96** is open. After SC-96 delivers, backlog refill is needed.

| # | Ticket | Title | Priority | Status | Notes |
|---|--------|-------|----------|--------|-------|
| 1 | SC-96 | Catalog filtering and search semantics | p2 | ready | Next task — smaller scope than planned |

**Post-SC-96 refill candidates (Phase 2 extended / Phase 3 preview):**

| # | Candidate | Title | Priority | Rationale |
|---|-----------|-------|----------|-----------|
| A | SC-97 | Improve metadata fill rate for "unknown" roast and process | p2 | 30–50% unknown values hurt filter UX; parser pattern improvement |
| B | SC-98 | Historical deal baseline per variant | p1 | Required for trustworthy sale-score in Phase 3 Today view |
| C | SC-99 | Server-side product sort: quality-first, freshness-aware | p2 | Corpus-wide sort instead of client-window sort |
| D | SC-100 | Metadata fill rate dashboard widget | p2 | Visibility into normalization coverage over time |
| E | SC-101 | Expand merchant set: verify + import 10 more from seed | p2 | Coverage drives catalog depth; now that crawl is serialized, safe to add |
| F | SC-102 | Today view deal-score with historical baseline | p1 | Phase 3 core — needs SC-98 first |
| G | SC-103 | Brew feedback influence on recommendation scoring | p2 | Phase 2d learning loop (3 brew sessions already logged) |

---

## Acceptance Criteria

Phase 2 completion criteria (from `goal.yaml`):

- [x] Autopilot can start and complete a normal cycle without startup-noise failures
- [x] Coffee metadata normalization: canonical `origin_country`, `roast_level`, `process_family` with confidence/provenance on active products
- [ ] Metadata coverage and trust improve enough that origin/roast filtering is product-trustworthy (blocked by "unknown" fill rate; partially met at 63% origin, 70%+ roast recognized)
- [x] Crawl quality observable per merchant (crawl_quality_score, reliability signals)
- [x] Serialized low-CPU crawl execution (1 merchant per tick)
- [ ] Next backlog refilled with metadata/crawl-focused tickets and ≥2 ready tasks (backlog refill needed after SC-96)
- [x] Backend tests pass and touched contracts remain green

---

## Risks and Open Questions

### Risk 1 — "unknown" values in filter UI (MEDIUM)
roast_level=unknown (277/918) and process_family=unknown (458/918) will appear in filter dropdowns. Should be suppressed in the UI to avoid confusing the user with a meaningless filter option.

### Risk 2 — Metadata coverage plateau (LOW-MEDIUM)
63% origin_country, 70% roast recognized — further improvement needs richer crawl text (descriptions stored, not just names). This is a Phase 2 extended concern, not a blocker for SC-96.

### Risk 3 — Backlog low after SC-96 (HIGH)
Only 1 ready ticket exists now. After SC-96 delivers, the next run must trigger backlog refill (count drops to 0 < min_ready_tasks=2). Candidates A–G above provide strong material for the next create-tickets run.

### Open Questions
- Should `roast_level=unknown` and `process_family=unknown` be filtered out from the canonical display as "no data" or kept as a debug signal? (Recommend: treat as null for UX, keep in DB.)
- Is Phase 2 goal considered "satisfied" once SC-96 ships, or does metadata fill rate need to cross a higher threshold first? (Recommend: ship SC-96, declare Phase 2 done, enter Phase 3 with SC-97/SC-98 as first tickets.)

---

## Routing Notes

- **Next autopilot action:** deliver SC-96 (it is the only unblocked ready task)
- **SC-96 scope refinement:** Focus on frontend semantics alignment; backend filter queries are already correct. This makes SC-96 lighter than the original plan estimated.
- **After SC-96:** Trigger brainstorm or direct create-tickets for Phase 3 preview candidates (SC-97 through SC-103), with SC-98 (historical deal baselines) as the highest-leverage Phase 3 unlocker.
- **Escalation watch:** None currently — no ambiguity blockers or dependency gaps.

_Phase 2 foundation status: 4 of 4 core tickets done or in flight. Phase 3 can start after SC-96._
