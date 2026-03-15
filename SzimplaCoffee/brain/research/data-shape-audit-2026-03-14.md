# Data Shape Audit — 2026-03-14

Findings from inspecting the actual SQLite database (`szimplacoffee.db`).

## Volume

| Table | Count | Notes |
|-------|-------|-------|
| merchants | 16 | 14 Shopify, 1 WooCommerce, 1 agentic |
| merchant_candidates | 2 | Pending discovery |
| products | 910 | SEY has 243, Intelligentsia 167 |
| product_variants | 3207 | Verve 716, SEY 660, Partners 597 |
| offer_snapshots | 9352 | All from 2026-03-09 (single crawl day) |
| promo_snapshots | 201 | |
| merchant_promos | 37 | Canonical deduplicated promos |
| purchase_history | 3 | Seed data only |
| brew_feedback | 3 | |
| crawl_runs | 55 | |
| recommendation_runs | 7 | |
| shipping_policies | 321 | |
| merchant_quality_profiles | 4 | Only 4 of 16 merchants |
| merchant_personal_profiles | 2 | Only Olympia and Camber |
| merchant_sources | 4 | |

## Key Findings

### Merchants
- **Trusted (2):** Olympia Coffee, Camber Coffee
- **Candidates (14):** Counter Culture, Stumptown, George Howell, Black & White, SEY, Passenger, Intelligentsia, Verve, Ceremony, Partners, Heart, La Cabra, Goshen, Onyx
- All tier A or B, all active

### Product Data Richness — MAJOR GAP
- `origin_text`, `process_text`, `tasting_notes_text` are **mostly empty**
- Parsing wasn't wired into the crawl pipeline yet
- `is_espresso_recommended` is set but seems unreliable without proper note parsing
- `image_url` is populated for most products ✅

### Price Distribution
- Range: $0.00 — $1,732.80
- Average: $80.02 (skewed by bulk sizes)
- 1,920 offers marked as on_sale
- No subscription prices captured yet

### Weight Distribution (most common)
- 2,268g (5lb) — 823 variants
- 340g (12oz) — 801 variants
- 907g (32oz/2lb) — 332 variants
- Then various non-standard weights (318g, 367g, 386g)

### Shipping
- Free shipping thresholds range $22–$50
- Most merchants offer 3-day estimated delivery
- High confidence scores (0.9)

### Temporal Coverage
- All offer snapshots from single day (2026-03-09)
- No time-series depth yet — can't chart price trends
- Need recurring crawls to build price history

## Implications for React Frontend

1. **Dashboard metrics** are real and meaningful (16 merchants, 910 products, etc.)
2. **Product table** will be data-rich but note fields will be sparse
3. **Price history charts** won't have temporal data until we run more crawls
4. **Recommendation console** has 7 historical runs to display
5. **Merchant detail** needs quality profiles for 12 more merchants
6. **Discovery page** has only 2 candidates — light data for now
