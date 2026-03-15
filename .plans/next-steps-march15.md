Here is a comprehensive plan for where we should go from here: ```Findings

P1 The app cannot yet tell you the “biggest sales today” in a trustworthy way because it has no real time-series price baseline. The crawler stores snapshots, but the live database only has 1 distinct offer day, so every “deal” is being inferred from current price plus compare-at hints, not from merchant or variant history. The recommendation logic also only looks at the latest offer per variant and scores value with a simple landed-price heuristic. See recommendations.py (line 40), recommendations.py (line 259), recommendations.py (line 329), recommendations.py (line 409).
P1 Automated refresh is not actually running. The app initializes the DB on startup, but it does not start any recurring crawl worker or APScheduler loop, so “daily sales across 500 shops” would require manual or ad hoc triggering. The scheduler code exists, but it is only a calculator right now. See main.py (line 22), scheduler.py (line 1), crawl.py (line 1).
P1 Search and ranking on the products page are not product-trustworthy yet. The backend search endpoint only matches Product.name, while the UI tells you it searches origin, process, and tasting notes. On top of that, price, price-per-ounce, and discount sorting are done client-side over only the currently loaded pages, not across the full corpus. That means “best sale first” is incorrect as soon as the catalog is larger than the current infinite-scroll window. See products.py (line 193), products.py (line 218), products.lazy.tsx (line 351), products.lazy.tsx (line 424).
P1 The backend regression suite is broken after the migration. pytest fails during collection because tests still import UI helper functions from szimplacoffee.main that no longer exist there. That is a hard quality gate failure for any further feature work. See test_recommendations.py (line 3).
P2 Stock state is misrepresented in the catalog UI. Product cards use product.is_active to render “In stock” versus “Unavailable”, but is_active is really “still present in latest crawl”, not live inventory. Variant-level availability exists and should drive the stock label. See products.lazy.tsx (line 182), products.lazy.tsx (line 275).
P2 The metadata model is too free-text-heavy for the product you want. You want fast filtering by country of origin and roast level across 500 merchants, but the schema only stores text blobs like origin_text, process_text, and roast_cues. There are no canonical origin-country, roast-level, or process-family fields to facet on reliably. See models.py (line 114), coffee_parser.py (line 19).
P2 Discovery and platform detection are still brittle for 500-merchant coverage. Discovery currently scrapes Bing HTML, applies heuristic filtering, and then probes homepages for platform fingerprints. That is good enough for seeding, but not for a stable ingestion pipeline at scale. It will miss merchants, over-admit noisy domains, and require ongoing hand-tuning. See discovery.py (line 121), discovery.py (line 266), platforms.py (line 98).
P2 The coffee-product classifier has conflicting logic that will create false negatives. \_is_coffee_product() rejects any item containing filter, then later treats filter as a positive coffee signal. That means valid coffees can be filtered out before they ever reach the positive check. See crawlers.py (line 268).
P3 Query patterns and repo hygiene need cleanup before scaling. list_merchants() computes totals by loading full result sets into memory, and the old top-level src/ still contains stale package artifacts that blur the actual runtime boundary. See merchants.py (line 61), src.
Observed State

Verified: frontend build passes with npm run build.
Verified: backend tests currently fail on import during collection.
Current DB snapshot: 16 merchants, 891 active products, 3207 variants, 9352 offer snapshots, but only 1 offer day.
Metadata coverage is improving, but still incomplete for faceted search: 566 active products with origin, 130 with process, 139 with roast cues.
Assumptions

“Top 500 coffee shops” should be interpreted as top 500 U.S. roasters / online coffee merchants that ship nationally, not general cafes.
The product should stay local-first, single-user for now. SQLite is still fine at this scale if queries are fixed and crawl work is serialized or queued.
The daily dashboard should focus on whole-bean, in-stock, quality-clearing offers, not every item in every catalog.
Where To Go From Here
The current platform is a good prototype for merchant ingestion and browsing. It is not yet a reliable daily buying utility. The next version should optimize for one job: “show me the best quality-clearing coffee deals today, with filters I trust.”

The clean product direction is:

Treat coverage, quality, and deal intelligence as separate systems.
Make search and sorting server-side and truth-based.
Add normalized coffee metadata so origin and roast filters are real, not fuzzy.
Add recurring crawls and price history so “sale” means “down versus recent baseline,” not just “has compare-at.”
Comprehensive Plan

Stabilize the current system before adding more surface area

Fix the broken backend tests and update them to target current modules.
Remove or quarantine stale top-level src/ artifacts so there is one obvious backend package root.
Correct stock semantics in the frontend so cards reflect variant availability, not product presence.
Replace the misleading search placeholder until backend search actually supports those fields.
Acceptance bar: backend tests green, frontend build green, product cards use true stock state.
Make the product queryable the way you want to shop

Add canonical fields to Product or a companion normalized table:
origin_country
origin_region
roast_level (light, light-medium, medium, medium-dark, dark, unknown)
process_family (washed, natural, honey, anaerobic, wet-hulled, blend, unknown)
is_blend
is_decaf
metadata_confidence
metadata_source (structured, parser, agentic, override)
Keep the original free-text columns for display and audit.
Extend /products/search to support server-side filters for:
origin_country
roast_level
process_family
merchant_ids
in_stock_only
whole_bean_only
sale_only
min_price_per_oz, max_price_per_oz
Move sorting into the API:
newest
price_low
price_high
price_per_oz_low
discount_percent
deal_score
Acceptance bar: you can filter the full corpus by country and roast level from the backend, and sort results globally.
Build real deal intelligence

Add a daily fact layer, either materialized in SQLite or computed on demand:
latest_offer_per_variant
variant_price_history_daily
variant_deal_fact
Define “sale” using multiple signals:
compare-at discount
drop versus 7-day median
drop versus 30-day median
drop versus merchant’s own historical low/high range
landed price per ounce versus category baseline
Compute a daily deal_score that combines:
historical price delta
current compare-at or promo signal
shipping threshold effect
bag-size fit
merchant trust floor
Add a biggest sales today endpoint that returns only quality-clearing offers.
Acceptance bar: the dashboard can show “best sales today” with reasons rooted in actual price history.
Turn crawling into a proper pipeline

Split crawling into four adapter layers, in priority order:
Structured feeds: Shopify JSON, WooCommerce Store API, Squarespace commerce endpoints where available.
Structured page data: JSON-LD Product, Next/Nuxt hydration payloads, inline product config objects.
DOM extraction: deterministic HTML extraction for custom storefronts.
Agentic fallback: browser-driven extraction with provenance when deterministic extraction fails.
Add per-merchant crawl strategy records:
catalog_strategy
promo_strategy
shipping_strategy
metadata_strategy
last_success_rate
Add a crawl-quality score:
product count stability
metadata fill rate
price parse success rate
availability parse success rate
Add merchant-specific adapters only when generic extraction quality is low but merchant value is high.
Acceptance bar: the top 100 merchants crawl reliably without hand intervention, and low-confidence merchants are visibly flagged.
Upgrade metadata extraction

Keep the current regex parser as pass 1, but add a normalized extractor pipeline:
country dictionary + alias map
roast keyword map with merchant-specific synonyms
process ontology
bundle-size and multi-pack weight resolver
blend/single-origin classifier
Add confidence scores per field, not just per product.
Add override tables:
merchant_field_patterns
product_metadata_overrides
Add agentic extraction only for low-confidence products, and store provenance so the UI can show structured, parsed, or agentic.
Acceptance bar: origin country and roast level are filled for the majority of active coffee SKUs on the watchlist.
Add the daily utility views

Today dashboard:
biggest sales today
best 12 to 18 oz buys
best 2 lb buys
new promos from trusted merchants
crawl failures / stale merchants
Catalog Explorer:
fast filters for origin, roast, process, merchant, price per oz, availability
Merchant Watch:
top merchants by trust
crawl health
promo cadence
Review Queue:
low-confidence metadata
suspicious price changes
agentic extractions awaiting trust
Acceptance bar: you can open the app and answer “what should I buy today?” in under a minute.
Scale to the top 500 merchants deliberately

Build a merchant registry, not just a discovered list:
watchlist
trusted
candidate
low-value
manual-only
Seed from high-signal roaster lists and known specialty roasters first.
Tier crawl cadence:
Tier A: every 4 to 6 hours
Tier B: daily
Tier C: every 3 to 7 days
Tier D: manual / discovery only
Only include merchants in the “biggest sales today” view if they clear:
crawl quality threshold
metadata quality threshold
trust threshold
Acceptance bar: the top 500 registry exists, but only high-quality merchants influence the main buying dashboard.
Recommended Immediate Next Slice

Fix the broken backend tests and clean up the package boundary.
Implement normalized origin_country and roast_level fields plus server-side filters/sorting.
Start automatic crawl scheduling and collect at least 14 days of offer history before trying to perfect the “biggest sales” ranking.
Build the first Today dashboard against those server-side deal facts.
Only after that, expand merchant coverage aggressively.``` Write this p
