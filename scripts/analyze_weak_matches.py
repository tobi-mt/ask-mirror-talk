#!/usr/bin/env python3
"""
Analyze weak match / unanswered questions to identify content gaps.

Helps understand what topics users are asking about that we don't have
good coverage for in the episode library.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, create_engine
from app.core.config import settings


def analyze_weak_matches(days: int = 180):
    """Analyze weak match questions and identify patterns."""
    engine = create_engine(str(settings.database_url))
    
    with engine.connect() as db:
        # Get all unanswered/weak match questions
        query = text("""
            SELECT 
                question,
                user_ip,
                created_at,
                latency_ms,
                is_answered,
                episode_ids
            FROM qa_logs
            WHERE 
                is_answered = FALSE
                AND created_at >= NOW() - INTERVAL ':days days'
            ORDER BY created_at DESC
        """)
        
        results = db.execute(query, {"days": days}).fetchall()
        
        if not results:
            print("✅ No weak matches found! All questions are being answered well.")
            return
        
        print(f"\n{'='*80}")
        print(f"📊 WEAK MATCH ANALYSIS - Last {days} Days")
        print(f"Total weak matches: {len(results)}")
        print(f"{'='*80}\n")
        
        # Group by similar keywords to find patterns
        keyword_counts = {}
        for row in results:
            question = row[0].lower()
            words = question.split()
            # Extract meaningful words (ignore common words)
            stop_words = {'how', 'what', 'why', 'when', 'where', 'who', 'do', 'i', 'a', 'an', 'the', 'is', 'am', 'are', 'to', 'from', 'with', 'about', 'my', 'me', 'myself'}
            keywords = [w.strip('?.!,') for w in words if w.strip('?.!,') not in stop_words and len(w) > 3]
            
            for keyword in keywords:
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        # Show top keywords in unanswered questions
        print("🔍 TOP KEYWORDS IN UNANSWERED QUESTIONS:")
        print("-" * 80)
        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
        for keyword, count in sorted_keywords[:20]:
            print(f"   {keyword:25s} → {count:3d} times")
        
        print(f"\n{'='*80}")
        print("📋 FULL LIST OF UNANSWERED QUESTIONS:")
        print(f"{'='*80}\n")
        
        for i, row in enumerate(results, 1):
            question, ip, created, latency, is_answered, episode_ids = row
            citations = len(episode_ids) if episode_ids else 0
            print(f"{i}. {question}")
            print(f"   Asked: {created}")
            print(f"   Answered: {is_answered} | Citations: {citations} | Latency: {latency or 0}ms")
            print()
        
        print(f"{'='*80}")
        print("💡 RECOMMENDATIONS:")
        print(f"{'='*80}\n")
        print("1. Look for patterns in the keywords above - do certain topics repeat?")
        print("2. Consider these actions:")
        print("   • Ingest episodes covering these topics")
        print("   • Pre-warm cache with best-effort answers for common questions")
        print("   • Update question guardrails if questions are off-topic")
        print("   • Review citation threshold settings if match scores are borderline")
        print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Analyze weak match questions")
    parser.add_argument("--days", type=int, default=180, help="Number of days to analyze")
    args = parser.parse_args()
    
    analyze_weak_matches(args.days)
