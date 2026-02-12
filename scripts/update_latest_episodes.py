#!/usr/bin/env python3
"""
Update with latest episodes from RSS feed.
This script ingests only new episodes that aren't in the database yet.
Run this periodically (e.g., daily) to keep data fresh.
"""
import os
import sys
from datetime import datetime

print("="*60)
print("UPDATING WITH LATEST EPISODES")
print("="*60)
print(f"Time: {datetime.now().isoformat()}")
print(f"RSS URL: {os.getenv('RSS_URL', 'Not set')}")
print(f"Database: {os.getenv('DATABASE_URL', 'Not set')[:50]}...")
print(f"Max new episodes per run: {os.getenv('MAX_EPISODES_PER_RUN', '10')}")
print("="*60)

# Import and run the optimized pipeline
from app.ingestion.pipeline_optimized import main

if __name__ == "__main__":
    try:
        main()
        print("\n" + "="*60)
        print("✓ UPDATE COMPLETE")
        print("="*60)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
