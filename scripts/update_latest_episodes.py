#!/usr/bin/env python3
"""
Update with latest episodes from RSS feed.
This script ingests only new episodes that aren't in the database yet.
Run this periodically (e.g., daily) to keep data fresh.
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# Ensure the project root is on sys.path so `app.*` imports work
# regardless of how or where this script is invoked (CI, cron, etc.)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

print("=" * 60)
print("UPDATING WITH LATEST EPISODES")
print("=" * 60)
print(f"Time: {datetime.now().isoformat()}")
print(f"RSS URL: {os.getenv('RSS_URL', 'Not set')}")
print(f"Database: {'...' if os.getenv('DATABASE_URL') else 'Not set'}")
print(f"Max new episodes per run: {os.getenv('MAX_EPISODES_PER_RUN', '10')}")
print("=" * 60)

from app.ingestion.pipeline_optimized import run_ingestion_optimized
from app.core.db import get_session_local

if __name__ == "__main__":
    max_eps = int(os.getenv("MAX_EPISODES_PER_RUN", "10"))
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        run_ingestion_optimized(db, max_episodes=max_eps)
        print("\n" + "=" * 60)
        print("✓ UPDATE COMPLETE")
        print("=" * 60)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()
