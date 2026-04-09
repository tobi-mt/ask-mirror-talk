import re

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_client_ip
from app.api.rate_limit import enforce_rate_limit
from app.core.config import settings
from app.core.db import get_db
from app.qa.guardrails import inspect_question, log_guardrail_block

router = APIRouter()

_PLACEHOLDER_PATTERNS = (
    re.compile(r"^\{\{\s*[a-z0-9_.-]+\s*\}\}$", re.IGNORECASE),
    re.compile(r"^\{\s*[a-z0-9_.-]+\s*\}$", re.IGNORECASE),
    re.compile(r"^\[\s*[a-z0-9_.-]+\s*\]$", re.IGNORECASE),
    re.compile(r"^<\s*[a-z0-9_.-]+\s*>$", re.IGNORECASE),
)


class AskRequest(BaseModel):
    question: str
    context: list[dict] | None = None


def _normalize_incoming_question(raw_question: str) -> str:
    return re.sub(r"\s+", " ", raw_question).strip()


def _looks_like_placeholder_question(question: str) -> bool:
    normalized = question.strip()
    lowered = normalized.lower()
    if lowered in {"{{question}}", "{question}", "[question]", "<question>", "question"}:
        return True
    return any(pattern.fullmatch(normalized) for pattern in _PLACEHOLDER_PATTERNS)


@router.get("/health")
def health():
    """Health check endpoint - returns OK even if database is not ready."""
    return {"status": "ok"}


@router.options("/ask")
def ask_options():
    """Handle CORS preflight for /ask endpoint."""
    return {"status": "ok"}


@router.post("/ask")
def ask(
    payload: AskRequest,
    request: Request,
    db: Session = Depends(get_db),
    bypass_cache: bool = Query(default=False),
):
    ip = get_client_ip(request)
    enforce_rate_limit(ip)

    question = _normalize_incoming_question(payload.question)
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    if _looks_like_placeholder_question(question):
        raise HTTPException(status_code=400, detail="Please send a real question instead of a template placeholder")
    if len(question) > 500:
        raise HTTPException(status_code=400, detail="Question must be 500 characters or fewer")
    if settings.question_guardrails_enabled:
        decision = inspect_question(question)
        if not decision.allowed:
            log_guardrail_block(question=question, user_ip=ip, decision=decision, route="/ask")
            raise HTTPException(status_code=400, detail=decision.message)

    from app.qa.service import answer_question

    if bypass_cache:
        return answer_question(db, question, user_ip=ip, bypass_cache=True)
    return answer_question(db, question, user_ip=ip)


@router.post("/ask/stream")
def ask_stream(
    payload: AskRequest,
    request: Request,
    db: Session = Depends(get_db),
    bypass_cache: bool = Query(default=False),
):
    """Stream an answer using Server-Sent Events (SSE)."""
    ip = get_client_ip(request)
    enforce_rate_limit(ip)

    question = _normalize_incoming_question(payload.question)
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    if _looks_like_placeholder_question(question):
        raise HTTPException(status_code=400, detail="Please send a real question instead of a template placeholder")
    if len(question) > 500:
        raise HTTPException(status_code=400, detail="Question must be 500 characters or fewer")
    if settings.question_guardrails_enabled:
        decision = inspect_question(question)
        if not decision.allowed:
            log_guardrail_block(question=question, user_ip=ip, decision=decision, route="/ask/stream")
            raise HTTPException(status_code=400, detail=decision.message)

    from app.qa.service import answer_question_stream

    stream = (
        answer_question_stream(db, question, user_ip=ip, context=payload.context or [], bypass_cache=True)
        if bypass_cache
        else answer_question_stream(db, question, user_ip=ip, context=payload.context or [])
    )

    return StreamingResponse(
        stream,
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
