import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_client_ip
from app.core.db import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


class CitationClickRequest(BaseModel):
    qa_log_id: int
    episode_id: int
    timestamp: float | None = None


class UserFeedbackRequest(BaseModel):
    qa_log_id: int
    feedback_type: str
    rating: int | None = None
    comment: str | None = None


class ClientEventRequest(BaseModel):
    qa_log_id: int | None = None
    event_name: str
    metadata: dict[str, Any] | None = None


@router.post("/api/citation/click")
def track_citation_click(
    payload: CitationClickRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Track when a user clicks on a cited episode."""
    from app.storage.repository import log_citation_click

    try:
        log_citation_click(
            db,
            qa_log_id=payload.qa_log_id,
            episode_id=payload.episode_id,
            user_ip=get_client_ip(request),
            timestamp=payload.timestamp,
        )
        return {"status": "ok"}
    except Exception as e:
        logger.error("Error logging citation click: %s", e)
        raise HTTPException(status_code=500, detail="Failed to log click") from e


@router.post("/api/feedback")
def submit_feedback(
    payload: UserFeedbackRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Submit user feedback on an answer."""
    from app.storage.repository import log_user_feedback

    if payload.feedback_type not in ["positive", "negative", "neutral"]:
        raise HTTPException(status_code=400, detail="Invalid feedback_type")
    if payload.rating is not None and (payload.rating < 1 or payload.rating > 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    comment = payload.comment
    if comment is not None:
        import re as _re

        comment = _re.sub(r"<[^>]+>", "", comment).strip()[:500] or None

    try:
        log_user_feedback(
            db,
            qa_log_id=payload.qa_log_id,
            feedback_type=payload.feedback_type,
            user_ip=get_client_ip(request),
            rating=payload.rating,
            comment=comment,
        )
        return {"status": "ok"}
    except Exception as e:
        logger.error("Error logging user feedback: %s", e)
        raise HTTPException(status_code=500, detail="Failed to log feedback") from e


@router.post("/api/client-event")
def track_client_event(
    payload: ClientEventRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Track lightweight client-side product events for funnel analysis."""
    from app.storage.repository import log_product_event

    event_name = (payload.event_name or "").strip()[:80]
    if not event_name:
        raise HTTPException(status_code=400, detail="Missing event_name")

    user_ip = get_client_ip(request)

    try:
        log_product_event(
            db,
            event_name=event_name,
            user_ip=user_ip,
            qa_log_id=payload.qa_log_id,
            metadata=payload.metadata or {},
        )
        return {"status": "ok"}
    except Exception as e:
        logger.error(
            "Error logging client event: %s",
            {
                "event_name": event_name,
                "qa_log_id": payload.qa_log_id,
                "user_ip": user_ip,
                "metadata": payload.metadata or {},
                "error": str(e),
            },
        )
        raise HTTPException(status_code=500, detail="Failed to log client event") from e
