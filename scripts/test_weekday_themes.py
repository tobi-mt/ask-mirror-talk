#!/usr/bin/env python3
"""
Test weekday theme detection and prioritization.

This script verifies that:
1. Weekday themes are correctly configured for each day
2. Theme prioritization works as expected
3. The system correctly identifies today's themes
"""

import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text
from app.core.db import get_session_local
from app.notifications.push import get_today_weekday_themes


def test_weekday_configuration():
    """Display the complete weekday theme configuration."""
    print("\n=== Weekday Theme Configuration ===")
    
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        for day_num in range(7):
            print(f"\n{day_names[day_num]}:")
            themes = db.execute(
                text("""
                    SELECT theme, priority, description
                    FROM weekday_themes
                    WHERE active = true AND day_of_week = :dow
                    ORDER BY priority DESC
                """),
                {"dow": day_num}
            ).fetchall()
            
            if themes:
                for theme, priority, description in themes:
                    print(f"  {priority:2d}. {theme:15s} - {description}")
            else:
                print("  (no themes configured)")
                
    finally:
        db.close()


def test_today_detection():
    """Test detection of today's weekday themes."""
    print("\n=== Today's Weekday Themes ===")
    
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        today = date.today()
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        today_name = day_names[today.weekday()]
        
        themes = get_today_weekday_themes(db)
        
        if themes:
            print(f"✓ TODAY ({today_name}, {today}):")
            print(f"  Priority themes: {', '.join(themes)}")
        else:
            print(f"ℹ TODAY ({today_name}, {today}): No weekday themes configured")
            
    finally:
        db.close()


def test_theme_question_availability():
    """Check how many QOTD questions are available for each weekday theme."""
    print("\n=== QOTD Question Availability by Weekday Theme ===")
    
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        # Get all unique themes from weekday_themes
        themes = db.execute(
            text("SELECT DISTINCT theme FROM weekday_themes WHERE active = true ORDER BY theme")
        ).fetchall()
        
        for (theme,) in themes:
            count = db.execute(
                text("SELECT COUNT(*) FROM push_qotd_questions WHERE theme = :theme"),
                {"theme": theme}
            ).scalar()
            
            status = "✓" if count > 0 else "⚠"
            print(f"  {status} {theme:15s}: {count} question(s)")
            
    finally:
        db.close()


def test_motivation_availability():
    """Check how many midday motivation messages are available for each weekday theme."""
    print("\n=== Midday Motivation Availability by Weekday Theme ===")
    
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        # Get all unique themes from weekday_themes
        themes = db.execute(
            text("SELECT DISTINCT theme FROM weekday_themes WHERE active = true ORDER BY theme")
        ).fetchall()
        
        for (theme,) in themes:
            count = db.execute(
                text("SELECT COUNT(*) FROM push_motivation_messages WHERE theme = :theme"),
                {"theme": theme}
            ).scalar()
            
            status = "✓" if count > 0 else "⚠"
            print(f"  {status} {theme:15s}: {count} message(s)")
            
    finally:
        db.close()


def test_weekly_pattern():
    """Show what themes would be prioritized for the next 7 days."""
    print("\n=== Next 7 Days Theme Preview ===")
    
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        today = date.today()
        
        for i in range(7):
            test_date = today + timedelta(days=i)
            day_num = test_date.weekday()
            day_name = day_names[day_num]
            
            themes = db.execute(
                text("""
                    SELECT theme FROM weekday_themes
                    WHERE active = true AND day_of_week = :dow
                    ORDER BY priority DESC
                    LIMIT 2
                """),
                {"dow": day_num}
            ).fetchall()
            
            theme_str = ", ".join([t[0] for t in themes]) if themes else "none"
            marker = "→" if i == 0 else " "
            print(f"  {marker} {test_date} ({day_name:9s}): {theme_str}")
            
    finally:
        db.close()


def main():
    print("=" * 70)
    print("WEEKDAY THEME DETECTION TEST")
    print("=" * 70)
    
    test_weekday_configuration()
    test_today_detection()
    test_theme_question_availability()
    test_motivation_availability()
    test_weekly_pattern()
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
