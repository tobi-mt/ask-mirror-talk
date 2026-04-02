from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_client_ip
from app.api.rate_limit import enforce_rate_limit
from app.core.db import get_db

router = APIRouter()


class AskRequest(BaseModel):
    question: str
    context: list[dict] | None = None


@router.get("/health")
def health():
    """Health check endpoint - returns OK even if database is not ready."""
    return {"status": "ok"}


@router.options("/ask")
def ask_options():
    """Handle CORS preflight for /ask endpoint."""
    return {"status": "ok"}


@router.post("/ask")
def ask(payload: AskRequest, request: Request, db: Session = Depends(get_db)):
    ip = get_client_ip(request)
    enforce_rate_limit(ip)

    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    if len(question) > 500:
        raise HTTPException(status_code=400, detail="Question must be 500 characters or fewer")

    from app.qa.service import answer_question

    return answer_question(db, question, user_ip=ip)


@router.post("/ask/stream")
def ask_stream(payload: AskRequest, request: Request, db: Session = Depends(get_db)):
    """Stream an answer using Server-Sent Events (SSE)."""
    ip = get_client_ip(request)
    enforce_rate_limit(ip)

    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    if len(question) > 500:
        raise HTTPException(status_code=400, detail="Question must be 500 characters or fewer")

    from app.qa.service import answer_question_stream

    return StreamingResponse(
        answer_question_stream(db, question, user_ip=ip, context=payload.context or []),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/api/cache/stats")
def get_cache_stats():
    """Return answer cache statistics."""
    from app.qa.cache import get_answer_cache

    return get_answer_cache().stats()
