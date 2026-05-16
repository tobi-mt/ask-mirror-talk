#!/usr/bin/env python3
"""
Migration: Add card_template_variants table for A/B testing template performance.
Tracks which template family/variant was shown and engagement metrics.
"""
import sys
from sqlalchemy import text, create_engine
from app.core.config import settings

def run_migration():
    """Create card_template_variants table if it doesn't exist."""
    engine = create_engine(settings.database_url)
    
    sql = """
    CREATE TABLE IF NOT EXISTS card_template_variants (
        id SERIAL PRIMARY KEY,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
        user_ip VARCHAR(100) NOT NULL,
        device_id VARCHAR(64),
        template_family VARCHAR(50) NOT NULL,
        template_variant INTEGER NOT NULL,
        qa_log_id INTEGER,
        question_theme VARCHAR(100),
        was_shared BOOLEAN NOT NULL DEFAULT false,
        was_liked BOOLEAN NOT NULL DEFAULT false,
        was_skipped BOOLEAN NOT NULL DEFAULT false,
        shares_count INTEGER NOT NULL DEFAULT 0,
        engagement_score FLOAT NOT NULL DEFAULT 0.0,
        ab_test_group VARCHAR(50) NOT NULL DEFAULT 'control'
    );
    
    CREATE INDEX IF NOT EXISTS idx_card_template_variants_created_at 
        ON card_template_variants(created_at DESC);
    
    CREATE INDEX IF NOT EXISTS idx_card_template_variants_user_ip 
        ON card_template_variants(user_ip);
    
    CREATE INDEX IF NOT EXISTS idx_card_template_variants_device_id 
        ON card_template_variants(device_id);
    
    CREATE INDEX IF NOT EXISTS idx_card_template_variants_template_family 
        ON card_template_variants(template_family);
    
    CREATE INDEX IF NOT EXISTS idx_card_template_variants_was_shared 
        ON card_template_variants(was_shared);
    
    CREATE INDEX IF NOT EXISTS idx_card_template_variants_ab_test_group 
        ON card_template_variants(ab_test_group);
    
    CREATE INDEX IF NOT EXISTS idx_card_template_variants_engagement 
        ON card_template_variants(template_family, engagement_score DESC);
    """
    
    try:
        with engine.begin() as conn:
            conn.execute(text(sql))
        print("✅ Migration successful: card_template_variants table created/verified")
        return 0
    except Exception as e:
        print(f"❌ Migration failed: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    exit(run_migration())
