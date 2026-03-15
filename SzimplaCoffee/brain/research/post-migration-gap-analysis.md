# Post-Migration Gap Analysis — Sprint 2 Planning

**Date:** 2026-03-14
**Context:** React migration (SC-10..29) complete. Assessing what blocks the north star.

---

## North Star Recap

> "If I want to order coffee right now, where should I buy from, what should I buy, and why?"

The recommendation must be: **personalized, espresso-aware, inventory-aware, quality-aware, deal-aware, explainable.**

---

## Current Data Reality (Hard Numbers)

| Metric | Value | Impact |
|---|---|---|
| Products | 910 | ✅ Good coverage |
| Products with `origin_text` | 59 (6.5%) | 🔴 **Critical** — origin matching is blind |
| Products with `process_text` | 43 (4.7%) | 🔴 **Critical** — `_espresso_fit()` scores on empty strings |
| Products with `tasting_notes_text` | 189 (20.8%) | 🟠 Moderate — flavor signals weak |
| Products marked `is_espresso_recommended` | 35 (3.8%) | 🟠 Rarely set by crawlers |
| Products marked `is_single_origin` | 102 (11.2%) | 🟠 Under-detected |
| Distinct offer snapshot dates | **1** | 🔴 **Critical** — no price history, no temporal trends |
| Merchants with quality profiles | 4 / 16 | 🔴 **Critical** — 75% of merchants have default 0.5 scores |
| Purchase history records | 3 | 🟡 Expected for v1, but feedback loop is thin |
| Brew feedback records | 3 | 🟡 Exists but no UI to add more |

---

## Gap Prioritization Against North Star

### Tier 1: Recommendation Engine Is Flying Blind 🔴

These gaps mean **the recommendation is currently unreliable**. The scoring functions operate on empty data, so recommendations are essentially random noise weighted by merchant defaults.

**Gap 1: Product metadata extraction missing (origin, process, tasting notes)**

The `_espresso_fit()` function scores on `product.process_text.lower()` and `product.tasting_notes_text.lower()`. With 95% of products having empty process text, this function returns the same baseline score for almost every product. The recommendation cannot differentiate a washed Ethiopian from a natural Brazilian — they all score 0.55.

Similarly, `_history_fit()` tries to match against liked origins and processes, but there's nothing to match against.

**Root cause:** The Shopify/WooCommerce crawlers grab price and availability but don't parse product descriptions for coffee-specific metadata. The data is *in the HTML* — it just never gets extracted.

**Gap 2: Only 4/16 merchants have quality profiles**

`_merchant_quality_score()` returns 0.5 for 12 of 16 merchants. This means merchant quality differentiation — the #1 signal for "should I trust this roaster" — is flat across 75% of the universe. The north star specifically says: "rank trusted merchants and proven roasters higher."

**Gap 3: Single-day snapshots = no price intelligence**

All 9,352 offer snapshots are from 2026-03-09. The system cannot detect price drops, sales patterns, or whether "now" is a good time to buy. The north star says the product "should be allowed to say wait" — but it has zero temporal data to make that call.

### Tier 2: Core Product Features Missing 🟠

**Gap 4: No crawl scheduling / automated re-crawl**

Without scheduled re-crawling, the data stays frozen at 2026-03-09. Even if we fix extraction, we need fresh data flowing in. The north star envisions "merchant discovery runs, catalog refreshes, promotion refreshes" running automatically.

**Gap 5: No brew feedback input UI**

The learning loop ("every coffee we buy should improve the system") requires users to record purchases and feedback. There are 3 seed records but no way to add more from the UI. The recommendation engine's `_preference_profile()` function works — it just starves for data.

**Gap 6: No purchase history viewer/editor**

Tied to Gap 5. Users need to log what they bought, rate it, and track their coffee inventory. This is the "inventory-aware" part of the north star.

### Tier 3: UX Polish for Usability 🟡

**Gap 7: Products page with search**

Users need to browse and search the catalog independent of merchant detail pages. Useful for answering "who sells [X origin] right now?"

**Gap 8: Toast notifications + loading states**

Crawl triggers, promotions, and mutations give no feedback. Users don't know if actions succeeded. Minor for recommendation quality but important for usability.

**Gap 9: Mobile responsive layout**

Single-user app but likely used on phone sometimes. Not blocking recommendations but blocking daily usage patterns.

### Tier 4: Engineering Quality / Nice-to-Have 🟢

**Gap 10: Bundle size (889KB)**
**Gap 11: Error boundaries**
**Gap 12: Frontend tests**
**Gap 13: Health check endpoint**
**Gap 14: Dark mode**

These matter for long-term quality but don't block the north star question.

---

## Critical Insight: The Recommendation Is Only As Good As Its Data

The current system has a well-designed scoring engine (`recommendations.py` is ~280 lines of thoughtful scoring logic) sitting on top of hollow data. Fixing the UI won't help. The priority is:

1. **Fill the product metadata** — make `_espresso_fit()` and `_history_fit()` actually work
2. **Fill merchant quality profiles** — make `_merchant_quality_score()` differentiate
3. **Get temporal data flowing** — scheduled re-crawls for price history
4. **Build the feedback loop** — brew feedback + purchase tracking UI

Only after these 4 are done does the recommendation answer become trustworthy.

---

## Proposed Ticket Batch: SC-30 through SC-42

### Data Quality (SC-30 → SC-33) — Must-do first

| ID | Title | Priority | Why |
|---|---|---|---|
| SC-30 | Coffee metadata parser — extract origin, process, tasting notes from product descriptions | P0 | Unlocks espresso_fit scoring |
| SC-31 | Wire metadata parser into crawl pipeline + backfill existing products | P0 | Actually populates the data |
| SC-32 | Merchant quality profile generator — auto-score all 16 merchants | P1 | Unlocks merchant differentiation |
| SC-33 | Crawl scheduler — cron-based re-crawl with configurable intervals per tier | P1 | Enables temporal data + freshness |

### Feedback Loop (SC-34 → SC-36)

| ID | Title | Priority | Why |
|---|---|---|---|
| SC-34 | Purchase history form — log coffee purchases from the UI | P1 | Enables learning loop |
| SC-35 | Brew feedback form — rate coffees and record espresso outcomes | P1 | Feeds _preference_profile() |
| SC-36 | Purchase history viewer — browse, edit, and delete past purchases | P2 | Manage the learning data |

### Catalog & Search (SC-37 → SC-38)

| ID | Title | Priority | Why |
|---|---|---|---|
| SC-37 | Standalone products page with filtering and search | P2 | Browse catalog by origin, process, merchant |
| SC-38 | Product detail page — full metadata, price history chart, variants | P2 | Deep-dive before buying |

### UX Foundation (SC-39 → SC-42)

| ID | Title | Priority | Why |
|---|---|---|---|
| SC-39 | Toast notification system for async operations | P2 | Feedback for crawls, saves, mutations |
| SC-40 | Responsive mobile layout for key pages | P2 | Use on phone while ordering |
| SC-41 | Error boundaries + global error handling | P3 | Graceful degradation |
| SC-42 | Code-splitting with dynamic imports for route-level chunks | P3 | Bundle size from 889KB → target <300KB initial |

---

## Execution Order Recommendation

```
Sprint 2a (Data Foundation):  SC-30 → SC-31 → SC-32 → SC-33
Sprint 2b (Feedback Loop):    SC-34 → SC-35 → SC-36
Sprint 2c (Catalog + Polish): SC-37 → SC-38 → SC-39 → SC-40
Sprint 2d (Engineering):      SC-41 → SC-42
```

After Sprint 2a, re-run the recommendation engine and validate that results actually differentiate coffees meaningfully. That's the acid test.

---

## Decision Record

**DR-005: Data quality over UI polish**

We chose to prioritize product metadata extraction and merchant quality profiles over UI features (products page, mobile layout, dark mode) because the recommendation engine's scoring functions operate on data that is 93-95% empty. No amount of UI polish makes a recommendation trustworthy when the underlying scores are noise. The north star is "confident coffee recommendations" — confidence requires data.
