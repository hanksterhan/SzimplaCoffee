"""SC-33: Crawl scheduler API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import get_session, session_scope
from ..models import CrawlRun, Merchant
from ..services.scheduler import get_crawl_schedule, get_merchants_due_for_crawl
from ..services.crawlers import crawl_merchant

router = APIRouter(prefix="/crawl", tags=["crawl"])


class CrawlScheduleItem(BaseModel):
    merchant_id: int
    name: str
    crawl_tier: str
    interval_hours: int | None
    last_crawl_at: str | None
    next_due_at: str | None
    is_due: bool
    status: str


class RunDueResponse(BaseModel):
    triggered: int
    merchant_ids: list[int]


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


def _enqueue_crawl(session: Session, merchant: Merchant) -> tuple[CrawlRun, bool]:
    from sqlalchemy import select

    latest_run = session.scalar(
        select(CrawlRun)
        .where(CrawlRun.merchant_id == merchant.id)
        .order_by(CrawlRun.started_at.desc())
        .limit(1)
    )
    if latest_run and latest_run.status in {"queued", "started"}:
        return latest_run, False
    run = CrawlRun(
        merchant_id=merchant.id,
        run_type="scheduled_refresh",
        adapter_name=merchant.platform_type,
        status="queued",
        confidence=0.0,
        records_written=0,
    )
    session.add(run)
    session.flush()
    return run, True


@router.get("/due", response_model=list[CrawlScheduleItem])
def get_due_merchants(db: Session = Depends(get_session)) -> list[CrawlScheduleItem]:
    """Return merchants that are currently due for a crawl based on their tier."""
    due = get_merchants_due_for_crawl(db)
    schedule = get_crawl_schedule(db)
    # Filter schedule to only due merchants
    due_ids = {m.id for m in due}
    return [CrawlScheduleItem(**item) for item in schedule if item["merchant_id"] in due_ids]


@router.get("/schedule", response_model=list[CrawlScheduleItem])
def get_schedule(db: Session = Depends(get_session)) -> list[CrawlScheduleItem]:
    """Return full crawl schedule for all active merchants."""
    schedule = get_crawl_schedule(db)
    return [CrawlScheduleItem(**item) for item in schedule]


@router.post("/run-due", response_model=RunDueResponse)
def run_due_merchants(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_session),
) -> RunDueResponse:
    """Trigger crawls for all merchants that are due based on their tier schedule."""
    due_merchants = get_merchants_due_for_crawl(db)
    triggered_ids: list[int] = []

    for merchant in due_merchants:
        run, should_schedule = _enqueue_crawl(db, merchant)
        if should_schedule:
            triggered_ids.append(merchant.id)
            background_tasks.add_task(_background_crawl, merchant.id, run.id)

    db.commit()
    return RunDueResponse(triggered=len(triggered_ids), merchant_ids=triggered_ids)
