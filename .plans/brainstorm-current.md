# Discovery Completion Packet — SzimplaCoffee Sprint 2
_Generated: 2026-03-18T04:46:00Z by autopilot brainstorm refresh_

---

## Problem Statement

SzimplaCoffee has a sophisticated recommendation engine, crawl infrastructure, and React SPA — but it is **data-starved**. The core loop (crawl → parse metadata → recommend → buy → feedback) has never run end-to-end with real data. Specific blockers:

1. **Merchant coverage is critically thin** — only 2 merchants, ~38 products. 15+ merchants are needed for meaningful recommendations.
2. **Coffee metadata is 93–95% empty** — origin, process, roast_level, and variety are missing on almost all products. The coffee_parser may not be wired into the post-crawl flow.
3. **Recommendation engine returns empty/wait** — even when products exist, the candidate pipeline filters everything out. VariantDealFact rows may be missing or threshold logic is too strict.
4. **The learning loop is untested** — purchase logging and brew feedback forms have never been exercised with real data, so the feedback → re-ranking path is dead.
5. **Watch queue UX is passive** — merchants appear in the review queue but trust tier promotion/demotion requires manual DB edits.

---

## Consensus Solution

Execute Sprint 2 in four ordered phases that unblock each other:

### Phase 2a — Data Foundation (merchant coverage + crawl pipeline)
Import ≥15 merchants from `SzimplaCoffee/brain/merchants/top-500-seed.md`, run crawls, verify product ingestion. Build a bulk-import CLI to make this repeatable. Promote high-quality crawled merchants to Tier A.

### Phase 2b — Metadata Pipeline (coffee_parser + fill rate)
Audit coffee_parser wiring into the post-crawl scheduler. Improve origin, process, and roast level regex patterns. Run backfill. Target ≥50% origin fill rate and ≥70% process/roast fill rate. Add fill-rate metrics to the dashboard.

### Phase 2c — Recommendation Engine (diagnosis + fix + enhancements)
Trigger a real recommendation run and trace the exact filter/scoring step that eliminates all candidates. Fix it. Ensure VariantDealFact rows are created post-crawl. Optionally add explain mode for future debugging.

### Phase 2d — Learning Loop (purchase + feedback + UI)
Log 5 real purchases and 3 real brew sessions. Link purchases to recommendation runs. Wire brew ratings into scoring penalty. Add crawl health visibility and trust promotion to the Watch page.

---

## Task Candidates

Ordered by priority (p1 before p2, dependency-unlocking before leaf tasks):

| # | Ticket | Title | Priority | Phase | Unblocks |
|---|--------|-------|----------|-------|---------|
| 1 | SC-59 | Bulk merchant import CLI | p2 | 2a | SC-57, SC-58 |
| 2 | SC-57 | Bulk-import 15 merchants from seed | p1 | 2a | SC-58, SC-60, SC-65 |
| 3 | SC-58 | Run crawls on all imported merchants | p1 | 2a | SC-60, SC-61, SC-65, SC-68 |
| 4 | SC-61 | Audit coffee_parser wiring + fill rate | p1 | 2b | SC-62, SC-63 |
| 5 | SC-62 | Improve origin extraction patterns | p1 | 2b | SC-64 |
| 6 | SC-63 | Improve process + roast level patterns | p1 | 2b | SC-64 |
| 7 | SC-68 | Ensure VariantDealFact rows post-crawl | p1 | 2c | SC-65, SC-66 |
| 8 | SC-65 | Diagnose empty recommendation | p1 | 2c | SC-66 |
| 9 | SC-66 | Fix recommendation engine returns empty | p1 | 2c | SC-67, SC-72 |
| 10 | SC-60 | Review and promote merchants by quality | p2 | 2a | — |
| 11 | SC-64 | Dashboard metadata fill-rate metrics | p2 | 2b | — |
| 12 | SC-67 | Recommendation explain mode | p2 | 2c | — |
| 13 | SC-69 | Log 5 real purchases via UI | p2 | 2d | SC-70 |
| 14 | SC-70 | Purchase-to-recommendation linkage | p2 | 2d | — |
| 15 | SC-71 | Log 3 brew sessions | p2 | 2d | SC-72 |
| 16 | SC-72 | Wire brew ratings into scoring | p2 | 2d | — |
| 17 | SC-73 | Watch page trust promotion UI | p2 | 2d | — |
| 18 | SC-74 | Watch page crawl health visibility | p2 | 2d | — |

**Note:** SC-59 (bulk import CLI) is p2 but unlocks SC-57 (p1) with less manual friction. Deliver SC-59 first if a coding task is selected, or proceed directly with SC-57 manual import if SC-59 adds too much scope.

---

## Acceptance Criteria

Success criteria from `autopilot/goal.yaml` — all must be satisfied before goal is complete:

- [ ] 15+ real specialty coffee merchants crawled and in the DB at Tier A or B
- [ ] Coffee metadata (origin, process, roast_level, variety) populated on ≥70% of products
- [ ] Recommendation engine produces meaningful results (not empty/wait) for a real request
- [ ] "Today" view returns a ranked recommendation on every use
- [ ] Purchase history has ≥10 real logged purchases
- [ ] Brew feedback loop exercised (at least 3 real sessions logged)
- [ ] All app UI interactions work correctly (dropdowns, filters, forms)
- [ ] Backend tests pass (≥84 tests green)

---

## Risks and Open Questions

### Risk 1 — Merchant URL validity (HIGH)
`top-500-seed.md` URLs have never been verified. Some may be 404, redirected, or non-coffee merchants. SC-57 must HTTP-verify before import.

### Risk 2 — Crawl adapter coverage (MEDIUM)
New merchants may use Shopify, WooCommerce, or custom platforms. The adapter auto-detection may fail for unknown platforms. SC-58 explicitly expects some crawl failures — these should be logged but not block the batch.

### Risk 3 — coffee_parser may be unwired (HIGH)
The 93–95% empty metadata suggests the parser is not called post-crawl or its patterns are too narrow. SC-61 is the diagnostic step. If unwired, fixing the scheduler hook is a small change; if patterns are simply weak, SC-62/SC-63 cover that.

### Risk 4 — VariantDealFact as recommendation blocker (HIGH)
If the recommendation engine hard-requires VariantDealFact rows and none exist, recommendations will always return empty regardless of product count. SC-68 must be delivered before SC-65/SC-66 can be meaningfully tested.

### Risk 5 — UI forms untested (LOW)
PurchaseForm and BrewFeedbackForm have never been exercised. Form submission errors are possible. SC-69 and SC-71 include bug-fix scope.

### Open Questions
- Does `szimpla add-merchant` block on crawl or just register and queue? (Inspect CLI behavior in SC-57)
- What is the current VariantDealFact row count? (Query in SC-68)
- Does the recommendation API accept an inventory payload via the UI Today view, or only via direct API call? (Check in SC-65)

---

## Routing Notes

- **Next autopilot action:** deliver
- **First task:** SC-59 (bulk import CLI) — coding task, well-scoped, unblocks SC-57
  - _Alternative:_ SC-61 (coffee_parser audit) if merchant import is considered human-gated (requires reviewing seed list URLs)
- **Escalation triggers to watch:**
  - SC-57 if URL verification fails for all candidates → human needs to curate the seed list
  - SC-68 if VariantDealFact computation is a complex algorithm rewrite → escalate
  - SC-65/SC-66 if recommendation fix requires schema changes → review with human

_Dependency chain for fastest path to first meaningful recommendation:_
`SC-59 → SC-57 → SC-58 → SC-68 → SC-61 → SC-62 → SC-65 → SC-66`
