import gc
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.ingestion.rss import fetch_feed, normalize_entries
from app.ingestion.audio import download_audio
from app.ingestion.transcription import transcribe_audio
from app.indexing.chunking import chunk_segments
from app.indexing.tagging import tag_chunk
from app.indexing.embeddings import embed_text_batch
from app.storage import repository
from app.storage import models

logger = logging.getLogger(__name__)


def run_ingestion_optimized(db: Session, max_episodes: int | None = None, entries_to_process: list | None = None):
    """Optimized ingestion pipeline with batching and better logging.
    
    Args:
        db: Database session
        max_episodes: Maximum number of episodes to process
        entries_to_process: Pre-filtered list of entries to process. If None, will fetch and filter from RSS feed.
    """
    max_episodes = max_episodes or settings.max_episodes_per_run
    run = repository.create_ingest_run(db, status="started")
    
    logger.info("Starting ingestion run (max_episodes=%s)", max_episodes)
    
    # If entries are provided, use them directly. Otherwise fetch from RSS feed.
    if entries_to_process is None:
        if not settings.rss_url:
            raise ValueError("RSS URL is not configured")
        feed = fetch_feed(settings.rss_url)
        entries = normalize_entries(feed)
    else:
        entries = entries_to_process
        logger.info("Using pre-filtered entries (%s episodes)", len(entries))
    
    processed = 0
    skipped = 0
    audio_path = None  # Track current audio file for cleanup

    try:
        for idx, entry in enumerate(entries):
            if processed >= max_episodes:
                logger.info("Reached max episodes limit (%s), stopping", max_episodes)
                break

            if not entry["audio_url"]:
                logger.warning("[%s/%s] Skipping entry with no audio URL: %s", 
                             idx + 1, len(entries), entry["title"])
                skipped += 1
                continue

            # Only check if episode exists if we're not using pre-filtered entries
            if entries_to_process is None:
                existing = repository.get_episode_by_guid(db, entry["guid"])
                if existing:
                    logger.info("[%s/%s] Episode already exists: %s", 
                               idx + 1, len(entries), entry["title"])
                    skipped += 1
                    continue

            logger.info("[%s/%s] Processing episode: %s", 
                       idx + 1, len(entries), entry["title"])
            
            try:
                # Refresh database connection to prevent idle timeout
                try:
                    db.execute("SELECT 1")
                except Exception:
                    logger.warning("Database connection lost, refreshing...")
                    db.rollback()
                
                # 1. Create episode
                episode = repository.create_episode(db, **entry)
                logger.info("  ├─ Created episode (id=%s)", episode.id)
                
                # 2. Download audio
                audio_filename = f"episode_{episode.id}.mp3"
                audio_path = download_audio(entry["audio_url"], settings.audio_dir, audio_filename)
                logger.info("  ├─ Downloaded audio: %s", audio_path.name)

                # 3. Transcribe
                logger.info("  ├─ Transcribing (model=%s)...", settings.whisper_model)
                transcript = transcribe_audio(
                    audio_path,
                    provider=settings.transcription_provider,
                    model_name=settings.whisper_model,
                )
                logger.info("  ├─ Transcription complete (%s segments)", len(transcript["segments"]))

                # 4. Save transcript
                repository.create_transcript(
                    db,
                    episode_id=episode.id,
                    provider=settings.transcription_provider,
                    raw_text=transcript["raw_text"],
                    segments=transcript["segments"],
                )

                # 5. Chunk segments
                chunks = chunk_segments(
                    transcript["segments"],
                    max_chars=settings.max_chunk_chars,
                    min_chars=settings.min_chunk_chars,
                )
                logger.info("  ├─ Created %s chunks", len(chunks))

                # 6. Tag chunks (fast, no need to batch)
                tagged_chunks = []
                for chunk in chunks:
                    topic, tone, domain = tag_chunk(chunk["text"])
                    tagged_chunks.append({
                        "start": chunk["start"],
                        "end": chunk["end"],
                        "text": chunk["text"],
                        "topic": topic,
                        "emotional_tone": tone,
                        "growth_domain": domain,
                    })

                # 7. BATCH EMBED all chunks at once (MUCH FASTER!)
                logger.info("  ├─ Embedding %s chunks (batch mode)...", len(tagged_chunks))
                chunk_texts = [c["text"] for c in tagged_chunks]
                embeddings = embed_text_batch(chunk_texts)
                
                # Combine tags with embeddings
                enriched_chunks = []
                for tagged_chunk, embedding in zip(tagged_chunks, embeddings):
                    enriched_chunks.append({**tagged_chunk, "embedding": embedding})

                # 8. BATCH INSERT all chunks at once (MUCH FASTER!)
                logger.info("  ├─ Saving %s chunks to database...", len(enriched_chunks))
                _bulk_create_chunks(db, episode.id, enriched_chunks)
                
                logger.info("  └─ ✓ Episode complete (id=%s)", episode.id)
                processed += 1
                
                # Clean up audio file immediately after processing to save disk space
                if audio_path and audio_path.exists():
                    try:
                        audio_path.unlink()
                        logger.info("  └─ Cleaned up audio file")
                        audio_path = None
                    except Exception as e:
                        logger.warning("  └─ Failed to cleanup audio file: %s", e)
                
            except ValueError as e:
                # Handle known errors (e.g., file too large, compression failed)
                logger.warning("  └─ ⚠️  Skipping episode: %s", str(e))
                skipped += 1
                # Clean up audio file if download succeeded but transcription failed
                if audio_path and audio_path.exists():
                    try:
                        audio_path.unlink()
                        audio_path = None
                    except Exception:
                        pass
                continue
                
            except Exception as e:
                # Log error but continue with next episode
                logger.error("  └─ ❌ Episode failed: %s", str(e), exc_info=True)
                skipped += 1
                # Clean up audio file on any error
                if audio_path and audio_path.exists():
                    try:
                        audio_path.unlink()
                        audio_path = None
                    except Exception:
                        pass
                continue
            
            finally:
                # Force garbage collection after each episode to free memory
                gc.collect()

        message = f"processed={processed}, skipped={skipped}"
        repository.finish_ingest_run(db, run.id, status="success", message=message)
        logger.info("Ingestion complete: %s", message)
        return {"processed": processed, "skipped": skipped}
        
    except Exception as exc:
        logger.exception("Ingestion failed: %s", exc)
        repository.finish_ingest_run(db, run.id, status="failed", message=str(exc))
        raise


def _bulk_create_chunks(db: Session, episode_id: int, chunks: list[dict]):
    """Bulk insert chunks for better performance."""
    chunk_objects = [
        models.Chunk(
            episode_id=episode_id,
            start_time=chunk["start"],
            end_time=chunk["end"],
            text=chunk["text"],
            topic=chunk["topic"],
            emotional_tone=chunk["emotional_tone"],
            growth_domain=chunk["growth_domain"],
            embedding=chunk["embedding"],
        )
        for chunk in chunks
    ]
    db.bulk_save_objects(chunk_objects)
    db.commit()
