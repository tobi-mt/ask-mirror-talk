#!/usr/bin/env python3
"""
Theme Performance Analytics for Ask Mirror Talk Notifications.

Analyzes which themes perform best across different strategies:
- Holiday themes
- Weekday themes
- Normal rotation
- Personalized messages

Usage:
  python3 scripts/analyze_theme_performance.py [--days 30] [--detailed]
"""

import sys
import os
from datetime import datetime, timedelta
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text
from app.core.db import get_session_local


def parse_args():
    parser = argparse.ArgumentParser(description="Analyze notification theme performance")
    parser.add_argument("--days", type=int, default=30, help="Number of days to analyze (default: 30)")
    parser.add_argument("--detailed", action="store_true", help="Show detailed breakdown")
    return parser.parse_args()


def print_header(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def analyze_overall_performance(db, since_date):
    """Show overall theme performance across all notifications."""
    print_header("OVERALL THEME PERFORMANCE")
    
    results = db.execute(
        text("""
            SELECT 
                metadata_json::json->>'theme' AS theme,
                COUNT(*) AS total_sent,
                COUNT(DISTINCT metadata_json::json->>'day_name') AS days_active
            FROM product_events
            WHERE event_name IN ('themed_notification_sent_qotd', 'themed_notification_sent_midday_motivation')
              AND created_at >= :since
              AND metadata_json::json->>'theme' IS NOT NULL
            GROUP BY metadata_json::json->>'theme'
            ORDER BY total_sent DESC
        """),
        {"since": since_date}
    ).fetchall()
    
    if not results:
        print("  No theme data found for this period.")
        return
    
    print(f"\n{'Theme':20s} {'Sent':>10s} {'Active Days':>12s}")
    print("-" * 80)
    for theme, sent, days in results:
        print(f"{theme:20s} {sent:>10d} {days:>12d}")
    
    total = sum(r[1] for r in results)
    print("-" * 80)
    print(f"{'TOTAL':20s} {total:>10d}")


def analyze_by_strategy(db, since_date):
    """Show performance breakdown by selection strategy."""
    print_header("PERFORMANCE BY SELECTION STRATEGY")
    
    results = db.execute(
        text("""
            SELECT 
                metadata_json::json->>'strategy' AS strategy,
                COUNT(*) AS total_sent,
                COUNT(DISTINCT metadata_json::json->>'theme') AS unique_themes
            FROM product_events
            WHERE event_name IN ('themed_notification_sent_qotd', 'themed_notification_sent_midday_motivation')
              AND created_at >= :since
              AND metadata_json::json->>'strategy' IS NOT NULL
            GROUP BY metadata_json::json->>'strategy'
            ORDER BY total_sent DESC
        """),
        {"since": since_date}
    ).fetchall()
    
    if not results:
        print("  No strategy data found for this period.")
        return
    
    total = sum(r[1] for r in results)
    
    print(f"\n{'Strategy':20s} {'Sent':>10s} {'%':>8s} {'Themes':>10s}")
    print("-" * 80)
    for strategy, sent, themes in results:
        pct = (sent / total * 100) if total > 0 else 0
        print(f"{strategy:20s} {sent:>10d} {pct:>7.1f}% {themes:>10d}")
    print("-" * 80)
    print(f"{'TOTAL':20s} {total:>10d} {100.0:>7.1f}%")


def analyze_by_day_of_week(db, since_date):
    """Show performance by day of week."""
    print_header("PERFORMANCE BY DAY OF WEEK")
    
    results = db.execute(
        text("""
            SELECT 
                metadata_json::json->>'day_name' AS day_name,
                metadata_json::json->>'strategy' AS strategy,
                COUNT(*) AS total_sent
            FROM product_events
            WHERE event_name IN ('themed_notification_sent_qotd', 'themed_notification_sent_midday_motivation')
              AND created_at >= :since
              AND metadata_json::json->>'day_name' IS NOT NULL
            GROUP BY metadata_json::json->>'day_name', metadata_json::json->>'strategy'
            ORDER BY 
                CASE metadata_json::json->>'day_name'
                    WHEN 'Monday' THEN 1
                    WHEN 'Tuesday' THEN 2
                    WHEN 'Wednesday' THEN 3
                    WHEN 'Thursday' THEN 4
                    WHEN 'Friday' THEN 5
                    WHEN 'Saturday' THEN 6
                    WHEN 'Sunday' THEN 7
                END,
                total_sent DESC
        """),
        {"since": since_date}
    ).fetchall()
    
    if not results:
        print("  No day-of-week data found for this period.")
        return
    
    # Group by day
    days = {}
    for day, strategy, count in results:
        if day not in days:
            days[day] = {"total": 0, "strategies": {}}
        days[day]["total"] += count
        days[day]["strategies"][strategy] = count
    
    print(f"\n{'Day':12s} {'Total':>10s} {'Holiday':>10s} {'Weekday':>10s} {'Normal':>10s} {'Personal':>10s}")
    print("-" * 80)
    
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for day in day_order:
        if day in days:
            data = days[day]
            total = data["total"]
            holiday = data["strategies"].get("holiday", 0)
            weekday = data["strategies"].get("weekday", 0)
            normal = data["strategies"].get("normal", 0)
            personal = data["strategies"].get("personalized", 0)
            print(f"{day:12s} {total:>10d} {holiday:>10d} {weekday:>10d} {normal:>10d} {personal:>10d}")


def analyze_holiday_performance(db, since_date):
    """Show performance of holiday-themed notifications."""
    print_header("HOLIDAY THEME PERFORMANCE")
    
    results = db.execute(
        text("""
            SELECT 
                metadata_json::json->>'holiday_name' AS holiday_name,
                metadata_json::json->>'theme' AS theme,
                COUNT(*) AS total_sent,
                MIN(created_at::date) AS first_sent,
                MAX(created_at::date) AS last_sent
            FROM product_events
            WHERE event_name IN ('themed_notification_sent_qotd', 'themed_notification_sent_midday_motivation')
              AND created_at >= :since
              AND metadata_json::json->>'strategy' = 'holiday'
              AND metadata_json::json->>'holiday_name' IS NOT NULL
            GROUP BY metadata_json::json->>'holiday_name', metadata_json::json->>'theme'
            ORDER BY MAX(created_at) DESC
        """),
        {"since": since_date}
    ).fetchall()
    
    if not results:
        print("  No holiday notifications found for this period.")
        return
    
    print(f"\n{'Holiday':30s} {'Theme':15s} {'Sent':>8s} {'Date':>12s}")
    print("-" * 80)
    for holiday, theme, sent, first, last in results:
        date_str = str(last) if last else str(first)
        print(f"{holiday:30s} {theme:15s} {sent:>8d} {date_str:>12s}")


def analyze_notification_type(db, since_date):
    """Compare QOTD vs Midday Motivation performance."""
    print_header("QOTD vs MIDDAY MOTIVATION")
    
    results = db.execute(
        text("""
            SELECT 
                CASE 
                    WHEN event_name = 'themed_notification_sent_qotd' THEN 'QOTD'
                    WHEN event_name = 'themed_notification_sent_midday_motivation' THEN 'Midday'
                    ELSE 'Other'
                END AS notification_type,
                metadata_json::json->>'strategy' AS strategy,
                COUNT(*) AS total_sent
            FROM product_events
            WHERE event_name IN ('themed_notification_sent_qotd', 'themed_notification_sent_midday_motivation')
              AND created_at >= :since
            GROUP BY notification_type, strategy
            ORDER BY notification_type, total_sent DESC
        """),
        {"since": since_date}
    ).fetchall()
    
    if not results:
        print("  No notification type data found for this period.")
        return
    
    # Group by type
    types = {}
    for ntype, strategy, count in results:
        if ntype not in types:
            types[ntype] = {"total": 0, "strategies": {}}
        types[ntype]["total"] += count
        types[ntype]["strategies"][strategy] = count
    
    print(f"\n{'Type':12s} {'Total':>10s} {'Holiday':>10s} {'Weekday':>10s} {'Normal':>10s} {'Personal':>10s}")
    print("-" * 80)
    
    for ntype in ["QOTD", "Midday"]:
        if ntype in types:
            data = types[ntype]
            total = data["total"]
            holiday = data["strategies"].get("holiday", 0)
            weekday = data["strategies"].get("weekday", 0)
            normal = data["strategies"].get("normal", 0)
            personal = data["strategies"].get("personalized", 0)
            print(f"{ntype:12s} {total:>10d} {holiday:>10d} {weekday:>10d} {normal:>10d} {personal:>10d}")


def analyze_detailed_themes(db, since_date):
    """Show detailed theme breakdown by strategy."""
    print_header("DETAILED THEME BREAKDOWN BY STRATEGY")
    
    results = db.execute(
        text("""
            SELECT 
                metadata_json::json->>'theme' AS theme,
                metadata_json::json->>'strategy' AS strategy,
                COUNT(*) AS total_sent,
                COUNT(DISTINCT created_at::date) AS days_active
            FROM product_events
            WHERE event_name IN ('themed_notification_sent_qotd', 'themed_notification_sent_midday_motivation')
              AND created_at >= :since
              AND metadata_json::json->>'theme' IS NOT NULL
            GROUP BY metadata_json::json->>'theme', metadata_json::json->>'strategy'
            ORDER BY metadata_json::json->>'theme', total_sent DESC
        """),
        {"since": since_date}
    ).fetchall()
    
    if not results:
        print("  No detailed theme data found for this period.")
        return
    
    current_theme = None
    for theme, strategy, sent, days in results:
        if theme != current_theme:
            if current_theme:
                print()
            print(f"\n{theme}:")
            current_theme = theme
        print(f"  {strategy:15s}: {sent:>6d} sent across {days:>3d} days")


def main():
    args = parse_args()
    
    SessionLocal = get_session_local()
    db = SessionLocal()
    
    try:
        since_date = datetime.now() - timedelta(days=args.days)
        
        print("=" * 80)
        print("THEME PERFORMANCE ANALYTICS")
        print("=" * 80)
        print(f"\nAnalyzing last {args.days} days (since {since_date.date()})")
        
        analyze_overall_performance(db, since_date)
        analyze_by_strategy(db, since_date)
        analyze_by_day_of_week(db, since_date)
        analyze_notification_type(db, since_date)
        analyze_holiday_performance(db, since_date)
        
        if args.detailed:
            analyze_detailed_themes(db, since_date)
        
        print("\n" + "=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80)
        print("\nTip: Use --detailed flag for more granular theme breakdown")
        print("     Use --days N to change the analysis window")
        
    finally:
        db.close()


if __name__ == "__main__":
    main()
