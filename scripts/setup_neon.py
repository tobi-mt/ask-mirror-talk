#!/usr/bin/env python3
"""
Neon Database Setup Script
Initializes the Neon Postgres database with required schema and pgvector extension
"""

import sys
import os
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.db import engine, init_db
from app.core.config import settings
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def verify_pgvector():
    """Verify pgvector extension is installed"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT * FROM pg_extension WHERE extname = 'vector'"
            ))
            if result.fetchone():
                logger.info("✓ pgvector extension is enabled")
                return True
            else:
                logger.warning("✗ pgvector extension not found")
                logger.info("Attempting to create pgvector extension...")
                try:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                    conn.commit()
                    logger.info("✓ pgvector extension created successfully")
                    return True
                except Exception as e:
                    logger.error(f"✗ Failed to create pgvector extension: {e}")
                    logger.error("Please enable pgvector in Neon dashboard:")
                    logger.error("1. Go to Neon console")
                    logger.error("2. Open SQL Editor")
                    logger.error("3. Run: CREATE EXTENSION IF NOT EXISTS vector;")
                    return False
    except Exception as e:
        logger.error(f"✗ Error checking pgvector: {e}")
        return False


def verify_connection():
    """Test database connection"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"✓ Connected to database: {version}")
            return True
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        logger.error(f"DATABASE_URL: {settings.database_url.split('@')[0]}@***")
        return False


def check_tables():
    """Check if tables exist and show counts"""
    try:
        with engine.connect() as conn:
            # Check episodes
            result = conn.execute(text("SELECT COUNT(*) FROM episodes"))
            episode_count = result.scalar()
            logger.info(f"✓ Episodes table exists ({episode_count} records)")
            
            # Check chunks
            result = conn.execute(text("SELECT COUNT(*) FROM chunks"))
            chunk_count = result.scalar()
            logger.info(f"✓ Chunks table exists ({chunk_count} records)")
            
            return True
    except Exception as e:
        logger.info(f"Tables not found or error: {e}")
        return False


def main():
    """Main setup function"""
    logger.info("=" * 60)
    logger.info("Neon Database Setup for Ask Mirror Talk")
    logger.info("=" * 60)
    
    # Step 1: Verify connection
    logger.info("\n[1/4] Verifying database connection...")
    if not verify_connection():
        logger.error("\n✗ Setup failed: Cannot connect to database")
        logger.error("\nPlease check:")
        logger.error("1. DATABASE_URL is set correctly")
        logger.error("2. Neon database is active (not paused)")
        logger.error("3. Connection string includes ?sslmode=require")
        logger.error("4. Connection string has +psycopg in the dialect")
        return 1
    
    # Step 2: Verify pgvector
    logger.info("\n[2/4] Verifying pgvector extension...")
    if not verify_pgvector():
        logger.error("\n✗ Setup failed: pgvector extension required")
        return 1
    
    # Step 3: Initialize database
    logger.info("\n[3/4] Creating database schema...")
    try:
        init_db()
        logger.info("✓ Database schema created successfully")
    except Exception as e:
        logger.error(f"✗ Failed to create schema: {e}")
        return 1
    
    # Step 4: Verify tables
    logger.info("\n[4/4] Verifying tables...")
    if check_tables():
        logger.info("✓ All tables verified")
    else:
        logger.warning("⚠ Tables created but verification had issues")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Setup Complete! ✓")
    logger.info("=" * 60)
    logger.info("\nNext steps:")
    logger.info("1. Load initial data:")
    logger.info("   python -m app.ingestion.pipeline_optimized")
    logger.info("\n2. Or use bulk ingestion:")
    logger.info("   python scripts/bulk_ingest.py --max-episodes 10")
    logger.info("\n3. Test the API:")
    logger.info("   python -m uvicorn app.api.main:app --reload")
    logger.info("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
