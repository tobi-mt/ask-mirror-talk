"""
Monitor ingestion progress and automatically detect when complete.

This script monitors the database for changes in episode and chunk counts,
and reports when ingestion is complete.

Usage:
    python scripts/monitor_ingestion.py
"""
import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from sqlalchemy import func
from app.core.db import get_session_local
from app.storage import models


def get_stats(db):
    """Get current database stats."""
    total_episodes = db.query(models.Episode).count()
    episodes_with_chunks = (
        db.query(models.Episode.id)
        .join(models.Chunk)
        .distinct()
        .count()
    )
    total_chunks = db.query(models.Chunk).count()
    
    # Episodes being processed (0 chunks)
    episodes_processing = (
        db.query(models.Episode.id)
        .outerjoin(models.Chunk)
        .group_by(models.Episode.id)
        .having(func.count(models.Chunk.id) == 0)
        .count()
    )
    
    return {
        'total_episodes': total_episodes,
        'episodes_with_chunks': episodes_with_chunks,
        'episodes_processing': episodes_processing,
        'total_chunks': total_chunks,
        'coverage': (episodes_with_chunks / total_episodes * 100) if total_episodes > 0 else 0
    }


def print_stats(stats, iteration):
    """Print current stats."""
    print(f"\n{'='*80}")
    print(f"📊 Ingestion Monitor - Check #{iteration} - {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*80}")
    print(f"Total Episodes:          {stats['total_episodes']:>6}")
    print(f"Episodes with Chunks:    {stats['episodes_with_chunks']:>6} ({stats['coverage']:.1f}%)")
    print(f"Episodes Processing:     {stats['episodes_processing']:>6} (0 chunks)")
    print(f"Total Chunks:            {stats['total_chunks']:>6,}")
    print(f"{'='*80}")


def monitor_ingestion(check_interval=30, max_checks=60):
    """
    Monitor ingestion progress.
    
    Args:
        check_interval: Seconds between checks (default: 30)
        max_checks: Maximum number of checks before stopping (default: 60 = 30 min)
    """
    print("🚀 Starting ingestion monitor...")
    print(f"Check interval: {check_interval} seconds")
    print(f"Maximum runtime: {check_interval * max_checks / 60:.1f} minutes")
    
    Session = get_session_local()
    db = Session()
    
    try:
        prev_stats = get_stats(db)
        print_stats(prev_stats, 0)
        
        for i in range(1, max_checks + 1):
            time.sleep(check_interval)
            
            current_stats = get_stats(db)
            print_stats(current_stats, i)
            
            # Check if anything changed
            chunks_added = current_stats['total_chunks'] - prev_stats['total_chunks']
            episodes_completed = prev_stats['episodes_processing'] - current_stats['episodes_processing']
            
            if chunks_added > 0:
                print(f"✅ Progress: +{chunks_added} chunks, +{episodes_completed} episodes completed")
            else:
                print("⏳ No new chunks added...")
            
            # Check if complete (no episodes processing)
            if current_stats['episodes_processing'] == 0:
                print(f"\n{'='*80}")
                print("🎉 INGESTION COMPLETE!")
                print(f"{'='*80}")
                print(f"Final Stats:")
                print(f"  Total Episodes: {current_stats['total_episodes']}")
                print(f"  Episodes with Chunks: {current_stats['episodes_with_chunks']} ({current_stats['coverage']:.1f}%)")
                print(f"  Total Chunks: {current_stats['total_chunks']:,}")
                print(f"{'='*80}")
                break
            
            # Check if stuck (no progress for 3 consecutive checks)
            if i >= 3 and chunks_added == 0:
                print("\n⚠️  WARNING: No progress detected. Ingestion may be stuck.")
                print("Check the ingestion logs for errors:")
                print("  tail -f ingestion_*.txt")
                print("  OR")
                print("  tail -f reingest_*.txt")
            
            prev_stats = current_stats
        
        else:
            print(f"\n⏱️  Maximum runtime reached ({max_checks} checks).")
            print("Ingestion may still be running. Check manually:")
            print("  python scripts/analyze_episode_engagement.py")
    
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor ingestion progress")
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Seconds between checks (default: 30)"
    )
    parser.add_argument(
        "--max-time",
        type=int,
        default=30,
        help="Maximum runtime in minutes (default: 30)"
    )
    
    args = parser.parse_args()
    max_checks = (args.max_time * 60) // args.interval
    
    monitor_ingestion(check_interval=args.interval, max_checks=max_checks)
