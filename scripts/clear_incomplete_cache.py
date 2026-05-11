#!/usr/bin/env python3
"""
Clear incomplete cached answers from the cache.

This script identifies and removes cached answers that are incomplete
(e.g., ending mid-sentence) to prevent them from being served to users.
"""

import sys
import os

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.qa.cache import get_answer_cache, normalize_question


def clear_incomplete_answer(question: str):
    """Clear a specific cached answer by question."""
    cache = get_answer_cache()
    norm_q = normalize_question(question)
    
    # Check if it exists and what it contains
    cached = cache.get_exact(norm_q)
    if cached:
        answer = cached.get("answer", "")
        print(f"Found cached answer:")
        print(f"  Question: {question}")
        print(f"  Answer length: {len(answer)} chars")
        print(f"  Answer ends with: '...{answer[-100:]}'")
        print()
        
        # Delete it
        if cache.delete(norm_q):
            print("✓ Successfully deleted incomplete cached answer")
        else:
            print("✗ Failed to delete cached answer")
    else:
        print(f"No cached answer found for: {question}")


if __name__ == "__main__":
    # The specific question that has an incomplete cached answer
    question = "What does rest really look like in a culture of hustle?"
    
    print(f"Clearing incomplete cached answer for: {question}")
    print("-" * 80)
    
    clear_incomplete_answer(question)
    
    print()
    print("Cache stats after deletion:")
    cache = get_answer_cache()
    stats = cache.stats()
    print(f"  Total entries: {stats['entries']}")
    print(f"  Total hits: {stats['total_hits']}")
