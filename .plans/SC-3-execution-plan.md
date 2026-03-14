# SC-3 — Custom-Platform Product Crawler (Squarespace) — Execution Plan

## Summary

Expand platform detection to identify Squarespace-hosted stores, implement a `StaticHtmlAdapter` that follows the standard adapter interface for static product page extraction, and write a decision record capturing the custom-platform crawl strategy. The adapter should return confidence scores reflecting the inherent uncertainty of HTML scraping.

---

## Slices

### S1 — Expand platform detection to identify Squarespace/custom platforms

**Goal:** `platforms.py` can detect Squarespace with reasonable confidence from a homepage HTML response.

**Files to create:**
- `tests/test_platform_detection_squarespace.py`

**Files to modify:**
- `src/szimplacoffee/services/platforms.py`

**Implementation notes:**

Squarespace detection signals (check in HTML `<head>` and response headers):
- `<meta name="generator" content="Squarespace ...">` → strong signal (0.95)
- `static.squarespace.com` in script/link src → strong signal (0.9)
- `squarespace-cdn.com` in resources → moderate signal (0.7)
- `/commerce/v2/` API path in page source → strong signal (0.9)

Add `detect_squarespace(html: str, url: str) -> float` returning confidence 0.0–1.0.

Threshold: return `platform_type = "squarespace"` if confidence ≥ 0.7.

Test with:
- Fixture HTML with Squarespace meta tag → should detect
- Fixture HTML with Squarespace CDN reference → should detect
- Fixture HTML with no Squarespace signals → should not detect

**Checks:**
```bash
ruff check src/ tests/
pytest tests/test_platform_detection_squarespace.py -v
```

---

### S2 — Implement StaticHtmlAdapter with standard adapter interface

**Goal:** A working adapter that can extract products from static HTML pages using BeautifulSoup, following the standard adapter contract.

**Files to create:**
- `src/szimplacoffee/services/adapters/static_html.py`
- `tests/test_static_html_adapter.py`

**Files to modify:**
- `src/szimplacoffee/services/crawlers.py` (register adapter for `custom` and `squarespace` platform types)

**Implementation notes:**

Adapter interface (same as Shopify/WooCommerce adapters):
```python
class StaticHtmlAdapter:
    def detect(self, url: str) -> float: ...
    def discover_entrypoints(self, merchant) -> list[str]: ...
    def crawl_catalog(self, merchant) -> list[ProductRecord]: ...
    def crawl_promos(self, merchant) -> list[PromoRecord]: ...
    def crawl_shipping(self, merchant) -> ShippingPolicy | None: ...
    def normalize(self, payload) -> tuple[list, float]: ...
```

Static HTML extraction strategy for catalog:
1. `discover_entrypoints`: Try common shop paths: `/shop`, `/collections/all`, `/products`, `/store`
2. `crawl_catalog`: Fetch each entrypoint, use BeautifulSoup to find product cards
   - Product name: look for `<h2>`, `<h3>`, `.product-title` patterns
   - Price: look for `.price`, `[data-price]`, `$\d+` patterns near product containers
   - Product URL: follow `<a>` tags within product card containers
3. Confidence: 0.5 for name+price, 0.3 for name-only, 0.7 for structured data (JSON-LD)

For Squarespace specifically:
- Try `/commerce/v2/website/products?format=json` (returns JSON if accessible)
- Fall back to static HTML parse

Test with:
- Fixture HTML with clear product cards → extracts name + price
- Fixture HTML with JSON-LD product schema → extracts structured data at higher confidence
- Empty or non-product page → returns empty list, confidence 0.0

**Checks:**
```bash
ruff check src/ tests/
pytest tests/test_static_html_adapter.py -v
```

---

### S3 — Write ADR for custom-platform crawl strategy

**Goal:** Document the decision and rationale so future agents don't revisit the same question.

**Files to create:**
- `SzimplaCoffee/brain/decisions/001-custom-platform-crawl-strategy.md`

**Implementation notes:**

Use the decision record template from `brain/index.md`. Cover:

**Context:** Many specialty roasters use Squarespace or bespoke sites. No official API. Static HTML is the only practical path without browser automation.

**Options considered:**
1. Browser-only for all custom platforms — reliable but slow, resource-heavy
2. Static HTML first, browser fallback when confidence < 0.3 — balanced
3. Skip custom-platform merchants entirely — simplest but limits coverage

**Decision:** Option 2 — static first, browser only when needed.

**Consequences:**
- Coverage expands to Squarespace merchants
- Some products may be missed (client-rendered content)
- Confidence scores distinguish reliable vs uncertain extractions

**Checks:**
```bash
ls SzimplaCoffee/brain/decisions/001-custom-platform-crawl-strategy.md
```

---

## Verification Steps

```bash
ruff check src/ tests/
pytest tests/ -v
ls SzimplaCoffee/brain/decisions/001-custom-platform-crawl-strategy.md
```

---

## Notes

- Do not default to browser. Static first is the project rule.
- Confidence < 0.3 after static attempt is the trigger for browser fallback, not the default.
- JSON-LD (`application/ld+json` with `@type: Product`) is the highest-fidelity path for any static HTML adapter.
