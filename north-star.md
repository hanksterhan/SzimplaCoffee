# SzimplaCoffee North Star

## Purpose

SzimplaCoffee exists to help us buy coffee the way we actually want to buy it: with a strong bias toward quality, freshness, espresso suitability, and real delivered value.

This is not a generic coffee deal scraper. It is a personal coffee sourcing utility that understands:

- our espresso equipment and techniques
- our quality bar
- our preferred roaster style
- our inventory constraints
- the real economics of coffee buying, including shipping, bulk sizes, subscriptions, promotions, and personal credits

The product should answer a simple question with high confidence:

**If I want to order coffee right now, where should I buy from, what should I buy, and why?**

## User

The initial user is an experienced home espresso drinker with:

- a Decent DE1 XL Pro
- a Timemore Sculptor 078S
- 58mm and 49mm step-down baskets from sworksdesign / sworkstudio
- different prep workflows for 58mm and 49mm shots
- interest in cremina-style lever shots, modern espresso, turbo shots, and other experimental espresso techniques

The user prefers high-quality specialty coffee but does not need the most extreme, hype-driven, or heavily funky coffees. Trusted preference anchors include roasters like Olympia Coffee and Camber Coffee.

## Core Product Truth

The best coffee to buy is not the cheapest coffee.

The best coffee to buy is the coffee that best fits:

- the current espresso goal
- the desired bag size
- the acceptable freshness and delivery window
- the quality floor
- the total landed cost

SzimplaCoffee should optimize for **best buy above a quality threshold**, not lowest price.

## North Star Outcome

When invoked, the utility should produce a recommendation that is:

- personalized
- espresso-aware
- inventory-aware
- quality-aware
- deal-aware
- explainable

A good recommendation tells us:

- which roaster or shop to order from
- which coffee to buy
- which size to buy
- whether to buy now or wait
- why this is the best current option

## Product Principles

### 1. Quality Before Coverage in Ranking

We want broad market coverage, potentially hundreds or thousands of merchants, but broad coverage must not flatten quality differences.

The system should:

- maintain a large merchant universe
- crawl widely enough to capture sales and buying opportunities
- rank trusted merchants and proven roasters higher
- down-rank merchants with poor freshness signals, weak metadata, poor shipping clarity, or low trust

Coverage is important for discovery. Trust is important for ranking.

### 2. Personal History Matters

The system should learn from our actual coffee purchases and outcomes.

A merchant or coffee should get a lift when:

- we have purchased from them before
- the coffee matched our espresso use well
- the coffee was worth the price
- we would reorder from them

A merchant or coffee should get penalized when:

- the coffee was hard to dial without reward
- the freshness window was poor
- the merchant disappointed on quality, detail, or shipping experience

### 3. Espresso Context Is Mandatory

Recommendations must be aware of shot style and technique.

The system should support at least these modes:

- 58mm modern espresso
- 49mm lever or cremina-style espresso
- turbo shots
- high-extraction or experimental espresso

The same coffee may rank differently depending on the intended brew style.

### 4. Bag Size Must Change the Recommendation

The user must be able to state whether they want:

- only 12 to 18 oz
- up to 2 lb
- up to 5 lb
- the best option under a personal inventory cap

Bulk discounts matter, but they only matter if the user can realistically use the coffee well. The product should optimize for usable value, not theoretical unit economics.

### 5. Promotions Are Real Data

Sales, subscription discounts, free shipping thresholds, compare-at pricing, seasonal deals, and personal wallet credits are all part of the recommendation.

The system should understand:

- base price
- price by size
- delivered price
- free shipping threshold
- subscription pricing
- temporary promotions
- personal credits such as Shop Cash or equivalent wallet value

### 6. The Product Must Be Allowed to Say “Wait”

Sometimes the best move is not to buy now.

If current options are below the quality bar or if the best-value roasters are likely to run a known sale soon, the product should be allowed to recommend waiting.

## Product Shape

SzimplaCoffee should start as a **local-first web application** with a companion CLI.

### Why a web application

We need to:

- browse the merchant database
- inspect products and pricing
- review trust scores and overrides
- manage promotions and crawl results
- understand why recommendations were made

This is much easier in a local web UI than in a CLI alone.

### Why a CLI also exists

The CLI should support fast operations and automation, such as:

- add a merchant
- crawl a merchant
- refresh promotions
- sync personal bean history
- request a recommendation

## System Boundaries

### What SzimplaCoffee is

- a personal sourcing and recommendation system
- a merchant and coffee catalog tracker
- a quality-gated deal finder
- a tool for optimizing coffee buying decisions

### What SzimplaCoffee is not

- a generic coffee review site
- a mass-market café directory
- a pure price scraper
- a social app
- a marketplace

## Data Strategy

The operational source of truth should be **SQLite**.

Why:

- local-first and simple to operate
- structured enough for merchants, products, offers, history, and crawl state
- supports indexing and full-text search
- easy to back up and evolve

Notion should remain an input and reference layer, not the primary operational database.

CSV should be used for import and export only.

## Merchant Universe Strategy

The database should support both manual and automated growth.

### Merchant ingestion paths

- manual add by URL
- discovery crawler for U.S. coffee roasters and online shops
- seeded imports from curated sources and known industry lists

### Merchant tiers

- **Tier A**: trusted and high-value merchants, crawled frequently
- **Tier B**: promising merchants with strong metadata or strong fit, crawled daily
- **Tier C**: long-tail merchants, crawled weekly or on demand
- **Tier D**: excluded or low-trust merchants, retained in registry but not recommended by default

The merchant universe can be large. Recommendation quality must still be selective.

## Quality Bar

Each merchant should have both an objective quality profile and a personal trust profile.

### Positive signals

- clear roast-date or roast-to-order practices
- clear shipping policies
- strong product metadata
- espresso-relevant coffees
- reliable size options such as 12 oz, 2 lb, and 5 lb
- consistent quality from prior orders

### Negative signals

- poor freshness transparency
- weak or generic metadata
- unclear shipping cadence
- weak quality track record
- poor customer experience
- repeated mismatch with our preferences

## Recommendation Contract

Every recommendation should include:

- merchant
- coffee
- size
- delivered price estimate
- timing recommendation
- confidence
- rationale

The rationale should explain:

- why the coffee fits the requested espresso style
- why the merchant clears the quality bar
- how bag size affects the value proposition
- which deal signals influenced the recommendation

## Learning Loop

Every coffee we buy should improve the system.

The product should capture:

- what we bought
- what we paid
- how much we bought
- how it performed
- whether we would buy it again
- what shot styles it worked well for

This feedback loop is a core advantage. Over time, the system should become better than a generic coffee search engine because it learns our actual palate and technique preferences.

## Automation Vision

SzimplaCoffee should eventually maintain hot data automatically.

This includes:

- merchant discovery runs
- catalog refreshes
- promotion refreshes
- shipping and threshold checks
- personal credit or wallet updates where available

Automation should keep the system current without requiring manual upkeep for every merchant.

## First Version Definition

Version one should prove the core recommendation loop, not boil the ocean.

V1 should:

- support a local web application
- use SQLite as the source of truth
- ingest personal coffee history from Notion
- track a curated set of trusted and adjacent merchants
- crawl at least Shopify and WooCommerce stores well
- support espresso-mode recommendations
- support size-sensitive recommendations such as 12 to 18 oz vs 2 lb
- account for shipping thresholds and obvious promotions

## Success Criteria

SzimplaCoffee is succeeding when:

- it consistently recommends coffees we actually want to buy
- it surfaces better value than ad hoc manual browsing
- it helps us decide between small-bag and bulk-buy options with confidence
- it saves time without lowering our coffee quality
- it gets smarter as our purchase history grows

## Decision Standard

When we make future product and engineering choices, we should ask:

**Does this help SzimplaCoffee recommend the right coffee, from the right merchant, in the right size, at the right moment, with the right balance of quality and value?**

If the answer is no, it is probably not core.
