# SC-32 Execution Plan: Merchant Quality Profile Generator

## Overview
Auto-generate quality profiles for all merchants based on observable data signals.

## Execution

### S1: Quality scorer service (2 hours)
**Create:** `backend/src/szimplacoffee/services/quality_scorer.py`

**Scoring signals (all 0.0-1.0):**

1. **freshness_transparency_score:**
   - % of product descriptions mentioning "roast date", "roasted to order", "roasted on", "fresh roasted"
   - Presence of roast date on product pages
   - Score: 0.3 (no signals) to 1.0 (clear freshness policy)

2. **shipping_clarity_score:**
   - Has ShippingPolicy record? +0.3
   - Has free_shipping_threshold? +0.2
   - Multiple shipping options? +0.2
   - Score based on policy completeness

3. **metadata_quality_score:**
   - % of products with non-empty origin_text
   - % with process_text
   - % with tasting_notes_text
   - Weighted average → score

4. **espresso_relevance_score:**
   - % of products with is_espresso_recommended = true
   - % of descriptions mentioning "espresso"
   - Presence of espresso-specific products

5. **service_confidence_score:**
   - Product count (more = higher, diminishing returns)
   - Crawl success rate (successful runs / total runs)
   - Data consistency (few errors)

6. **overall_quality_score:**
   - Weighted: freshness(0.25) + shipping(0.15) + metadata(0.25) + espresso(0.20) + service(0.15)

### S2: CLI + API + post-crawl hook (1 hour)
- CLI: `szimplacoffee score-merchants` — runs scorer for all merchants, prints table
- API: POST /api/v1/merchants/{id}/rescore
- Post-crawl: call `score_merchant()` at end of `crawl_merchant()`

## Verification
1. Run scorer: `python -m szimplacoffee.cli score-merchants`
2. Check all 16 merchants have profiles
3. Verify differentiation: merchants with rich data score higher
