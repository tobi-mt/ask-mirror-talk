from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


# Lazy engine creation - don't create connection pool at import time
# This prevents blocking app startup if database is slow/unavailable
_engine = None
_SessionLocal = None


def get_engine():
    """Get or create the database engine lazily."""
    global _engine
    if _engine is None:
        # Log the database URL (redacted) for debugging
        url_parts = settings.database_url.split('@')
        if len(url_parts) > 1:
            logger.info("Database URL format: %s://***@%s", settings.database_url.split(':')[0], url_parts[1])
        else:
            logger.info("Database URL format: %s://...", settings.database_url.split(':')[0])
        
        # Ensure we're using psycopg3, not psycopg2
        # Add connection pool settings to prevent idle timeouts
        # Force IPv4 for Neon compatibility on Railway
        _engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,  # Verify connections before using them
            pool_recycle=120,    # Recycle connections every 2 min (Neon kills idle connections)
            pool_size=2,         # Minimal pool — Neon serverless has tight limits
            max_overflow=3,      # Max additional connections
            pool_timeout=30,     # Wait up to 30s for a connection from the pool
            echo=False,          # Set to True for SQL query logging
            connect_args={
                "connect_timeout": 10,  # 10 second timeout
                "options": "-c client_encoding=utf8 -c idle_in_transaction_session_timeout=15000",
            }
        )
    return _engine


def get_session_local():
    """Get SessionLocal class (not an instance)."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autocommit=False, autoflush=False)
    return _SessionLocal


def get_db():
    """FastAPI dependency that yields a database session."""
    session = get_session_local()()
    try:
        yield session
    finally:
        session.close()


def init_db():
    """Initialize database with pgvector extension and create tables."""
    try:
        # Get the actual engine instance
        db_engine = get_engine()
        
        # Ensure pgvector extension exists and create tables
        with db_engine.connect() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            connection.commit()
        logger.info("✓ pgvector extension enabled")

        # Late import to avoid circulars
        from app.storage.models import Base  # noqa: WPS433

        Base.metadata.create_all(bind=db_engine)
        logger.info("✓ Database tables created/verified")
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
        raise


# Backward-compatible aliases used by scripts/
# Scripts use `SessionLocal()()` (call the function, then call the sessionmaker),
# so aliasing directly to the factory functions is the correct approach.
SessionLocal = get_session_local
engine = get_engine
