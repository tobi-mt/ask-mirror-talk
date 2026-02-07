from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse
import ipaddress
import secrets
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
import time

from app.core.config import settings
from app.core.db import get_db
from app.core.logging import setup_logging
from app.qa.service import answer_question
from app.ingestion.pipeline import run_ingestion

setup_logging()

app = FastAPI(title=settings.app_name)

_rate_limit_bucket: dict[str, list[float]] = {}
_security = HTTPBasic()


class AskRequest(BaseModel):
    question: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask")
def ask(payload: AskRequest, request: Request, db: Session = Depends(get_db)):
    _enforce_rate_limit(request.client.host)

    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    response = answer_question(db, payload.question.strip(), user_ip=request.client.host)
    return response


@app.post("/ingest")
def ingest(db: Session = Depends(get_db)):
    return run_ingestion(db)


def _enforce_rate_limit(ip: str):
    now = time.time()
    window = 60
    bucket = _rate_limit_bucket.get(ip, [])
    bucket = [t for t in bucket if now - t < window]
    if len(bucket) >= settings.rate_limit_per_minute:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    bucket.append(now)
    _rate_limit_bucket[ip] = bucket


def _ip_allowed(ip: str) -> bool:
    if not settings.admin_ip_allowlist:
        return True
    ranges = [r.strip() for r in settings.admin_ip_allowlist.split(",") if r.strip()]
    if not ranges:
        return True
    try:
        ip_addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    for entry in ranges:
        try:
            if ip_addr in ipaddress.ip_network(entry, strict=False):
                return True
        except ValueError:
            if entry == ip:
                return True
    return False


def _admin_auth(credentials: HTTPBasicCredentials | None, request: Request):
    if not settings.admin_enabled:
        raise HTTPException(status_code=404, detail="Not found")
    if not _ip_allowed(request.client.host):
        raise HTTPException(status_code=403, detail="Forbidden")
    if credentials is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    is_user = secrets.compare_digest(credentials.username, settings.admin_user)
    is_pass = secrets.compare_digest(credentials.password, settings.admin_password)
    if not (is_user and is_pass):
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(_security),
    db: Session = Depends(get_db),
):
    _admin_auth(credentials, request)

    runs = db.execute(
        text(
            "SELECT id, started_at, finished_at, status, message "
            "FROM ingest_runs ORDER BY started_at DESC LIMIT 20"
        )
    ).all()
    logs = db.execute(
        text(
            "SELECT id, created_at, question, latency_ms, user_ip "
            "FROM qa_logs ORDER BY created_at DESC LIMIT 20"
        )
    ).all()

    runs_rows = "".join(
        f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2] or ''}</td><td>{r[3]}</td><td>{r[4]}</td></tr>"
        for r in runs
    )
    logs_rows = "".join(
        f"<tr><td>{l[0]}</td><td>{l[1]}</td><td>{l[2][:120]}</td><td>{l[3]}</td><td>{l[4]}</td></tr>"
        for l in logs
    )

    html = f"""
    <html>
      <head>
        <title>Ask Mirror Talk Admin</title>
        <style>
          body {{ font-family: Arial, sans-serif; margin: 24px; }}
          table {{ width: 100%; border-collapse: collapse; margin-bottom: 24px; }}
          th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
          th {{ background: #f5f5f5; }}
          h2 {{ margin-top: 0; }}
        </style>
      </head>
      <body>
        <h1>Ask Mirror Talk Admin</h1>
        <h2>Recent Ingestion Runs</h2>
        <table>
          <thead><tr><th>ID</th><th>Started</th><th>Finished</th><th>Status</th><th>Message</th></tr></thead>
          <tbody>{runs_rows}</tbody>
        </table>
        <h2>Recent Questions</h2>
        <table>
          <thead><tr><th>ID</th><th>Time</th><th>Question</th><th>Latency (ms)</th><th>IP</th></tr></thead>
          <tbody>{logs_rows}</tbody>
        </table>
      </body>
    </html>
    """
    return HTMLResponse(content=html)
