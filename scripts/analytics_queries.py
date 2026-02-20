#!/usr/bin/env python3
"""
Analytics SQL Queries for Ask Mirror Talk

This script provides ready-to-use SQL queries to analyze existing qa_logs data.
Run individual queries or generate a complete analytics report.

Usage:
    python scripts/analytics_queries.py --all              # Run all queries
    python scripts/analytics_queries.py --questions        # Most common questions
    python scripts/analytics_queries.py --episodes         # Most cited episodes
    python scripts/analytics_queries.py --trends           # Usage trends
    python scripts/analytics_queries.py --days 30          # Analyze last 30 days
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.db import SessionLocal


def run_query(db, query, params=None, description=""):
    """Run a query and display results"""
    print(f"\n{'='*80}")
    print(f"📊 {description}")
    print(f"{'='*80}\n")
    
    try:
        result = db.execute(text(query), params or {})
        rows = result.fetchall()
        
        if not rows:
            print("No data found.\n")
            return
        
        # Print column headers
        if result.keys():
            headers = list(result.keys())
            print(" | ".join(str(h).ljust(20) for h in headers))
            print("-" * (len(headers) * 23))
        
        # Print rows
        for row in rows:
            print(" | ".join(str(val)[:20].ljust(20) for val in row))
        
        print(f"\n{len(rows)} rows returned.\n")
        
    except Exception as e:
        print(f"❌ Error: {e}\n")


def analyze_common_questions(db, days=7):
    """Find most frequently asked questions"""
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    query = """
        SELECT 
            question,
            COUNT(*) as count,
            AVG(latency_ms) as avg_latency,
            MIN(created_at) as first_asked,
            MAX(created_at) as last_asked
        FROM qa_logs 
        WHERE created_at >= :cutoff
        GROUP BY question 
        ORDER BY count DESC 
        LIMIT 20
    """
    
    run_query(
        db, query, {"cutoff": cutoff},
        f"Most Common Questions (Last {days} Days)"
    )


def analyze_cited_episodes(db, days=7):
    """Find most frequently cited episodes"""
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    query = """
        SELECT 
            e.id,
            e.title,
            e.published_at,
            COUNT(*) as citation_count,
            COUNT(DISTINCT q.id) as unique_questions
        FROM qa_logs q
        CROSS JOIN LATERAL UNNEST(STRING_TO_ARRAY(q.episode_ids, ',')) AS episode_id
        JOIN episodes e ON e.id = episode_id::int
        WHERE q.created_at >= :cutoff
        GROUP BY e.id, e.title, e.published_at
        ORDER BY citation_count DESC
        LIMIT 20
    """
    
    run_query(
        db, query, {"cutoff": cutoff},
        f"Most Cited Episodes (Last {days} Days)"
    )


def analyze_usage_trends(db, days=30):
    """Analyze usage trends over time"""
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    query = """
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as total_questions,
            COUNT(DISTINCT user_ip) as unique_users,
            AVG(latency_ms) as avg_latency_ms,
            MIN(latency_ms) as min_latency_ms,
            MAX(latency_ms) as max_latency_ms
        FROM qa_logs
        WHERE created_at >= :cutoff
        GROUP BY DATE(created_at)
        ORDER BY date DESC
    """
    
    run_query(
        db, query, {"cutoff": cutoff},
        f"Daily Usage Trends (Last {days} Days)"
    )


def analyze_user_behavior(db, days=7):
    """Analyze user behavior patterns"""
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    query = """
        SELECT 
            user_ip,
            COUNT(*) as total_questions,
            AVG(latency_ms) as avg_latency,
            MIN(created_at) as first_question,
            MAX(created_at) as last_question,
            EXTRACT(EPOCH FROM (MAX(created_at) - MIN(created_at)))/3600 as hours_active
        FROM qa_logs
        WHERE created_at >= :cutoff
        GROUP BY user_ip
        HAVING COUNT(*) > 1
        ORDER BY total_questions DESC
        LIMIT 20
    """
    
    run_query(
        db, query, {"cutoff": cutoff},
        f"Most Active Users (Last {days} Days)"
    )


def analyze_episode_diversity(db, days=7):
    """Analyze episode diversity in citations"""
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    query = """
        WITH question_episode_counts AS (
            SELECT 
                q.id,
                q.question,
                ARRAY_LENGTH(STRING_TO_ARRAY(q.episode_ids, ','), 1) as num_episodes_cited
            FROM qa_logs q
            WHERE q.created_at >= :cutoff
        )
        SELECT 
            num_episodes_cited,
            COUNT(*) as question_count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
        FROM question_episode_counts
        GROUP BY num_episodes_cited
        ORDER BY num_episodes_cited
    """
    
    run_query(
        db, query, {"cutoff": cutoff},
        f"Episode Diversity Distribution (Last {days} Days)"
    )


def analyze_latency_breakdown(db, days=7):
    """Analyze response time distribution"""
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    query = """
        SELECT 
            CASE 
                WHEN latency_ms < 1000 THEN '< 1s'
                WHEN latency_ms < 2000 THEN '1-2s'
                WHEN latency_ms < 3000 THEN '2-3s'
                WHEN latency_ms < 5000 THEN '3-5s'
                ELSE '> 5s'
            END as latency_bucket,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
        FROM qa_logs
        WHERE created_at >= :cutoff
        GROUP BY latency_bucket
        ORDER BY 
            CASE latency_bucket
                WHEN '< 1s' THEN 1
                WHEN '1-2s' THEN 2
                WHEN '2-3s' THEN 3
                WHEN '3-5s' THEN 4
                ELSE 5
            END
    """
    
    run_query(
        db, query, {"cutoff": cutoff},
        f"Response Time Distribution (Last {days} Days)"
    )


def analyze_hourly_patterns(db, days=7):
    """Analyze usage patterns by hour of day"""
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    query = """
        SELECT 
            EXTRACT(HOUR FROM created_at) as hour_of_day,
            COUNT(*) as total_questions,
            COUNT(DISTINCT user_ip) as unique_users,
            AVG(latency_ms) as avg_latency
        FROM qa_logs
        WHERE created_at >= :cutoff
        GROUP BY hour_of_day
        ORDER BY hour_of_day
    """
    
    run_query(
        db, query, {"cutoff": cutoff},
        f"Hourly Usage Patterns (Last {days} Days, UTC)"
    )


def generate_summary_report(db, days=7):
    """Generate a comprehensive summary report"""
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    print("\n" + "="*80)
    print(f"📊 ANALYTICS SUMMARY REPORT - Last {days} Days")
    print(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("="*80)
    
    # Overall metrics
    total_questions = db.execute(
        text("SELECT COUNT(*) FROM qa_logs WHERE created_at >= :cutoff"),
        {"cutoff": cutoff}
    ).scalar()
    
    unique_users = db.execute(
        text("SELECT COUNT(DISTINCT user_ip) FROM qa_logs WHERE created_at >= :cutoff"),
        {"cutoff": cutoff}
    ).scalar()
    
    avg_latency = db.execute(
        text("SELECT AVG(latency_ms) FROM qa_logs WHERE created_at >= :cutoff"),
        {"cutoff": cutoff}
    ).scalar()
    
    total_episodes = db.execute(text("SELECT COUNT(*) FROM episodes")).scalar()
    total_chunks = db.execute(text("SELECT COUNT(*) FROM chunks")).scalar()
    
    print(f"\n📈 Overall Metrics:")
    print(f"   Total Questions: {total_questions or 0}")
    print(f"   Unique Users: {unique_users or 0}")
    print(f"   Avg Response Time: {round(avg_latency, 2) if avg_latency else 0}ms")
    print(f"   Total Episodes: {total_episodes or 0}")
    print(f"   Total Chunks: {total_chunks or 0}")
    
    # Run all analyses
    analyze_common_questions(db, days)
    analyze_cited_episodes(db, days)
    analyze_episode_diversity(db, days)
    analyze_latency_breakdown(db, days)
    analyze_usage_trends(db, days)
    
    print("\n" + "="*80)
    print("✅ Report Complete")
    print("="*80 + "\n")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run analytics queries on Ask Mirror Talk data")
    parser.add_argument("--all", action="store_true", help="Run all queries (summary report)")
    parser.add_argument("--questions", action="store_true", help="Analyze common questions")
    parser.add_argument("--episodes", action="store_true", help="Analyze cited episodes")
    parser.add_argument("--trends", action="store_true", help="Analyze usage trends")
    parser.add_argument("--users", action="store_true", help="Analyze user behavior")
    parser.add_argument("--diversity", action="store_true", help="Analyze episode diversity")
    parser.add_argument("--latency", action="store_true", help="Analyze response times")
    parser.add_argument("--hourly", action="store_true", help="Analyze hourly patterns")
    parser.add_argument("--days", type=int, default=7, help="Number of days to analyze (default: 7)")
    
    args = parser.parse_args()
    
    # Default to --all if no specific query is selected
    if not any([args.all, args.questions, args.episodes, args.trends, args.users, 
                args.diversity, args.latency, args.hourly]):
        args.all = True
    
    db = SessionLocal()()  # Call SessionLocal() to get the session factory, then call it again to get a session instance
    
    try:
        if args.all:
            generate_summary_report(db, args.days)
        else:
            if args.questions:
                analyze_common_questions(db, args.days)
            if args.episodes:
                analyze_cited_episodes(db, args.days)
            if args.trends:
                analyze_usage_trends(db, args.days)
            if args.users:
                analyze_user_behavior(db, args.days)
            if args.diversity:
                analyze_episode_diversity(db, args.days)
            if args.latency:
                analyze_latency_breakdown(db, args.days)
            if args.hourly:
                analyze_hourly_patterns(db, args.days)
    
    except Exception as e:
        print(f"\n❌ Error running analytics: {e}\n")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    main()
