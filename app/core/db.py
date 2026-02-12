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
            pool_recycle=3600,   # Recycle connections after 1 hour
            pool_size=5,         # Number of connections to maintain
            max_overflow=10,     # Max additional connections
            echo=False,          # Set to True for SQL query logging
            connect_args={
                "connect_timeout": 10,  # 10 second timeout
                "options": "-c client_encoding=utf8",  # Ensure UTF-8 encoding
            }
        )
    return _engine


def get_session_local():
    """Get SessionLocal class (not an instance)."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autocommit=False, autoflush=False)
    return _SessionLocal


# Module-level references for backwards compatibility
# Note: These are function references, not calls - engine/SessionLocal are created on first use
engine = get_engine
SessionLocal = get_session_local


def get_db():
    db = SessionLocal()()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database with pgvector extension and create tables."""
    import logging
    logger = logging.getLogger(__name__)
    
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
