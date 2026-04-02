from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.core.db import get_session_local
from app.core.logging import setup_logging
from app.api.routes.ask import router as ask_router
from app.api.routes.discovery import router as discovery_router, QOTD_POOL, TOPIC_CATALOG
from app.api.routes.analytics import router as analytics_router
from app.api.routes.push import router as push_router
from app.api.routes.interactions import router as interactions_router
from app.api.routes.system import router as system_router
from app.api.routes.ingest import router as ingest_router
from app.api.routes.admin import router as admin_router
from app.api.runtime import is_db_initialized, mark_db_initialized

# Setup logging BEFORE any other operations
setup_logging()
logger = logging.getLogger(__name__)

# Log startup immediately
logger.info("="*60)
logger.info("STARTING ASK MIRROR TALK API")
logger.info("="*60)

async def _init_db_background():
    """Initialize database in background without blocking startup."""
    import asyncio
    await asyncio.sleep(2)  # Give app time to start and pass healthcheck
    
    try:
        from app.core.db import init_db
        init_db()
        mark_db_initialized()
        logger.info("✓ Background database initialization complete")
    except Exception as e:
        logger.error(f"✗ Background database initialization failed: {e}", exc_info=True)
        logger.warning("⚠️  Some endpoints may not work until database is accessible")


async def _prewarm_cache():
    """Pre-warm the answer cache with QOTD and topic queries after DB is ready."""
    import asyncio

    # Wait for DB to be ready (poll every 2s, up to 60s)
    for _ in range(30):
        if is_db_initialized():
            break
        await asyncio.sleep(2)

    if not is_db_initialized():
        logger.warning("⚠️  Cache pre-warm skipped: DB not ready after 60s")
        return

    logger.info("🔥 Starting cache pre-warm...")

    from app.qa.cache import get_answer_cache, prewarm_from_db_history

    cache = get_answer_cache()

    # ── Phase 1: restore top user questions from DB (no OpenAI cost) ──
    logger.info("  📚 Loading historical user questions from DB...")
    SessionLocal = get_session_local()
    hist_db = SessionLocal()
    try:
        n = prewarm_from_db_history(cache, hist_db, limit=40)
        logger.info("  ✓ DB history prewarm: %d entries loaded", n)
    except Exception as e:
        logger.warning("  ✗ DB history prewarm failed: %s", e)
    finally:
        hist_db.close()

    # ── Phase 2: prewarm QOTD + topic queries via full answer pipeline ──
    # Collect unique questions: all QOTD + all topic queries
    questions: list[str] = []
    for entry in QOTD_POOL:
        questions.append(entry["question"])
    for topic in TOPIC_CATALOG:
        q = topic["query"]
        if q not in questions:
            questions.append(q)

    from app.qa.service import answer_question

    warmed = 0
    failed = 0

    for question in questions:
        try:
            db = SessionLocal()
            try:
                answer_question(db, question, user_ip="cache-prewarm")
                warmed += 1
                logger.info("  ✓ Pre-warmed (%d/%d): %.50s…", warmed, len(questions), question)
            finally:
                db.close()
            # Small delay to avoid hammering the OpenAI API
            await asyncio.sleep(0.5)
        except Exception as e:
            failed += 1
            logger.warning("  ✗ Pre-warm failed for '%.50s…': %s", question, e)

    logger.info("🔥 Cache pre-warm complete: %d warmed, %d failed, %d total", warmed, failed, len(questions))


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    """Application lifespan: initialize DB on startup."""
    import asyncio
    logger.info("="*60)
    logger.info("STARTUP EVENT TRIGGERED")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"App name: {settings.app_name}")
    logger.info("="*60)
    logger.info("✓ Application startup complete (DB init deferred)")
    logger.info("Starting background DB initialization task...")
    asyncio.create_task(_init_db_background())
    asyncio.create_task(_prewarm_cache())
    yield
    logger.info("Application shutting down")


app = FastAPI(title=settings.app_name, lifespan=_lifespan)
app.include_router(ask_router)
app.include_router(discovery_router)
app.include_router(analytics_router)
app.include_router(push_router)
app.include_router(interactions_router)
app.include_router(system_router)
app.include_router(ingest_router)
app.include_router(admin_router)


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
