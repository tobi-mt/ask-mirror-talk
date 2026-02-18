#!/usr/bin/env python3
"""
Test MMR Episode Diversity Algorithm

This script tests the MMR implementation by:
1. Asking multiple questions
2. Tracking which episodes are cited
3. Calculating diversity metrics
4. Comparing to expected behavior

Run: python scripts/test_mmr_diversity.py
"""

import sys
import os
from collections import Counter

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.indexing.embeddings import embed_text
from app.qa.retrieval import retrieve_chunks, load_episode_map


def test_mmr_diversity():
    """Test MMR algorithm with multiple questions"""
    
    # Test questions covering different topics
    test_questions = [
        "What does Matt say about self-awareness?",
        "How can I improve my relationships?",
        "What is the Hoffman Process?",
        "Tell me about meditation and mindfulness",
        "How do I deal with difficult emotions?",
        "What advice does Matt give about career?",
    ]
    
    print("=" * 80)
    print("🧪 Testing MMR Episode Diversity Algorithm")
    print("=" * 80)
    print()
    
    db: Session = SessionLocal()()
    all_episode_ids = []
    question_results = []
    
    try:
        for i, question in enumerate(test_questions, 1):
            print(f"Question {i}: {question}")
            print("-" * 80)
            
            # Get embedding and retrieve chunks
            query_embedding = embed_text(question)
            retrieved = retrieve_chunks(db, query_embedding)
            
            # Get episode info
            episode_ids = [chunk.episode_id for chunk, _ in retrieved]
            episode_map = load_episode_map(db, episode_ids)
            
            # Display results
            print(f"Found {len(retrieved)} chunks from {len(set(episode_ids))} unique episodes")
            print()
            
            for j, (chunk, similarity) in enumerate(retrieved, 1):
                episode = episode_map.get(chunk.episode_id)
                if episode:
                    print(f"  {j}. Episode {episode.id}: {episode.title[:60]}...")
                    print(f"     Similarity: {similarity:.3f}")
                    print()
            
            # Track for analysis
            all_episode_ids.extend(episode_ids)
            question_results.append({
                'question': question,
                'episode_ids': episode_ids,
                'similarities': [sim for _, sim in retrieved]
            })
            
            print()
        
        # Analyze diversity
        print("=" * 80)
        print("📊 Diversity Analysis")
        print("=" * 80)
        print()
        
        # Total unique episodes
        unique_episodes = set(all_episode_ids)
        total_citations = len(all_episode_ids)
        
        print(f"Total Citations: {total_citations}")
        print(f"Unique Episodes: {len(unique_episodes)}")
        print(f"Diversity Rate: {len(unique_episodes) / total_citations * 100:.1f}%")
        print()
        
        # Most common episodes
        episode_counts = Counter(all_episode_ids)
        print("Top 10 Most Cited Episodes:")
        for episode_id, count in episode_counts.most_common(10):
            percentage = count / total_citations * 100
            print(f"  Episode {episode_id}: {count} times ({percentage:.1f}%)")
        print()
        
        # Calculate overlap between questions
        print("Question Overlap Analysis:")
        overlaps = []
        for i in range(len(question_results)):
            for j in range(i + 1, len(question_results)):
                set_i = set(question_results[i]['episode_ids'])
                set_j = set(question_results[j]['episode_ids'])
                overlap = len(set_i & set_j)
                total = len(set_i | set_j)
                overlap_pct = overlap / total * 100 if total > 0 else 0
                overlaps.append(overlap_pct)
        
        avg_overlap = sum(overlaps) / len(overlaps) if overlaps else 0
        print(f"  Average Overlap: {avg_overlap:.1f}%")
        print("  Expected: 33-50% (with MMR)")
        print("  Baseline: ~83% (without MMR)")
        print()
        
        # Relevance check (first result should be highly relevant)
        print("Relevance Quality Check:")
        avg_top_similarity = sum(r['similarities'][0] for r in question_results) / len(question_results)
        avg_all_similarity = sum(sum(r['similarities']) for r in question_results) / total_citations
        
        print(f"  Avg Top Result Similarity: {avg_top_similarity:.3f}")
        print(f"  Avg All Results Similarity: {avg_all_similarity:.3f}")
        print(f"  Top/Avg Ratio: {avg_top_similarity / avg_all_similarity:.2f}x")
        print()
        
        # Success criteria
        print("=" * 80)
        print("✅ Success Criteria")
        print("=" * 80)
        print()
        
        criteria = [
            ("Diversity Rate > 70%", len(unique_episodes) / total_citations > 0.70),
            ("Average Overlap < 60%", avg_overlap < 60),
            ("Top Result Highly Relevant", avg_top_similarity > 0.3),
            ("No Episode Dominates (< 30%)", max(episode_counts.values()) / total_citations < 0.30),
        ]
        
        all_passed = True
        for criterion, passed in criteria:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status}: {criterion}")
            if not passed:
                all_passed = False
        
        print()
        
        if all_passed:
            print("🎉 All criteria passed! MMR is working correctly.")
        else:
            print("⚠️  Some criteria failed. Consider tuning DIVERSITY_LAMBDA.")
            print()
            print("Tuning suggestions:")
            if avg_overlap > 60:
                print("  - Decrease DIVERSITY_LAMBDA (e.g., 0.5-0.6) for more diversity")
            if avg_top_similarity < 0.3:
                print("  - Increase DIVERSITY_LAMBDA (e.g., 0.8-0.9) for more relevance")
        
        print()
        
    finally:
        db.close()


if __name__ == "__main__":
    test_mmr_diversity()
