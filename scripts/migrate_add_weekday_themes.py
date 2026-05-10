#!/usr/bin/env python3
"""
Migration: Add weekday_themes table for day-of-week themed QOTD and midday motivation.

This table defines which themes are prioritized on each day of the week, allowing
for intelligent weekly patterns like "Monday motivation" or "Friday gratitude."

Usage:
  python3 scripts/migrate_add_weekday_themes.py
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
        # ── Create weekday_themes table ──────────────────────────────────
        db.execute(
            text("""
                CREATE TABLE IF NOT EXISTS weekday_themes (
                    id              SERIAL PRIMARY KEY,
                    day_of_week     SMALLINT NOT NULL,  -- 0=Monday, 6=Sunday
                    theme           VARCHAR(100) NOT NULL,
                    priority        SMALLINT NOT NULL DEFAULT 1,  -- Higher = more preferred
                    description     TEXT,
                    active          BOOLEAN NOT NULL DEFAULT true,
                    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    
                    CONSTRAINT chk_day_of_week CHECK (day_of_week BETWEEN 0 AND 6),
                    CONSTRAINT chk_priority CHECK (priority > 0),
                    UNIQUE (day_of_week, theme)
                )
            """)
        )
        db.commit()
        print("✓ weekday_themes table created (or already existed)")

        # ── Seed with intelligent weekly patterns ───────────────────────
        count = db.execute(text("SELECT COUNT(*) FROM weekday_themes")).scalar()
        if count == 0:
            print("Seeding weekday_themes with smart weekly patterns...")
            
            # Monday - Start the week with empowerment and purpose
            weekday_data = [
                # MONDAY (0) - Empowerment & Purpose
                {
                    "day_of_week": 0,
                    "theme": "Empowerment",
                    "priority": 10,
                    "description": "Monday motivation - start strong with agency and confidence"
                },
                {
                    "day_of_week": 0,
                    "theme": "Purpose",
                    "priority": 9,
                    "description": "Monday clarity - align with calling and direction"
                },
                {
                    "day_of_week": 0,
                    "theme": "Leadership",
                    "priority": 8,
                    "description": "Monday leadership - step into influence with integrity"
                },
                
                # TUESDAY (1) - Growth & Courage
                {
                    "day_of_week": 1,
                    "theme": "Growth",
                    "priority": 10,
                    "description": "Tuesday momentum - embrace change and learning"
                },
                {
                    "day_of_week": 1,
                    "theme": "Courage",
                    "priority": 9,
                    "description": "Tuesday bravery - take the next honest step"
                },
                {
                    "day_of_week": 1,
                    "theme": "Transition",
                    "priority": 7,
                    "description": "Tuesday navigation - move through change with care"
                },
                
                # WEDNESDAY (2) - Inner Peace & Healing (Hump day self-care)
                {
                    "day_of_week": 2,
                    "theme": "Inner peace",
                    "priority": 10,
                    "description": "Wednesday calm - find steadiness mid-week"
                },
                {
                    "day_of_week": 2,
                    "theme": "Healing",
                    "priority": 9,
                    "description": "Wednesday restoration - tend to what needs care"
                },
                {
                    "day_of_week": 2,
                    "theme": "Self-worth",
                    "priority": 8,
                    "description": "Wednesday worthiness - return to your center"
                },
                
                # THURSDAY (3) - Purpose & Boundaries (Push through with clarity)
                {
                    "day_of_week": 3,
                    "theme": "Purpose",
                    "priority": 10,
                    "description": "Thursday direction - stay aligned with what matters"
                },
                {
                    "day_of_week": 3,
                    "theme": "Boundaries",
                    "priority": 9,
                    "description": "Thursday protection - honor your yes and no"
                },
                {
                    "day_of_week": 3,
                    "theme": "Empowerment",
                    "priority": 8,
                    "description": "Thursday strength - reclaim your voice"
                },
                
                # FRIDAY (4) - Gratitude & Relationships (Celebrate progress)
                {
                    "day_of_week": 4,
                    "theme": "Gratitude",
                    "priority": 10,
                    "description": "Friday celebration - notice what carried you"
                },
                {
                    "day_of_week": 4,
                    "theme": "Relationships",
                    "priority": 9,
                    "description": "Friday connection - love with clarity"
                },
                {
                    "day_of_week": 4,
                    "theme": "Community",
                    "priority": 8,
                    "description": "Friday belonging - acknowledge support received"
                },
                
                # SATURDAY (5) - Self-worth & Identity (Personal reflection)
                {
                    "day_of_week": 5,
                    "theme": "Identity",
                    "priority": 10,
                    "description": "Saturday reflection - reconnect with your voice"
                },
                {
                    "day_of_week": 5,
                    "theme": "Self-worth",
                    "priority": 9,
                    "description": "Saturday worthiness - remember your value"
                },
                {
                    "day_of_week": 5,
                    "theme": "Growth",
                    "priority": 7,
                    "description": "Saturday learning - reflect on becoming"
                },
                
                # SUNDAY (6) - Faith & Inner Peace (Rest & spiritual reflection)
                {
                    "day_of_week": 6,
                    "theme": "Faith",
                    "priority": 10,
                    "description": "Sunday spiritual - trust in the quiet"
                },
                {
                    "day_of_week": 6,
                    "theme": "Inner peace",
                    "priority": 9,
                    "description": "Sunday rest - release what's been bracing you"
                },
                {
                    "day_of_week": 6,
                    "theme": "Gratitude",
                    "priority": 8,
                    "description": "Sunday appreciation - honor the week's grace"
                },
            ]

            for entry in weekday_data:
                db.execute(
                    text("""
                        INSERT INTO weekday_themes 
                        (day_of_week, theme, priority, description, active)
                        VALUES (:day_of_week, :theme, :priority, :description, true)
                    """),
                    entry,
                )

            db.commit()
            count = db.execute(text("SELECT COUNT(*) FROM weekday_themes")).scalar()
            print(f"✓ Seeded {count} weekday theme preferences")
        else:
            print(f"✓ weekday_themes table already has {count} entries")

        print("\n✓ Migration complete: weekday_themes table for intelligent weekly patterns")

    finally:
        db.close()


if __name__ == "__main__":
    apply_migration()
