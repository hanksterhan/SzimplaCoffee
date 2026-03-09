from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from .bootstrap import bootstrap_if_empty, init_db
from .config import STATIC_DIR, TEMPLATES_DIR
from .db import get_session, session_scope
from .models import Merchant, OfferSnapshot, Product, ProductVariant
from .services.crawlers import crawl_merchant
from .services.platforms import detect_platform
from .services.recommendations import RecommendationRequest, build_recommendations, persist_recommendation_run


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    with session_scope() as session:
        bootstrap_if_empty(session)
    yield


app = FastAPI(title="SzimplaCoffee", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _dashboard_metrics(session: Session) -> dict:
    merchant_count = len(session.scalars(select(Merchant.id)).all())
    product_count = len(session.scalars(select(Product.id)).all())
    variant_count = len(session.scalars(select(ProductVariant.id)).all())
    latest_offer_count = len(session.scalars(select(OfferSnapshot.id)).all())
    return {
        "merchant_count": merchant_count,
        "product_count": product_count,
        "variant_count": variant_count,
        "offer_count": latest_offer_count,
    }


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    merchants = session.scalars(select(Merchant).order_by(Merchant.trust_tier.asc(), Merchant.name.asc())).all()
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "metrics": _dashboard_metrics(session),
            "merchants": merchants,
        },
    )


@app.get("/merchants/new", response_class=HTMLResponse)
def merchant_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "merchant_form.html", {"errors": []})


@app.post("/merchants/new")
def create_merchant(
    url: str = Form(...),
    crawl_tier: str = Form("B"),
    trust_tier: str = Form("candidate"),
    crawl_now: bool = Form(False),
    session: Session = Depends(get_session),
):
    detection = detect_platform(url)
    existing = session.scalar(select(Merchant).where(Merchant.canonical_domain == detection.domain))
    if existing:
        if crawl_now:
            crawl_merchant(session, existing)
            session.commit()
        return RedirectResponse(url=f"/merchants/{existing.id}", status_code=303)

    merchant = Merchant(
        name=detection.merchant_name,
        canonical_domain=detection.domain,
        homepage_url=detection.normalized_url,
        platform_type=detection.platform_type,
        crawl_tier=crawl_tier,
        trust_tier=trust_tier,
    )
    session.add(merchant)
    session.commit()
    session.refresh(merchant)

    if crawl_now:
        crawl_merchant(session, merchant)
        session.commit()
    return RedirectResponse(url=f"/merchants/{merchant.id}", status_code=303)


@app.get("/merchants/{merchant_id}", response_class=HTMLResponse)
def merchant_detail(merchant_id: int, request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    merchant = session.get(Merchant, merchant_id)
    products = session.scalars(select(Product).where(Product.merchant_id == merchant_id).order_by(Product.name.asc())).all()
    return templates.TemplateResponse(
        request,
        "merchant_detail.html",
        {
            "merchant": merchant,
            "products": products,
        },
    )


@app.post("/merchants/{merchant_id}/crawl")
def crawl_merchant_route(merchant_id: int, session: Session = Depends(get_session)):
    merchant = session.get(Merchant, merchant_id)
    crawl_merchant(session, merchant)
    session.commit()
    return RedirectResponse(url=f"/merchants/{merchant_id}", status_code=303)


@app.get("/recommend", response_class=HTMLResponse)
def recommend_page(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    candidates = build_recommendations(
        session,
        RecommendationRequest(shot_style="modern_58mm", quantity_mode="12-18 oz", bulk_allowed=False),
    )
    return templates.TemplateResponse(
        request,
        "recommendation.html",
        {
            "candidates": candidates,
            "selected": {"shot_style": "modern_58mm", "quantity_mode": "12-18 oz", "bulk_allowed": False},
        },
    )


@app.post("/recommend", response_class=HTMLResponse)
def recommend_action(
    request: Request,
    shot_style: str = Form("modern_58mm"),
    quantity_mode: str = Form("12-18 oz"),
    bulk_allowed: bool = Form(False),
    session: Session = Depends(get_session),
) -> HTMLResponse:
    payload = RecommendationRequest(
        shot_style=shot_style,  # type: ignore[arg-type]
        quantity_mode=quantity_mode,  # type: ignore[arg-type]
        bulk_allowed=bulk_allowed,
    )
    candidates = build_recommendations(session, payload)
    persist_recommendation_run(session, payload, candidates)
    session.commit()
    return templates.TemplateResponse(
        request,
        "recommendation.html",
        {
            "candidates": candidates,
            "selected": payload.__dict__,
        },
    )

