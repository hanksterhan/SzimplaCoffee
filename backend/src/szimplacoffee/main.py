from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import BackgroundTasks, Depends, FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session

from .api import api_router
from .bootstrap import bootstrap_if_empty, init_db
from .db import get_session, session_scope
from .models import CrawlRun, Merchant, MerchantCandidate
from .services.crawlers import crawl_merchant
from .services.discovery import promote_candidate, run_discovery
from .services.platforms import detect_platform, recommended_crawl_tier


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    with session_scope() as session:
        bootstrap_if_empty(session)
    yield


app = FastAPI(title="SzimplaCoffee", lifespan=lifespan)

# CORS for development (Vite dev server on :5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the API router
app.include_router(api_router)


# ---------------------------------------------------------------------------
# Background crawl helpers (preserved from Jinja era)
# ---------------------------------------------------------------------------

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


def _latest_crawl_run(session: Session, merchant_id: int) -> CrawlRun | None:
    return session.scalar(
        select(CrawlRun)
        .where(CrawlRun.merchant_id == merchant_id)
        .order_by(CrawlRun.started_at.desc())
        .limit(1)
    )


# ---------------------------------------------------------------------------
# Legacy HTML form endpoints — now thin wrappers that POST to the API layer
# These keep curl/form-submit compatibility while the React SPA is the UI.
# ---------------------------------------------------------------------------

@app.post("/merchants/new")
def create_merchant_form(
    background_tasks: BackgroundTasks,
    url: str = Form(...),
    trust_tier: str = Form("candidate"),
    session: Session = Depends(get_session),
):
    """Form-compatible endpoint for adding a merchant (used by scripts/CLI)."""
    detection = detect_platform(url)
    existing = session.scalar(select(Merchant).where(Merchant.canonical_domain == detection.domain))
    if existing:
        run, should_schedule = _enqueue_crawl(session, existing)
        session.commit()
        if should_schedule:
            background_tasks.add_task(_background_crawl, existing.id, run.id)
        return {"merchant_id": existing.id, "status": "existing"}

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
    return {"merchant_id": merchant.id, "status": "created"}


@app.post("/merchants/{merchant_id}/crawl-form")
def crawl_merchant_form(
    merchant_id: int,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    """Form-compatible endpoint to trigger a crawl."""
    merchant = session.get(Merchant, merchant_id)
    run, should_schedule = _enqueue_crawl(session, merchant)
    session.commit()
    if should_schedule:
        background_tasks.add_task(_background_crawl, merchant.id, run.id)
    return {"merchant_id": merchant_id, "run_id": run.id, "scheduled": should_schedule}


@app.post("/discovery/run-form")
def discovery_run_form(session: Session = Depends(get_session)):
    """Form-compatible endpoint to trigger discovery."""
    run_discovery(session)
    session.commit()
    return {"status": "ok"}


@app.post("/discovery/{candidate_id}/promote-form")
def discovery_promote_form(candidate_id: int, session: Session = Depends(get_session)):
    """Form-compatible endpoint to promote a candidate."""
    candidate = session.get(MerchantCandidate, candidate_id)
    merchant = promote_candidate(session, candidate)
    session.flush()
    crawl_merchant(session, merchant)
    session.commit()
    return {"merchant_id": merchant.id}


@app.post("/discovery/{candidate_id}/reject-form")
def discovery_reject_form(candidate_id: int, session: Session = Depends(get_session)):
    """Form-compatible endpoint to reject a candidate."""
    candidate = session.get(MerchantCandidate, candidate_id)
    candidate.status = "rejected"
    session.commit()
    return {"status": "rejected", "candidate_id": candidate_id}


# ---------------------------------------------------------------------------
# Production SPA serving — only active when frontend/dist exists
# ---------------------------------------------------------------------------

FRONTEND_DIST = Path(__file__).resolve().parents[3] / "frontend" / "dist"

if FRONTEND_DIST.exists():
    # Serve compiled JS/CSS assets
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="static-assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str) -> FileResponse:
        """SPA catch-all: serve index.html for all non-API routes."""
        if full_path.startswith("api/"):
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="API route not found")
        # Serve an exact file if it exists (favicon, robots.txt, etc.)
        file_path = FRONTEND_DIST / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        # Fall back to index.html for React Router
        return FileResponse(str(FRONTEND_DIST / "index.html"))
