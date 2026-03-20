# SC-107: Historical deal baseline per variant

**Delivered:** 2026-03-20  
**Branch:** sc-107-variant-price-baseline → merged to stage

## What Changed

- `models.py`: Added `VariantPriceBaseline` model (variant_price_baselines table) with `variant_id` (FK unique), `median_price_cents`, `min_price_cents`, `max_price_cents`, `sample_count`, `baseline_window_days` (default 90), `computed_at`. Added `price_baseline` back-reference on `ProductVariant`.
- `alembic/versions/20260320_02_...py`: Idempotent migration using `CREATE TABLE IF NOT EXISTS` — needed because `init_db()` (Base.metadata.create_all) had already created the table before the migration ran.
- `services/baseline_service.py`: New service `compute_variant_baselines(db, merchant_id=None, window_days=90)`. Fetches OfferSnapshot prices within window, computes `statistics.median`, min, max, count. Upserts VariantPriceBaseline rows. Returns dict with computed/skipped/total_variants.
- `cli.py`: Added `szimpla compute-baselines [--merchant-id N] [--window-days N]` command.
- `schemas/products.py`: Added `baseline_price`, `baseline_min_price`, `baseline_max_price`, `baseline_sample_count` (all Optional) to `ProductDetail`.
- `api/products.py`: Updated `get_product()` to `selectinload(price_baseline)` and attach the most-sampled variant's baseline to the response.
- `tests/test_baseline_service.py`: 10 tests covering no history, single snapshot, multi-snapshot median, 90-day window cutoff, custom window, upsert deduplication, merchant filter, invalid merchant.

## Key Numbers

- Live DB: **8,878 baselines** computed from existing OfferSnapshot history on first run.
- **308 backend tests** pass.
- Ruff clean.

## Surprises / Edge Cases

- `Product.external_product_id` is NOT NULL in the schema — test helper needed this field. Used a module-level counter to generate unique IDs.
- `init_db()` creates tables via `Base.metadata.create_all()` before migrations run on the live DB. Used `CREATE TABLE IF NOT EXISTS` in the migration to handle this gracefully. Pattern should be followed in future migrations that add new tables.
- The `VariantPriceBaseline` import was removed from `api/products.py` after ruff flagged it unused — the model is accessed only via the ORM relationship, not by direct class reference.

## What SC-109 Should Know

- `VariantPriceBaseline.median_price_cents` is the primary deal-score input.
- All existing variants have baselines (8878/8878). No variants with zero offer history exist.
- Baseline computation is idempotent — safe to re-run after crawls.
- Consider hooking `compute_variant_baselines()` as a post-crawl callback once SC-109 ships.
- The `get_product` endpoint returns `baseline_price` (median, in dollars) — use this in frontend product detail pages to show vs. current price.
