#!/usr/bin/env python3
"""
Ingest ALL episodes from RSS feed without limit.
This script will process all available episodes.
"""
import os
import sys

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
from app.ingestion.pipeline_optimized import main

if __name__ == "__main__":
    try:
        main()
        print("\n" + "="*60)
        print("✓ INGESTION COMPLETE")
        print("="*60)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
