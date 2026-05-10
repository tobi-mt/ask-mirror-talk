#!/usr/bin/env python3
"""
Migration: Add holidays table for themed QOTD and midday motivation.

This table defines special dates (holidays, observances) that should trigger
themed questions. Supports both fixed dates (e.g., January 1) and calculated
dates (e.g., 2nd Sunday in May for Mother's Day).

Usage:
  python3 scripts/migrate_add_holidays.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text
from app.core.db import get_session_local


def apply_migration() -> None:
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        # ── Create holidays table ─────────────────────────────────────────
        db.execute(
            text("""
                CREATE TABLE IF NOT EXISTS holidays (
                    id              SERIAL PRIMARY KEY,
                    name            VARCHAR(200) NOT NULL,
                    description     TEXT,
                    theme           VARCHAR(100) NOT NULL,
                    
                    -- For fixed-date holidays (e.g., January 1, July 4)
                    fixed_month     SMALLINT,
                    fixed_day       SMALLINT,
                    
                    -- For calculated holidays (e.g., 2nd Sunday in May)
                    calc_month      SMALLINT,
                    calc_week       SMALLINT,      -- 1=first, 2=second, -1=last
                    calc_day_of_week SMALLINT,     -- 0=Monday, 6=Sunday
                    
                    active          BOOLEAN NOT NULL DEFAULT true,
                    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    
                    -- Constraints
                    CONSTRAINT chk_date_type CHECK (
                        (fixed_month IS NOT NULL AND fixed_day IS NOT NULL AND 
                         calc_month IS NULL AND calc_week IS NULL AND calc_day_of_week IS NULL)
                        OR
                        (calc_month IS NOT NULL AND calc_week IS NOT NULL AND calc_day_of_week IS NOT NULL AND
                         fixed_month IS NULL AND fixed_day IS NULL)
                    ),
                    CONSTRAINT chk_fixed_month CHECK (fixed_month BETWEEN 1 AND 12),
                    CONSTRAINT chk_fixed_day CHECK (fixed_day BETWEEN 1 AND 31),
                    CONSTRAINT chk_calc_month CHECK (calc_month BETWEEN 1 AND 12),
                    CONSTRAINT chk_calc_week CHECK (calc_week BETWEEN -1 AND 5 AND calc_week != 0),
                    CONSTRAINT chk_calc_day_of_week CHECK (calc_day_of_week BETWEEN 0 AND 6)
                )
            """)
        )
        db.commit()
        print("✓ holidays table created (or already existed)")

        # ── Seed with common holidays ────────────────────────────────────
        count = db.execute(text("SELECT COUNT(*) FROM holidays")).scalar()
        if count == 0:
            print("Seeding holidays table with common holidays...")
            holidays_data = [
                # Fixed-date holidays
                {
                    "name": "New Year's Day",
                    "description": "Start of a new year, fresh beginnings",
                    "theme": "Purpose",
                    "fixed_month": 1,
                    "fixed_day": 1,
                },
                {
                    "name": "Valentine's Day",
                    "description": "Day of love and relationships",
                    "theme": "Relationships",
                    "fixed_month": 2,
                    "fixed_day": 14,
                },
                {
                    "name": "International Women's Day",
                    "description": "Celebrating women's achievements",
                    "theme": "Empowerment",
                    "fixed_month": 3,
                    "fixed_day": 8,
                },
                {
                    "name": "Earth Day",
                    "description": "Environmental awareness and stewardship",
                    "theme": "Gratitude",
                    "fixed_month": 4,
                    "fixed_day": 22,
                },
                {
                    "name": "Independence Day (US)",
                    "description": "Freedom and independence",
                    "theme": "Empowerment",
                    "fixed_month": 7,
                    "fixed_day": 4,
                },
                {
                    "name": "World Mental Health Day",
                    "description": "Mental health awareness",
                    "theme": "Healing",
                    "fixed_month": 10,
                    "fixed_day": 10,
                },
                {
                    "name": "World Kindness Day",
                    "description": "Acts of kindness and compassion",
                    "theme": "Community",
                    "fixed_month": 11,
                    "fixed_day": 13,
                },
                {
                    "name": "Christmas Eve",
                    "description": "Eve of Christmas celebration",
                    "theme": "Faith",
                    "fixed_month": 12,
                    "fixed_day": 24,
                },
                {
                    "name": "Christmas Day",
                    "description": "Christmas celebration",
                    "theme": "Faith",
                    "fixed_month": 12,
                    "fixed_day": 25,
                },
                {
                    "name": "New Year's Eve",
                    "description": "Reflection on the year ending",
                    "theme": "Gratitude",
                    "fixed_month": 12,
                    "fixed_day": 31,
                },
                # Calculated holidays (US-based for now)
                {
                    "name": "Mother's Day",
                    "description": "Honoring mothers and motherhood",
                    "theme": "Parenting",
                    "calc_month": 5,
                    "calc_week": 2,
                    "calc_day_of_week": 6,  # Sunday
                },
                {
                    "name": "Father's Day",
                    "description": "Honoring fathers and fatherhood",
                    "theme": "Parenting",
                    "calc_month": 6,
                    "calc_week": 3,
                    "calc_day_of_week": 6,  # Sunday
                },
                {
                    "name": "Thanksgiving (US)",
                    "description": "Day of gratitude and thankfulness",
                    "theme": "Gratitude",
                    "calc_month": 11,
                    "calc_week": 4,
                    "calc_day_of_week": 3,  # Thursday
                },
            ]

            for holiday in holidays_data:
                if "fixed_month" in holiday and holiday.get("fixed_month"):
                    db.execute(
                        text("""
                            INSERT INTO holidays 
                            (name, description, theme, fixed_month, fixed_day, active)
                            VALUES (:name, :description, :theme, :fixed_month, :fixed_day, true)
                        """),
                        holiday,
                    )
                else:
                    db.execute(
                        text("""
                            INSERT INTO holidays 
                            (name, description, theme, calc_month, calc_week, calc_day_of_week, active)
                            VALUES (:name, :description, :theme, :calc_month, :calc_week, :calc_day_of_week, true)
                        """),
                        holiday,
                    )

            db.commit()
            count = db.execute(text("SELECT COUNT(*) FROM holidays")).scalar()
            print(f"✓ Seeded {count} holidays")
        else:
            print(f"✓ holidays table already has {count} entries")

        print("\n✓ Migration complete: holidays table for themed QOTD")

    finally:
        db.close()


if __name__ == "__main__":
    apply_migration()
