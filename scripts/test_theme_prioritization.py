#!/usr/bin/env python3
"""
Combined test for holiday + weekday theme detection.

Shows the complete theme prioritization system in action:
1. Holiday themes (highest priority)
2. Weekday themes (medium priority)
3. Normal rotation (fallback)
"""

import sys
import os
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text
from app.core.db import get_session_local
from app.notifications.push import get_today_holiday_theme, get_today_weekday_themes


def test_combined_theme_selection():
    """Show how holiday and weekday themes work together."""
    print("=" * 70)
    print("COMBINED THEME SELECTION TEST")
    print("=" * 70)
    
    SessionLocal = get_session_local()
    db = SessionLocal()
    
    try:
        today = date.today()
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        today_name = day_names[today.weekday()]
        
        print(f"\nToday: {today} ({today_name})")
        print("-" * 70)
        
        # Check for holiday
        holiday_theme, holiday_name = get_today_holiday_theme(db)
        
        # Check for weekday themes
        weekday_themes = get_today_weekday_themes(db)
        
        # Display the prioritization
        print("\n🎯 THEME PRIORITIZATION:")
        print()
        
        if holiday_theme:
            print(f"  ⭐ PRIORITY 1 - HOLIDAY THEME")
            print(f"     🎉 {holiday_name}")
            print(f"     → Theme: {holiday_theme}")
            print()
            
        if weekday_themes:
            print(f"  📅 PRIORITY 2 - WEEKDAY THEMES")
            print(f"     {today_name} prioritization:")
            for i, theme in enumerate(weekday_themes, 1):
                print(f"     {i}. {theme}")
            print()
        
        print(f"  🔄 PRIORITY 3 - NORMAL ROTATION")
        print(f"     Any unseen question/message")
        print()
        
        # Show what will actually be used
        print("=" * 70)
        print("ACTIVE SELECTION STRATEGY:")
        print("=" * 70)
        
        if holiday_theme:
            print(f"\n✅ Today's QOTD/Midday will prioritize: {holiday_theme}")
            print(f"   Reason: {holiday_name} (holiday overrides weekday themes)")
            
            if weekday_themes:
                print(f"\n   (If {holiday_theme} content is exhausted, will use:")
                print(f"    {', '.join(weekday_themes[:2])})")
        elif weekday_themes:
            print(f"\n✅ Today's QOTD/Midday will prioritize: {', '.join(weekday_themes[:2])}")
            print(f"   Reason: {today_name} weekday theming")
        else:
            print(f"\n✅ Today's QOTD/Midday will use: Normal rotation")
            print(f"   Reason: No special themes configured")
        
        # Show content availability for active themes
        print("\n" + "=" * 70)
        print("CONTENT AVAILABILITY FOR ACTIVE THEMES:")
        print("=" * 70)
        
        active_themes = []
        if holiday_theme:
            active_themes.append(holiday_theme)
        if weekday_themes:
            active_themes.extend(weekday_themes[:2])
        
        if active_themes:
            print("\nQOTD Questions:")
            for theme in active_themes:
                count = db.execute(
                    text("SELECT COUNT(*) FROM push_qotd_questions WHERE theme = :theme"),
                    {"theme": theme}
                ).scalar()
                status = "✓" if count > 0 else "⚠"
                print(f"  {status} {theme:15s}: {count} question(s)")
            
            print("\nMidday Motivation Messages:")
            for theme in active_themes:
                count = db.execute(
                    text("SELECT COUNT(*) FROM push_motivation_messages WHERE theme = :theme"),
                    {"theme": theme}
                ).scalar()
                status = "✓" if count > 0 else "⚠"
                print(f"  {status} {theme:15s}: {count} message(s)")
        
        print("\n" + "=" * 70)
        
    finally:
        db.close()


if __name__ == "__main__":
    test_combined_theme_selection()
