from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, selectinload

from ..db import get_session
from ..models import Merchant, OfferSnapshot, Product, ProductVariant
from ..schemas.common import CursorPage
from pydantic import BaseModel

from ..schemas.products import DealFactSchema, OfferSnapshotSchema, ProductDetail, ProductSort, ProductSummary


class ProductMerchantOption(BaseModel):
    merchant_id: int
    merchant_name: str


@dataclass
class ProductResultRow:
    summary: ProductSummary
    has_stock: bool
    has_whole_bean: bool
    is_on_sale: bool
    price_per_oz: float | None
    merchant_quality_score: float = 0.5

router = APIRouter(tags=["products"])


MERCH_NAME_EXCLUSIONS = (
    "tee",
    "t-shirt",
    "shirt",
    "hoodie",
    "crewneck",
    "sweatshirt",
    "hat",
    "cap",
    "beanie",
    "tote",
    "mug",
    "pin",
    "sticker",
    "magnet",
    "glass",
    "straw",
)


def _normalize_query_default(value: Any):
    if hasattr(value, "default"):
        return value.default
    return value


def _parse_categories(category: str | None) -> list[str]:
    category = _normalize_query_default(category)
    if not category:
        return ["coffee"]
    categories = [part.strip() for part in category.split(",") if part.strip()]
    if not categories:
        return ["coffee"]
    if "all" in categories:
        return ["all"]
    return list(dict.fromkeys(categories))


def _parse_csv_values(value: str | None) -> list[str]:
    value = _normalize_query_default(value)
    if not value:
        return []
    return list(dict.fromkeys(part.strip() for part in value.split(",") if part.strip()))


def _parse_csv_ints(value: str | None) -> list[int]:
    ids: list[int] = []
    for item in _parse_csv_values(value):
        try:
            ids.append(int(item))
        except ValueError:
            continue
    return list(dict.fromkeys(ids))


def _coffee_like_merch_clause():
    exclusions = [Product.name.ilike(f"%{term}%") for term in MERCH_NAME_EXCLUSIONS]
    return and_(
        Product.product_category == "merch",
        Product.name.not_ilike("%subscription%"),
        ~or_(*exclusions),
        Product.variants.any(
            and_(
                ProductVariant.is_whole_bean.is_(True),
                ProductVariant.weight_grams.is_not(None),
                ProductVariant.weight_grams >= 340,
            )
        ),
    )


def _apply_category_filter(stmt, category: str | None):
    categories = _parse_categories(category)
    if "all" in categories:
        return stmt

    clauses = []
    for cat in categories:
        if cat == "coffee":
            clauses.append(or_(Product.product_category == "coffee", _coffee_like_merch_clause()))
        else:
            clauses.append(Product.product_category == cat)
    return stmt.where(or_(*clauses))


def _variant_latest_offer(variant: ProductVariant):
    latest_offer = getattr(variant, "latest_offer", None)
    if latest_offer is not None:
        return latest_offer
    offers = getattr(variant, "offers", None) or []
    if not offers:
        return None
    return max(offers, key=lambda offer: offer.observed_at)


def _offer_is_on_sale(offer: OfferSnapshot | None) -> bool:
    if offer is None:
        return False
    return bool(
        offer.is_on_sale
        or (
            offer.compare_at_price_cents
            and offer.compare_at_price_cents > offer.price_cents
        )
    )


def _price_per_oz(price_cents: int | None, weight_grams: int | None) -> float | None:
    if not price_cents or not weight_grams:
        return None
    ounces = weight_grams / 28.3495
    if ounces <= 0:
        return None
    return (price_cents / 100) / ounces



def _select_primary_variant(product: Product) -> tuple[ProductVariant, Any] | None:
    variants_with_offer = []
    for variant in product.variants:
        latest_offer = _variant_latest_offer(variant)
        if latest_offer is not None:
            variants_with_offer.append((variant, latest_offer))

    if not variants_with_offer:
        return None

    whole_bean = [item for item in variants_with_offer if item[0].is_whole_bean and item[0].weight_grams]
    pool = whole_bean or variants_with_offer
    return min(pool, key=lambda item: item[1].price_cents)


def _build_product_result(product: Product, merchant_name: str, merchant_quality_score: float = 0.5) -> ProductResultRow:
    summary = _product_summary_with_merchant(product, merchant_name)
    has_stock = False
    has_whole_bean = False
    is_on_sale = False

    for variant in product.variants:
        latest_offer = _variant_latest_offer(variant)
        if variant.is_whole_bean:
            has_whole_bean = True
        if variant.is_available and latest_offer and latest_offer.is_available:
            has_stock = True
        if _offer_is_on_sale(latest_offer):
            is_on_sale = True

    summary.has_stock = has_stock  # propagate variant-level stock truth to summary field
    return ProductResultRow(
        summary=summary,
        has_stock=has_stock,
        has_whole_bean=has_whole_bean,
        is_on_sale=is_on_sale,
        price_per_oz=_price_per_oz(summary.latest_price_cents, summary.primary_weight_grams),
        merchant_quality_score=merchant_quality_score,
    )


def _matches_result_filters(
    result: ProductResultRow,
    *,
    in_stock: bool | None,
    whole_bean_only: bool | None,
    on_sale: bool | None,
    price_per_oz_min: float | None,
    price_per_oz_max: float | None,
) -> bool:
    if in_stock is not None and result.has_stock != in_stock:
        return False
    if whole_bean_only is not None and result.has_whole_bean != whole_bean_only:
        return False
    if on_sale is not None and result.is_on_sale != on_sale:
        return False
    if price_per_oz_min is not None:
        if result.price_per_oz is None or result.price_per_oz < price_per_oz_min:
            return False
    if price_per_oz_max is not None:
        if result.price_per_oz is None or result.price_per_oz > price_per_oz_max:
            return False
    return True


def _sort_results(rows: list[ProductResultRow], sort: ProductSort) -> list[ProductResultRow]:
    if sort == "quality":
        return sorted(
            rows,
            key=lambda row: (
                -int(row.has_stock),
                -(row.merchant_quality_score or 0.0),
                -row.summary.metadata_confidence,
                -row.summary.last_seen_at.timestamp(),
                row.summary.merchant_name.lower(),
                row.summary.name.lower(),
                row.summary.id,
            ),
        )
    if sort == "freshness":
        return sorted(
            rows,
            key=lambda row: (
                -int(row.has_stock),
                -row.summary.last_seen_at.timestamp(),
                row.summary.merchant_name.lower(),
                row.summary.name.lower(),
                row.summary.id,
            ),
        )
    if sort == "merchant":
        return sorted(
            rows,
            key=lambda row: (
                row.summary.merchant_name.lower(),
                row.summary.name.lower(),
                row.summary.id,
            ),
        )
    if sort == "price_low":
        return sorted(
            rows,
            key=lambda row: (
                row.summary.latest_price_cents if row.summary.latest_price_cents is not None else float("inf"),
                row.summary.name.lower(),
                row.summary.id,
            ),
        )
    if sort == "price_high":
        return sorted(
            rows,
            key=lambda row: (
                -(row.summary.latest_price_cents or -1),
                row.summary.name.lower(),
                row.summary.id,
            ),
        )
    if sort == "price_per_oz_low":
        return sorted(
            rows,
            key=lambda row: (
                row.price_per_oz if row.price_per_oz is not None else float("inf"),
                row.summary.name.lower(),
                row.summary.id,
            ),
        )
    if sort == "price_per_oz_high":
        return sorted(
            rows,
            key=lambda row: (
                -(row.price_per_oz or -1),
                row.summary.name.lower(),
                row.summary.id,
            ),
        )
    if sort == "discount":
        return sorted(
            rows,
            key=lambda row: (
                -(row.summary.latest_discount_percent or -1),
                row.summary.latest_price_cents if row.summary.latest_price_cents is not None else float("inf"),
                row.summary.name.lower(),
                row.summary.id,
            ),
        )
    return sorted(
        rows,
        key=lambda row: (
            -int(row.has_stock),
            -row.summary.metadata_confidence,
            -row.summary.last_seen_at.timestamp(),
            row.summary.merchant_name.lower(),
            row.summary.name.lower(),
            row.summary.id,
        ),
    )


def _paginate_results(rows: list[ProductResultRow], cursor: int | None, limit: int) -> CursorPage[ProductSummary]:
    start = max(cursor or 0, 0)
    items = rows[start : start + limit]
    has_more = start + limit < len(rows)
    next_cursor = start + limit if has_more else None
    return CursorPage(
        items=[row.summary for row in items],
        next_cursor=next_cursor,
        has_more=has_more,
    )


def _apply_catalog_filters(
    stmt,
    *,
    q: str | None = None,
    merchant_ids: list[int] | None = None,
    is_active: bool | None = None,
    is_espresso_recommended: bool | None = None,
    is_single_origin: bool | None = None,
    category: str | None = None,
    origin_country: str | None = None,
    process_family: str | None = None,
    roast_level: str | None = None,
):
    if is_active is not None:
        stmt = stmt.where(Product.is_active == is_active)
    if q:
        stmt = stmt.where(Product.name.ilike(f"%{q}%"))
    if merchant_ids:
        stmt = stmt.where(Product.merchant_id.in_(merchant_ids))
    if is_espresso_recommended is not None:
        stmt = stmt.where(Product.is_espresso_recommended == is_espresso_recommended)
    if is_single_origin is not None:
        stmt = stmt.where(Product.is_single_origin == is_single_origin)
    stmt = _apply_category_filter(stmt, category)

    origin_countries = _parse_csv_values(origin_country)
    if origin_countries:
        stmt = stmt.where(Product.origin_country.in_(origin_countries))

    process_families = _parse_csv_values(process_family)
    if process_families:
        stmt = stmt.where(Product.process_family.in_(process_families))

    roast_levels = _parse_csv_values(roast_level)
    if roast_levels:
        stmt = stmt.where(Product.roast_level.in_(roast_levels))

    return stmt


def _merchant_options_query(db: Session, category: str | None = None, q: str | None = None):
    category = _normalize_query_default(category)
    q = _normalize_query_default(q)

    stmt = (
        select(Merchant.id, Merchant.name)
        .join(Product, Product.merchant_id == Merchant.id)
        .where(Product.is_active.is_(True), Merchant.is_active.is_(True))
    )
    if q:
        stmt = stmt.where(Product.name.ilike(f"%{q}%"))
    stmt = _apply_category_filter(stmt, category)
    stmt = stmt.distinct().order_by(Merchant.name)
    return stmt


def _deal_fact_schema_from_variant(variant: ProductVariant | None) -> DealFactSchema | None:
    """Extract a DealFactSchema from the primary variant's VariantDealFact relationship."""
    if variant is None:
        return None
    deal_fact = getattr(variant, "deal_fact", None)
    if deal_fact is None:
        return None
    return DealFactSchema(
        baseline_30d_cents=deal_fact.baseline_30d_cents,
        price_drop_30d_percent=deal_fact.price_drop_30d_percent if deal_fact.price_drop_30d_percent else None,
        compare_at_discount_percent=deal_fact.compare_at_discount_percent if deal_fact.compare_at_discount_percent else None,
        historical_low_cents=deal_fact.historical_low_cents if deal_fact.historical_low_cents else None,
    )


def _product_summary_with_merchant(product: Product, merchant_name: str) -> ProductSummary:
    """Build a ProductSummary and inject merchant_name + derived card metadata."""
    summary = ProductSummary.model_validate(product)
    summary.merchant_name = merchant_name
    primary_variant = _select_primary_variant(product)
    if primary_variant:
        variant, latest_offer = primary_variant
        summary.latest_price_cents = latest_offer.price_cents
        summary.latest_compare_at_price_cents = latest_offer.compare_at_price_cents
        if latest_offer.compare_at_price_cents and latest_offer.compare_at_price_cents > latest_offer.price_cents:
            savings_ratio = 1 - (latest_offer.price_cents / latest_offer.compare_at_price_cents)
            summary.latest_discount_percent = int(round(savings_ratio * 100))
        summary.primary_weight_grams = variant.weight_grams
        summary.primary_is_whole_bean = variant.is_whole_bean
        summary.deal_fact = _deal_fact_schema_from_variant(variant)
    return summary


@router.get("/merchants/{merchant_id}/products", response_model=CursorPage[ProductSummary])
def list_products_for_merchant(
    merchant_id: int,
    db: Session = Depends(get_session),
    is_active: bool | None = Query(None),
    is_espresso_recommended: bool | None = Query(None),
    is_single_origin: bool | None = Query(None),
    in_stock: bool | None = Query(None),
    whole_bean_only: bool | None = Query(None),
    on_sale: bool | None = Query(None),
    category: str | None = Query("coffee", description="Filter by product category. Use 'all' for no filter."),
    origin_country: str | None = Query(None, description="Comma-separated normalized origin countries."),
    process_family: str | None = Query(None, description="Comma-separated normalized process families."),
    roast_level: str | None = Query(None, description="Comma-separated normalized roast levels."),
    price_per_oz_min: float | None = Query(None, ge=0),
    price_per_oz_max: float | None = Query(None, ge=0),
    sort: ProductSort = Query("featured"),
    limit: int = Query(24, ge=1, le=200),
    cursor: int | None = Query(None, ge=0, description="Zero-based offset into the sorted result set."),
) -> CursorPage[ProductSummary]:
    is_active = _normalize_query_default(is_active)
    is_espresso_recommended = _normalize_query_default(is_espresso_recommended)
    is_single_origin = _normalize_query_default(is_single_origin)
    in_stock = _normalize_query_default(in_stock)
    whole_bean_only = _normalize_query_default(whole_bean_only)
    on_sale = _normalize_query_default(on_sale)
    category = _normalize_query_default(category)
    origin_country = _normalize_query_default(origin_country)
    process_family = _normalize_query_default(process_family)
    roast_level = _normalize_query_default(roast_level)
    price_per_oz_min = _normalize_query_default(price_per_oz_min)
    price_per_oz_max = _normalize_query_default(price_per_oz_max)
    sort = _normalize_query_default(sort)
    limit = _normalize_query_default(limit)
    cursor = _normalize_query_default(cursor)
    merchant = db.scalars(
        select(Merchant)
        .options(selectinload(Merchant.quality_profile))
        .where(Merchant.id == merchant_id)
    ).first()
    merchant_name = merchant.name if merchant else ""
    merchant_quality = (merchant.quality_profile.overall_quality_score if merchant and merchant.quality_profile else 0.5)
    stmt = (
        select(Product)
        .options(
            selectinload(Product.variants)
            .selectinload(ProductVariant.offers),
            selectinload(Product.variants)
            .selectinload(ProductVariant.deal_fact),
        )
        .where(Product.merchant_id == merchant_id)
    )
    stmt = _apply_catalog_filters(
        stmt,
        is_active=is_active,
        is_espresso_recommended=is_espresso_recommended,
        is_single_origin=is_single_origin,
        category=category,
        origin_country=origin_country,
        process_family=process_family,
        roast_level=roast_level,
    )
    rows = [
        row
        for row in (
            _build_product_result(product, merchant_name, merchant_quality)
            for product in db.scalars(stmt).all()
        )
        if _matches_result_filters(
            row,
            in_stock=in_stock,
            whole_bean_only=whole_bean_only,
            on_sale=on_sale,
            price_per_oz_min=price_per_oz_min,
            price_per_oz_max=price_per_oz_max,
        )
    ]
    return _paginate_results(_sort_results(rows, sort), cursor, limit)


@router.get("/products/catalog", response_model=CursorPage[ProductSummary])
def catalog_products(
    db: Session = Depends(get_session),
    q: str | None = Query(None, description="Search term for product name"),
    merchant_id: str | None = Query(None, description="Comma-separated merchant IDs."),
    is_espresso_recommended: bool | None = Query(None),
    is_active: bool | None = Query(None),
    is_single_origin: bool | None = Query(None),
    in_stock: bool | None = Query(None),
    whole_bean_only: bool | None = Query(None),
    on_sale: bool | None = Query(None),
    category: str | None = Query("coffee", description="Filter by product category. Use 'all' for no filter."),
    origin_country: str | None = Query(None, description="Comma-separated normalized origin countries."),
    process_family: str | None = Query(None, description="Comma-separated normalized process families."),
    roast_level: str | None = Query(None, description="Comma-separated normalized roast levels."),
    price_per_oz_min: float | None = Query(None, ge=0),
    price_per_oz_max: float | None = Query(None, ge=0),
    sort: ProductSort = Query("quality", description="Sort order. Default is quality-first (merchant quality score descending)."),
    limit: int = Query(24, ge=1, le=200),
    cursor: int | None = Query(None, ge=0, description="Zero-based offset into the sorted result set."),
) -> CursorPage[ProductSummary]:
    """Corpus-wide catalog endpoint with quality-first default sort.

    Default sort (quality): products ranked by merchant quality score descending,
    then by crawl freshness. Also supports freshness, price, and discount sorts.
    """
    q = _normalize_query_default(q)
    merchant_id = _normalize_query_default(merchant_id)
    is_espresso_recommended = _normalize_query_default(is_espresso_recommended)
    is_active = _normalize_query_default(is_active)
    is_single_origin = _normalize_query_default(is_single_origin)
    in_stock = _normalize_query_default(in_stock)
    whole_bean_only = _normalize_query_default(whole_bean_only)
    on_sale = _normalize_query_default(on_sale)
    category = _normalize_query_default(category)
    origin_country = _normalize_query_default(origin_country)
    process_family = _normalize_query_default(process_family)
    roast_level = _normalize_query_default(roast_level)
    price_per_oz_min = _normalize_query_default(price_per_oz_min)
    price_per_oz_max = _normalize_query_default(price_per_oz_max)
    sort = _normalize_query_default(sort)
    limit = _normalize_query_default(limit)
    cursor = _normalize_query_default(cursor)
    merchant_ids = _parse_csv_ints(merchant_id)
    stmt = (
        select(Product)
        .options(
            selectinload(Product.variants)
            .selectinload(ProductVariant.offers),
            selectinload(Product.variants)
            .selectinload(ProductVariant.deal_fact),
        )
        .join(Merchant, Product.merchant_id == Merchant.id)
        .where(Merchant.is_active.is_(True))
    )
    stmt = _apply_catalog_filters(
        stmt,
        q=q,
        merchant_ids=merchant_ids,
        is_active=is_active if is_active is not None else True,
        is_espresso_recommended=is_espresso_recommended,
        is_single_origin=is_single_origin,
        category=category,
        origin_country=origin_country,
        process_family=process_family,
        roast_level=roast_level,
    )
    products = db.scalars(stmt).all()
    merchants_by_id: dict[int, Merchant] = {
        merchant.id: merchant
        for merchant in db.scalars(
            select(Merchant)
            .options(selectinload(Merchant.quality_profile))
            .where(Merchant.id.in_({product.merchant_id for product in products}))
        ).all()
    }
    merchant_names = {mid: m.name for mid, m in merchants_by_id.items()}
    merchant_quality_scores = {
        mid: (m.quality_profile.overall_quality_score if m.quality_profile else 0.5)
        for mid, m in merchants_by_id.items()
    }
    rows = [
        row
        for row in (
            _build_product_result(
                product,
                merchant_names.get(product.merchant_id, ""),
                merchant_quality_scores.get(product.merchant_id, 0.5),
            )
            for product in products
        )
        if _matches_result_filters(
            row,
            in_stock=in_stock,
            whole_bean_only=whole_bean_only,
            on_sale=on_sale,
            price_per_oz_min=price_per_oz_min,
            price_per_oz_max=price_per_oz_max,
        )
    ]
    return _paginate_results(_sort_results(rows, sort), cursor, limit)


@router.get("/products/search", response_model=CursorPage[ProductSummary])
def search_products(
    db: Session = Depends(get_session),
    q: str | None = Query(None, description="Search term for product name"),
    merchant_id: str | None = Query(None, description="Comma-separated merchant IDs."),
    is_espresso_recommended: bool | None = Query(None),
    is_active: bool | None = Query(None),
    is_single_origin: bool | None = Query(None),
    in_stock: bool | None = Query(None),
    whole_bean_only: bool | None = Query(None),
    on_sale: bool | None = Query(None),
    category: str | None = Query("coffee", description="Filter by product category. Use 'all' to search everything."),
    origin_country: str | None = Query(None, description="Comma-separated normalized origin countries."),
    process_family: str | None = Query(None, description="Comma-separated normalized process families."),
    roast_level: str | None = Query(None, description="Comma-separated normalized roast levels."),
    price_per_oz_min: float | None = Query(None, ge=0),
    price_per_oz_max: float | None = Query(None, ge=0),
    sort: ProductSort = Query("featured"),
    limit: int = Query(24, ge=1, le=200),
    cursor: int | None = Query(None, ge=0, description="Zero-based offset into the sorted result set."),
) -> CursorPage[ProductSummary]:
    q = _normalize_query_default(q)
    merchant_id = _normalize_query_default(merchant_id)
    is_espresso_recommended = _normalize_query_default(is_espresso_recommended)
    is_active = _normalize_query_default(is_active)
    is_single_origin = _normalize_query_default(is_single_origin)
    in_stock = _normalize_query_default(in_stock)
    whole_bean_only = _normalize_query_default(whole_bean_only)
    on_sale = _normalize_query_default(on_sale)
    category = _normalize_query_default(category)
    origin_country = _normalize_query_default(origin_country)
    process_family = _normalize_query_default(process_family)
    roast_level = _normalize_query_default(roast_level)
    price_per_oz_min = _normalize_query_default(price_per_oz_min)
    price_per_oz_max = _normalize_query_default(price_per_oz_max)
    sort = _normalize_query_default(sort)
    limit = _normalize_query_default(limit)
    cursor = _normalize_query_default(cursor)
    merchant_ids = _parse_csv_ints(merchant_id)
    stmt = (
        select(Product)
        .options(
            selectinload(Product.variants)
            .selectinload(ProductVariant.offers),
            selectinload(Product.variants)
            .selectinload(ProductVariant.deal_fact),
        )
        .join(Merchant, Product.merchant_id == Merchant.id)
        .where(Merchant.is_active.is_(True))
    )
    stmt = _apply_catalog_filters(
        stmt,
        q=q,
        merchant_ids=merchant_ids,
        is_active=is_active if is_active is not None else True,
        is_espresso_recommended=is_espresso_recommended,
        is_single_origin=is_single_origin,
        category=category,
        origin_country=origin_country,
        process_family=process_family,
        roast_level=roast_level,
    )
    products = db.scalars(stmt).all()
    merchants_by_id = {
        merchant.id: merchant
        for merchant in db.scalars(
            select(Merchant)
            .options(selectinload(Merchant.quality_profile))
            .where(Merchant.id.in_({product.merchant_id for product in products}))
        ).all()
    }
    merchant_names = {mid: m.name for mid, m in merchants_by_id.items()}
    merchant_quality_scores = {
        mid: (m.quality_profile.overall_quality_score if m.quality_profile else 0.5)
        for mid, m in merchants_by_id.items()
    }
    rows = [
        row
        for row in (
            _build_product_result(
                product,
                merchant_names.get(product.merchant_id, ""),
                merchant_quality_scores.get(product.merchant_id, 0.5),
            )
            for product in products
        )
        if _matches_result_filters(
            row,
            in_stock=in_stock,
            whole_bean_only=whole_bean_only,
            on_sale=on_sale,
            price_per_oz_min=price_per_oz_min,
            price_per_oz_max=price_per_oz_max,
        )
    ]
    return _paginate_results(_sort_results(rows, sort), cursor, limit)


@router.get("/products/merchant-options", response_model=list[ProductMerchantOption])
def list_product_merchant_options(
    db: Session = Depends(get_session),
    category: str | None = Query("coffee"),
    q: str | None = Query(None, description="Optional search term to narrow merchant options"),
) -> list[ProductMerchantOption]:
    rows = db.execute(_merchant_options_query(db, category=category, q=q)).all()
    return [ProductMerchantOption(merchant_id=row[0], merchant_name=row[1]) for row in rows]


@router.get("/products/{product_id}", response_model=ProductDetail)
def get_product(product_id: int, db: Session = Depends(get_session)) -> ProductDetail:
    p = db.scalar(
        select(Product)
        .options(
            selectinload(Product.variants).selectinload(ProductVariant.offers),
            selectinload(Product.variants).selectinload(ProductVariant.deal_fact),
            selectinload(Product.variants).selectinload(ProductVariant.price_baseline),
        )
        .where(Product.id == product_id)
    )
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    # Attach latest offer per variant for schema
    for v in p.variants:
        if v.offers:
            v.latest_offer = max(v.offers, key=lambda o: o.observed_at)
        else:
            v.latest_offer = None
    detail = ProductDetail.model_validate(p)
    # Compute has_stock from variant-level availability truth (same logic as catalog)
    detail.has_stock = any(
        v.is_available and v.latest_offer is not None and v.latest_offer.is_available
        for v in p.variants
    )
    # SC-107: attach baseline from the primary (cheapest available) variant's baseline
    # Use the variant with a baseline that has the most samples, prefer available variants
    best_baseline = None
    for v in p.variants:
        if v.price_baseline is not None:
            if best_baseline is None or v.price_baseline.sample_count > best_baseline.sample_count:
                best_baseline = v.price_baseline
    if best_baseline is not None:
        detail.baseline_price = best_baseline.median_price_cents / 100
        detail.baseline_min_price = best_baseline.min_price_cents / 100
        detail.baseline_max_price = best_baseline.max_price_cents / 100
        detail.baseline_sample_count = best_baseline.sample_count
    return detail


@router.get("/products/{product_id}/offers", response_model=list[OfferSnapshotSchema])
def get_product_offers(
    product_id: int,
    db: Session = Depends(get_session),
    limit: int = Query(100, ge=1, le=500),
) -> list[OfferSnapshotSchema]:
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    # Get all variant IDs for this product
    variant_ids = db.scalars(
        select(ProductVariant.id).where(ProductVariant.product_id == product_id)
    ).all()
    if not variant_ids:
        return []
    offers = db.scalars(
        select(OfferSnapshot)
        .where(OfferSnapshot.variant_id.in_(variant_ids))
        .order_by(OfferSnapshot.observed_at.desc())
        .limit(limit)
    ).all()
    return [OfferSnapshotSchema.model_validate(o) for o in offers]
