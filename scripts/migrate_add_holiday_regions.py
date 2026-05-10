#!/usr/bin/env python3
"""
Migration: Add region support to holidays table and seed international holidays.

Adds a 'region' column to support regional holiday variations (US, UK, EU, etc.)
and seeds common international holidays.

Usage:
  python3 scripts/migrate_add_holiday_regions.py
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
        # ── Add region column to holidays table ──────────────────────────
        print("Adding region support to holidays table...")
        db.execute(
            text("""
                ALTER TABLE holidays 
                ADD COLUMN IF NOT EXISTS region VARCHAR(10) DEFAULT 'global';
            """)
        )
        db.commit()
        print("✓ Added region column")

        # Update existing holidays to US region
        db.execute(
            text("""
                UPDATE holidays 
                SET region = 'US' 
                WHERE region = 'global' 
                  AND name IN (
                    'Independence Day (US)', 
                    'Thanksgiving (US)',
                    'Mother''s Day',
                    'Father''s Day'
                  );
            """)
        )
        db.commit()
        print("✓ Updated US-specific holidays")

        # ── Seed international holidays ──────────────────────────────────
        print("\nSeeding international holidays...")
        
        international_holidays = [
            # UK Holidays
            {
                "name": "Boxing Day",
                "description": "Day after Christmas, family and giving",
                "theme": "Community",
                "fixed_month": 12,
                "fixed_day": 26,
                "region": "UK"
            },
            {
                "name": "St. Patrick's Day",
                "description": "Irish cultural celebration",
                "theme": "Community",
                "fixed_month": 3,
                "fixed_day": 17,
                "region": "IE"
            },
            {
                "name": "Canada Day",
                "description": "Canadian independence celebration",
                "theme": "Gratitude",
                "fixed_month": 7,
                "fixed_day": 1,
                "region": "CA"
            },
            {
                "name": "Australia Day",
                "description": "Australian national day",
                "theme": "Community",
                "fixed_month": 1,
                "fixed_day": 26,
                "region": "AU"
            },
            {
                "name": "Anzac Day",
                "description": "Australian and New Zealand remembrance",
                "theme": "Gratitude",
                "fixed_month": 4,
                "fixed_day": 25,
                "region": "AU"
            },
            {
                "name": "Diwali",
                "description": "Festival of lights, new beginnings",
                "theme": "Faith",
                "fixed_month": 11,
                "fixed_day": 1,  # Approximate, varies by lunar calendar
                "region": "IN"
            },
            {
                "name": "International Day of Peace",
                "description": "UN day dedicated to world peace",
                "theme": "Inner peace",
                "fixed_month": 9,
                "fixed_day": 21,
                "region": "global"
            },
            {
                "name": "World Gratitude Day",
                "description": "Global day of thankfulness",
                "theme": "Gratitude",
                "fixed_month": 9,
                "fixed_day": 21,
                "region": "global"
            },
            {
                "name": "International Day of Families",
                "description": "UN day celebrating family bonds",
                "theme": "Relationships",
                "fixed_month": 5,
                "fixed_day": 15,
                "region": "global"
            },
            {
                "name": "World Kindness Day",
                "description": "Global kindness awareness (already exists, making global)",
                "theme": "Community",
                "fixed_month": 11,
                "fixed_day": 13,
                "region": "global"
            },
            # UK Mother's/Father's Day (same as US for simplicity)
            # Note: UK Mothering Sunday is actually based on Easter (3 weeks before)
            # For now, using approximate dates that work with our system
            {
                "name": "Mothering Sunday (UK)",
                "description": "UK Mother's Day (approximate)",
                "theme": "Parenting",
                "calc_month": 3,
                "calc_week": 4,  # 4th Sunday in March (approximate)
                "calc_day_of_week": 6,
                "region": "UK"
            },
            {
                "name": "Father's Day (UK)",
                "description": "UK Father's Day",
                "theme": "Parenting",
                "calc_month": 6,
                "calc_week": 3,  # Same as US (3rd Sunday in June)
                "calc_day_of_week": 6,
                "region": "UK"
            },
        ]

        inserted = 0
        for holiday in international_holidays:
            # Check if holiday already exists
            existing = db.execute(
                text("SELECT id FROM holidays WHERE name = :name"),
                {"name": holiday["name"]}
            ).fetchone()
            
            if existing:
                print(f"  - {holiday['name']} already exists, skipping")
                continue
            
            if "fixed_month" in holiday and holiday.get("fixed_month"):
                db.execute(
                    text("""
                        INSERT INTO holidays 
                        (name, description, theme, fixed_month, fixed_day, region, active)
                        VALUES (:name, :description, :theme, :fixed_month, :fixed_day, :region, true)
                    """),
                    holiday,
                )
            else:
                db.execute(
                    text("""
                        INSERT INTO holidays 
                        (name, description, theme, calc_month, calc_week, calc_day_of_week, region, active)
                        VALUES (:name, :description, :theme, :calc_month, :calc_week, :calc_day_of_week, :region, true)
                    """),
                    holiday,
                )
            inserted += 1

        db.commit()
        print(f"✓ Added {inserted} international holidays")

        # Show summary
        print("\n=== Holiday Summary by Region ===")
        regions = db.execute(
            text("SELECT region, COUNT(*) FROM holidays WHERE active = true GROUP BY region ORDER BY region")
        ).fetchall()
        
        for region, count in regions:
            print(f"  {region:8s}: {count} holiday(s)")

        total = db.execute(text("SELECT COUNT(*) FROM holidays WHERE active = true")).scalar()
        print(f"\n✓ Total active holidays: {total}")
        print("\n✓ Migration complete: Regional holiday support added")

    finally:
        db.close()


if __name__ == "__main__":
    apply_migration()
