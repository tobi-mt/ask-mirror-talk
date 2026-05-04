#!/usr/bin/env python3
"""
Update with latest episodes from RSS feed.
This script ingests only new episodes that aren't in the database yet.
Run this periodically (e.g., daily) to keep data fresh.
"""
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# Ensure the project root is on sys.path so `app.*` imports work
# regardless of how or where this script is invoked (CI, cron, etc.)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

print("=" * 60)
print("UPDATING WITH LATEST EPISODES")
print("=" * 60)
print(f"Time: {datetime.now().isoformat()}")
print(f"RSS URL: {'set' if os.getenv('RSS_URL') else 'NOT SET'}")
print(f"Database: {'set' if os.getenv('DATABASE_URL') else 'NOT SET'}")
print(f"OpenAI key: {'set' if os.getenv('OPENAI_API_KEY') else 'NOT SET'}")
print(f"Max new episodes per run: {os.getenv('MAX_EPISODES_PER_RUN', '10')}")
print("=" * 60)

# Fail early with clear message if required env vars are missing
missing = []
if not os.getenv("DATABASE_URL"):
    missing.append("DATABASE_URL")
if not os.getenv("RSS_URL"):
    missing.append("RSS_URL")
if missing:
    print(f"\n✗ FATAL: Missing required environment variables: {', '.join(missing)}")
    print("  → Add them as GitHub repository secrets:")
    print("    https://github.com/<owner>/<repo>/settings/secrets/actions")
    sys.exit(1)

from app.ingestion.pipeline_optimized import run_ingestion_optimized
from app.notifications.push import send_new_episode_notification
from app.core.config import settings
from app.core.db import get_session_local


def _as_utc(value):
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _newest_recent_episode(episodes: list[dict]) -> dict | None:
    if not episodes:
        return None

    now = datetime.now(timezone.utc)
    max_age_days = max(0, settings.notify_new_episode_max_age_days)
    recent = []
    for episode in episodes:
        published_at = _as_utc(episode.get("published_at"))
        if not published_at:
            continue
        age_days = (now - published_at).total_seconds() / 86400
        if 0 <= age_days <= max_age_days:
            recent.append({**episode, "published_at": published_at})

    if not recent:
        return None
    return max(recent, key=lambda item: item["published_at"])

if __name__ == "__main__":
    max_eps = int(os.getenv("MAX_EPISODES_PER_RUN", "10"))
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        result = run_ingestion_optimized(db, max_episodes=max_eps)
        processed_episodes = result.get("processed_episodes", [])
        episode_to_notify = _newest_recent_episode(processed_episodes)
        if settings.notify_new_episode_after_ingest and episode_to_notify:
            print(f"Sending new episode alert: {episode_to_notify['title']}")
            notify_db = SessionLocal()
            try:
                notify_result = send_new_episode_notification(
                    notify_db,
                    episode_title=episode_to_notify["title"],
                    episode_id=episode_to_notify["id"],
                )
            finally:
                notify_db.close()
            print(f"✓ New episode alert result: {notify_result}")
        elif processed_episodes:
            print(
                "ℹ New episodes were ingested, but none were recent enough "
                f"for a push alert (max age: {settings.notify_new_episode_max_age_days} days)."
            )
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
