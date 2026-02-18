import gc
import logging
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.core.db import get_session_local
from app.ingestion.rss import fetch_feed, normalize_entries
from app.ingestion.audio import download_audio
from app.ingestion.transcription import transcribe_audio
from app.indexing.chunking import chunk_segments
from app.indexing.tagging import tag_chunk
from app.indexing.embeddings import embed_text_batch
from app.storage import repository
from app.storage import models

logger = logging.getLogger(__name__)


def refresh_db_connection(db: Session) -> Session:
    """Create a fresh database session to prevent idle timeout errors."""
    try:
        db.close()
    except:
        pass
    
    SessionMaker = get_session_local()
    return SessionMaker()


def check_episode_complete(db: Session, guid: str) -> bool:
    """Check if episode is completely processed (has transcript and chunks)."""
    try:
        episode = repository.get_episode_by_guid(db, guid)
        if not episode:
            return False
        
        # Episode must have chunks to be considered complete
        # (chunks are only created after successful transcription)
        chunk_count = db.query(models.Chunk).filter(models.Chunk.episode_id == episode.id).count()
        
        return chunk_count > 0
    except Exception as e:
        logger.error("Error checking episode completeness: %s", e)
        return False


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
    failed = 0
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

            # Refresh database connection at start of each episode to prevent idle timeout
            logger.info("Database connection lost, refreshing...")
            db = refresh_db_connection(db)

            # Check if episode is COMPLETELY processed (has transcript AND chunks)
            # Only check if we're not using pre-filtered entries
            if entries_to_process is None:
                if check_episode_complete(db, entry["guid"]):
                    logger.info("[%s/%s] Episode already complete, skipping: %s", 
                               idx + 1, len(entries), entry["title"])
                    skipped += 1
                    continue
                
                # Check if episode exists but is incomplete (needs re-processing)
                existing = repository.get_episode_by_guid(db, entry["guid"])
                if existing:
                    logger.info("[%s/%s] Episode exists but incomplete, re-processing: %s", 
                               idx + 1, len(entries), entry["title"])
                    # Delete incomplete episode data to start fresh
                    # Must delete in correct order due to foreign key constraints
                    db.query(models.Chunk).filter(models.Chunk.episode_id == existing.id).delete()
                    db.query(models.TranscriptSegment).filter(
                        models.TranscriptSegment.transcript_id.in_(
                            db.query(models.Transcript.id).filter(models.Transcript.episode_id == existing.id)
                        )
                    ).delete(synchronize_session=False)
                    db.query(models.Transcript).filter(models.Transcript.episode_id == existing.id).delete()
                    db.delete(existing)
                    db.commit()
                    logger.info("  ├─ Deleted incomplete episode data")

            logger.info("[%s/%s] Processing episode: %s", 
                       idx + 1, len(entries), entry["title"])
            
            try:
                
                # 1. Create episode
                episode = repository.create_episode(db, **entry)
                logger.info("  ├─ Created episode (id=%s)", episode.id)
                
                # 2. Download audio
                audio_filename = f"episode_{episode.id}.mp3"
                audio_path = download_audio(entry["audio_url"], settings.audio_dir, audio_filename)
                logger.info("  ├─ Downloaded audio: %s", audio_path.name)

                # 3. Transcribe
                logger.info("  ├─ Transcribing (model=%s)...", settings.whisper_model)
                # Store episode ID before transcription (will need it after connection refresh)
                episode_id = episode.id
                episode_guid = entry["guid"]
                
                transcript = transcribe_audio(
                    audio_path,
                    provider=settings.transcription_provider,
                    model_name=settings.whisper_model,
                )
                logger.info("  ├─ Transcription complete (%s segments)", len(transcript["segments"]))

                # Refresh database connection after long transcription operation
                # Transcription can take several minutes, causing idle timeout
                logger.info("Database connection lost after transcription, refreshing...")
                db = refresh_db_connection(db)
                
                # Re-fetch episode from new session
                episode = repository.get_episode_by_guid(db, episode_guid)
                if not episode:
                    raise Exception(f"Episode lost after connection refresh (guid={episode_guid})")

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
                failed += 1
                
                # Try to rollback and refresh connection
                try:
                    db.rollback()
                except:
                    pass
                
                try:
                    db = refresh_db_connection(db)
                except Exception as refresh_err:
                    logger.error("  └─ ⚠️  Failed to refresh connection: %s", refresh_err)
                
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

        message = f"processed={processed}, skipped={skipped}, failed={failed}"
        repository.finish_ingest_run(db, run.id, status="success", message=message)
        logger.info("Ingestion complete: %s", message)
        return {"processed": processed, "skipped": skipped, "failed": failed}
        
    except Exception as exc:
        logger.exception("Ingestion failed: %s", exc)
        # Refresh connection before trying to update the run status
        try:
            db.rollback()
        except:
            pass
        try:
            db = refresh_db_connection(db)
            repository.finish_ingest_run(db, run.id, status="failed", message=str(exc))
        except Exception as finish_err:
            logger.error("Failed to update ingest run status: %s", finish_err)
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
