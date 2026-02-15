#!/usr/bin/env python3
"""
Ingest a single episode by searching for it in the RSS feed.

Usage:
    python scripts/ingest_single_episode.py <episode-title-keyword>

Example:
    python scripts/ingest_single_episode.py "power of intention"
"""
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.db import SessionLocal, init_db
from app.core.config import settings
from app.core.logging import setup_logging
from app.ingestion.pipeline_optimized import run_ingestion_optimized
from app.ingestion.rss import fetch_feed, normalize_entries

setup_logging()
import logging
logger = logging.getLogger(__name__)


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/ingest_single_episode.py <episode-title-keyword>")
        print("\nExample:")
        print('  python scripts/ingest_single_episode.py "power of intention"')
        sys.exit(1)
    
    search_term = sys.argv[1].lower()
    
    logger.info("=" * 60)
    logger.info("SINGLE EPISODE INGESTION")
    logger.info("=" * 60)
    logger.info(f"Searching for: {search_term}")
    
    # Initialize database
    init_db()
    
    # Fetch RSS feed
    logger.info(f"Fetching RSS feed from: {settings.rss_url}")
    feed = fetch_feed(settings.rss_url)
    entries = normalize_entries(feed)
    
    logger.info(f"Found {len(entries)} total episodes in feed")
    
    # Find matching episodes
    matched = [e for e in entries if search_term in e.get("title", "").lower()]
    
    if not matched:
        logger.error(f"❌ No episodes found matching: {search_term}")
        logger.info("\nAvailable episodes:")
        for i, e in enumerate(entries[:10], 1):
            logger.info(f"  {i}. {e.get('title')}")
        if len(entries) > 10:
            logger.info(f"  ... and {len(entries) - 10} more")
        return 1
    
    if len(matched) > 1:
        logger.warning(f"⚠️  Found {len(matched)} matching episodes:")
        for i, e in enumerate(matched, 1):
            logger.info(f"  {i}. {e.get('title')}")
        logger.info("\n💡 Please be more specific with your search term.")
        return 1
    
    # Found exactly one match
    episode = matched[0]
    logger.info(f"\n✅ Found episode: {episode.get('title')}")
    logger.info(f"   Published: {episode.get('published')}")
    logger.info(f"   Audio URL: {episode.get('audio_url', 'N/A')}")
    
    # Ingest it
    logger.info("\n" + "=" * 60)
    logger.info("Starting ingestion...")
    logger.info("=" * 60)
    
    with SessionLocal() as db:
        success = run_ingestion_optimized(db, episode)
        
        if success:
            logger.info("\n" + "=" * 60)
            logger.info("✅ INGESTION SUCCESSFUL!")
            logger.info("=" * 60)
            logger.info(f"Episode '{episode.get('title')}' is now available in the database.")
            logger.info("It can be queried via the API immediately.")
            return 0
        else:
            logger.error("\n" + "=" * 60)
            logger.error("❌ INGESTION FAILED")
            logger.error("=" * 60)
            logger.error("Check the logs above for details.")
            return 1


if __name__ == "__main__":
    sys.exit(main())
