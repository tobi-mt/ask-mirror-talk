#!/usr/bin/env python3
"""
Migration: Add push_qotd_history table.

Tracks which QOTD questions have been sent to each subscriber so each user
receives no-repeat, individualised questions cycling through the full pool.

Safe to run multiple times (CREATE TABLE IF NOT EXISTS).
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.db import get_engine
from sqlalchemy import text


def main():
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS push_qotd_history (
                id              SERIAL PRIMARY KEY,
                subscription_id INTEGER NOT NULL,
                qotd_id         INTEGER NOT NULL,
                sent_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS push_qotd_history_sub_idx
            ON push_qotd_history (subscription_id)
        """))
        conn.commit()

    print("✓ push_qotd_history table and index created (or already existed)")


if __name__ == "__main__":
    main()
