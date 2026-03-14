# SC-2 — Reduce Promo False Positives — Execution Plan

## Summary

Introduce a promo confidence scoring module that evaluates extracted promo text against heuristic patterns (discount codes, percent/dollar-off patterns, explicit promo keywords). Low-confidence promos are stored but excluded from recommendation scoring. Test coverage uses real fixtures from known merchants.

---

## Slices

### S1 — Add promo confidence heuristics to crawler extraction layer

**Goal:** A standalone `promo_confidence.py` module scores promo candidates before they are stored.

**Files to create:**
- `src/szimplacoffee/services/promo_confidence.py`
- `tests/test_promo_confidence.py`

**Files to modify:**
- `src/szimplacoffee/services/crawlers.py` (call confidence scorer before writing promo_snapshot)

**Implementation notes:**

1. `promo_confidence.py` — implement `score_promo(title: str, details: str, code: str | None) -> float`:

   **Positive signals (add to score):**
   - Discount code present: +0.4
   - Percent-off pattern (`\d+%\s*off`): +0.3
   - Dollar-off pattern (`\$\d+\s*off`): +0.3
   - Explicit keywords: `sale`, `promo`, `discount`, `deal`, `limited time`, `flash`: +0.2 each, max +0.3
   - Free shipping threshold mention: +0.1

   **Negative signals (subtract from score):**
   - Generic shipping notice (`free shipping on orders`, `we ship`): -0.5
   - Newsletter signup text: -0.6
   - General site banner without price signal: -0.3
   - Confidence floor: 0.0, ceiling: 1.0

2. In `crawlers.py`, before writing to `promo_snapshots`:
   - Call `score_promo(title, details, code)` and store result in `confidence` field
   - Do not suppress storage — store all, but include confidence score

3. Test fixtures (in `test_promo_confidence.py`):

   **Known false positives (should score < 0.4):**
   - "Free shipping on orders over $50" → ~0.1
   - "Sign up for our newsletter for updates" → ~0.0
   - "New arrivals every week" → ~0.0

   **Known true positives (should score ≥ 0.4):**
   - "20% off sitewide — use code SPRING20" → ~0.9
   - "Flash sale: $5 off any 12oz bag" → ~0.7
   - "Buy 2 get 1 free — this weekend only" → ~0.5

**Checks:**
```bash
ruff check src/ tests/
pytest tests/test_promo_confidence.py -v
```

---

### S2 — Wire confidence threshold into recommendation scoring

**Goal:** The `deal_score` calculation ignores promo_snapshots with confidence < 0.4.

**Files to modify:**
- `src/szimplacoffee/services/recommendations.py`
- `tests/test_recommendations.py`

**Implementation notes:**

1. In `recommendations.py`, when computing `deal_score` for a merchant:
   - Filter `promo_snapshots` to only those where `confidence >= 0.4`
   - If no qualifying promos, `deal_score` contribution from promos = 0
   - Document the threshold constant: `PROMO_CONFIDENCE_THRESHOLD = 0.4`

2. Update existing recommendation tests to:
   - Confirm a merchant with only low-confidence promos doesn't get inflated deal_score
   - Confirm a merchant with a high-confidence promo gets appropriate deal_score boost

**Checks:**
```bash
ruff check src/ tests/
pytest tests/test_recommendations.py -v
```

---

## Verification Steps

```bash
ruff check src/ tests/
pytest tests/ -v
```

Manual check:
1. Run a crawl on a merchant known to have shipping-only banners
2. Confirm promo_snapshots are written with low confidence scores
3. Confirm that merchant does not appear in recommendations with inflated deal_score

---

## Notes

- `PROMO_CONFIDENCE_THRESHOLD = 0.4` should be a named constant, not a magic number.
- Consider exposing confidence in the merchant detail promo section in a future ticket.
- Do not retroactively update historical snapshots — apply only to new crawl runs.
