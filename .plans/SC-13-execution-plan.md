# SC-13 Execution Plan: /api/v1/products Endpoints

## Router: `backend/src/szimplacoffee/api/products.py`

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload, selectinload

from ..db import get_db
from ..models import OfferSnapshot, Product, ProductVariant
from ..schemas.common import PaginatedResponse
from ..schemas.products import OfferSnapshotSchema, ProductDetail, ProductSummary, ProductVariantSchema

router = APIRouter(tags=["products"])


@router.get("/merchants/{merchant_id}/products", response_model=PaginatedResponse[ProductSummary])
def list_products_for_merchant(
    merchant_id: int,
    db: Session = Depends(get_db),
    is_active: bool | None = Query(None),
    is_espresso_recommended: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> PaginatedResponse[ProductSummary]:
    q = db.query(Product).filter(Product.merchant_id == merchant_id)
    if is_active is not None:
        q = q.filter(Product.is_active == is_active)
    if is_espresso_recommended is not None:
        q = q.filter(Product.is_espresso_recommended == is_espresso_recommended)
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(
        items=[ProductSummary.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size < total),
    )


@router.get("/products", response_model=PaginatedResponse[ProductSummary])
def search_products(
    db: Session = Depends(get_db),
    name: str | None = Query(None),
    is_espresso_recommended: bool | None = Query(None),
    weight_grams: int | None = Query(None),
    min_price_cents: int | None = Query(None),
    max_price_cents: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> PaginatedResponse[ProductSummary]:
    q = db.query(Product).filter(Product.is_active == True)
    if name:
        q = q.filter(Product.name.ilike(f"%{name}%"))
    if is_espresso_recommended is not None:
        q = q.filter(Product.is_espresso_recommended == is_espresso_recommended)
    if weight_grams:
        q = q.join(Product.variants).filter(ProductVariant.weight_grams == weight_grams)
    if min_price_cents or max_price_cents:
        q = q.join(Product.variants).join(ProductVariant.offers)
        if min_price_cents:
            q = q.filter(OfferSnapshot.price_cents >= min_price_cents)
        if max_price_cents:
            q = q.filter(OfferSnapshot.price_cents <= max_price_cents)
    q = q.distinct()
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(
        items=[ProductSummary.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size < total),
    )


@router.get("/products/{product_id}", response_model=ProductDetail)
def get_product(product_id: int, db: Session = Depends(get_db)) -> ProductDetail:
    p = (
        db.query(Product)
        .options(
            selectinload(Product.variants).selectinload(ProductVariant.offers)
        )
        .filter(Product.id == product_id)
        .first()
    )
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    # Attach only latest offer per variant for summary
    for v in p.variants:
        if v.offers:
            v._latest_offer = max(v.offers, key=lambda o: o.observed_at)
        else:
            v._latest_offer = None
    return ProductDetail.model_validate(p)


@router.get(
    "/products/{product_id}/variants/{variant_id}/offers",
    response_model=list[OfferSnapshotSchema],
)
def get_offer_history(
    product_id: int,
    variant_id: int,
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
) -> list[OfferSnapshotSchema]:
    variant = db.query(ProductVariant).filter(
        ProductVariant.id == variant_id,
        ProductVariant.product_id == product_id,
    ).first()
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    offers = (
        db.query(OfferSnapshot)
        .filter(OfferSnapshot.variant_id == variant_id)
        .order_by(OfferSnapshot.observed_at.desc())
        .limit(limit)
        .all()
    )
    return [OfferSnapshotSchema.model_validate(o) for o in offers]
```

## Key Data Facts
- 910 products across 16 merchants
- 3207 variants (avg ~3.5 per product)
- 9352 offer snapshots, all from 2026-03-09
- Price range: $0 - $1732.80 (price_cents 0 - 173280), avg ~$80
- Weight: 340g (12oz) and 2268g (5lb) most common
- Most products have empty origin_text, process_text, tasting_notes_text

## Update `ProductVariantSchema` to include latest_offer
Add to `schemas/products.py`:
```python
class ProductVariantSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    label: str
    weight_grams: Optional[int]
    is_whole_bean: bool
    is_available: bool
    latest_offer: Optional[OfferSnapshotSchema] = None
    offers: list[OfferSnapshotSchema] = []
```
