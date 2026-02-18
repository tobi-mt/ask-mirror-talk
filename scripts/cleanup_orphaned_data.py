#!/usr/bin/env python3
"""
Clean up orphaned transcripts and transcript segments.
Run this before re-running ingestion to fix database inconsistencies.
"""
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app.core.db import SessionLocal, init_db
from app.storage import models
from sqlalchemy import text

def cleanup_orphaned_data():
    """Remove orphaned transcripts and segments that have null episode_id"""
    init_db()
    db = SessionLocal()()
    
    try:
        print("="*60)
        print("CLEANING UP ORPHANED DATA")
        print("="*60)
        
        # Count orphaned data first
        orphaned_segments = db.query(models.TranscriptSegment).filter(
            models.TranscriptSegment.transcript_id.in_(
                db.query(models.Transcript.id).filter(models.Transcript.episode_id == None)
            )
        ).count()
        
        orphaned_transcripts = db.query(models.Transcript).filter(
            models.Transcript.episode_id == None
        ).count()
        
        print(f"Found {orphaned_segments} orphaned transcript segments")
        print(f"Found {orphaned_transcripts} orphaned transcripts")
        
        if orphaned_segments == 0 and orphaned_transcripts == 0:
            print("\n✓ No orphaned data found - database is clean!")
            return
        
        # Delete orphaned transcript segments first (due to foreign key)
        if orphaned_segments > 0:
            deleted_segments = db.query(models.TranscriptSegment).filter(
                models.TranscriptSegment.transcript_id.in_(
                    db.query(models.Transcript.id).filter(models.Transcript.episode_id == None)
                )
            ).delete(synchronize_session=False)
            print(f"✓ Deleted {deleted_segments} orphaned transcript segments")
        
        # Delete orphaned transcripts
        if orphaned_transcripts > 0:
            deleted_transcripts = db.query(models.Transcript).filter(
                models.Transcript.episode_id == None
            ).delete(synchronize_session=False)
            print(f"✓ Deleted {deleted_transcripts} orphaned transcripts")
        
        db.commit()
        
        print("\n" + "="*60)
        print("✓ CLEANUP COMPLETE")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_orphaned_data()
