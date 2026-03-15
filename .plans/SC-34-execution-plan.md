# SC-34 Execution Plan: Purchase History Form

## Overview
Build a purchase logging form so users can record what they buy, feeding the recommendation learning loop.

## Execution

### S1: API endpoints (1 hour)
- Check if POST /api/v1/purchases already exists
- Add: POST /api/v1/purchases (create), GET /api/v1/purchases (list)
- Request body: merchant_id, product_id (optional), product_name (freetext fallback), variant_id (optional), price_paid_cents, quantity, purchase_date, notes
- Allow logging purchases for products not in the catalog (freetext merchant + product name)

### S2: Purchase form page (2 hours)
- Route: /purchases/new
- Cascading selects: Merchant → Product → Variant (all loaded via API)
- Freetext fallback: "Can't find your coffee? Enter manually"
- Date picker (default: today)
- Price input with $ formatting
- Optional notes field
- Submit → success toast → redirect to /purchases

### S3: Quick-log from recommendations (30 min)
- Add "I bought this" button to ResultCard in recommend.tsx
- Navigates to /purchases/new?merchant={name}&product={name}&price={cents}
- Form reads query params and pre-fills

## Verification
1. Navigate to /purchases/new, fill and submit
2. Verify record appears in DB
3. Run recommendation → click "I bought this" → verify pre-fill
4. Run recommendation engine again, verify new purchase influences results
