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
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.db import SessionLocal

INTERNAL_USER_IP = "cache-prewarm"
PLACEHOLDER_QUESTION_SQL = """
AND COALESCE(TRIM(question), '') != ''
AND LOWER(TRIM(question)) NOT IN ('{{question}}', '{question}', '[question]', '<question>', 'question')
AND TRIM(question) !~ '^\\{\\{[^}]+\\}\\}$'
AND TRIM(question) !~ '^\\{[^}]+\\}$'
AND TRIM(question) !~ '^\\[[^]]+\\]$'
AND TRIM(question) !~ '^<[^>]+>$'
"""


def _with_internal_filter(query: str, table_alias: str | None = None) -> str:
    target = f"{table_alias}.user_ip" if table_alias else "user_ip"
    return query.replace("{{INTERNAL_FILTER}}", f"AND COALESCE({target}, '') != :internal_user_ip")


def _with_question_quality_filter(query: str, table_alias: str | None = None) -> str:
    target = f"{table_alias}.question" if table_alias else "question"
    clause = PLACEHOLDER_QUESTION_SQL.replace("question", target)
    return query.replace("{{QUESTION_FILTER}}", clause)


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
            # Calculate column widths based on content
            col_widths = [len(str(h)) for h in headers]
            for row in rows:
                for i, val in enumerate(row):
                    col_widths[i] = max(col_widths[i], len(str(val)))
            
            print(" | ".join(str(h).ljust(col_widths[i]) for i, h in enumerate(headers)))
            print("-+-".join("-" * w for w in col_widths))
        
        # Print rows
        for row in rows:
            print(" | ".join(str(val).ljust(col_widths[i]) for i, val in enumerate(row)))
        
        print(f"\n{len(rows)} rows returned.\n")
        
    except Exception as e:
        print(f"❌ Error: {e}\n")
        db.rollback()


def analyze_common_questions(db, days=7):
    """Find most frequently asked questions"""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    query = """
        SELECT 
            question,
            COUNT(*) as count,
            AVG(latency_ms) as avg_latency,
            MIN(created_at) as first_asked,
            MAX(created_at) as last_asked
        FROM qa_logs 
        WHERE created_at >= :cutoff
          {{INTERNAL_FILTER}}
          {{QUESTION_FILTER}}
        GROUP BY question 
        ORDER BY count DESC 
        LIMIT 20
    """
    
    run_query(
        db, _with_question_quality_filter(_with_internal_filter(query)), {"cutoff": cutoff, "internal_user_ip": INTERNAL_USER_IP},
        f"Most Common Questions (Last {days} Days)"
    )


def analyze_cited_episodes(db, days=7):
    """Find most frequently cited episodes"""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
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
          {{INTERNAL_FILTER}}
          {{QUESTION_FILTER}}
        GROUP BY e.id, e.title, e.published_at
        ORDER BY citation_count DESC
        LIMIT 20
    """
    
    run_query(
        db, _with_question_quality_filter(_with_internal_filter(query, "q"), "q"), {"cutoff": cutoff, "internal_user_ip": INTERNAL_USER_IP},
        f"Most Cited Episodes (Last {days} Days)"
    )


def analyze_usage_trends(db, days=30):
    """Analyze usage trends over time"""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
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
          {{INTERNAL_FILTER}}
          {{QUESTION_FILTER}}
        GROUP BY DATE(created_at)
        ORDER BY date DESC
    """
    
    run_query(
        db, _with_question_quality_filter(_with_internal_filter(query)), {"cutoff": cutoff, "internal_user_ip": INTERNAL_USER_IP},
        f"Daily Usage Trends (Last {days} Days)"
    )


def analyze_user_behavior(db, days=7):
    """Analyze user behavior patterns"""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
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
          {{INTERNAL_FILTER}}
          {{QUESTION_FILTER}}
        GROUP BY user_ip
        HAVING COUNT(*) > 1
        ORDER BY total_questions DESC
        LIMIT 20
    """
    
    run_query(
        db, _with_question_quality_filter(_with_internal_filter(query)), {"cutoff": cutoff, "internal_user_ip": INTERNAL_USER_IP},
        f"Most Active Users (Last {days} Days)"
    )


def analyze_episode_diversity(db, days=7):
    """Analyze episode diversity in citations"""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    query = """
        WITH question_episode_counts AS (
            SELECT 
                q.id,
                q.question,
                ARRAY_LENGTH(STRING_TO_ARRAY(q.episode_ids, ','), 1) as num_episodes_cited
            FROM qa_logs q
            WHERE q.created_at >= :cutoff
              {{INTERNAL_FILTER}}
              {{QUESTION_FILTER}}
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
        db, _with_question_quality_filter(_with_internal_filter(query, "q"), "q"), {"cutoff": cutoff, "internal_user_ip": INTERNAL_USER_IP},
        f"Episode Diversity Distribution (Last {days} Days)"
    )


def analyze_latency_breakdown(db, days=7):
    """Analyze response time distribution"""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
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
          {{INTERNAL_FILTER}}
          {{QUESTION_FILTER}}
        GROUP BY 
            CASE 
                WHEN latency_ms < 1000 THEN '< 1s'
                WHEN latency_ms < 2000 THEN '1-2s'
                WHEN latency_ms < 3000 THEN '2-3s'
                WHEN latency_ms < 5000 THEN '3-5s'
                ELSE '> 5s'
            END
        ORDER BY 
            MIN(latency_ms)
    """
    
    run_query(
        db, _with_question_quality_filter(_with_internal_filter(query)), {"cutoff": cutoff, "internal_user_ip": INTERNAL_USER_IP},
        f"Response Time Distribution (Last {days} Days)"
    )


def analyze_cache_performance(db, days=7):
    """Analyze cache hit rate and latency by cache status."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    query = """
        SELECT
            CASE WHEN is_cached THEN 'cached' ELSE 'fresh' END as response_type,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage,
            ROUND(AVG(latency_ms), 2) as avg_latency_ms,
            MIN(latency_ms) as min_latency_ms,
            MAX(latency_ms) as max_latency_ms
        FROM qa_logs
        WHERE created_at >= :cutoff
          {{INTERNAL_FILTER}}
          {{QUESTION_FILTER}}
        GROUP BY is_cached
        ORDER BY is_cached DESC
    """

    run_query(
        db, _with_question_quality_filter(_with_internal_filter(query)), {"cutoff": cutoff, "internal_user_ip": INTERNAL_USER_IP},
        f"Cache Performance (Last {days} Days)"
    )


def analyze_bursty_usage(db, days=30):
    """Find days dominated by a small number of IPs or repeated questions."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    query = """
        WITH daily_ip_counts AS (
            SELECT
                DATE(created_at) AS day,
                user_ip,
                COUNT(*) AS question_count
            FROM qa_logs
            WHERE created_at >= :cutoff
              {{INTERNAL_FILTER}}
              {{QUESTION_FILTER}}
            GROUP BY DATE(created_at), user_ip
        ),
        daily_totals AS (
            SELECT
                DATE(created_at) AS day,
                COUNT(*) AS total_questions
            FROM qa_logs
            WHERE created_at >= :cutoff
              {{INTERNAL_FILTER}}
              {{QUESTION_FILTER}}
            GROUP BY DATE(created_at)
        ),
        ranked AS (
            SELECT
                d.day,
                d.user_ip,
                d.question_count,
                t.total_questions,
                ROUND(d.question_count * 100.0 / NULLIF(t.total_questions, 0), 2) AS pct_of_day,
                ROW_NUMBER() OVER (PARTITION BY d.day ORDER BY d.question_count DESC, d.user_ip) AS rn
            FROM daily_ip_counts d
            JOIN daily_totals t ON t.day = d.day
        )
        SELECT
            day,
            total_questions,
            user_ip AS top_ip,
            question_count AS top_ip_questions,
            pct_of_day
        FROM ranked
        WHERE rn = 1
        ORDER BY total_questions DESC, pct_of_day DESC
        LIMIT 20
    """

    run_query(
        db, _with_question_quality_filter(_with_internal_filter(query)), {"cutoff": cutoff, "internal_user_ip": INTERNAL_USER_IP},
        f"Bursty Usage Risk — Top IP Share By Day (Last {days} Days)"
    )


def analyze_repeated_question_bursts(db, days=30):
    """Find identical questions repeated heavily on the same day."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    query = """
        SELECT
            DATE(created_at) AS day,
            question,
            COUNT(*) AS repeats,
            COUNT(DISTINCT user_ip) AS unique_users,
            ROUND(AVG(latency_ms), 2) AS avg_latency_ms
        FROM qa_logs
        WHERE created_at >= :cutoff
          {{INTERNAL_FILTER}}
          {{QUESTION_FILTER}}
        GROUP BY DATE(created_at), question
        HAVING COUNT(*) >= 5
        ORDER BY repeats DESC, day DESC
        LIMIT 20
    """

    run_query(
        db, _with_question_quality_filter(_with_internal_filter(query)), {"cutoff": cutoff, "internal_user_ip": INTERNAL_USER_IP},
        f"Repeated Question Bursts (Last {days} Days)"
    )


def analyze_prompt_origin_usage(db, days=30):
    """Show which question origins and prompt systems are being used."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    query = """
        SELECT
            COALESCE(metadata_json::jsonb->>'origin', metadata_json::jsonb->>'label', 'unknown') AS origin,
            COUNT(*) AS event_count,
            COUNT(DISTINCT user_ip) AS unique_users
        FROM product_events
        WHERE created_at >= :cutoff
          AND event_name = 'question_submitted'
        GROUP BY origin
        ORDER BY event_count DESC, origin
    """

    run_query(
        db, query, {"cutoff": cutoff},
        f"Question Origin Breakdown (Last {days} Days)"
    )


def analyze_feature_engagement(db, days=30):
    """Show which engagement surfaces are actually being used."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    query = """
        SELECT
            event_name,
            COALESCE(
                metadata_json::jsonb->>'action',
                metadata_json::jsonb->>'origin',
                metadata_json::jsonb->>'method',
                metadata_json::jsonb->>'theme',
                '—'
            ) AS detail,
            COUNT(*) AS event_count,
            COUNT(DISTINCT user_ip) AS unique_users
        FROM product_events
        WHERE created_at >= :cutoff
          AND event_name IN (
              'question_origin_selected',
              'question_submitted',
              'continuation_action_used',
              'share_cta_used',
              'share_panel_shown',
              'reflection_note_opened',
              'reflection_note_saved',
              'low_match_action'
          )
        GROUP BY event_name, detail
        ORDER BY event_name, event_count DESC, detail
    """

    run_query(
        db, query, {"cutoff": cutoff},
        f"Feature Engagement Breakdown (Last {days} Days)"
    )


def analyze_product_event_mix(db, days=30):
    """Summarize product events to make funnel instrumentation visible."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    query = """
        SELECT
            event_name,
            COUNT(*) AS event_count,
            COUNT(DISTINCT user_ip) AS unique_users
        FROM product_events
        WHERE created_at >= :cutoff
        GROUP BY event_name
        ORDER BY event_count DESC, event_name
    """

    run_query(
        db, query, {"cutoff": cutoff},
        f"Product Event Mix (Last {days} Days)"
    )


def analyze_weak_match_details(db, days=30):
    """Show recent unanswered / no-citation logs so weak-match spikes are actionable."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    query = """
        SELECT
            question,
            COUNT(*) AS weak_logs,
            COUNT(DISTINCT user_ip) AS unique_users,
            MIN(created_at) AS first_seen,
            MAX(created_at) AS last_seen,
            ROUND(AVG(latency_ms), 2) AS avg_latency_ms,
            SUM(CASE WHEN COALESCE(latency_ms, 0) = 0 THEN 1 ELSE 0 END) AS instant_logs
        FROM qa_logs
        WHERE created_at >= :cutoff
          AND is_answered = FALSE
          {{INTERNAL_FILTER}}
          {{QUESTION_FILTER}}
        GROUP BY question
        ORDER BY weak_logs DESC, last_seen DESC
        LIMIT 20
    """

    run_query(
        db,
        _with_question_quality_filter(_with_internal_filter(query)),
        {"cutoff": cutoff, "internal_user_ip": INTERNAL_USER_IP},
        f"Recent Weak Match / No-Citation Questions (Last {days} Days)"
    )


def analyze_hourly_patterns(db, days=7):
    """Analyze usage patterns by hour of day"""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    query = """
        SELECT 
            EXTRACT(HOUR FROM created_at) as hour_of_day,
            COUNT(*) as total_questions,
            COUNT(DISTINCT user_ip) as unique_users,
            AVG(latency_ms) as avg_latency
        FROM qa_logs
        WHERE created_at >= :cutoff
          {{INTERNAL_FILTER}}
          {{QUESTION_FILTER}}
        GROUP BY hour_of_day
        ORDER BY hour_of_day
    """
    
    run_query(
        db, _with_question_quality_filter(_with_internal_filter(query)), {"cutoff": cutoff, "internal_user_ip": INTERNAL_USER_IP},
        f"Hourly Usage Patterns (Last {days} Days, UTC)"
    )


def generate_summary_report(db, days=7):
    """Generate a comprehensive summary report"""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    print("\n" + "="*80)
    print(f"📊 ANALYTICS SUMMARY REPORT - Last {days} Days")
    print(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("="*80)
    
    # Overall metrics
    total_questions = db.execute(
        text(f"SELECT COUNT(*) FROM qa_logs WHERE created_at >= :cutoff AND COALESCE(user_ip, '') != :internal_user_ip {PLACEHOLDER_QUESTION_SQL}"),
        {"cutoff": cutoff, "internal_user_ip": INTERNAL_USER_IP}
    ).scalar()
    
    unique_users = db.execute(
        text(f"SELECT COUNT(DISTINCT user_ip) FROM qa_logs WHERE created_at >= :cutoff AND COALESCE(user_ip, '') != :internal_user_ip {PLACEHOLDER_QUESTION_SQL}"),
        {"cutoff": cutoff, "internal_user_ip": INTERNAL_USER_IP}
    ).scalar()
    
    avg_latency = db.execute(
        text(f"SELECT AVG(latency_ms) FROM qa_logs WHERE created_at >= :cutoff AND COALESCE(user_ip, '') != :internal_user_ip {PLACEHOLDER_QUESTION_SQL}"),
        {"cutoff": cutoff, "internal_user_ip": INTERNAL_USER_IP}
    ).scalar()
    
    total_episodes = db.execute(text("SELECT COUNT(*) FROM episodes")).scalar()
    total_chunks = db.execute(text("SELECT COUNT(*) FROM chunks")).scalar()
    
    print(f"\n📈 Overall Metrics:")
    print(f"   Total Questions: {total_questions or 0}")
    print(f"   Unique Users: {unique_users or 0}")
    print(f"   Avg Response Time: {round(avg_latency, 2) if avg_latency else 0}ms")
    print(f"   Total Episodes: {total_episodes or 0}")
    print(f"   Total Chunks: {total_chunks or 0}")

    cached_questions = db.execute(
        text(f"SELECT COUNT(*) FROM qa_logs WHERE created_at >= :cutoff AND is_cached = TRUE AND COALESCE(user_ip, '') != :internal_user_ip {PLACEHOLDER_QUESTION_SQL}"),
        {"cutoff": cutoff, "internal_user_ip": INTERNAL_USER_IP}
    ).scalar()
    unanswered_questions = db.execute(
        text(f"SELECT COUNT(*) FROM qa_logs WHERE created_at >= :cutoff AND is_answered = FALSE AND COALESCE(user_ip, '') != :internal_user_ip {PLACEHOLDER_QUESTION_SQL}"),
        {"cutoff": cutoff, "internal_user_ip": INTERNAL_USER_IP}
    ).scalar()
    print(f"   Cached Questions: {cached_questions or 0}")
    print(f"   Unanswered / Weak Match Logs: {unanswered_questions or 0}")
    
    # Run all analyses
    analyze_common_questions(db, days)
    analyze_cited_episodes(db, days)
    analyze_episode_diversity(db, days)
    analyze_latency_breakdown(db, days)
    analyze_cache_performance(db, days)
    analyze_usage_trends(db, days)
    analyze_bursty_usage(db, min(days, 30))
    analyze_repeated_question_bursts(db, min(days, 30))
    analyze_prompt_origin_usage(db, min(days, 30))
    analyze_feature_engagement(db, min(days, 30))
    analyze_product_event_mix(db, min(days, 30))
    analyze_weak_match_details(db, min(days, 30))
    
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
    parser.add_argument("--cache", action="store_true", help="Analyze cache performance")
    parser.add_argument("--bursts", action="store_true", help="Analyze bursty traffic concentration")
    parser.add_argument("--origins", action="store_true", help="Analyze prompt and question origin usage")
    parser.add_argument("--days", type=int, default=7, help="Number of days to analyze (default: 7)")
    
    args = parser.parse_args()
    
    # Default to --all if no specific query is selected
    if not any([args.all, args.questions, args.episodes, args.trends, args.users, 
                args.diversity, args.latency, args.hourly, args.cache, args.bursts, args.origins]):
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
            if args.cache:
                analyze_cache_performance(db, args.days)
            if args.bursts:
                analyze_bursty_usage(db, args.days)
                analyze_repeated_question_bursts(db, args.days)
            if args.origins:
                analyze_prompt_origin_usage(db, args.days)
                analyze_product_event_mix(db, args.days)
    
    except Exception as e:
        print(f"\n❌ Error running analytics: {e}\n")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    main()
