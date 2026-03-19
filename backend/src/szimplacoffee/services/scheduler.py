"""SC-33 / SC-95: tier-based crawl scheduler for merchants."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import CrawlRun, Merchant

# Tier → crawl interval in hours (Tier D = manual only, never auto-scheduled)
TIER_INTERVALS: dict[str, int | None] = {
    "A": 6,
    "B": 24,
    "C": 7 * 24,  # 168 hours
    "D": None,    # manual only
}

# SC-95: keep routine automatic crawl work conservative.
DEFAULT_SCHEDULED_CRAWL_BATCH_SIZE = 1
RECENT_CRAWL_SIGNAL_WINDOW = 5


def _get_last_successful_crawl(session: Session, merchant_id: int) -> datetime | None:
    """Return the started_at time of the most recent completed crawl run."""
    run = session.scalar(
        select(CrawlRun)
        .where(
            CrawlRun.merchant_id == merchant_id,
            CrawlRun.status == "completed",
        )
        .order_by(CrawlRun.started_at.desc())
        .limit(1)
    )
    return run.started_at if run else None


def _get_recent_runs(
    session: Session,
    merchant_ids: Iterable[int],
    *,
    limit_per_merchant: int = RECENT_CRAWL_SIGNAL_WINDOW,
) -> dict[int, list[CrawlRun]]:
    ids = list(merchant_ids)
    if not ids:
        return {}

    runs = session.scalars(
        select(CrawlRun)
        .where(CrawlRun.merchant_id.in_(ids))
        .order_by(CrawlRun.merchant_id.asc(), CrawlRun.started_at.desc())
    ).all()

    grouped: dict[int, list[CrawlRun]] = {merchant_id: [] for merchant_id in ids}
    for run in runs:
        bucket = grouped.setdefault(run.merchant_id, [])
        if len(bucket) < limit_per_merchant:
            bucket.append(run)
    return grouped


def _sort_due_merchants(session: Session, merchants: list[Merchant]) -> list[Merchant]:
    # Sort: overdue first (oldest last-crawl first), then never-crawled.
    def sort_key(m: Merchant) -> tuple[int, datetime]:
        lc = _get_last_successful_crawl(session, m.id)
        if lc is None:
            return (0, datetime.min.replace(tzinfo=UTC))
        if lc.tzinfo is None:
            lc = lc.replace(tzinfo=UTC)
        return (1, lc)

    ordered = list(merchants)
    ordered.sort(key=sort_key)
    return ordered


def get_merchants_due_for_crawl(session: Session, *, limit: int | None = None) -> list[Merchant]:
    """Return merchants whose last successful crawl is older than their tier threshold.

    Tier D merchants are never included (manual only).
    Merchants with no crawl history are always considered due.
    When ``limit`` is set, return only the oldest/highest-priority due merchants.
    """
    merchants = session.scalars(
        select(Merchant).where(Merchant.is_active.is_(True))
    ).all()

    now = datetime.now(UTC)
    due: list[Merchant] = []

    for merchant in merchants:
        interval_hours = TIER_INTERVALS.get(merchant.crawl_tier)
        if interval_hours is None:
            continue

        last_crawl = _get_last_successful_crawl(session, merchant.id)
        if last_crawl is None:
            due.append(merchant)
            continue

        lc = last_crawl if last_crawl.tzinfo else last_crawl.replace(tzinfo=UTC)
        threshold = timedelta(hours=interval_hours)
        if (now - lc) >= threshold:
            due.append(merchant)

    ordered = _sort_due_merchants(session, due)
    if limit is not None:
        return ordered[:limit]
    return ordered


def get_crawl_schedule(session: Session) -> list[dict]:
    """Return schedule info plus recent crawl-reliability signals for all active merchants."""
    merchants = session.scalars(
        select(Merchant).where(Merchant.is_active.is_(True))
    ).all()

    now = datetime.now(UTC)
    rows = []
    recent_runs_by_merchant = _get_recent_runs(session, [merchant.id for merchant in merchants])

    for merchant in merchants:
        interval_hours = TIER_INTERVALS.get(merchant.crawl_tier)
        last_crawl = _get_last_successful_crawl(session, merchant.id)
        recent_runs = recent_runs_by_merchant.get(merchant.id, [])

        if interval_hours is None:
            next_due = None
            is_due = False
            status = "manual"
        elif last_crawl is None:
            next_due = None
            is_due = True
            status = "never_crawled"
        else:
            lc = last_crawl if last_crawl.tzinfo else last_crawl.replace(tzinfo=UTC)
            next_due = lc + timedelta(hours=interval_hours)
            is_due = now >= next_due
            age_hours = (now - lc).total_seconds() / 3600
            overdue_pct = age_hours / interval_hours if interval_hours else 0
            if is_due:
                status = "overdue"
            elif overdue_pct >= 0.8:
                status = "approaching"
            else:
                status = "fresh"

        completed_runs = [run for run in recent_runs if run.status == "completed"]
        failed_runs = [run for run in recent_runs if run.status == "failed"]
        success_rate = len(completed_runs) / len(recent_runs) if recent_runs else None
        latest_run = recent_runs[0] if recent_runs else None
        last_completed_quality = completed_runs[0].crawl_quality_score if completed_runs else None

        rows.append(
            {
                "merchant_id": merchant.id,
                "name": merchant.name,
                "crawl_tier": merchant.crawl_tier,
                "interval_hours": interval_hours,
                "last_crawl_at": last_crawl.isoformat() if last_crawl else None,
                "next_due_at": next_due.isoformat() if next_due else None,
                "is_due": is_due,
                "status": status,
                "recent_run_count": len(recent_runs),
                "recent_success_rate": round(success_rate, 4) if success_rate is not None else None,
                "recent_failure_count": len(failed_runs),
                "last_completed_crawl_quality_score": round(last_completed_quality, 4)
                if last_completed_quality is not None
                else None,
                "latest_run_status": latest_run.status if latest_run else None,
                "latest_error_summary": latest_run.error_summary if latest_run and latest_run.error_summary else None,
            }
        )

    priority = {"overdue": 0, "never_crawled": 0, "approaching": 1, "fresh": 2, "manual": 3}
    rows.sort(key=lambda r: priority.get(r["status"], 9))
    return rows
