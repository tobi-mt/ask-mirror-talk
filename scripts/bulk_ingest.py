#!/usr/bin/env python3
"""
Bulk Ingestion Script

Run this to ingest all episodes from your RSS feed in one go.
This is optimized for initial data loading.

Usage:
    python scripts/bulk_ingest.py [--max-episodes N] [--dry-run]

Examples:
    # Ingest all episodes
    python scripts/bulk_ingest.py

    # Ingest only first 10 episodes
    python scripts/bulk_ingest.py --max-episodes 10

    # See what would be processed without actually doing it
    python scripts/bulk_ingest.py --dry-run
"""

import argparse
import logging
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.db import SessionLocal, init_db
from app.core.config import settings
from app.core.logging import setup_logging
from app.ingestion.pipeline_optimized import run_ingestion_optimized
from app.ingestion.rss import fetch_feed, normalize_entries
from app.storage import repository

setup_logging()
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Bulk ingest podcast episodes")
    parser.add_argument(
        "--max-episodes",
        type=int,
        default=None,
        help="Maximum number of episodes to process (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be processed without actually doing it",
    )
    args = parser.parse_args()

    if not settings.rss_url:
        logger.error("RSS_URL is not configured. Please set it in your .env file.")
        return 1

    logger.info("=" * 60)
    logger.info("BULK INGESTION SCRIPT")
    logger.info("=" * 60)
    logger.info("RSS Feed: %s", settings.rss_url)
    logger.info("Max Episodes: %s", args.max_episodes or "unlimited")
    logger.info("Whisper Model: %s", settings.whisper_model)
    logger.info("Embedding Provider: %s", settings.embedding_provider)
    logger.info("Dry Run: %s", args.dry_run)
    logger.info("=" * 60)

    # Initialize database
    init_db()

    # Check what's in the feed
    logger.info("Fetching RSS feed...")
    feed = fetch_feed(settings.rss_url)
    entries = normalize_entries(feed)
    logger.info("Found %s episodes in feed", len(entries))

    # Check what we already have
    db = SessionLocal()
    try:
        existing_count = 0
        new_episodes = []
        
        for entry in entries:
            existing = repository.get_episode_by_guid(db, entry["guid"])
            if existing:
                existing_count += 1
            else:
                new_episodes.append(entry)
                if args.max_episodes and len(new_episodes) >= args.max_episodes:
                    break

        logger.info("Already ingested: %s episodes", existing_count)
        logger.info("New episodes to process: %s", len(new_episodes))

        if not new_episodes:
            logger.info("✓ All episodes already ingested!")
            return 0

        if args.dry_run:
            logger.info("\n--- DRY RUN: Episodes that would be processed ---")
            for idx, entry in enumerate(new_episodes[:10], 1):  # Show first 10
                logger.info("%s. %s", idx, entry["title"])
            if len(new_episodes) > 10:
                logger.info("... and %s more", len(new_episodes) - 10)
            logger.info("\nRun without --dry-run to actually process these episodes")
            return 0

        # Confirm with user
        logger.info("\nAbout to ingest %s new episodes", len(new_episodes))
        logger.info("Estimated time: %s minutes", len(new_episodes) * 3)
        
        response = input("\nProceed? [y/N]: ")
        if response.lower() not in ["y", "yes"]:
            logger.info("Cancelled by user")
            return 0

        # Run the optimized ingestion
        logger.info("\nStarting ingestion...\n")
        result = run_ingestion_optimized(db, max_episodes=args.max_episodes)
        
        logger.info("\n" + "=" * 60)
        logger.info("✓ INGESTION COMPLETE")
        logger.info("=" * 60)
        logger.info("Processed: %s episodes", result["processed"])
        logger.info("Skipped: %s episodes", result["skipped"])
        logger.info("=" * 60)

        # Verify chunks were created
        from sqlalchemy import text
        chunk_count = db.execute(text("SELECT COUNT(*) FROM chunks")).scalar()
        logger.info("Total chunks in database: %s", chunk_count)

        if chunk_count > 0:
            logger.info("\n✓ Your website is ready to answer questions!")
        else:
            logger.warning("\n⚠ No chunks created. Check for errors above.")

        return 0

    except KeyboardInterrupt:
        logger.info("\n\nInterrupted by user")
        return 130
    except Exception as exc:
        logger.exception("Ingestion failed: %s", exc)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
