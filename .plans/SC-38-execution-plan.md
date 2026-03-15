# SC-38 Execution Plan: Product Detail Page

## Overview
Full product detail with metadata, variants, price history chart, and buy link.

## Execution
1. **API:** GET /api/v1/products/{id}/price-history → array of {date, variant_id, variant_label, price_cents}
2. **Page:** Route /products/{productId} — metadata section, variant table, price chart, merchant info
3. **Metadata:** Origin, process, tasting notes, roast level, altitude, varietal — show what's available, hide empty
4. **Variants:** Table with label, weight, current price, availability. Highlight best value.
5. **Price chart:** Recharts LineChart, one line per variant, x-axis = date, y-axis = price. Show "No history yet" if single day.
6. **Actions:** Buy link (external), Log Purchase button (links to SC-34 form)
