from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import logging
import socket

from app.core.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


# Lazy engine creation - don't create connection pool at import time
# This prevents blocking app startup if database is slow/unavailable
_engine = None
_SessionLocal = None


def _resolve_to_ipv4(hostname: str, port: int = 5432) -> str | None:
    """
    Resolve a hostname to its first IPv4 address.
    Returns the IP string or None if resolution fails.
    """
    try:
        results = socket.getaddrinfo(hostname, port, socket.AF_INET, socket.SOCK_STREAM)
        if results:
            ipv4 = results[0][4][0]
            logger.info("Resolved DB host %s → %s (forced IPv4)", hostname, ipv4)
            return ipv4
    except Exception as exc:
        logger.warning("IPv4 resolution failed for %s: %s", hostname, exc)
    return None


def get_engine():
    """Get or create the database engine lazily."""
    global _engine
    if _engine is None:
        db_url = settings.database_url

        # Log the database URL (redacted) for debugging
        url_parts = db_url.split('@')
        if len(url_parts) > 1:
            logger.info("Database URL format: %s://***@%s", db_url.split(':')[0], url_parts[1])
        else:
            logger.info("Database URL format: %s://...", db_url.split(':')[0])

        # ── Force IPv4 for Neon on Railway ──
        # Neon uses SNI-based routing, so we MUST keep the hostname in the
        # connection string for TLS to work. But we also pass `hostaddr`
        # (the resolved IPv4 IP) so libpq connects to the IPv4 address
        # while still sending the correct SNI hostname during the TLS
        # handshake. This is the official libpq approach.
        # Note: do NOT pass idle_in_transaction_session_timeout in options —
        # Neon's pooled endpoints (PgBouncer) reject it as an unsupported
        # startup parameter. We mitigate idle-in-transaction issues by
        # closing DB sessions before long-running operations (see service.py).
        connect_args = {
            "connect_timeout": 10,
            "options": "-c client_encoding=utf8",
        }

        # Extract hostname from the URL and pre-resolve to IPv4
        from urllib.parse import urlparse
        parsed = urlparse(db_url)
        hostname = parsed.hostname
        if hostname and hostname != "localhost" and hostname != "127.0.0.1":
            ipv4 = _resolve_to_ipv4(hostname, parsed.port or 5432)
            if ipv4:
                # hostaddr tells libpq to connect to this IP, while the
                # 'host' (from the URL) is still used for SNI / cert check
                connect_args["hostaddr"] = ipv4

        # Connection pool settings tuned for Neon serverless:
        # - pool_pre_ping: verify connection liveness before handing it out
        # - pool_recycle: recreate connections every 2 min (Neon kills idle ones)
        # - pool_size / max_overflow: minimal footprint for serverless limits
        # - idle_in_transaction_session_timeout: Neon hard-kills idle txns;
        #   set our own timeout lower so SQLAlchemy sees the error cleanly
        _engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=120,
            pool_size=2,
            max_overflow=3,
            pool_timeout=30,
            echo=False,
            connect_args=connect_args,
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
