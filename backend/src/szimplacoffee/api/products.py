from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, selectinload

from ..db import get_session
from ..models import Merchant, OfferSnapshot, Product, ProductVariant
from ..schemas.common import CursorPage, PaginatedResponse
from ..schemas.products import OfferSnapshotSchema, ProductDetail, ProductSummary

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
    return summary


@router.get("/merchants/{merchant_id}/products", response_model=CursorPage[ProductSummary])
def list_products_for_merchant(
    merchant_id: int,
    db: Session = Depends(get_session),
    is_active: bool | None = Query(None),
    is_espresso_recommended: bool | None = Query(None),
    category: str | None = Query("coffee", description="Filter by product category. Use 'all' for no filter."),
    limit: int = Query(24, ge=1, le=200),
    cursor: int | None = Query(None, description="Last product ID seen; returns products with id > cursor"),
) -> CursorPage[ProductSummary]:
    is_active = _normalize_query_default(is_active)
    is_espresso_recommended = _normalize_query_default(is_espresso_recommended)
    category = _normalize_query_default(category)
    limit = _normalize_query_default(limit)
    cursor = _normalize_query_default(cursor)
    merchant = db.get(Merchant, merchant_id)
    merchant_name = merchant.name if merchant else ""
    q = (
        select(Product)
        .options(selectinload(Product.variants).selectinload(ProductVariant.offers))
        .where(Product.merchant_id == merchant_id)
    )
    if is_active is not None:
        q = q.where(Product.is_active == is_active)
    if is_espresso_recommended is not None:
        q = q.where(Product.is_espresso_recommended == is_espresso_recommended)
    q = _apply_category_filter(q, category)
    if cursor is not None:
        q = q.where(Product.id > cursor)
    q = q.order_by(Product.id)
    # Fetch limit+1 to detect has_more
    rows = db.scalars(q.limit(limit + 1)).all()
    has_more = len(rows) > limit
    items = rows[:limit]
    next_cursor = items[-1].id if has_more and items else None
    return CursorPage(
        items=[_product_summary_with_merchant(p, merchant_name) for p in items],
        next_cursor=next_cursor,
        has_more=has_more,
    )


@router.get("/products/search", response_model=CursorPage[ProductSummary])
def search_products(
    db: Session = Depends(get_session),
    q: str | None = Query(None, description="Search term for product name"),
    is_espresso_recommended: bool | None = Query(None),
    is_active: bool | None = Query(None),
    category: str | None = Query("coffee", description="Filter by product category. Use 'all' to search everything."),
    limit: int = Query(24, ge=1, le=200),
    cursor: int | None = Query(None, description="Last product ID seen; returns products with id > cursor"),
) -> CursorPage[ProductSummary]:
    q = _normalize_query_default(q)
    is_espresso_recommended = _normalize_query_default(is_espresso_recommended)
    is_active = _normalize_query_default(is_active)
    category = _normalize_query_default(category)
    limit = _normalize_query_default(limit)
    cursor = _normalize_query_default(cursor)
    stmt = (
        select(Product)
        .options(selectinload(Product.variants).selectinload(ProductVariant.offers))
        .join(Merchant, Product.merchant_id == Merchant.id)
    )
    if is_active is not None:
        stmt = stmt.where(Product.is_active == is_active)
    else:
        stmt = stmt.where(Product.is_active.is_(True))
    if q:
        stmt = stmt.where(Product.name.ilike(f"%{q}%"))
    if is_espresso_recommended is not None:
        stmt = stmt.where(Product.is_espresso_recommended == is_espresso_recommended)
    stmt = _apply_category_filter(stmt, category)
    if cursor is not None:
        stmt = stmt.where(Product.id > cursor)
    stmt = stmt.order_by(Product.id)
    # Fetch limit+1 to detect has_more
    rows = db.scalars(stmt.limit(limit + 1)).all()
    has_more = len(rows) > limit
    items = rows[:limit]
    next_cursor = items[-1].id if has_more and items else None
    # Build merchant name lookup for the result set
    merchant_ids = {p.merchant_id for p in items}
    merchants = {
        m.id: m.name
        for m in db.scalars(select(Merchant).where(Merchant.id.in_(merchant_ids))).all()
    }
    return CursorPage(
        items=[_product_summary_with_merchant(p, merchants.get(p.merchant_id, "")) for p in items],
        next_cursor=next_cursor,
        has_more=has_more,
    )


@router.get("/products/{product_id}", response_model=ProductDetail)
def get_product(product_id: int, db: Session = Depends(get_session)) -> ProductDetail:
    p = db.scalar(
        select(Product)
        .options(
            selectinload(Product.variants).selectinload(ProductVariant.offers)
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
    return ProductDetail.model_validate(p)


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
