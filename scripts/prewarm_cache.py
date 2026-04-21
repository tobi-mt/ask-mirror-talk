#!/usr/bin/env python3
"""
Pre-warm the answer cache with most commonly asked questions.

Runs the top N questions through the QA system and caches the results,
so future users get instant responses for popular queries.

Should be run after deploys or when new episodes are ingested.
"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, create_engine
from app.core.config import settings
from app.qa.service import answer_question
from app.core.db import get_session_local


TOP_QUESTIONS = [
    # Top 20 from analytics - manually curated
    "What does courage look like in everyday life?",
    "How do I stop comparing myself to others?",
    "How do I love someone without losing myself?",
    "How do I set boundaries without feeling guilty?",
    "What can I learn from failure?",
    "How do I deal with grief and loss?",
    "How do I reconnect with my faith after doubt?",
    "How do I find peace when everything feels uncertain?",
    "How do I carry grief without losing myself?",
    "How do I stop running from my emotions?",
    "How do I deal with loneliness even when I'm surrounded by people?",
    "What does forgiveness require when trust has been damaged deeply?",
    "What does it mean to truly forgive someone?",
    "How do I move forward after a major life change?",
    "How can I rebuild trust after it's been broken?",
    "How do I have hard conversations without damaging the relationship?",
    "What does it mean to love myself first?",
    "How do I stop people-pleasing?",
    "What's the difference between confidence and arrogance?",
    "How do I know if I'm growing or just getting older?",
]


async def prewarm_cache(questions: list[str] | None = None, force: bool = False):
    """Pre-warm the cache with common questions."""
    questions_to_cache = questions or TOP_QUESTIONS
    
    print(f"\n{'='*80}")
    print(f"🔥 CACHE PRE-WARMING")
    print(f"{'='*80}\n")
    print(f"Questions to cache: {len(questions_to_cache)}")
    print(f"Force refresh: {force}")
    print()
    
    success_count = 0
    error_count = 0
    
    SessionLocal = get_session_local()
    
    for i, question in enumerate(questions_to_cache, 1):
        print(f"[{i}/{len(questions_to_cache)}] Pre-warming: {question}")
        db = SessionLocal()
        try:
            result = answer_question(
                db=db,
                question=question,
                user_ip="cache-prewarm",
                log_interaction=False,  # Don't log prewarm queries
                bypass_cache=force,
            )
            
            if result.get("cached"):
                print(f"   ✓ Already cached (similarity: {result.get('cache_similarity', 0):.2f})")
            else:
                print(f"   ✓ Cached! ({len(result.get('citations', []))} citations, {result.get('latency_ms', 0):.0f}ms)")
            
            success_count += 1
            
        except Exception as e:
            print(f"   ✗ Error: {e}")
            error_count += 1
        finally:
            db.close()
        
        print()
    
    print(f"{'='*80}")
    print(f"✅ Pre-warming complete!")
    print(f"   Success: {success_count}/{len(questions_to_cache)}")
    print(f"   Errors: {error_count}")
    print(f"{'='*80}\n")


def get_top_questions_from_analytics(days: int = 180, limit: int = 30) -> list[str]:
    """Get most asked questions from analytics."""
    engine = create_engine(str(settings.database_url))
    
    with engine.connect() as db:
        query = text("""
            SELECT question, COUNT(*) as count
            FROM qa_logs
            WHERE created_at >= NOW() - INTERVAL ':days days'
                AND is_answered = TRUE
            GROUP BY question
            ORDER BY count DESC
            LIMIT :limit
        """)
        
        results = db.execute(query, {"days": days, "limit": limit}).fetchall()
        return [row[0] for row in results]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Pre-warm answer cache")
    parser.add_argument("--from-analytics", action="store_true", help="Use top questions from analytics instead of hardcoded list")
    parser.add_argument("--days", type=int, default=180, help="Days of analytics to consider (with --from-analytics)")
    parser.add_argument("--limit", type=int, default=30, help="Number of top questions to cache (with --from-analytics)")
    parser.add_argument("--force", action="store_true", help="Force refresh even if already cached")
    args = parser.parse_args()
    
    questions = None
    if args.from_analytics:
        print("📊 Fetching top questions from analytics...")
        questions = get_top_questions_from_analytics(args.days, args.limit)
        print(f"Found {len(questions)} questions\n")
    
    asyncio.run(prewarm_cache(questions, force=args.force))
