"""
Migration: Add motivation message pool and message tracking.

Changes:
  push_motivation_messages (new table):
    - id, title, body, theme, source, created_at
    — Shared pool of midday motivation messages.  Source is one of:
        'static'       — seeded from the hard-coded list in push.py
        'generated'    — AI-generated generic messages (batch)
        'personalized' — AI-generated per-subscriber based on their qa_logs

  push_motivation_history:
    - message_id  INTEGER REFERENCES push_motivation_messages(id)  (nullable)
    — Added so we can track exactly which message each subscriber received,
      enabling no-repeat delivery from the shared pool.

Run once against your database:
  python3 scripts/migrate_add_motivation_pool.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.db import get_session_local
from sqlalchemy import text


def migrate():
    SessionLocal = get_session_local()
    db = SessionLocal()

    try:
        # ── push_motivation_messages: shared pool ─────────────────────────────
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS push_motivation_messages (
                id         SERIAL PRIMARY KEY,
                title      TEXT        NOT NULL,
                body       TEXT        NOT NULL,
                theme      VARCHAR(100),
                source     VARCHAR(20) NOT NULL DEFAULT 'static',
                created_at TIMESTAMP   NOT NULL DEFAULT NOW()
            );
        """))

        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_motivation_messages_source
            ON push_motivation_messages (source);
        """))

        # ── push_motivation_history: add message_id column ───────────────────
        db.execute(text("""
            ALTER TABLE push_motivation_history
            ADD COLUMN IF NOT EXISTS message_id INTEGER
                REFERENCES push_motivation_messages(id) ON DELETE SET NULL;
        """))

        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_motivation_history_message
            ON push_motivation_history (message_id);
        """))

        db.commit()
        print("✓ Migration applied: push_motivation_messages table + message_id column on push_motivation_history")

    except Exception as e:
        db.rollback()
        print(f"✗ Migration failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate()
