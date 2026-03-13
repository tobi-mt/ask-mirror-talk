#!/usr/bin/env python3
"""
Generate UX/Analytics Report for Ask Mirror Talk
Analyzes user behavior, engagement metrics, and provides actionable insights
"""

import sys
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import defaultdict
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, func
from app.core.db import SessionLocal
from app.storage.models import QALog, CitationClick, UserFeedback, Episode


def print_header(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def analyze_engagement_metrics(db, days=7):
    """Analyze overall engagement metrics"""
    print_header(f"📊 ENGAGEMENT METRICS (Last {days} Days)")
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Total questions asked
    total_questions = db.query(func.count(QALog.id)).filter(
        QALog.created_at >= cutoff
    ).scalar()
    
    # Unique users (by IP)
    unique_users = db.query(func.count(func.distinct(QALog.user_ip))).filter(
        QALog.created_at >= cutoff
    ).scalar()
    
    # Average questions per user
    avg_questions_per_user = total_questions / unique_users if unique_users > 0 else 0
    
    # Average latency
    avg_latency = db.query(func.avg(QALog.latency_ms)).filter(
        QALog.created_at >= cutoff
    ).scalar() or 0
    
    # Citation clicks
    total_clicks = db.query(func.count(CitationClick.id)).filter(
        CitationClick.clicked_at >= cutoff
    ).scalar()
    
    # Citation click rate
    click_rate = (total_clicks / total_questions * 100) if total_questions > 0 else 0
    
    # Feedback count
    positive_feedback = db.query(func.count(UserFeedback.id)).filter(
        UserFeedback.created_at >= cutoff,
        UserFeedback.feedback_type == 'positive'
    ).scalar()
    
    negative_feedback = db.query(func.count(UserFeedback.id)).filter(
        UserFeedback.created_at >= cutoff,
        UserFeedback.feedback_type == 'negative'
    ).scalar()
    
    total_feedback = positive_feedback + negative_feedback
    satisfaction_rate = (positive_feedback / total_feedback * 100) if total_feedback > 0 else 0
    
    print(f"Total Questions:        {total_questions:,}")
    print(f"Unique Users:           {unique_users:,}")
    print(f"Avg Q per User:         {avg_questions_per_user:.2f}")
    print(f"Avg Response Time:      {avg_latency:.0f}ms")
    print(f"Citation Clicks:        {total_clicks:,}")
    print(f"Click-through Rate:     {click_rate:.1f}%")
    print(f"Positive Feedback:      {positive_feedback}")
    print(f"Negative Feedback:      {negative_feedback}")
    print(f"Satisfaction Rate:      {satisfaction_rate:.1f}%")
    
    # Trend analysis
    print(f"\n📈 TRENDS:")
    compare_days = days * 2
    prev_cutoff = datetime.now(timezone.utc) - timedelta(days=compare_days)
    prev_questions = db.query(func.count(QALog.id)).filter(
        QALog.created_at >= prev_cutoff,
        QALog.created_at < cutoff
    ).scalar()
    
    if prev_questions > 0:
        growth_rate = ((total_questions - prev_questions) / prev_questions * 100)
        trend_icon = "📈" if growth_rate > 0 else "📉"
        print(f"{trend_icon} Question Volume:    {growth_rate:+.1f}%")
    
    return {
        'total_questions': total_questions,
        'unique_users': unique_users,
        'avg_latency': avg_latency,
        'click_rate': click_rate,
        'satisfaction_rate': satisfaction_rate
    }


def analyze_popular_topics(db, days=7):
    """Analyze most popular topics from questions"""
    print_header(f"🔥 POPULAR TOPICS (Last {days} Days)")
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Get most asked questions
    query = text("""
        SELECT 
            question,
            COUNT(*) as count
        FROM qa_logs
        WHERE created_at >= :cutoff
        GROUP BY question
        ORDER BY count DESC
        LIMIT 10
    """)
    
    result = db.execute(query, {"cutoff": cutoff})
    rows = result.fetchall()
    
    if not rows:
        print("No data available.\n")
        return
    
    for i, row in enumerate(rows, 1):
        question = row[0][:60] + "..." if len(row[0]) > 60 else row[0]
        count = row[1]
        print(f"{i:2d}. [{count:3d}x] {question}")


def analyze_episode_engagement(db, days=7):
    """Analyze most cited episodes"""
    print_header(f"🎙️ TOP EPISODES (Last {days} Days)")
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    query = text("""
        SELECT 
            e.id,
            e.title,
            COUNT(DISTINCT c.id) as clicks,
            COUNT(DISTINCT q.id) as mentions
        FROM episodes e
        LEFT JOIN citation_clicks c ON c.episode_id = e.id AND c.clicked_at >= :cutoff
        LEFT JOIN qa_logs q ON q.episode_ids LIKE '%' || CAST(e.id AS TEXT) || '%' 
            AND q.created_at >= :cutoff
        WHERE clicks > 0 OR mentions > 0
        GROUP BY e.id, e.title
        ORDER BY clicks DESC, mentions DESC
        LIMIT 15
    """)
    
    result = db.execute(query, {"cutoff": cutoff})
    rows = result.fetchall()
    
    if not rows:
        print("No episode engagement data available.\n")
        return
    
    for i, row in enumerate(rows, 1):
        episode_id = row[0]
        title = row[1][:50] + "..." if len(row[1]) > 50 else row[1]
        clicks = row[2]
        mentions = row[3]
        engagement_score = clicks * 2 + mentions  # Weight clicks higher
        print(f"{i:2d}. Ep {episode_id:3d}: {title}")
        print(f"     📊 {mentions} mentions | 👆 {clicks} clicks | Score: {engagement_score}")


def analyze_user_journey(db, days=7):
    """Analyze user journey patterns"""
    print_header(f"🗺️ USER JOURNEY ANALYSIS (Last {days} Days)")
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Questions by hour of day
    query = text("""
        SELECT 
            EXTRACT(HOUR FROM created_at) as hour,
            COUNT(*) as count
        FROM qa_logs
        WHERE created_at >= :cutoff
        GROUP BY hour
        ORDER BY hour
    """)
    
    result = db.execute(query, {"cutoff": cutoff})
    rows = result.fetchall()
    
    if rows:
        print("⏰ Peak Activity Hours:")
        hour_data = {int(row[0]): row[1] for row in rows}
        max_count = max(hour_data.values()) if hour_data else 1
        
        for hour in range(24):
            count = hour_data.get(hour, 0)
            bar_length = int((count / max_count) * 30) if max_count > 0 else 0
            bar = "█" * bar_length
            print(f"   {hour:02d}:00 | {bar} {count}")
    
    # Return rate (users who come back)
    query = text("""
        SELECT 
            user_ip,
            COUNT(DISTINCT DATE(created_at)) as visit_days
        FROM qa_logs
        WHERE created_at >= :cutoff
        GROUP BY user_ip
        HAVING COUNT(DISTINCT DATE(created_at)) > 1
    """)
    
    result = db.execute(query, {"cutoff": cutoff})
    returning_users = len(result.fetchall())
    
    total_users = db.query(func.count(func.distinct(QALog.user_ip))).filter(
        QALog.created_at >= cutoff
    ).scalar()
    
    return_rate = (returning_users / total_users * 100) if total_users > 0 else 0
    
    print(f"\n🔄 User Retention:")
    print(f"   Returning Users:  {returning_users}/{total_users} ({return_rate:.1f}%)")


def generate_recommendations(metrics):
    """Generate actionable recommendations based on metrics"""
    print_header("💡 RECOMMENDATIONS")
    
    recommendations = []
    
    # Performance recommendations
    if metrics['avg_latency'] > 3000:
        recommendations.append({
            'priority': 'HIGH',
            'category': 'Performance',
            'issue': f"Average response time is {metrics['avg_latency']:.0f}ms (target: <3s)",
            'action': "• Implement Redis caching for frequent questions\n"
                     "• Optimize embedding retrieval queries\n"
                     "• Consider using smaller OpenAI model for faster responses"
        })
    
    # Engagement recommendations
    if metrics['click_rate'] < 20:
        recommendations.append({
            'priority': 'MEDIUM',
            'category': 'Engagement',
            'issue': f"Citation click rate is only {metrics['click_rate']:.1f}% (target: >30%)",
            'action': "• Make episode citations more prominent\n"
                     "• Add inline audio player previews\n"
                     "• Show episode thumbnails\n"
                     "• Add 'Why this episode?' context"
        })
    
    # User satisfaction recommendations
    if metrics['satisfaction_rate'] < 80 and metrics['satisfaction_rate'] > 0:
        recommendations.append({
            'priority': 'HIGH',
            'category': 'Quality',
            'issue': f"User satisfaction is {metrics['satisfaction_rate']:.1f}% (target: >85%)",
            'action': "• Review negative feedback for patterns\n"
                     "• Improve answer quality with better prompts\n"
                     "• Add clarifying questions before answering\n"
                     "• Implement answer quality self-assessment"
        })
    
    # Growth recommendations
    if metrics['total_questions'] < 100:
        recommendations.append({
            'priority': 'MEDIUM',
            'category': 'Growth',
            'issue': f"Low question volume ({metrics['total_questions']} questions/week)",
            'action': "• Increase QOTD push notification frequency\n"
                     "• Add social sharing features\n"
                     "• Create compelling og:image cards\n"
                     "• Launch daily challenge program"
        })
    
    # Retention recommendations
    avg_per_user = metrics['total_questions'] / metrics['unique_users'] if metrics['unique_users'] > 0 else 0
    if avg_per_user < 2:
        recommendations.append({
            'priority': 'HIGH',
            'category': 'Retention',
            'issue': f"Low engagement per user ({avg_per_user:.1f} questions/user)",
            'action': "• Implement streak tracking and gamification\n"
                     "• Add personalized question recommendations\n"
                     "• Create user profile with progress tracking\n"
                     "• Send follow-up notifications for related content"
        })
    
    # Print recommendations
    if not recommendations:
        print("✅ All metrics look great! Keep up the good work.\n")
        print("💡 Consider implementing Priority 2-3 features from UX_IMPROVEMENT_PLAN.md\n")
        return
    
    for rec in recommendations:
        priority_icon = "🔴" if rec['priority'] == 'HIGH' else "🟡"
        print(f"{priority_icon} [{rec['priority']}] {rec['category']}")
        print(f"   Issue:  {rec['issue']}")
        print(f"   Action: {rec['action']}")
        print()


def generate_summary_report(db, days=7):
    """Generate complete summary report"""
    print("\n" + "="*80)
    print(f"  ASK MIRROR TALK - UX/ANALYTICS REPORT")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Run all analyses
    metrics = analyze_engagement_metrics(db, days)
    analyze_popular_topics(db, days)
    analyze_episode_engagement(db, days)
    analyze_user_journey(db, days)
    generate_recommendations(metrics)
    
    print_header("📋 NEXT STEPS")
    print("1. Review recommendations above")
    print("2. Check UX_IMPROVEMENT_PLAN.md for detailed features")
    print("3. Test new v4.0 enhancements on staging")
    print("4. Monitor metrics after deploying improvements")
    print("5. Run this report weekly to track progress")
    print()
    
    print("🚀 Quick Wins Deployed (v4.0):")
    print("   ✅ Enhanced visual feedback & micro-interactions")
    print("   ✅ Progress indicators with time estimation")
    print("   ✅ Haptic feedback for mobile")
    print("   ✅ Reading time calculations")
    print("   ✅ Success celebrations")
    print("   ✅ Skeleton loaders")
    print("   ✅ Smooth animations")
    print()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Generate UX/Analytics Report')
    parser.add_argument('--days', type=int, default=7, help='Number of days to analyze')
    args = parser.parse_args()
    
    db = SessionLocal()
    try:
        generate_summary_report(db, args.days)
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == '__main__':
    main()
