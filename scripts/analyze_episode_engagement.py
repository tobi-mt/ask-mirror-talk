#!/usr/bin/env python3
"""
Analyze Episode Engagement Metrics

Tracks:
- Which episodes are being cited
- Episode discovery rate
- Diversity trends over time
- Most/least cited episodes

Run: python scripts/analyze_episode_engagement.py
"""

import sys
import os
from collections import Counter
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, func, text
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.storage.models import Episode, Chunk


def analyze_engagement():
    """Analyze episode engagement metrics"""
    
    print("=" * 80)
    print("📊 Episode Engagement Analysis")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    db: Session = SessionLocal()
    
    try:
        # Total episodes in database
        total_episodes = db.execute(select(func.count(Episode.id))).scalar()
        print(f"Total Episodes in Database: {total_episodes}")
        print()
        
        # Episodes with chunks (ingested)
        episodes_with_chunks = db.execute(
            select(func.count(func.distinct(Chunk.episode_id)))
        ).scalar()
        print(f"Episodes Ingested (with chunks): {episodes_with_chunks}")
        if total_episodes > 0:
            print(f"Coverage: {episodes_with_chunks / total_episodes * 100:.1f}%")
        print()
        
        # Most chunked episodes (potential over-representation)
        print("Top 10 Episodes by Chunk Count:")
        print("-" * 80)
        result = db.execute(
            select(
                Episode.id,
                Episode.title,
                func.count(Chunk.id).label('chunk_count')
            )
            .join(Chunk, Episode.id == Chunk.episode_id)
            .group_by(Episode.id, Episode.title)
            .order_by(func.count(Chunk.id).desc())
            .limit(10)
        ).all()
        
        for episode_id, title, chunk_count in result:
            title_short = title[:60] if title else "Untitled"
            print(f"  {episode_id:3d}. {title_short:<60} ({chunk_count} chunks)")
        print()
        
        # Episodes with fewest chunks
        print("Episodes with Fewest Chunks:")
        print("-" * 80)
        result = db.execute(
            select(
                Episode.id,
                Episode.title,
                func.count(Chunk.id).label('chunk_count')
            )
            .join(Chunk, Episode.id == Chunk.episode_id)
            .group_by(Episode.id, Episode.title)
            .order_by(func.count(Chunk.id).asc())
            .limit(10)
        ).all()
        
        for episode_id, title, chunk_count in result:
            title_short = title[:60] if title else "Untitled"
            print(f"  {episode_id:3d}. {title_short:<60} ({chunk_count} chunks)")
        print()
        
        # Average chunks per episode
        avg_chunks = db.execute(
            select(func.avg(func.count(Chunk.id)))
            .select_from(Chunk)
            .group_by(Chunk.episode_id)
        ).scalar()
        if avg_chunks:
            print(f"Average Chunks per Episode: {avg_chunks:.1f}")
        print()
        
        # Chunk distribution
        print("Chunk Count Distribution:")
        print("-" * 80)
        result = db.execute(
            text("""
                SELECT 
                    CASE 
                        WHEN chunk_count < 5 THEN '1-4 chunks'
                        WHEN chunk_count < 10 THEN '5-9 chunks'
                        WHEN chunk_count < 20 THEN '10-19 chunks'
                        WHEN chunk_count < 50 THEN '20-49 chunks'
                        ELSE '50+ chunks'
                    END as bucket,
                    COUNT(*) as episode_count
                FROM (
                    SELECT episode_id, COUNT(*) as chunk_count
                    FROM chunks
                    GROUP BY episode_id
                ) as counts
                GROUP BY bucket
                ORDER BY 
                    CASE 
                        WHEN bucket = '1-4 chunks' THEN 1
                        WHEN bucket = '5-9 chunks' THEN 2
                        WHEN bucket = '10-19 chunks' THEN 3
                        WHEN bucket = '20-49 chunks' THEN 4
                        ELSE 5
                    END
            """)
        ).all()
        
        for bucket, count in result:
            print(f"  {bucket:<15} {count:3d} episodes")
        print()
        
        print("=" * 80)
        print("✅ Analysis Complete")
        print()
        print("💡 Recommendations:")
        print("  - Episodes with many chunks may appear more often in results")
        print("  - MMR helps balance this by ensuring episode diversity")
        print("  - Monitor if high-chunk episodes still dominate after MMR")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    analyze_engagement()
