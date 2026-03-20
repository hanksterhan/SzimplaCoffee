# Discovery Completion Packet — SzimplaCoffee Phase 3 (Post SC-109)
_Generated: 2026-03-20T11:34:00Z by autopilot brainstorm refresh_

---

## Problem Statement

SzimplaCoffee has completed Phase 2 fully and delivered Phase 3 foundations ahead of
schedule. The current state is:

**What exists:**
- **36 active merchants** (33 Tier A, 3 Tier C), **1,613 active products**, **5,765 available variants**
- **8,878 price baselines** and **deal facts** covering all variants
- **Canonical metadata normalization**: origin_country, roast_level, process_family
  with confidence/provenance on all products
- **Deal-aware Today view**: baseline deal_score, deal_badge, and blended quality+deal
  ranking (0.7 quality + 0.3 deal)
- **Quality-first catalog sort** (SC-108): corpus-wide `/products/catalog` endpoint
  with quality, freshness, and alphabetical sort modes
- **Brew feedback boost** (SC-103/SC-109): well-rated products boosted in recommendations
- **Crawl quality signals** observable per merchant, serialized execution
- **333 backend tests passing**, frontend build/tsc clean

**Phase 3 success criteria from goal.yaml — evaluated:**
- ✅ Historical offer baselines support trustworthy sale/deal scoring
- ✅ Today view ranks quality-clearing deals from trusted merchants
- ✅ Product search and sorting are server-side and corpus-wide
- ✅ Merchant expansion has continued (16 → 36 active merchants)

Phase 3 is now functionally complete. The bottleneck for the next phase is:

1. **Origin coverage is still weak** — 56% origin_country known on active products.
   SC-104 stored `description_text` for all products, but a description-based backfill
   re-pass has not yet been run to extract origin from those richer descriptions.
2. **Merchant catalog depth** — 36 merchants covers anchor roasters well, but the seed
   list has ~14 more high-quality Tier A/B candidates not yet imported. Broader coverage
   = better daily deal discovery.
3. **Today view explainability** — recommendations show deal_badge and quality score
   but lack a human-readable "why this coffee" narrative. The north star asks for an
   explainable recommendation.
4. **Purchase history intelligence** — 10 purchases logged but no analysis surface:
   no "time since last order," no "roasters I haven't tried lately," no value-per-gram
   tracking.
5. **Espresso profile-awareness is incomplete** — the user has a DE1 with 58mm and 49mm
   baskets. Basket-type preference is not yet factored into ranking. `is_espresso_recommended`
   is a product flag but shot_style preference is not a first-class input.

---

## Consensus Solution

The next batch of tickets (SC-110 through SC-116) should focus on:

1. **Description-based metadata backfill re-pass** (SC-110): re-run the metadata parser
   over all products that have `description_text != NULL` but still have weak/missing
   origin, roast, or process fields. This should be a single CLI command + verification
   of fill rate improvement. Expected origin gain: 56% → 70%+.

2. **Merchant expansion batch 3** (SC-111): import the next 10–12 highest-priority
   merchants from the seed list that haven't been added yet. Anchor targets: Olympia
   Coffee, Camber Coffee, Ritual Coffee Roasters, Broadsheet Coffee, Bird Rock Coffee,
   Equator Coffees, Greater Goods Coffee, Temple Coffee, Huckleberry Roasters, Methodical
   Coffee. Use serial `add-merchant` CLI. Do not overload CPU.

3. **Recommendation explainability: "why" narrative** (SC-112): add a brief `why_text`
   field to the top recommendation and runner-ups in the Today view. Should explain in
   1–2 sentences why this coffee ranks first: e.g., "Ethiopian washed natural at 15%
   below its 30-day baseline from a Tier A roaster with 3 positive brew sessions."
   Backend: populate `why_text` in recommendation scoring. Frontend: render below the
   coffee name in TopPickCard.

4. **Purchase history intelligence panel** (SC-113): add a small "My buying patterns"
   section to the Today or Purchases page: days since last order, top 3 roasters by
   purchase count, estimated weekly coffee consumption from purchase gaps. Backend:
   compute from existing `purchase_history` rows. Frontend: simple stats card.

5. **Variant availability freshness signal** (SC-114): surface "last seen" date on
   variants in product detail and catalog. If a variant hasn't been seen in >30 days,
   mark it visually as "stale" rather than "available." This improves trust in the
   catalog's current accuracy without requiring a crawl trigger.

6. **Espresso profile: shot-style ranking preference** (SC-115): add `shot_style`
   parameter to recommendation requests (values: `modern_58mm` | `lever_49mm` | `any`).
   When set, boost products with matching `is_espresso_recommended` affinity for the
   basket type. Requires no new data — just a routing signal in recommendation scoring
   and a UI selector in the Today view request form.

7. **Merchant expansion batch 4** (SC-116): import the remaining 10 Tier B candidates
   from the seed list once batch 3 stabilizes. Depends on SC-111 completing cleanly.

---

## Task Candidates

| # | Ticket | Title | Priority | Unblocked | Notes |
|---|--------|-------|----------|-----------|-------|
| 1 | SC-110 | Description-based metadata backfill re-pass | p1 | ✅ | Origin 56%→70%+; SC-104 stored descriptions, just needs re-run |
| 2 | SC-111 | Merchant expansion batch 3 (10 roasters) | p1 | ✅ | Serial crawl, ~10 new merchants from seed |
| 3 | SC-112 | Recommendation explainability: why_text narrative | p2 | ✅ | Backend scoring + frontend TopPickCard |
| 4 | SC-113 | Purchase history intelligence panel | p2 | ✅ | Dashboard/Purchases stats card |
| 5 | SC-114 | Variant availability freshness signal | p2 | ✅ | last_seen display + stale badge |
| 6 | SC-115 | Espresso profile: shot-style ranking preference | p2 | ✅ | shot_style param in recs API + Today UI |
| 7 | SC-116 | Merchant expansion batch 4 | p3 | Depends on SC-111 | Next 10 Tier B seed candidates |

---

## Acceptance Criteria

Phase 3+ success criteria (extending goal.yaml):

- [ ] Origin coverage ≥ 70% on active coffee products (up from 56%)
- [ ] Merchant count ≥ 46 active merchants with products
- [ ] Today view top recommendation includes human-readable `why_text` narrative
- [ ] Purchase history surface shows days-since-last-order and top roasters
- [ ] Variant last-seen date visible in product detail and catalog
- [ ] Shot-style preference influences recommendation ranking when specified
- [ ] Backend tests continue passing (333+)
- [ ] Ruff + frontend build + tsc remain clean

---

## Risks and Open Questions

### Risk 1 — Description backfill quality plateau (MEDIUM)
Even with stored description_text, some products have terse descriptions with no origin
signal. The fill rate gain may be less than expected. Target is 70%+ but may land at
65–68%. Accept the gain and move on; do not try to force-fill with low-confidence guesses.

### Risk 2 — Merchant expansion crawl failures (LOW-MEDIUM)
Some seed candidates may have bot-protection or non-Shopify platforms that yield 0 products.
Use the same pattern as SC-101/SC-105: import all 10, report success/failure counts, don't
block the ticket on stragglers.

### Risk 3 — why_text generation scope (LOW)
Generating natural-language narrative from scored fields is scope-bounded: keep it template-
based (not LLM-generated) for predictability. A set of ~8 template fragments composed from
deal_badge, quality_tier, brew_feedback_count, and process/origin fields is sufficient.

### Risk 4 — shot_style preference model depth (LOW)
SC-115 should be simple: a routing parameter, not a new ML feature. Just boost or filter
by `is_espresso_recommended=True` for espresso requests and add the shot_style hint.
Do not introduce a new scoring sub-model in this ticket.

### Open Questions
- Should the description backfill re-pass (SC-110) run via CLI or via a migration? (Recommend CLI, same pattern as `szimpla backfill-metadata`.)
- Should `why_text` be persisted to `recommendation_runs` or computed on-the-fly? (Recommend on-the-fly in the API response for now, no schema change needed.)
- Is SC-116 worth planning now or should it wait for SC-111 crawl quality review? (Recommend: create the ticket but mark `depends_on: SC-111`.)

---

## Routing Notes

- **Next autopilot action:** create-tickets (SC-110 through SC-116) using this packet
- **First delivery target:** SC-110 (description backfill re-pass) — highest leverage,
  lowest risk, standalone CLI ticket
- **Second delivery target:** SC-111 (merchant expansion batch 3) — broadens deal discovery
- **Third target:** SC-112 (why_text) — highest UX value for the north star question
- **Escalation watch:** None — no ambiguity blockers or credential dependencies
- **Phase 4 seed:** Espresso profile depth (DE1 shot profiles, dial-in history),
  wallet/credit tracking, cloud sync readiness

_Phase 3 complete. Phase 4 preview: personal espresso intelligence layer._
