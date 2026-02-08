#!/usr/bin/env python3
"""
Quick script to clear production database and reload with correct embeddings
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.db import SessionLocal, engine
from sqlalchemy import text

def clear_data():
    """Delete all episodes, transcripts, and chunks from production."""
    db = SessionLocal()
    try:
        print("Clearing existing data from production database...")
        
        # Delete in correct order (respect foreign keys)
        db.execute(text("DELETE FROM chunks"))
        db.execute(text("DELETE FROM transcripts"))
        db.execute(text("DELETE FROM episodes"))
        db.execute(text("DELETE FROM ingestion_runs"))
        db.commit()
        
        print("✓ All data cleared!")
        
        # Verify
        episode_count = db.execute(text("SELECT COUNT(*) FROM episodes")).scalar()
        chunk_count = db.execute(text("SELECT COUNT(*) FROM chunks")).scalar()
        print(f"Episodes: {episode_count}, Chunks: {chunk_count}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("CLEAR PRODUCTION DATABASE")
    print("=" * 60)
    print("This will delete all episodes and chunks from production.")
    print("You'll need to re-run ingestion after this.")
    print("=" * 60)
    
    response = input("\nAre you sure? [y/N]: ")
    if response.lower() in ["y", "yes"]:
        if clear_data():
            print("\n✓ Ready to reload data with correct embeddings!")
            print("Run: python scripts/bulk_ingest.py --max-episodes 5 --no-confirm")
    else:
        print("Cancelled.")
