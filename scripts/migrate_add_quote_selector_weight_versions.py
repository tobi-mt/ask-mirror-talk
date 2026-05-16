#!/usr/bin/env python3
"""Create quote_selector_weight_versions table for persisted tuning state."""

from sqlalchemy import text

from app.core.db import SessionLocal, safe_close_session


def main() -> None:
    db = SessionLocal()()
    try:
        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS quote_selector_weight_versions (
                    id SERIAL PRIMARY KEY,
                    version INTEGER NOT NULL,
                    weights_json TEXT NOT NULL,
                    metrics_json TEXT,
                    is_active BOOLEAN NOT NULL DEFAULT false,
                    rollback_from_version INTEGER,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        )
        db.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS idx_quote_selector_weight_versions_active
                ON quote_selector_weight_versions (is_active, version DESC)
                """
            )
        )
        db.commit()
        print("✓ quote_selector_weight_versions migration complete")
    finally:
        safe_close_session(db, context="migrate_quote_selector_weight_versions")


if __name__ == "__main__":
    main()
