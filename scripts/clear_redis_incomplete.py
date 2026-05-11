#!/usr/bin/env python3
"""
Immediately clear incomplete answers from Redis cache.
Run this in production to clean up incomplete answers without waiting for restart.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.qa.cache import get_answer_cache, normalize_question, _is_incomplete_answer


def clear_incomplete_from_redis():
    """Clear incomplete answers from Redis immediately."""
    cache = get_answer_cache()
    
    if not cache._redis:
        print("⚠️  No Redis connection - cache is in-memory only")
        return
    
    print("🔍 Scanning Redis for incomplete cached answers...")
    print("=" * 80)
    
    try:
        # Get all cache entry keys from Redis
        keys = cache._redis.zrange(cache._redis_index_key, 0, -1)
        print(f"Found {len(keys)} total cache entries in Redis")
        print()
        
        deleted_count = 0
        checked_count = 0
        
        for key in keys:
            raw = cache._redis.get(key)
            if raw is None:
                continue
            
            entry = cache._deserialize_entry(raw)
            if entry is None:
                continue
            
            checked_count += 1
            answer = entry.response.get("answer", "")
            
            # Check if incomplete
            if _is_incomplete_answer(answer):
                deleted_count += 1
                print(f"✗ INCOMPLETE: {entry.question[:70]}...")
                print(f"  Ends with: '...{answer[-50:]}'")
                print(f"  Hit count: {entry.hit_count}")
                
                # Delete from Redis
                cache._redis.delete(key)
                cache._redis.zrem(cache._redis_index_key, key)
                print(f"  ✓ Deleted from Redis")
                print()
        
        print("=" * 80)
        print(f"Checked {checked_count} entries")
        print(f"Deleted {deleted_count} incomplete answers from Redis")
        
        if deleted_count > 0:
            print()
            print("✓ Incomplete answers removed from Redis!")
            print("⚠️  Note: In-memory cache still has incomplete answers until app restarts")
            print("   Consider restarting the app or waiting for next deploy")
        else:
            print()
            print("✓ No incomplete answers found in Redis - cache is clean!")
        
    except Exception as e:
        print(f"✗ Error scanning Redis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    clear_incomplete_from_redis()
