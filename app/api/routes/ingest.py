from fastapi import APIRouter, BackgroundTasks, Depends, Request
from fastapi.security import HTTPBasicCredentials

from app.api.auth import admin_auth, security
from app.core.db import get_session_local

router = APIRouter()


def _run_ingestion_bg() -> None:
    from app.ingestion.pipeline import run_ingestion

    db = get_session_local()()
    try:
        run_ingestion(db)
    finally:
        db.close()


@router.post("/ingest")
def ingest(
    background_tasks: BackgroundTasks,
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security),
):
    admin_auth(credentials, request)
    background_tasks.add_task(_run_ingestion_bg)
    return {"status": "accepted"}
