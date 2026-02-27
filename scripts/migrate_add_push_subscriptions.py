"""
Migration: Add push_subscriptions table for Web Push notifications.

Run this script once against your database to create the table.
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
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS push_subscriptions (
                id SERIAL PRIMARY KEY,
                endpoint TEXT NOT NULL UNIQUE,
                p256dh_key VARCHAR(200) NOT NULL,
                auth_key VARCHAR(100) NOT NULL,
                user_ip VARCHAR(100) NOT NULL DEFAULT '',
                active BOOLEAN NOT NULL DEFAULT true,
                notify_qotd BOOLEAN NOT NULL DEFAULT true,
                notify_new_episodes BOOLEAN NOT NULL DEFAULT true,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW()
            );
        """))

        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_push_subscriptions_active
            ON push_subscriptions (active) WHERE active = true;
        """))

        db.commit()
        print("✓ push_subscriptions table created successfully")
    except Exception as e:
        db.rollback()
        print(f"✗ Migration failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate()
