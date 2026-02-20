#!/usr/bin/env python3
"""
Database Migration: Add Analytics Tables

Adds citation_clicks and user_feedback tables to the database.

Usage:
    python scripts/migrate_add_analytics_tables.py
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.db import get_engine, Base
from app.storage.models import CitationClick, UserFeedback
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate():
    """Create new analytics tables"""
    
    logger.info("="*80)
    logger.info("DATABASE MIGRATION: Adding Analytics Tables")
    logger.info("="*80)
    
    try:
        # Import all models to ensure they're registered
        from app.storage import models
        
        logger.info("\n📋 Tables to create:")
        logger.info("   - citation_clicks (track episode citation clicks)")
        logger.info("   - user_feedback (track user feedback on answers)")
        
        # Create only the new tables (won't affect existing tables)
        logger.info("\n🔨 Creating tables...")
        engine = get_engine()  # Call the function to get the engine instance
        Base.metadata.create_all(bind=engine)
        
        logger.info("\n✅ Migration complete!")
        logger.info("\nNew tables created:")
        logger.info("   ✓ citation_clicks")
        logger.info("   ✓ user_feedback")
        
        logger.info("\n📊 API Endpoints now available:")
        logger.info("   POST /api/citation/click - Track citation clicks")
        logger.info("   POST /api/feedback - Submit user feedback")
        logger.info("   GET /api/analytics/summary - Get analytics summary")
        logger.info("   GET /api/analytics/episodes - Get episode analytics")
        
        logger.info("\n" + "="*80)
        
    except Exception as e:
        logger.error(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    migrate()
