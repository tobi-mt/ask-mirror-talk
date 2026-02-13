#!/usr/bin/env python3
"""
Ingest ALL episodes from RSS feed without limit.
This script will process all available episodes.
"""
import os
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Remove the episode limit
os.environ['MAX_EPISODES_PER_RUN'] = '999'

print("="*60)
print("INGESTING ALL EPISODES FROM RSS")
print("="*60)
print(f"RSS URL: {os.getenv('RSS_URL', 'Not set')}")
print(f"Database: {os.getenv('DATABASE_URL', 'Not set')[:50]}...")
print(f"Max episodes: UNLIMITED")
print("="*60)

# Import and run the optimized pipeline
from app.core.db import SessionLocal, init_db
from app.ingestion.pipeline_optimized import run_ingestion_optimized

if __name__ == "__main__":
    try:
        # Initialize database
        init_db()
        
        # Create database session
        db = SessionLocal()()
        
        try:
            # Run ingestion without episode limit
            result = run_ingestion_optimized(db, max_episodes=None)
            
            print("\n" + "="*60)
            print("✓ INGESTION COMPLETE")
            print("="*60)
            print(f"Processed: {result['processed']} episodes")
            print(f"Skipped: {result['skipped']} episodes")
            print("="*60)
        finally:
            db.close()
            
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        import traceback
        traceback.print_exc()
        sys.exit(1)
