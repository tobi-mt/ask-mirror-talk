#!/usr/bin/env python3
"""
Ingest a locally downloaded audio file directly.

This is useful for:
- Very large files that can't be processed via the standard pipeline
- Files you've manually downloaded
- Testing with local audio files

Usage:
    python scripts/ingest_local_file.py <audio_file_path> <episode_title> <episode_url>

Example:
    python scripts/ingest_local_file.py \\
        data/audio/episode-123.mp3 \\
        "The Power of Intention" \\
        "https://yourpodcast.com/episodes/123"
"""
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.db import SessionLocal, init_db
from app.core.config import settings
from app.core.logging import setup_logging
from app.ingestion.transcription_openai import transcribe_audio_openai
from app.ingestion.transcription import transcribe_audio
from app.indexing.chunking import chunk_segments
from app.indexing.embeddings import embed_text_batch
from app.indexing.tagging import tag_chunk
from app.storage import repository

setup_logging()
import logging
logger = logging.getLogger(__name__)


def main():
    if len(sys.argv) < 4:
        print("Usage: python scripts/ingest_local_file.py <audio_file_path> <episode_title> <episode_url>")
        print("\nExample:")
        print('  python scripts/ingest_local_file.py \\')
        print('      data/audio/episode-123.mp3 \\')
        print('      "The Power of Intention" \\')
        print('      "https://yourpodcast.com/episodes/123"')
        sys.exit(1)
    
    audio_file = Path(sys.argv[1])
    episode_title = sys.argv[2]
    episode_url = sys.argv[3]
    
    logger.info("=" * 60)
    logger.info("LOCAL FILE INGESTION")
    logger.info("=" * 60)
    
    # Validate audio file
    if not audio_file.exists():
        logger.error(f"❌ Audio file not found: {audio_file}")
        logger.info(f"\nMake sure the file exists at the path you specified.")
        return 1
    
    file_size_mb = audio_file.stat().st_size / 1024 / 1024
    logger.info(f"Audio File: {audio_file}")
    logger.info(f"File Size: {file_size_mb:.2f} MB")
    logger.info(f"Episode Title: {episode_title}")
    logger.info(f"Episode URL: {episode_url}")
    
    # Initialize database
    init_db()
    
    # Check if episode already exists
    with SessionLocal() as db:
        # Simple check by URL - if episode exists, confirm re-ingestion
        from sqlalchemy import select
        from app.storage.models import Episode
        
        stmt = select(Episode).where(Episode.audio_url == episode_url)
        existing = db.execute(stmt).scalar_one_or_none()
        
        if existing:
            logger.warning(f"\n⚠️  Episode already exists in database!")
            logger.info(f"   Title: {existing.title}")
            logger.info(f"   Ingested: {existing.created_at}")
            
            response = input("\nDo you want to re-ingest it? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                logger.info("Aborted.")
                return 0
            
            logger.info("Deleting existing episode and re-ingesting...")
            # Delete episode (cascades to chunks)
            db.delete(existing)
            db.commit()
    
    logger.info("\n" + "=" * 60)
    logger.info("STEP 1: Transcription")
    logger.info("=" * 60)
    logger.info(f"Provider: {settings.transcription_provider}")
    
    # Transcribe
    try:
        if settings.transcription_provider == "openai":
            if file_size_mb > 25:
                logger.error(f"❌ File is too large for OpenAI Whisper API ({file_size_mb:.2f}MB > 25MB)")
                logger.info("\n💡 Solution: Set TRANSCRIPTION_PROVIDER=faster_whisper in your .env file")
                logger.info("   Then run: pip install faster-whisper")
                return 1
            
            logger.info("Using OpenAI Whisper API...")
            transcript_result = transcribe_audio_openai(str(audio_file))
        else:
            logger.info(f"Using faster-whisper (model: {settings.whisper_model})...")
            transcript_result = transcribe_audio(
                audio_file,
                provider=settings.transcription_provider,
                model_name=settings.whisper_model
            )
        
        # Extract full text and segments
        if isinstance(transcript_result, dict):
            transcript_text = transcript_result.get("text", "")
            segments = transcript_result.get("segments", [])
        else:
            # If it's just a string, create a single segment
            transcript_text = transcript_result
            segments = [{"text": transcript_result, "start": 0.0, "end": 0.0}]
        
        logger.info(f"✅ Transcription complete: {len(transcript_text)} characters, {len(segments)} segments")
    
    except Exception as e:
        logger.error(f"❌ Transcription failed: {e}")
        logger.exception(e)
        return 1
    
    logger.info("\n" + "=" * 60)
    logger.info("STEP 2: Chunking")
    logger.info("=" * 60)
    
    # Chunk
    try:
        chunks = chunk_segments(
            segments,
            max_chars=settings.max_chunk_chars,
            min_chars=settings.min_chunk_chars
        )
        logger.info(f"✅ Created {len(chunks)} chunks")
        logger.info(f"   Max chunk size: {settings.max_chunk_chars} chars")
        logger.info(f"   Min chunk size: {settings.min_chunk_chars} chars")
    
    except Exception as e:
        logger.error(f"❌ Chunking failed: {e}")
        logger.exception(e)
        return 1
    
    logger.info("\n" + "=" * 60)
    logger.info("STEP 3: Tagging & Embedding")
    logger.info("=" * 60)
    logger.info(f"Embedding Provider: {settings.embedding_provider}")
    
    # Tag and embed
    try:
        # Tag all chunks
        tagged_chunks = []
        for chunk in chunks:
            topic, tone, domain = tag_chunk(chunk["text"])
            tagged_chunks.append({
                "start": chunk["start"],
                "end": chunk["end"],
                "text": chunk["text"],
                "topic": topic,
                "tone": tone,
                "domain": domain,
            })
        
        # Batch embed all chunks
        chunk_texts = [c["text"] for c in tagged_chunks]
        embeddings = embed_text_batch(chunk_texts)
        logger.info(f"✅ Generated {len(embeddings)} embeddings")
    
    except Exception as e:
        logger.error(f"❌ Tagging/Embedding failed: {e}")
        logger.exception(e)
        return 1
    
    logger.info("\n" + "=" * 60)
    logger.info("STEP 4: Database Storage")
    logger.info("=" * 60)
    
    # Store in database
    try:
        with SessionLocal() as db:
            # Create episode with full transcript
            episode = repository.create_episode(
                db,
                title=episode_title,
                audio_url=episode_url,
                transcript=transcript_text
            )
            logger.info(f"✅ Created episode record (ID: {episode.id})")
            
            # Store chunks with embeddings and tags
            for i, (chunk, embedding) in enumerate(zip(tagged_chunks, embeddings)):
                repository.create_chunk(
                    db,
                    episode_id=episode.id,
                    content=chunk["text"],
                    embedding=embedding,
                    chunk_index=i,
                    start_time=chunk["start"],
                    end_time=chunk["end"],
                    topic=chunk.get("topic"),
                    tone=chunk.get("tone"),
                    domain=chunk.get("domain"),
                )
                
                if (i + 1) % 10 == 0:
                    logger.info(f"   Stored {i + 1}/{len(chunks)} chunks...")
            
            db.commit()
            logger.info(f"✅ Stored {len(chunks)} chunks with embeddings and tags")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ INGESTION SUCCESSFUL!")
        logger.info("=" * 60)
        logger.info(f"Episode '{episode_title}' is now available in the database.")
        logger.info("It can be queried via the API immediately.")
        
        return 0
    
    except Exception as e:
        logger.error(f"❌ Storage failed: {e}")
        logger.exception(e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
