from fastapi import FastAPI, Depends, Request, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse
import ipaddress
import secrets
import logging
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
import time

from app.core.config import settings
from app.core.db import get_db, get_session_local
from app.core.logging import setup_logging
# Lazy imports to speed up startup:
# - app.qa.service (loads ML models)
# - app.ingestion.pipeline (heavy dependencies)
# - init_db (creates DB connection)

# Setup logging BEFORE any other operations
setup_logging()
logger = logging.getLogger(__name__)

# Log startup immediately
logger.info("="*60)
logger.info("STARTING ASK MIRROR TALK API")
logger.info("="*60)

app = FastAPI(title=settings.app_name)

logger.info("✓ FastAPI app created")

# Track if DB is initialized
_db_initialized = False


async def _init_db_background():
    """Initialize database in background without blocking startup."""
    global _db_initialized
    import asyncio
    await asyncio.sleep(2)  # Give app time to start and pass healthcheck
    
    try:
        # Lazy import to avoid loading at startup
        from app.core.db import init_db
        init_db()
        _db_initialized = True
        logger.info("✓ Background database initialization complete")
    except Exception as e:
        logger.error(f"✗ Background database initialization failed: {e}", exc_info=True)
        logger.warning("⚠️  Some endpoints may not work until database is accessible")


# Configure CORS - allows your WordPress site to call the API
# For maximum compatibility across ALL browsers (Safari, Chrome, Firefox, mobile browsers)
# We use the most permissive CORS configuration that works universally
if settings.allowed_origins:
    origins = [origin.strip() for origin in settings.allowed_origins.split(",") if origin.strip()]
    # Add both http and https variants, with and without www
    expanded_origins = []
    for origin in origins:
        expanded_origins.append(origin)
        # Add www variant if not present
        if "://www." not in origin and "://" in origin:
            expanded_origins.append(origin.replace("://", "://www."))
        # Add non-www variant if www is present
        if "://www." in origin:
            expanded_origins.append(origin.replace("://www.", "://"))
    origins = expanded_origins
    logger.info(f"CORS enabled for specific origins: {origins}")
else:
    # Default: Allow all origins - most permissive for development
    origins = ["*"]
    logger.warning("CORS enabled for ALL origins (*). Set ALLOWED_ORIGINS in production for security.")

# Always use allow_credentials=False for maximum browser compatibility
# When credentials=False, browsers don't send cookies/auth headers, avoiding CORS issues
allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicit methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers
)
logger.info(f"✓ CORS middleware configured (origins: {len(origins)}, credentials: {allow_credentials})")

_rate_limit_bucket: dict[str, list[float]] = {}
_security = HTTPBasic()


class AskRequest(BaseModel):
    question: str


@app.get("/health")
def health():
    """Health check endpoint - returns OK even if database is not ready."""
    logger.info("Health check called")
    return {"status": "ok"}


@app.options("/ask")
def ask_options():
    """Handle CORS preflight for /ask endpoint."""
    return {"status": "ok"}


@app.on_event("startup")
async def on_startup():
    """Initialize database on application startup."""
    logger.info("="*60)
    logger.info("STARTUP EVENT TRIGGERED")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"App name: {settings.app_name}")
    logger.info("="*60)
    
    # Skip DB initialization during healthcheck to start faster
    # DB will be initialized on first request if needed
    logger.info("✓ Application startup complete (DB init deferred)")
    
    # Initialize DB in background to not block startup
    import asyncio
    logger.info("Starting background DB initialization task...")
    asyncio.create_task(_init_db_background())


@app.post("/ask")
def ask(payload: AskRequest, request: Request, db: Session = Depends(get_db)):
    _enforce_rate_limit(request.client.host)

    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # Lazy import to avoid loading ML models at startup
    from app.qa.service import answer_question
    
    response = answer_question(db, payload.question.strip(), user_ip=request.client.host)
    return response


def _run_ingestion_bg() -> None:
    # Lazy import to avoid loading heavy dependencies at startup
    from app.ingestion.pipeline import run_ingestion
    
    db = get_session_local()()
    try:
        run_ingestion(db)
    finally:
        db.close()


@app.post("/ingest")
def ingest(background_tasks: BackgroundTasks):
    background_tasks.add_task(_run_ingestion_bg)
    return {"status": "accepted"}


@app.get("/status")
def status(db: Session = Depends(get_db)):
    """Get ingestion and system status."""
    global _db_initialized
    
    if not _db_initialized:
        return {
            "status": "initializing",
            "db_ready": False,
            "message": "Database is still initializing"
        }
    
    try:
        from sqlalchemy import text, func
        from app.storage.models import Episode, Chunk, IngestRun
        
        # Get counts
        episode_count = db.scalar(text("SELECT COUNT(*) FROM episodes"))
        chunk_count = db.scalar(text("SELECT COUNT(*) FROM chunks"))
        
        # Get latest ingest run
        latest_run = db.query(IngestRun).order_by(IngestRun.started_at.desc()).first()
        
        return {
            "status": "ok",
            "db_ready": True,
            "episodes": episode_count or 0,
            "chunks": chunk_count or 0,
            "ready": (chunk_count or 0) > 0,
            "latest_ingest_run": {
                "status": latest_run.status if latest_run else None,
                "started_at": latest_run.started_at.isoformat() if latest_run and latest_run.started_at else None,
                "finished_at": latest_run.finished_at.isoformat() if latest_run and latest_run.finished_at else None,
                "message": latest_run.message if latest_run else None,
            } if latest_run else None,
        }
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return {
            "status": "error",
            "db_ready": False,
            "message": str(e)
        }


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
