"""
Re-ingest episodes that have very few chunks.

This script identifies episodes with <5 chunks and re-processes them
with compression enabled to improve coverage.

Usage:
    export ENABLE_AUDIO_COMPRESSION=true
    export MAX_AUDIO_SIZE_MB=0
    python scripts/reingest_low_chunk_episodes.py
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from sqlalchemy import func
from app.core.db import get_session_local
from app.storage import models
from app.ingestion.pipeline_optimized import run_ingestion_optimized


def get_low_chunk_episodes(db, max_chunks: int = 4):
    """Get episodes with fewer than max_chunks chunks."""
    # Query episodes with chunk count
    results = (
        db.query(models.Episode, func.count(models.Chunk.id).label('chunk_count'))
        .outerjoin(models.Chunk)
        .group_by(models.Episode.id)
        .having(func.count(models.Chunk.id) <= max_chunks)
        .order_by(func.count(models.Chunk.id))
        .all()
    )
    
    return [(episode, chunk_count) for episode, chunk_count in results]


def main(skip_confirmation=False, dry_run=False):
    # Check environment
    compression_enabled = os.getenv('ENABLE_AUDIO_COMPRESSION', 'true').lower() == 'true'
    max_size = os.getenv('MAX_AUDIO_SIZE_MB', '25')
    
    print("🔍 Re-ingestion Configuration:")
    print(f"  ENABLE_AUDIO_COMPRESSION: {compression_enabled}")
    print(f"  MAX_AUDIO_SIZE_MB: {max_size}")
    print()
    
    if not compression_enabled and not skip_confirmation:
        print("⚠️  WARNING: Compression is disabled!")
        print("   Run: export ENABLE_AUDIO_COMPRESSION=true")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("❌ Cancelled")
            return
    
    SessionMaker = get_session_local()
    db = SessionMaker()
    
    try:
        # Get episodes with <5 chunks
        low_chunk_episodes = get_low_chunk_episodes(db, max_chunks=4)
        
        print(f"📊 Found {len(low_chunk_episodes)} episodes with ≤4 chunks\n")
        
        if not low_chunk_episodes:
            print("✅ No episodes need re-ingestion!")
            return
        
        # Show episodes
        print("Episodes to re-ingest:")
        print("-" * 80)
        for episode, chunk_count in low_chunk_episodes[:10]:
            title = episode.title[:60] + "..." if len(episode.title) > 60 else episode.title
            print(f"  [{episode.id}] {title} ({chunk_count} chunks)")
        
        if len(low_chunk_episodes) > 10:
            print(f"  ... and {len(low_chunk_episodes) - 10} more")
        print()
        
        if dry_run:
            print("🔍 DRY RUN - No changes will be made")
            return
        
        # Confirm
        if not skip_confirmation:
            response = input(f"Re-ingest {len(low_chunk_episodes)} episodes? (y/N): ")
            if response.lower() != 'y':
                print("❌ Cancelled")
                return
        
        # Convert to entry format BEFORE deleting (to avoid accessing deleted objects)
        entries = []
        for episode, _ in low_chunk_episodes:
            entries.append({
                'guid': episode.guid,
                'title': episode.title,
                'audio_url': episode.audio_url,
                'description': episode.description,
                'published_at': episode.published_at,
            })
        
        # Delete episodes and their related data before re-ingesting
        print(f"\n🗑️  Deleting {len(low_chunk_episodes)} episodes and their data...\n")
        
        episode_ids = [episode.id for episode, _ in low_chunk_episodes]
        
        # Get transcript IDs for these episodes
        transcript_ids = [t.id for t in db.query(models.Transcript.id).filter(models.Transcript.episode_id.in_(episode_ids)).all()]
        
        # Delete in order (foreign key constraints):
        # 1. Chunks (references episodes)
        chunks_deleted = db.query(models.Chunk).filter(models.Chunk.episode_id.in_(episode_ids)).delete(synchronize_session=False)
        print(f"  Deleted {chunks_deleted} chunks")
        
        # 2. Transcript segments (references transcripts)
        if transcript_ids:
            segments_deleted = db.query(models.TranscriptSegment).filter(models.TranscriptSegment.transcript_id.in_(transcript_ids)).delete(synchronize_session=False)
            print(f"  Deleted {segments_deleted} transcript segments")
        
        # 3. Transcripts (references episodes)
        transcripts_deleted = db.query(models.Transcript).filter(models.Transcript.episode_id.in_(episode_ids)).delete(synchronize_session=False)
        print(f"  Deleted {transcripts_deleted} transcripts")
        
        # 4. Episodes
        episodes_deleted = db.query(models.Episode).filter(models.Episode.id.in_(episode_ids)).delete(synchronize_session=False)
        print(f"  Deleted {episodes_deleted} episodes")
        
        db.commit()
        print("  ✅ Deletion complete\n")
        
        # Run ingestion with these specific entries
        print(f"🚀 Starting re-ingestion of {len(entries)} episodes...\n")
        
        result = run_ingestion_optimized(
            db,
            max_episodes=len(entries),
            entries_to_process=entries
        )
        
        print(f"\n✅ Re-ingestion complete!")
        print(f"  Processed: {result['processed']}")
        print(f"  Skipped: {result['skipped']}")
        print(f"  Failed: {result['failed']}")
        
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Re-ingest episodes with low chunk counts")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompts")
    parser.add_argument("--dry-run", action="store_true", help="Show episodes but don't process")
    args = parser.parse_args()
    
    main(skip_confirmation=args.yes, dry_run=args.dry_run)
