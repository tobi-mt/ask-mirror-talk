"""
Re-ingest the 30 episodes that were previously deleted.

This script will fetch these specific episodes from the RSS feed
and re-process them with compression enabled.

Usage:
    export ENABLE_AUDIO_COMPRESSION=true
    export MAX_AUDIO_SIZE_MB=0
    python scripts/ingest_missing_episodes.py
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.db import get_session_local
from app.ingestion.pipeline_optimized import run_ingestion_optimized


# The 30 episode GUIDs that were deleted
DELETED_EPISODE_GUIDS = [
    'e2c63a74-0aeb-4ad9-acc8-c88e7f0f8847',  # Channeling Your Power with Mike Acker
    'aaa7364e-0099-4c29-bc3a-4d66489579ec',  # 3 Qualities to Enhance Yourself...
    'c85c69e3-bfb8-489c-b3d9-1d4942251b5b',  # Donna Chacko: ONE Thing...
    '01f7bd0d-86ff-4b0c-8998-88ecd588d0ff',  # Unleashing the Champ with Kyle Sullivan
    '508082b4-e8c5-4724-be2d-915d158f1b25',  # Sharing Your Message with Neil Gordon
    '1f14dc13-7873-4f81-ba47-e6571f41364b',  # How To Live A Purposeful Life...
    'f9d96403-8856-42c5-8818-29b399003970',  # Creating Your Reality with Jay Campbell
    '4c2d1d8f-2179-451a-b05b-0b8f86c28d6a',  # Born This Way
    '15540fa7-8e9c-45d5-91e2-9cf16d7792e6',  # Mark Robinson: Black On Madison Avenue
    '13151685-689d-4f48-a712-805746d54761',  # Becoming Unconstrained with Myles Wakeham
    '5be47fa6-8d21-4f56-940d-1e7bf7426d75',  # Tapping Into the Power...
    '8c7ed59c-5845-4110-950c-4d2eef068520',  # Dr. Debi Silver: Are You Numbing...
    '41128e3d-5aef-486c-8474-563b2b23bb37',  # How to Fall in Love with Drs Grossman
    'e60bd1ab-4580-4ba6-8019-2bcb748af9cd',  # David Edwards: Benefits of Living...
    '01bc93ca-f80e-42dc-95d0-3d2d6b473e05',  # How To Make The Right Choice...
    '73698c61-1af7-45bc-b59f-dd6ad624047e',  # Becoming Aware of Your Emotions...
    '5aa74e26-66ee-4176-8e5c-3ba145f49234',  # Sending Out Positive Energy...
    'ad7233fa-dd8b-4ff4-b259-1a3b2c52ae7a',  # Beginning of A New Chapter
    '2ca74a08-3517-4a78-b07a-dff60236ec45',  # Living a Successful Life with JP Morgan
    'afade8c6-4e94-4291-89af-5cd38a2a35ef',  # Having Compassion on Yourself...
    'fce3fcdc-d4b9-4773-aa6e-c7a34d3aeae1',  # Defining Love with Philip Russotti
    'eb164f26-febc-4e8d-a9bd-0ac9984d5d3c',  # Mike Acker: How to Overcome The Fear...
    'b84a6600-75e8-4ac0-8b0b-81fc325855b4',  # Take Risks with Tom Glaser
    '25ec21ca-35f1-4320-b91d-777865ca34cd',  # Navigating Loss and Grief...
    '8321bc0c-3e1c-4dbc-937d-869a729f0284',  # Unlocking Financial Freedom...
    'bf884407-de40-48c8-90c7-4eec4d7347db',  # Managing Your Expectation...
    'ea4d94e6-319f-4187-be32-a21daf4b2687',  # How To Fight For Your Best Life...
    '036d54e8-4dab-47a5-9fe9-c2ab9001a5d2',  # Changing Perspectives with Claudia Monacelli
    '8b5c0dcf-2c12-4797-95a3-dfbcbf3b1897',  # You Deserve Positive Mirror Talk
    '4bf27b22-f124-4f99-a592-3ac431262d07',  # Cooling the Path to Recovery...
]


def main():
    # Check environment
    compression_enabled = os.getenv('ENABLE_AUDIO_COMPRESSION', 'true').lower() == 'true'
    max_size = os.getenv('MAX_AUDIO_SIZE_MB', '25')
    
    print("🔍 Re-ingestion Configuration:")
    print(f"  ENABLE_AUDIO_COMPRESSION: {compression_enabled}")
    print(f"  MAX_AUDIO_SIZE_MB: {max_size}")
    print()
    
    if not compression_enabled:
        print("⚠️  WARNING: Compression is disabled!")
        print("   Run: export ENABLE_AUDIO_COMPRESSION=true")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("❌ Cancelled")
            return
    
    SessionMaker = get_session_local()
    db = SessionMaker()
    
    try:
        print(f"📊 Will re-ingest {len(DELETED_EPISODE_GUIDS)} previously deleted episodes\n")
        
        # Confirm
        response = input(f"Re-ingest {len(DELETED_EPISODE_GUIDS)} episodes from RSS feed? (y/N): ")
        if response.lower() != 'y':
            print("❌ Cancelled")
            return
        
        # Run ingestion - the pipeline will fetch from RSS and filter by GUID
        print(f"\n🚀 Starting re-ingestion of {len(DELETED_EPISODE_GUIDS)} episodes...\n")
        print("Note: The pipeline will fetch ALL episodes from RSS and process only the deleted ones.\n")
        
        result = run_ingestion_optimized(
            db,
            max_episodes=len(DELETED_EPISODE_GUIDS),
            skip_existing=False  # Don't skip - we want to re-process these
        )
        
        print(f"\n✅ Re-ingestion complete!")
        print(f"  Processed: {result['processed']}")
        print(f"  Skipped: {result['skipped']}")
        print(f"  Failed: {result['failed']}")
        
    finally:
        db.close()


if __name__ == "__main__":
    main()
