"""
Add indexes to QALog table for better analytics query performance.

This migration adds indexes to frequently queried columns:
- created_at: for time-range queries in analytics
- user_ip: for IP-based analytics and bot detection
- is_cached: for cache performance analysis

Run this script manually to upgrade existing production databases:
    python scripts/migrate_add_qa_log_indexes.py
"""

import logging
from sqlalchemy import text
from app.core.db import get_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate():
    """Add performance indexes to qa_logs table."""
    engine = get_engine()
    
    indexes = [
        ("idx_qa_logs_created_at", "qa_logs", "created_at"),
        ("idx_qa_logs_user_ip", "qa_logs", "user_ip"),
        ("idx_qa_logs_is_cached", "qa_logs", "is_cached"),
    ]
    
    with engine.connect() as conn:
        for idx_name, table_name, column_name in indexes:
            try:
                # Check if index already exists
                check_sql = text("""
                    SELECT 1 FROM pg_indexes 
                    WHERE tablename = :table AND indexname = :idx
                """)
                result = conn.execute(
                    check_sql, 
                    {"table": table_name, "idx": idx_name}
                ).fetchone()
                
                if result:
                    logger.info(f"✓ Index {idx_name} already exists, skipping")
                    continue
                
                # Create index
                create_sql = text(
                    f"CREATE INDEX {idx_name} ON {table_name} ({column_name})"
                )
                conn.execute(create_sql)
                conn.commit()
                logger.info(f"✓ Created index: {idx_name}")
                
            except Exception as exc:
                logger.error(f"✗ Failed to create index {idx_name}: {exc}")
                conn.rollback()
    
    logger.info("Migration complete!")


if __name__ == "__main__":
    logger.info("Starting QALog index migration...")
    migrate()
