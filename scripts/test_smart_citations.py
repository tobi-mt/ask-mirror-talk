"""
Test Smart Episode Citations

This script tests the new smart citation feature by comparing
legacy citation behavior with smart episode selection.

Usage:
    python scripts/test_smart_citations.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from app.core.db import get_session_local
from app.qa.service import answer_question


def test_smart_citations():
    """Test smart citations with sample questions."""
    
    test_questions = [
        "How to overcome addiction",
        "Building healthy relationships",
        "Dealing with anxiety and fear",
        "Finding your purpose in life",
        "How to be successful in business",
    ]
    
    Session = get_session_local()
    db = Session()
    
    try:
        print("="*80)
        print("🧪 Testing Smart Episode Citations")
        print("="*80)
        print()
        
        for idx, question in enumerate(test_questions, 1):
            print(f"\n{'='*80}")
            print(f"Test {idx}/{len(test_questions)}: {question}")
            print(f"{'='*80}\n")
            
            # Test with legacy citations
            print("📝 Legacy Citations (All Chunks):")
            print("-" * 80)
            try:
                legacy_result = answer_question(db, question, "test_ip", use_smart_citations=False)
                legacy_episodes = {}
                for cit in legacy_result["citations"]:
                    ep_id = cit["episode_id"]
                    if ep_id not in legacy_episodes:
                        legacy_episodes[ep_id] = {
                            "title": cit["episode_title"],
                            "count": 0
                        }
                    legacy_episodes[ep_id]["count"] += 1
                
                print(f"Citations: {len(legacy_result['citations'])} chunks")
                print(f"Unique Episodes: {len(legacy_episodes)}")
                for ep_id, data in legacy_episodes.items():
                    print(f"  - {data['title'][:60]}... ({data['count']} chunks)")
            except Exception as e:
                print(f"❌ Error: {e}")
            
            print()
            
            # Test with smart citations
            print("🎯 Smart Citations (Top 5 Episodes):")
            print("-" * 80)
            try:
                smart_result = answer_question(db, question, "test_ip", use_smart_citations=True)
                
                print(f"Citations: {len(smart_result['citations'])} episodes")
                print(f"Unique Episodes: {len(set(c['episode_id'] for c in smart_result['citations']))}")
                
                for idx, cit in enumerate(smart_result["citations"], 1):
                    timestamp = cit.get("timestamp_start", "N/A")
                    title = cit["episode_title"]
                    if len(title) > 55:
                        title = title[:55] + "..."
                    
                    # Show relevance score if available
                    relevance = ""
                    if "relevance_score" in cit:
                        relevance = f" (Relevance: {cit['relevance_score']:.2f})"
                    
                    print(f"  {idx}. [{timestamp}] {title}{relevance}")
                
                print(f"\nAnswer Preview: {smart_result['answer'][:200]}...")
                print(f"Latency: {smart_result['latency_ms']}ms")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()
            
            print()
        
        print("\n" + "="*80)
        print("✅ Test Complete!")
        print("="*80)
        print()
        print("📊 Observations:")
        print("  - Smart citations should show exactly 5 unique episodes")
        print("  - Episodes should be highly relevant to the question")
        print("  - Each episode should have a clear timestamp")
        print("  - Legacy citations may have duplicates or fewer unique episodes")
        print()
        
    finally:
        db.close()


if __name__ == "__main__":
    test_smart_citations()
