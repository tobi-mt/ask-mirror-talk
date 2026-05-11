#!/usr/bin/env python3
"""
Scan and clean incomplete cached answers.

This script scans the entire cache for incomplete answers
(ending mid-sentence, too short, etc.) and removes them.
"""

import sys
import os

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.qa.cache import get_answer_cache, _is_incomplete_answer


def scan_and_clean_cache():
    """Scan the cache for incomplete answers and remove them."""
    cache = get_answer_cache()
    
    print("Scanning cache for incomplete answers...")
    print("-" * 80)
    
    incomplete_count = 0
    total_entries = 0
    
    with cache._lock:
        entries_to_delete = []
        
        for entry in cache._entries:
            total_entries += 1
            answer = entry.response.get("answer", "")
            
            if _is_incomplete_answer(answer):
                incomplete_count += 1
                entries_to_delete.append(entry.question)
                
                print(f"\n✗ Found incomplete answer:")
                print(f"  Question: {entry.question}")
                print(f"  Answer length: {len(answer)} chars")
                print(f"  Answer ends: '...{answer[-80:]}'")
                print(f"  Hit count: {entry.hit_count}")
    
    print()
    print("=" * 80)
    print(f"Scan complete: Found {incomplete_count} incomplete answers out of {total_entries} total entries")
    
    if incomplete_count > 0:
        print()
        response = input(f"Delete {incomplete_count} incomplete cached answers? (y/N): ")
        if response.lower() == 'y':
            deleted = 0
            for question in entries_to_delete:
                if cache.delete(question):
                    deleted += 1
            print(f"\n✓ Successfully deleted {deleted} incomplete cached answers")
        else:
            print("\nNo changes made.")
    else:
        print("\n✓ No incomplete answers found - cache is clean!")
    
    print()
    print("Final cache stats:")
    stats = cache.stats()
    print(f"  Total entries: {stats['entries']}")
    print(f"  Max entries: {stats['max_entries']}")
    print(f"  Total hits: {stats['total_hits']}")
    print(f"  TTL: {stats['ttl_seconds']}s")
    print(f"  Similarity threshold: {stats['similarity_threshold']}")


if __name__ == "__main__":
    scan_and_clean_cache()
