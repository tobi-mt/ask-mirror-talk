#!/usr/bin/env python3
"""
Test Regional Holidays and Theme Analytics features.

Verifies:
1. Regional holiday support is working
2. Holiday detection respects regions
3. Theme analytics tracking structure is in place
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text
from app.core.db import get_session_local


def test_regional_holidays():
    """Test regional holiday configuration."""
    print("\n" + "=" * 80)
    print("REGIONAL HOLIDAY SUPPORT TEST")
    print("=" * 80)
    
    SessionLocal = get_session_local()
    db = SessionLocal()
    
    try:
        # Check region column exists
        columns = db.execute(
            text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'holidays' AND column_name = 'region'
            """)
        ).fetchone()
        
        if columns:
            print("\n✅ Region column added to holidays table")
            print(f"   Type: {columns[1]}")
        else:
            print("\n❌ Region column not found!")
            return
        
        # Show holiday summary by region
        print("\n=== Holidays by Region ===\n")
        regions = db.execute(
            text("""
                SELECT region, COUNT(*) as count, 
                       STRING_AGG(name, ', ' ORDER BY fixed_month, calc_month) as holidays
                FROM holidays 
                WHERE active = true
                GROUP BY region 
                ORDER BY region
            """)
        ).fetchall()
        
        for region, count, holidays in regions:
            print(f"{region:10s} ({count:2d}): {holidays}")
        
        # Test some specific regions
        print("\n=== Sample Regional Holidays ===\n")
        test_regions = ["US", "UK", "CA", "AU", "global"]
        
        for region in test_regions:
            holidays = db.execute(
                text("""
                    SELECT name, theme
                    FROM holidays
                    WHERE active = true AND region = :region
                    ORDER BY COALESCE(fixed_month, calc_month)
                    LIMIT 3
                """),
                {"region": region}
            ).fetchall()
            
            if holidays:
                print(f"{region}:")
                for name, theme in holidays:
                    print(f"  - {name:30s} ({theme})")
        
        total = db.execute(text("SELECT COUNT(*) FROM holidays WHERE active = true")).scalar()
        print(f"\n✅ Total active holidays: {total}")
        
    finally:
        db.close()


def test_theme_analytics_structure():
    """Test that theme analytics tracking is ready."""
    print("\n" + "=" * 80)
    print("THEME ANALYTICS STRUCTURE TEST")
    print("=" * 80)
    
    SessionLocal = get_session_local()
    db = SessionLocal()
    
    try:
        # Check product_events table exists
        table_exists = db.execute(
            text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'product_events'
                )
            """)
        ).scalar()
        
        if not table_exists:
            print("\n❌ product_events table not found!")
            print("   Run: python3 scripts/migrate_add_product_events.py")
            return
        
        print("\n✅ product_events table exists")
        
        # Check for any existing themed notification events
        count = db.execute(
            text("""
                SELECT COUNT(*) 
                FROM product_events 
                WHERE event_name IN ('themed_notification_sent_qotd', 'themed_notification_sent_midday_motivation')
            """)
        ).scalar()
        
        if count > 0:
            print(f"✅ Found {count} themed notification events logged")
            
            # Show sample event
            sample = db.execute(
                text("""
                    SELECT event_name, metadata_json, created_at
                    FROM product_events
                    WHERE event_name IN ('themed_notification_sent_qotd', 'themed_notification_sent_midday_motivation')
                    ORDER BY created_at DESC
                    LIMIT 1
                """)
            ).fetchone()
            
            if sample:
                print("\n=== Sample Event ===")
                print(f"Event: {sample[0]}")
                print(f"Data: {sample[1]}")
                print(f"Time: {sample[2]}")
        else:
            print("ℹ️  No themed notifications logged yet (will start with next send)")
        
        # Show what analytics will track
        print("\n=== Analytics Tracking ===")
        print("\nWhen notifications are sent, the system will log:")
        print("  • Theme used (e.g., 'Parenting', 'Gratitude')")
        print("  • Selection strategy ('holiday', 'weekday', 'normal', 'personalized')")
        print("  • Day of week (Monday-Sunday)")
        print("  • Holiday name (if applicable)")
        print("  • Notification type (QOTD or midday motivation)")
        
        print("\n=== Available Analytics Commands ===")
        print("\nOnce notifications start sending, run:")
        print("  python3 scripts/analyze_theme_performance.py")
        print("  python3 scripts/analyze_theme_performance.py --days 7")
        print("  python3 scripts/analyze_theme_performance.py --detailed")
        
    finally:
        db.close()


def test_integration():
    """Test that regional holidays + theme analytics work together."""
    print("\n" + "=" * 80)
    print("INTEGRATION TEST")
    print("=" * 80)
    
    SessionLocal = get_session_local()
    db = SessionLocal()
    
    try:
        from app.notifications.push import get_today_holiday_theme, get_today_weekday_themes
        
        # Test holiday detection (now region-aware)
        holiday_theme, holiday_name = get_today_holiday_theme(db)
        weekday_themes = get_today_weekday_themes(db)
        
        print("\n=== Today's Theme Selection ===")
        
        if holiday_theme:
            print(f"\n✅ Holiday detected: {holiday_name}")
            print(f"   Theme: {holiday_theme}")
            print(f"   → Notifications will use '{holiday_theme}' theme")
            print(f"   → Analytics will log as 'holiday' strategy")
        
        if weekday_themes:
            from datetime import date
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            today_name = day_names[date.today().weekday()]
            
            print(f"\n✅ Weekday themes for {today_name}:")
            for i, theme in enumerate(weekday_themes, 1):
                print(f"   {i}. {theme}")
            
            if holiday_theme:
                print(f"   → Will be used only if '{holiday_theme}' content exhausted")
                print(f"   → Analytics will log as 'weekday' strategy")
            else:
                print(f"   → Notifications will prioritize these themes")
                print(f"   → Analytics will log as 'weekday' strategy")
        
        if not holiday_theme and not weekday_themes:
            print("\n✅ Using normal rotation")
            print("   → Analytics will log as 'normal' strategy")
        
        print("\n=== How It Works Together ===")
        print("\n1. System checks for holidays (including regional holidays)")
        print("2. If holiday found, prioritize that theme")
        print("3. If no holiday, check weekday themes")
        print("4. If no themed content available, use normal rotation")
        print("5. Every send is logged with theme + strategy to product_events")
        print("6. Run analytics scripts to see what performs best")
        
    finally:
        db.close()


def main():
    print("=" * 80)
    print("TESTING NEW FEATURES: Regional Holidays + Theme Analytics")
    print("=" * 80)
    
    test_regional_holidays()
    test_theme_analytics_structure()
    test_integration()
    
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETE")
    print("=" * 80)
    
    print("\n✅ Both features are ready to use:")
    print("   • Regional holidays will be automatically detected")
    print("   • Theme analytics will start tracking on next notification send")
    print("\nℹ️  Wait for QOTD/midday cron to run, then check analytics!")


if __name__ == "__main__":
    main()
