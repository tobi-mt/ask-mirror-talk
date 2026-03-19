#!/usr/bin/env python3
"""
Migration: Add push_qotd_questions table and seed with the static pool.

The table replaces the hardcoded _QOTD_POOL list in push.py and acts as the
authoritative source for all QOTD questions.  New questions are appended by
generate_qotd_batch() automatically during send_qotd_notification() when the
pool headroom drops below the refill threshold.

Safe to run multiple times (CREATE TABLE IF NOT EXISTS; seeds only if empty).
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.db import get_engine, get_session_local
from app.notifications.push import _ensure_pool_seeded
from sqlalchemy import text


def main():
    engine = get_engine()

    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS push_qotd_questions (
                id         SERIAL PRIMARY KEY,
                question   TEXT        NOT NULL,
                theme      VARCHAR(100),
                emoji      VARCHAR(20),
                hook       TEXT,
                source     VARCHAR(20) NOT NULL DEFAULT 'static',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """))
        conn.commit()

    print("✓ push_qotd_questions table created (or already existed)")

    # Seed the 40 static questions if the table is empty
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        _ensure_pool_seeded(db)
        count = db.execute(text("SELECT COUNT(*) FROM push_qotd_questions")).scalar()
        print(f"✓ push_qotd_questions now contains {count} questions")
    finally:
        db.close()


if __name__ == "__main__":
    main()
