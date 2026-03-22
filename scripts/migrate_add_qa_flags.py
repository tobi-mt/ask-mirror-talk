#!/usr/bin/env python3
"""
Migration: add is_cached and is_answered columns to qa_logs,
and ensure citation_clicks and user_feedback tables exist.

Safe to run multiple times (uses IF NOT EXISTS / IF NOT EXISTS column checks).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.db import get_session_local


def main():
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        print("➤ Adding is_cached column to qa_logs (if absent)…")
        db.execute(text("""
            ALTER TABLE qa_logs
                ADD COLUMN IF NOT EXISTS is_cached BOOLEAN NOT NULL DEFAULT FALSE;
        """))

        print("➤ Adding is_answered column to qa_logs (if absent)…")
        db.execute(text("""
            ALTER TABLE qa_logs
                ADD COLUMN IF NOT EXISTS is_answered BOOLEAN NOT NULL DEFAULT TRUE;
        """))

        print("➤ Ensuring citation_clicks table exists…")
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS citation_clicks (
                id          SERIAL PRIMARY KEY,
                qa_log_id   INTEGER NOT NULL REFERENCES qa_logs(id),
                episode_id  INTEGER NOT NULL REFERENCES episodes(id),
                clicked_at  TIMESTAMP NOT NULL DEFAULT NOW(),
                user_ip     VARCHAR(100),
                timestamp   FLOAT
            );
        """))

        print("➤ Ensuring user_feedback table exists…")
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS user_feedback (
                id            SERIAL PRIMARY KEY,
                qa_log_id     INTEGER NOT NULL REFERENCES qa_logs(id),
                feedback_type VARCHAR(20) NOT NULL,
                rating        INTEGER,
                comment       TEXT,
                created_at    TIMESTAMP NOT NULL DEFAULT NOW(),
                user_ip       VARCHAR(100)
            );
        """))

        db.commit()
        print("✅ Migration complete.")
    except Exception as e:
        db.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
