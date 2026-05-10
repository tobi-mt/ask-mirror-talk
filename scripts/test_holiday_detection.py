#!/usr/bin/env python3
"""
Test holiday detection and themed QOTD selection.

This script verifies that:
1. Holiday detection correctly identifies today's holiday (if any)
2. The correct theme is returned for known holidays
3. The Nth weekday calculation works correctly for Mother's Day, Father's Day, etc.
"""

import sys
import os
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text
from app.core.db import get_session_local
from app.notifications.push import get_today_holiday_theme, _calculate_nth_weekday


def test_nth_weekday_calculation():
    """Test that we can correctly calculate Nth weekday of a month."""
    print("\n=== Testing Nth Weekday Calculation ===")
    
    # Mother's Day 2026: 2nd Sunday in May (should be May 10, 2026)
    mothers_day_2026 = _calculate_nth_weekday(2026, 5, 2, 6)  # 6 = Sunday
    print(f"Mother's Day 2026 (2nd Sunday in May): May {mothers_day_2026}, 2026")
    
    # Father's Day 2026: 3rd Sunday in June (should be June 21, 2026)
    fathers_day_2026 = _calculate_nth_weekday(2026, 6, 3, 6)  # 6 = Sunday
    print(f"Father's Day 2026 (3rd Sunday in June): June {fathers_day_2026}, 2026")
    
    # Thanksgiving 2026: 4th Thursday in November (should be November 26, 2026)
    thanksgiving_2026 = _calculate_nth_weekday(2026, 11, 4, 3)  # 3 = Thursday
    print(f"Thanksgiving 2026 (4th Thursday in November): November {thanksgiving_2026}, 2026")
    
    # Test some edge cases
    # Last Friday of the month
    last_friday_may_2026 = _calculate_nth_weekday(2026, 5, -1, 4)  # 4 = Friday, -1 = last
    print(f"Last Friday of May 2026: May {last_friday_may_2026}, 2026")


def test_holiday_detection():
    """Test holiday detection for today and some known dates."""
    print("\n=== Testing Holiday Detection ===")
    
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        # Check today
        today = date.today()
        theme, name = get_today_holiday_theme(db)
        if theme and name:
            print(f"✓ TODAY ({today}): {name} (theme: {theme})")
        else:
            print(f"ℹ TODAY ({today}): No holiday detected")
        
        # List all holidays in the database
        print("\n=== All Holidays in Database ===")
        holidays = db.execute(
            text("""
                SELECT name, theme, fixed_month, fixed_day, 
                       calc_month, calc_week, calc_day_of_week, active
                FROM holidays
                ORDER BY COALESCE(fixed_month, calc_month), COALESCE(fixed_day, 1)
            """)
        ).fetchall()
        
        for h in holidays:
            name, theme, fixed_month, fixed_day, calc_month, calc_week, calc_dow, active = h
            status = "✓" if active else "✗"
            if fixed_month:
                date_str = f"{fixed_month}/{fixed_day}"
            else:
                dow_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                week_names = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 5: "5th", -1: "last"}
                dow_name = dow_names[calc_dow] if calc_dow is not None else "?"
                week_name = week_names.get(calc_week, "?")
                date_str = f"{week_name} {dow_name} of month {calc_month}"
            print(f"  {status} {name:30s} → {theme:15s} ({date_str})")
        
        # Check some specific dates
        print("\n=== Testing Specific Dates ===")
        test_dates = [
            (1, 1, "New Year's Day"),
            (2, 14, "Valentine's Day"),
            (12, 25, "Christmas Day"),
        ]
        
        for month, day, expected_name in test_dates:
            result = db.execute(
                text("""
                    SELECT name, theme FROM holidays
                    WHERE active = true
                      AND fixed_month = :month
                      AND fixed_day = :day
                    LIMIT 1
                """),
                {"month": month, "day": day}
            ).fetchone()
            if result:
                print(f"  ✓ {month}/{day}: {result[0]} (theme: {result[1]})")
            else:
                print(f"  ✗ {month}/{day}: Expected {expected_name} but not found")
        
    finally:
        db.close()


def test_themed_qotd_availability():
    """Check if we have QOTD questions for each holiday theme."""
    print("\n=== Checking QOTD Question Availability by Theme ===")
    
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        # Get all unique holiday themes
        holiday_themes = db.execute(
            text("SELECT DISTINCT theme FROM holidays WHERE active = true ORDER BY theme")
        ).fetchall()
        
        for (theme,) in holiday_themes:
            count = db.execute(
                text("SELECT COUNT(*) FROM push_qotd_questions WHERE theme = :theme"),
                {"theme": theme}
            ).scalar()
            
            status = "✓" if count > 0 else "⚠"
            print(f"  {status} {theme:15s}: {count} question(s)")
        
    finally:
        db.close()


def main():
    print("=" * 70)
    print("HOLIDAY DETECTION TEST")
    print("=" * 70)
    
    test_nth_weekday_calculation()
    test_holiday_detection()
    test_themed_qotd_availability()
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
