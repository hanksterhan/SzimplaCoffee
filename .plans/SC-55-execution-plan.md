# SC-55 Execution Plan

## Goal

Use `subscription_price_cents` from the latest `OfferSnapshot` in recommendation landed cost calculations. Surface subscription savings as a rationale.

## Context

North-star: "The system should understand subscription pricing." The `OfferSnapshot` model already captures `subscription_price_cents` but `_deal_score()` and landed cost calculation ignore it.

## Files Expected to Change

- `backend/src/szimplacoffee/services/recommendations.py` — use subscription price in deal scoring

## Implementation Steps

1. In `_deal_score()`: check `offer.subscription_price_cents`; if it's < `offer.price_cents * 0.95` (5%+ savings), use subscription price as effective landed cost
2. Add "Subscribe & save X%" to `deal_reasons` when applied
3. Pass subscription benefit through to `RecommendationCandidate.pros`
4. Add tests: subscription price is used when available and meaningful

## Risks / Notes

- Only apply when savings >= 5% to avoid noise from minor subscription discounts
- The WooCommerce and Shopify crawlers already capture subscription prices via `MerchantPromo`; this change is about using `OfferSnapshot.subscription_price_cents` directly in scoring

## Verification

- `pytest -q` — tests for subscription discount scoring
- Manual check: Merchants with subscription offers should rank higher

## Out of Scope

- Subscription management
- Auto-recurring order tracking
