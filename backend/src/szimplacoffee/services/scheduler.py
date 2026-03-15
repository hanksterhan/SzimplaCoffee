"""SC-33: Tier-based crawl scheduler for merchants."""

from __future__ import annotations

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


def get_merchants_due_for_crawl(session: Session) -> list[Merchant]:
    """Return merchants whose last successful crawl is older than their tier threshold.

    Tier D merchants are never included (manual only).
    Merchants with no crawl history are always considered due.
    """
    merchants = session.scalars(
        select(Merchant).where(Merchant.is_active.is_(True))
    ).all()

    now = datetime.now(UTC)
    due: list[Merchant] = []

    for merchant in merchants:
        interval_hours = TIER_INTERVALS.get(merchant.crawl_tier)
        if interval_hours is None:
            # Tier D: manual only
            continue

        last_crawl = _get_last_successful_crawl(session, merchant.id)
        if last_crawl is None:
            # Never crawled — always due
            due.append(merchant)
            continue

        lc = last_crawl if last_crawl.tzinfo else last_crawl.replace(tzinfo=UTC)
        threshold = timedelta(hours=interval_hours)
        if (now - lc) >= threshold:
            due.append(merchant)

    # Sort: overdue first (oldest last-crawl first), then never-crawled
    def sort_key(m: Merchant) -> tuple[int, datetime]:
        lc = _get_last_successful_crawl(session, m.id)
        if lc is None:
            return (0, datetime.min.replace(tzinfo=UTC))
        if lc.tzinfo is None:
            lc = lc.replace(tzinfo=UTC)
        return (1, lc)

    due.sort(key=sort_key)
    return due


def get_crawl_schedule(session: Session) -> list[dict]:
    """Return schedule info for all active merchants."""
    merchants = session.scalars(
        select(Merchant).where(Merchant.is_active.is_(True))
    ).all()

    now = datetime.now(UTC)
    rows = []

    for merchant in merchants:
        interval_hours = TIER_INTERVALS.get(merchant.crawl_tier)
        last_crawl = _get_last_successful_crawl(session, merchant.id)

        if interval_hours is None:
            # Tier D
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
            }
        )

    # Sort: overdue/never first, then approaching, then fresh
    priority = {"overdue": 0, "never_crawled": 0, "approaching": 1, "fresh": 2, "manual": 3}
    rows.sort(key=lambda r: priority.get(r["status"], 9))
    return rows
