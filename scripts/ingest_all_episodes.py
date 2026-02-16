#!/usr/bin/env python3
"""
Ingest ALL episodes from RSS feed without limit.
This script will process all available episodes.

Usage:
  python scripts/ingest_all_episodes.py

Requirements:
  - .env file with DATABASE_URL set to your Neon database
  - RSS_URL configured
  - OPENAI_API_KEY for transcription
"""
import os
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✓ Loaded environment from: {env_path}")
else:
    print(f"⚠️  No .env file found at: {env_path}")
    print("   Please create a .env file with your DATABASE_URL and other settings")
    sys.exit(1)

# Remove the episode limit
os.environ['MAX_EPISODES_PER_RUN'] = '999'

# Disable audio file size limit for local ingestion
# Set to 0 for unlimited (useful when processing large files locally)
os.environ['MAX_AUDIO_SIZE_MB'] = '0'  # Unlimited

# Validate required environment variables
required_vars = ['DATABASE_URL', 'RSS_URL']
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    print(f"\n✗ ERROR: Missing required environment variables: {', '.join(missing_vars)}")
    print("   Please set them in your .env file")
    sys.exit(1)

print("="*60)
print("INGESTING ALL EPISODES FROM RSS")
print("="*60)
print(f"RSS URL: {os.getenv('RSS_URL')}")
print(f"Database: {os.getenv('DATABASE_URL', 'Not set')[:70]}...")
print(f"Max episodes: UNLIMITED")
print(f"Max audio size: UNLIMITED (large files enabled)")
print(f"Transcription: {os.getenv('TRANSCRIPTION_PROVIDER', 'Not set')}")
print(f"OpenAI API Key: {'Set' if os.getenv('OPENAI_API_KEY') else 'NOT SET'}")
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
            
    except KeyboardInterrupt:
        print("\n\n✗ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
