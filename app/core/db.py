from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


# For psycopg3 (psycopg[binary]), SQLAlchemy 2.0+ uses postgresql+psycopg:// dialect
# Log the database URL (redacted) for debugging
url_parts = settings.database_url.split('@')
if len(url_parts) > 1:
    logger.info("Database URL format: %s://***@%s", settings.database_url.split(':')[0], url_parts[1])
else:
    logger.info("Database URL format: %s://...", settings.database_url.split(':')[0])
# Ensure we're using psycopg3, not psycopg2
# Add connection pool settings to prevent idle timeouts
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # Verify connections before using them
    pool_recycle=3600,   # Recycle connections after 1 hour
    pool_size=5,         # Number of connections to maintain
    max_overflow=10,     # Max additional connections
    echo=False           # Set to True for SQL query logging
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database with pgvector extension and create tables."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Ensure pgvector extension exists and create tables
        with engine.connect() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            connection.commit()
        logger.info("✓ pgvector extension enabled")

        # Late import to avoid circulars
        from app.storage.models import Base  # noqa: WPS433

        Base.metadata.create_all(bind=engine)
        logger.info("✓ Database tables created/verified")
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
        raise
