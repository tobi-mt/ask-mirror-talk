import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.runtime import is_db_initialized
from app.core.config import settings
from app.core.db import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/status")
def status(db: Session = Depends(get_db)):
    """Get ingestion and system status."""
    if not is_db_initialized():
        return {
            "status": "initializing",
            "db_ready": False,
            "message": "Database is still initializing",
        }

    try:
        from app.storage.models import IngestRun

        episode_count = db.scalar(text("SELECT COUNT(*) FROM episodes"))
        chunk_count = db.scalar(text("SELECT COUNT(*) FROM chunks"))
        latest_run = db.query(IngestRun).order_by(IngestRun.started_at.desc()).first()

        return {
            "status": "ok",
            "db_ready": True,
            "episodes": episode_count or 0,
            "chunks": chunk_count or 0,
            "ready": (chunk_count or 0) > 0,
            "model": settings.answer_generation_model,
            "followup_model": settings.answer_followup_model,
            "notification_generation_model": settings.notification_generation_model,
            "embedding_provider": settings.embedding_provider,
            "embedding_model": settings.embedding_model,
            "max_tokens": settings.answer_max_tokens,
            "temperature": settings.answer_temperature,
            "cache_similarity_threshold": settings.cache_similarity_threshold,
            "cache_ttl_seconds": settings.cache_ttl_seconds,
            "latest_ingest_run": {
                "status": latest_run.status if latest_run else None,
                "started_at": latest_run.started_at.isoformat() if latest_run and latest_run.started_at else None,
                "finished_at": latest_run.finished_at.isoformat() if latest_run and latest_run.finished_at else None,
                "message": latest_run.message if latest_run else None,
            }
            if latest_run
            else None,
        }
    except Exception as e:
        logger.error("Error getting status: %s", e)
        return {
            "status": "error",
            "db_ready": False,
            "message": str(e),
        }
