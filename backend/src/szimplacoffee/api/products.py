from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..db import get_session
from ..models import Merchant, OfferSnapshot, Product, ProductVariant
from ..schemas.common import PaginatedResponse
from ..schemas.products import OfferSnapshotSchema, ProductDetail, ProductSummary

router = APIRouter(tags=["products"])


def _product_summary_with_merchant(product: Product, merchant_name: str) -> ProductSummary:
    """Build a ProductSummary and inject merchant_name (not an ORM attribute)."""
    summary = ProductSummary.model_validate(product)
    summary.merchant_name = merchant_name
    return summary


@router.get("/merchants/{merchant_id}/products", response_model=PaginatedResponse[ProductSummary])
def list_products_for_merchant(
    merchant_id: int,
    db: Session = Depends(get_session),
    is_active: bool | None = Query(None),
    is_espresso_recommended: bool | None = Query(None),
    category: str | None = Query("coffee", description="Filter by product category. Use 'all' for no filter."),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> PaginatedResponse[ProductSummary]:
    merchant = db.get(Merchant, merchant_id)
    merchant_name = merchant.name if merchant else ""
    q = select(Product).where(Product.merchant_id == merchant_id)
    if is_active is not None:
        q = q.where(Product.is_active == is_active)
    if is_espresso_recommended is not None:
        q = q.where(Product.is_espresso_recommended == is_espresso_recommended)
    if category and category != "all":
        q = q.where(Product.product_category == category)
    total = len(db.scalars(q).all())
    items = db.scalars(q.offset((page - 1) * page_size).limit(page_size)).all()
    return PaginatedResponse(
        items=[_product_summary_with_merchant(p, merchant_name) for p in items],
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size < total),
    )


@router.get("/products/search", response_model=PaginatedResponse[ProductSummary])
def search_products(
    db: Session = Depends(get_session),
    q: str | None = Query(None, description="Search term for product name"),
    is_espresso_recommended: bool | None = Query(None),
    is_active: bool | None = Query(None),
    category: str | None = Query("coffee", description="Filter by product category. Use 'all' to search everything."),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> PaginatedResponse[ProductSummary]:
    stmt = select(Product).join(Merchant, Product.merchant_id == Merchant.id)
    if is_active is not None:
        stmt = stmt.where(Product.is_active == is_active)
    else:
        stmt = stmt.where(Product.is_active.is_(True))
    if q:
        stmt = stmt.where(Product.name.ilike(f"%{q}%"))
    if is_espresso_recommended is not None:
        stmt = stmt.where(Product.is_espresso_recommended == is_espresso_recommended)
    if category and category != "all":
        stmt = stmt.where(Product.product_category == category)
    total = len(db.scalars(stmt).all())
    items = db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).all()
    # Build merchant name lookup for the result set
    merchant_ids = {p.merchant_id for p in items}
    merchants = {
        m.id: m.name
        for m in db.scalars(select(Merchant).where(Merchant.id.in_(merchant_ids))).all()
    }
    return PaginatedResponse(
        items=[_product_summary_with_merchant(p, merchants.get(p.merchant_id, "")) for p in items],
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size < total),
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
