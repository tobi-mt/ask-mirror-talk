#!/usr/bin/env python3
"""
Migration: add product_events table for lightweight client-side funnel analytics.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.core.db import get_session_local


def main():
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS product_events (
                id SERIAL PRIMARY KEY,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                qa_log_id INTEGER NULL REFERENCES qa_logs(id),
                event_name VARCHAR(80) NOT NULL,
                metadata_json TEXT NULL,
                user_ip VARCHAR(100) NOT NULL
            );
        """))
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_product_events_created_at
            ON product_events (created_at DESC);
        """))
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_product_events_event_name
            ON product_events (event_name);
        """))
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_product_events_user_ip
            ON product_events (user_ip);
        """))
        db.commit()
        print("✅ product_events table is ready")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
