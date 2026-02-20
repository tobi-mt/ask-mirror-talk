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


class CitationClickRequest(BaseModel):
    qa_log_id: int
    episode_id: int
    timestamp: float | None = None


class UserFeedbackRequest(BaseModel):
    qa_log_id: int
    feedback_type: str  # 'positive', 'negative', 'neutral'
    rating: int | None = None  # 1-5 stars (optional)
    comment: str | None = None


@app.post("/api/citation/click")
def track_citation_click(
    payload: CitationClickRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Track when a user clicks on a cited episode"""
    from app.storage.repository import log_citation_click
    
    try:
        log_citation_click(
            db,
            qa_log_id=payload.qa_log_id,
            episode_id=payload.episode_id,
            user_ip=request.client.host,
            timestamp=payload.timestamp
        )
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error logging citation click: {e}")
        raise HTTPException(status_code=500, detail="Failed to log click")


@app.post("/api/feedback")
def submit_feedback(
    payload: UserFeedbackRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Submit user feedback on an answer"""
    from app.storage.repository import log_user_feedback
    
    # Validate feedback type
    if payload.feedback_type not in ['positive', 'negative', 'neutral']:
        raise HTTPException(status_code=400, detail="Invalid feedback_type")
    
    # Validate rating if provided
    if payload.rating is not None and (payload.rating < 1 or payload.rating > 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    try:
        log_user_feedback(
            db,
            qa_log_id=payload.qa_log_id,
            feedback_type=payload.feedback_type,
            user_ip=request.client.host,
            rating=payload.rating,
            comment=payload.comment
        )
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error logging user feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to log feedback")


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


@app.get("/api/analytics/summary")
def get_analytics_summary(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get analytics summary for the last N days"""
    from datetime import datetime, timedelta
    
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Total questions
        total_questions = db.execute(
            text("SELECT COUNT(*) FROM qa_logs WHERE created_at >= :cutoff"),
            {"cutoff": cutoff}
        ).scalar()
        
        # Unique users
        unique_users = db.execute(
            text("SELECT COUNT(DISTINCT user_ip) FROM qa_logs WHERE created_at >= :cutoff"),
            {"cutoff": cutoff}
        ).scalar()
        
        # Average latency
        avg_latency = db.execute(
            text("SELECT AVG(latency_ms) FROM qa_logs WHERE created_at >= :cutoff"),
            {"cutoff": cutoff}
        ).scalar()
        
        # Top questions
        top_questions = db.execute(
            text("""
                SELECT question, COUNT(*) as count 
                FROM qa_logs 
                WHERE created_at >= :cutoff
                GROUP BY question 
                ORDER BY count DESC 
                LIMIT 10
            """),
            {"cutoff": cutoff}
        ).fetchall()
        
        # Most cited episodes
        most_cited = db.execute(
            text("""
                SELECT 
                    e.id,
                    e.title,
                    COUNT(*) as citation_count
                FROM qa_logs q
                CROSS JOIN LATERAL UNNEST(STRING_TO_ARRAY(q.episode_ids, ',')) AS episode_id
                JOIN episodes e ON e.id = episode_id::int
                WHERE q.created_at >= :cutoff
                GROUP BY e.id, e.title
                ORDER BY citation_count DESC
                LIMIT 10
            """),
            {"cutoff": cutoff}
        ).fetchall()
        
        # Citation click-through rate (if clicks exist)
        try:
            total_citations = db.execute(
                text("""
                    SELECT COUNT(*)
                    FROM qa_logs q
                    CROSS JOIN LATERAL UNNEST(STRING_TO_ARRAY(q.episode_ids, ',')) AS episode_id
                    WHERE q.created_at >= :cutoff
                """),
                {"cutoff": cutoff}
            ).scalar()
            
            total_clicks = db.execute(
                text("SELECT COUNT(*) FROM citation_clicks WHERE clicked_at >= :cutoff"),
                {"cutoff": cutoff}
            ).scalar()
            
            ctr = (total_clicks / total_citations * 100) if total_citations > 0 else 0
        except:
            ctr = None  # Table might not exist yet
        
        return {
            "period_days": days,
            "total_questions": total_questions or 0,
            "unique_users": unique_users or 0,
            "avg_latency_ms": round(avg_latency, 2) if avg_latency else 0,
            "citation_ctr_percent": round(ctr, 2) if ctr is not None else None,
            "top_questions": [{"question": q[0], "count": q[1]} for q in top_questions],
            "most_cited_episodes": [
                {"id": e[0], "title": e[1], "citations": e[2]} 
                for e in most_cited
            ],
        }
    except Exception as e:
        logger.error(f"Error getting analytics summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/episodes")
def get_episode_analytics(db: Session = Depends(get_db)):
    """Get detailed episode analytics"""
    try:
        # Episodes with citation counts and click counts
        results = db.execute(
            text("""
                WITH episode_citations AS (
                    SELECT 
                        e.id,
                        e.title,
                        e.published_at,
                        COUNT(DISTINCT q.id) as total_citations
                    FROM episodes e
                    LEFT JOIN (
                        SELECT id, UNNEST(STRING_TO_ARRAY(episode_ids, ','))::int as episode_id
                        FROM qa_logs
                    ) q ON q.episode_id = e.id
                    GROUP BY e.id, e.title, e.published_at
                ),
                episode_clicks AS (
                    SELECT 
                        episode_id,
                        COUNT(*) as total_clicks
                    FROM citation_clicks
                    GROUP BY episode_id
                )
                SELECT 
                    ec.id,
                    ec.title,
                    ec.published_at,
                    ec.total_citations,
                    COALESCE(eck.total_clicks, 0) as total_clicks,
                    CASE 
                        WHEN ec.total_citations > 0 THEN 
                            ROUND((COALESCE(eck.total_clicks, 0)::float / ec.total_citations * 100), 2)
                        ELSE 0 
                    END as ctr_percent
                FROM episode_citations ec
                LEFT JOIN episode_clicks eck ON eck.episode_id = ec.id
                ORDER BY ec.total_citations DESC
                LIMIT 50
            """)
        ).fetchall()
        
        return {
            "episodes": [
                {
                    "id": r[0],
                    "title": r[1],
                    "published_at": r[2].isoformat() if r[2] else None,
                    "citations": r[3],
                    "clicks": r[4],
                    "ctr_percent": r[5]
                }
                for r in results
            ]
        }
    except Exception as e:
        logger.error(f"Error getting episode analytics: {e}")
        # If citation_clicks table doesn't exist yet, return simplified version
        try:
            results = db.execute(
                text("""
                    SELECT 
                        e.id,
                        e.title,
                        e.published_at,
                        COUNT(DISTINCT q.id) as total_citations
                    FROM episodes e
                    LEFT JOIN (
                        SELECT id, UNNEST(STRING_TO_ARRAY(episode_ids, ','))::int as episode_id
                        FROM qa_logs
                    ) q ON q.episode_id = e.id
                    GROUP BY e.id, e.title, e.published_at
                    ORDER BY total_citations DESC
                    LIMIT 50
                """)
            ).fetchall()
            
            return {
                "episodes": [
                    {
                        "id": r[0],
                        "title": r[1],
                        "published_at": r[2].isoformat() if r[2] else None,
                        "citations": r[3],
                        "clicks": None,
                        "ctr_percent": None
                    }
                    for r in results
                ]
            }
        except Exception as e2:
            logger.error(f"Error getting simplified episode analytics: {e2}")
            raise HTTPException(status_code=500, detail=str(e2))


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

    # Get analytics summary (7 days)
    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() - timedelta(days=7)
    
    # Summary stats
    total_questions = db.execute(
        text("SELECT COUNT(*) FROM qa_logs WHERE created_at >= :cutoff"),
        {"cutoff": cutoff}
    ).scalar() or 0
    
    unique_users = db.execute(
        text("SELECT COUNT(DISTINCT user_ip) FROM qa_logs WHERE created_at >= :cutoff"),
        {"cutoff": cutoff}
    ).scalar() or 0
    
    avg_latency = db.execute(
        text("SELECT AVG(latency_ms) FROM qa_logs WHERE created_at >= :cutoff"),
        {"cutoff": cutoff}
    ).scalar() or 0
    
    # Top cited episodes
    top_episodes = db.execute(
        text("""
            SELECT 
                e.id,
                e.title,
                COUNT(*) as citation_count
            FROM qa_logs q
            CROSS JOIN LATERAL UNNEST(STRING_TO_ARRAY(q.episode_ids, ',')) AS episode_id
            JOIN episodes e ON e.id = episode_id::int
            WHERE q.created_at >= :cutoff
            GROUP BY e.id, e.title
            ORDER BY citation_count DESC
            LIMIT 10
        """),
        {"cutoff": cutoff}
    ).fetchall()
    
    # Recent activity
    runs = db.execute(
        text(
            "SELECT id, started_at, finished_at, status, message "
            "FROM ingest_runs ORDER BY started_at DESC LIMIT 10"
        )
    ).all()
    
    logs = db.execute(
        text(
            "SELECT id, created_at, question, latency_ms, user_ip "
            "FROM qa_logs ORDER BY created_at DESC LIMIT 15"
        )
    ).all()

    runs_rows = "".join(
        f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2] or ''}</td><td>{r[3]}</td><td>{r[4][:100]}</td></tr>"
        for r in runs
    )
    logs_rows = "".join(
        f"<tr><td>{l[0]}</td><td>{l[1]}</td><td>{l[2][:100]}</td><td>{l[3]}</td><td>{l[4]}</td></tr>"
        for l in logs
    )
    
    top_episodes_rows = "".join(
        f"<tr><td>{e[0]}</td><td>{e[1][:100]}</td><td>{e[2]}</td></tr>"
        for e in top_episodes
    )

    html = f"""
    <html>
      <head>
        <title>Ask Mirror Talk Admin</title>
        <style>
          body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; 
                 margin: 0; padding: 24px; background: #f5f5f5; }}
          .container {{ max-width: 1400px; margin: 0 auto; }}
          h1 {{ color: #333; margin-bottom: 8px; }}
          .subtitle {{ color: #666; margin-bottom: 32px; }}
          .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                   gap: 16px; margin-bottom: 32px; }}
          .stat-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
          .stat-card h3 {{ margin: 0 0 8px 0; color: #666; font-size: 14px; font-weight: 500; }}
          .stat-card .value {{ font-size: 32px; font-weight: 700; color: #333; }}
          .stat-card .label {{ font-size: 12px; color: #999; margin-top: 4px; }}
          .section {{ background: white; padding: 24px; border-radius: 8px; 
                     box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 24px; }}
          h2 {{ margin: 0 0 16px 0; font-size: 18px; color: #333; }}
          table {{ width: 100%; border-collapse: collapse; }}
          th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
          th {{ background: #f9f9f9; font-weight: 600; font-size: 13px; color: #666; }}
          td {{ font-size: 14px; color: #333; }}
          tr:hover {{ background: #f9f9f9; }}
          .api-links {{ margin-bottom: 24px; }}
          .api-links a {{ display: inline-block; margin-right: 16px; padding: 8px 16px; 
                         background: #007bff; color: white; text-decoration: none; 
                         border-radius: 4px; font-size: 14px; }}
          .api-links a:hover {{ background: #0056b3; }}
        </style>
      </head>
      <body>
        <div class="container">
          <h1>📊 Ask Mirror Talk Admin</h1>
          <div class="subtitle">Analytics & System Dashboard</div>
          
          <div class="api-links">
            <a href="/api/analytics/summary?days=7" target="_blank">📊 Analytics API</a>
            <a href="/api/analytics/episodes" target="_blank">📚 Episode Analytics</a>
            <a href="/status" target="_blank">⚙️ System Status</a>
          </div>
          
          <div class="stats">
            <div class="stat-card">
              <h3>Questions (7 days)</h3>
              <div class="value">{total_questions}</div>
              <div class="label">Total queries</div>
            </div>
            <div class="stat-card">
              <h3>Unique Users</h3>
              <div class="value">{unique_users}</div>
              <div class="label">Last 7 days</div>
            </div>
            <div class="stat-card">
              <h3>Avg Response Time</h3>
              <div class="value">{int(avg_latency)}ms</div>
              <div class="label">Answer latency</div>
            </div>
          </div>
          
          <div class="section">
            <h2>🔥 Top Cited Episodes (7 days)</h2>
            <table>
              <thead><tr><th>ID</th><th>Episode Title</th><th>Citations</th></tr></thead>
              <tbody>{top_episodes_rows if top_episodes else '<tr><td colspan="3">No data yet</td></tr>'}</tbody>
            </table>
          </div>
          
          <div class="section">
            <h2>💬 Recent Questions</h2>
            <table>
              <thead><tr><th>ID</th><th>Time</th><th>Question</th><th>Latency (ms)</th><th>IP</th></tr></thead>
              <tbody>{logs_rows if logs else '<tr><td colspan="5">No questions yet</td></tr>'}</tbody>
            </table>
          </div>
          
          <div class="section">
            <h2>🔄 Recent Ingestion Runs</h2>
            <table>
              <thead><tr><th>ID</th><th>Started</th><th>Finished</th><th>Status</th><th>Message</th></tr></thead>
              <tbody>{runs_rows if runs else '<tr><td colspan="5">No ingestion runs yet</td></tr>'}</tbody>
            </table>
          </div>
        </div>
      </body>
    </html>
    """
    return HTMLResponse(content=html)
