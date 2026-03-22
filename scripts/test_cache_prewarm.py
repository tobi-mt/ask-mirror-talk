#!/usr/bin/env python3
"""Test the DB-based cache prewarm."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.db import get_session_local
from app.qa.cache import get_answer_cache, prewarm_from_db_history

cache = get_answer_cache()
db = get_session_local()()
try:
    n = prewarm_from_db_history(cache, db, limit=40)
    print(f"Prewarm loaded: {n} entries")
    stats = cache.stats()
    print(f"Cache stats: {stats}")
    # Test that a known top question now hits the cache
    if n > 0:
        from sqlalchemy import text
        sample = db.execute(text(
            "SELECT question FROM qa_logs GROUP BY question ORDER BY COUNT(*) DESC LIMIT 1"
        )).scalar()
        if sample:
            from app.qa.cache import normalize_question
            from app.indexing.embeddings import embed_text
            norm_q = normalize_question(sample)
            emb = embed_text(norm_q)
            hit = cache.get(norm_q, emb)
            print(f"Cache hit for top question '{sample[:60]}': {'✅ HIT' if hit else '❌ MISS'}")
finally:
    db.close()
