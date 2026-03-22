"""
Migration: Add timezone-aware delivery and midday motivation support.

Changes:
  push_subscriptions:
    - timezone            VARCHAR(100) DEFAULT 'UTC'   — IANA timezone name
    - preferred_qotd_hour SMALLINT    DEFAULT 8        — local hour for QOTD send
    - notify_midday       BOOLEAN     DEFAULT true     — opt-in for noon motivation

  push_motivation_history (new table):
    - id, subscription_id, sent_at                    — deduplication per day

Run once against your database:
  python3 scripts/migrate_add_timezone_motivation.py
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
        # ── push_subscriptions: timezone column ──────────────────────────────
        db.execute(text("""
            ALTER TABLE push_subscriptions
            ADD COLUMN IF NOT EXISTS timezone VARCHAR(100) NOT NULL DEFAULT 'UTC';
        """))

        # ── push_subscriptions: preferred send hour for QOTD ─────────────────
        db.execute(text("""
            ALTER TABLE push_subscriptions
            ADD COLUMN IF NOT EXISTS preferred_qotd_hour SMALLINT NOT NULL DEFAULT 8;
        """))

        # ── push_subscriptions: midday motivation opt-in ──────────────────────
        db.execute(text("""
            ALTER TABLE push_subscriptions
            ADD COLUMN IF NOT EXISTS notify_midday BOOLEAN NOT NULL DEFAULT true;
        """))

        # ── push_motivation_history: deduplication table ──────────────────────
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS push_motivation_history (
                id              SERIAL PRIMARY KEY,
                subscription_id INTEGER NOT NULL
                                REFERENCES push_subscriptions(id) ON DELETE CASCADE,
                sent_at         TIMESTAMP NOT NULL DEFAULT NOW()
            );
        """))

        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_motivation_history_sub_sent
            ON push_motivation_history (subscription_id, sent_at);
        """))

        db.commit()
        print("✓ Migration applied: timezone, preferred_qotd_hour, notify_midday, push_motivation_history")

    except Exception as e:
        db.rollback()
        print(f"✗ Migration failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate()
