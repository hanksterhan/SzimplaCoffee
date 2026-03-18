"""DE1 Visualizer bridge API — status and toggle endpoints (SC-79)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import DE1_AUTO_MATCH, VISUALIZER_USERNAME
from ..db import get_session
from ..models import De1BridgeState

router = APIRouter(prefix="/de1", tags=["de1"])


class De1StatusResponse(BaseModel):
    enabled: bool
    auto_match: bool
    last_poll_at: str | None
    shots_imported: int
    visualizer_username: str


class ToggleRequest(BaseModel):
    auto_match: bool


@router.get("/status", response_model=De1StatusResponse)
def get_de1_status(db: Session = Depends(get_session)) -> De1StatusResponse:
    state = db.scalar(select(De1BridgeState).limit(1))
    return De1StatusResponse(
        enabled=bool(VISUALIZER_USERNAME),
        auto_match=state.auto_match if state else DE1_AUTO_MATCH,
        last_poll_at=state.last_poll_at.isoformat() if state and state.last_poll_at else None,
        shots_imported=state.shots_imported if state else 0,
        visualizer_username=VISUALIZER_USERNAME,
    )


@router.post("/toggle", response_model=De1StatusResponse)
def toggle_de1(body: ToggleRequest, db: Session = Depends(get_session)) -> De1StatusResponse:
    state = db.scalar(select(De1BridgeState).limit(1))
    if state is None:
        state = De1BridgeState()
        db.add(state)
        db.flush()
    state.auto_match = body.auto_match
    db.commit()
    return De1StatusResponse(
        enabled=bool(VISUALIZER_USERNAME),
        auto_match=state.auto_match,
        last_poll_at=state.last_poll_at.isoformat() if state.last_poll_at else None,
        shots_imported=state.shots_imported or 0,
        visualizer_username=VISUALIZER_USERNAME,
    )
