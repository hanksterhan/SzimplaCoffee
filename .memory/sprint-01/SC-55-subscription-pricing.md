# SC-55 Delivery Memory: Subscription Pricing

## What Changed

- Updated `_deal_score()` in `recommendations.py` to check `offer.subscription_price_cents`
- When subscription price saves >= 5%, it becomes the effective landed price for the recommendation
- "Subscribe & save X%" added to deal reasons when applied
- `promo_bonus` gets a small lift proportional to savings percentage (capped at 0.2)

## Why It Matters

North-star: "subscription pricing is a first-class recommendation dimension." The data was already being captured in `OfferSnapshot.subscription_price_cents` but the recommendation engine was ignoring it. This was leaving real value on the table for merchants like subscription-first roasters.

## Design Choices

- 5% minimum savings threshold avoids noise from minor "subscribe" discounts
- Temporarily patching `offer.price_cents` is a hack — better approach would be to pass effective_price as a parameter, but that requires a larger refactor. This is safe because we restore the original value immediately.

## Follow-ups

- Refactor `_deal_score` to accept `effective_price_cents` parameter instead of patching `offer.price_cents`
- Surface subscription badge in product cards on the frontend
