from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from .bootstrap import bootstrap_if_empty, init_db
from .config import STATIC_DIR, TEMPLATES_DIR
from .db import get_session, session_scope
from .models import CrawlRun, Merchant, MerchantCandidate, MerchantPromo, OfferSnapshot, Product, ProductVariant, ShippingPolicy
from .services.crawlers import crawl_merchant
from .services.discovery import promote_candidate, run_discovery
from .services.platforms import detect_platform, recommended_crawl_tier
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


def _money(cents: int | None) -> str:
    if cents is None:
        return "n/a"
    return f"${cents / 100:.2f}"


def _weight_label(weight_grams: int | None) -> str:
    if not weight_grams:
        return "?"
    ounces = weight_grams / 28.3495
    pounds = ounces / 16
    if abs(pounds - round(pounds)) <= 0.06 and pounds >= 1.75:
        return f"{round(pounds):.0f} lb ({weight_grams} g)"
    return f"{weight_grams} g / {ounces:.1f} oz"


def _price_per_oz_label(price_cents: int | None, weight_grams: int | None) -> str:
    if price_cents is None or not weight_grams:
        return "n/a"
    ounces = weight_grams / 28.3495
    if ounces <= 0:
        return "n/a"
    return f"${price_cents / 100 / ounces:.2f}/oz"


def _latest_offer_for_variant(variant: ProductVariant) -> OfferSnapshot | None:
    if not variant.offers:
        return None
    return max(variant.offers, key=lambda offer: offer.observed_at)


def _visible_variants(product: Product) -> list[ProductVariant]:
    available = [variant for variant in product.variants if variant.is_available]
    return available or list(product.variants)


templates.env.globals.update(
    money=_money,
    weight_label=_weight_label,
    price_per_oz_label=_price_per_oz_label,
    latest_offer_for_variant=_latest_offer_for_variant,
    visible_variants=_visible_variants,
)


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


def _latest_crawl_run(session: Session, merchant_id: int) -> CrawlRun | None:
    return session.scalar(
        select(CrawlRun)
        .where(CrawlRun.merchant_id == merchant_id)
        .order_by(CrawlRun.started_at.desc())
        .limit(1)
    )


def _enqueue_crawl(session: Session, merchant: Merchant) -> tuple[CrawlRun, bool]:
    latest_run = _latest_crawl_run(session, merchant.id)
    if latest_run and latest_run.status in {"queued", "started"}:
        return latest_run, False
    run = CrawlRun(
        merchant_id=merchant.id,
        run_type="merchant_refresh",
        adapter_name=merchant.platform_type,
        status="queued",
        confidence=0.0,
        records_written=0,
    )
    session.add(run)
    session.flush()
    return run, True


def _background_crawl(merchant_id: int, run_id: int) -> None:
    try:
        with session_scope() as session:
            merchant = session.get(Merchant, merchant_id)
            run = session.get(CrawlRun, run_id)
            if merchant is None or run is None:
                return
            crawl_merchant(session, merchant, run=run)
    except Exception:
        return


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    merchants = session.scalars(select(Merchant).order_by(Merchant.trust_tier.asc(), Merchant.name.asc())).all()
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "metrics": _dashboard_metrics(session),
            "merchants": merchants,
            "pending_candidates": len(session.scalars(select(MerchantCandidate.id).where(MerchantCandidate.status == "pending")).all()),
        },
    )


@app.get("/merchants/new", response_class=HTMLResponse)
def merchant_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "merchant_form.html", {"errors": []})


@app.post("/merchants/new")
def create_merchant(
    background_tasks: BackgroundTasks,
    url: str = Form(...),
    trust_tier: str = Form("candidate"),
    session: Session = Depends(get_session),
):
    detection = detect_platform(url)
    existing = session.scalar(select(Merchant).where(Merchant.canonical_domain == detection.domain))
    if existing:
        run, should_schedule = _enqueue_crawl(session, existing)
        session.commit()
        if should_schedule:
            background_tasks.add_task(_background_crawl, existing.id, run.id)
        return RedirectResponse(url=f"/merchants/{existing.id}", status_code=303)

    merchant = Merchant(
        name=detection.merchant_name,
        canonical_domain=detection.domain,
        homepage_url=detection.normalized_url,
        platform_type=detection.platform_type,
        crawl_tier=recommended_crawl_tier(detection.platform_type, detection.confidence),
        trust_tier=trust_tier,
    )
    session.add(merchant)
    session.flush()
    run, should_schedule = _enqueue_crawl(session, merchant)
    session.commit()
    if should_schedule:
        background_tasks.add_task(_background_crawl, merchant.id, run.id)
    return RedirectResponse(url=f"/merchants/{merchant.id}", status_code=303)


@app.get("/merchants/{merchant_id}", response_class=HTMLResponse)
def merchant_detail(merchant_id: int, request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    merchant = session.get(Merchant, merchant_id)
    products = session.scalars(select(Product).where(Product.merchant_id == merchant_id).order_by(Product.name.asc())).all()
    promos = session.scalars(
        select(MerchantPromo)
        .where(MerchantPromo.merchant_id == merchant_id, MerchantPromo.is_active.is_(True))
        .order_by(MerchantPromo.estimated_value_cents.desc().nullslast(), MerchantPromo.last_seen_at.desc())
    ).all()
    shipping_policy = session.scalar(
        select(ShippingPolicy)
        .where(ShippingPolicy.merchant_id == merchant_id)
        .order_by(ShippingPolicy.observed_at.desc())
        .limit(1)
    )
    latest_crawl_run = _latest_crawl_run(session, merchant_id)
    return templates.TemplateResponse(
        request,
        "merchant_detail.html",
        {
            "merchant": merchant,
            "products": products,
            "promos": promos,
            "shipping_policy": shipping_policy,
            "latest_crawl_run": latest_crawl_run,
        },
    )


@app.post("/merchants/{merchant_id}/crawl")
def crawl_merchant_route(merchant_id: int, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    merchant = session.get(Merchant, merchant_id)
    run, should_schedule = _enqueue_crawl(session, merchant)
    session.commit()
    if should_schedule:
        background_tasks.add_task(_background_crawl, merchant.id, run.id)
    return RedirectResponse(url=f"/merchants/{merchant_id}", status_code=303)


@app.get("/merchants/{merchant_id}/status")
def merchant_status(merchant_id: int, session: Session = Depends(get_session)) -> dict:
    merchant = session.get(Merchant, merchant_id)
    latest_crawl_run = _latest_crawl_run(session, merchant_id)
    products_count = len(session.scalars(select(Product.id).where(Product.merchant_id == merchant_id, Product.is_active.is_(True))).all())
    return {
        "merchant_id": merchant_id,
        "merchant_name": merchant.name if merchant else "",
        "status": latest_crawl_run.status if latest_crawl_run else "idle",
        "records_written": latest_crawl_run.records_written if latest_crawl_run else 0,
        "error_summary": latest_crawl_run.error_summary if latest_crawl_run else "",
        "products_count": products_count,
    }


@app.get("/discovery", response_class=HTMLResponse)
def discovery_page(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    candidates = session.scalars(
        select(MerchantCandidate)
        .where(MerchantCandidate.status == "pending")
        .order_by(MerchantCandidate.confidence.desc(), MerchantCandidate.discovered_at.desc())
    ).all()
    return templates.TemplateResponse(request, "discovery.html", {"candidates": candidates})


@app.post("/discovery/run")
def discovery_run(session: Session = Depends(get_session)):
    run_discovery(session)
    session.commit()
    return RedirectResponse(url="/discovery", status_code=303)


@app.post("/discovery/{candidate_id}/promote")
def discovery_promote(candidate_id: int, session: Session = Depends(get_session)):
    candidate = session.get(MerchantCandidate, candidate_id)
    merchant = promote_candidate(session, candidate)
    session.flush()
    crawl_merchant(session, merchant)
    session.commit()
    return RedirectResponse(url=f"/merchants/{merchant.id}", status_code=303)


@app.post("/discovery/{candidate_id}/reject")
def discovery_reject(candidate_id: int, session: Session = Depends(get_session)):
    candidate = session.get(MerchantCandidate, candidate_id)
    candidate.status = "rejected"
    session.commit()
    return RedirectResponse(url="/discovery", status_code=303)


@app.get("/recommend", response_class=HTMLResponse)
def recommend_page(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    candidates = build_recommendations(
        session,
        RecommendationRequest(shot_style="modern_58mm", quantity_mode="12-18 oz", bulk_allowed=False, allow_decaf=False),
    )
    return templates.TemplateResponse(
        request,
        "recommendation.html",
        {
            "candidates": candidates,
            "selected": {"shot_style": "modern_58mm", "quantity_mode": "12-18 oz", "bulk_allowed": False, "allow_decaf": False},
        },
    )


@app.post("/recommend", response_class=HTMLResponse)
def recommend_action(
    request: Request,
    shot_style: str = Form("modern_58mm"),
    quantity_mode: str = Form("12-18 oz"),
    bulk_allowed: bool = Form(False),
    allow_decaf: bool = Form(False),
    session: Session = Depends(get_session),
) -> HTMLResponse:
    payload = RecommendationRequest(
        shot_style=shot_style,  # type: ignore[arg-type]
        quantity_mode=quantity_mode,  # type: ignore[arg-type]
        bulk_allowed=bulk_allowed,
        allow_decaf=allow_decaf,
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
