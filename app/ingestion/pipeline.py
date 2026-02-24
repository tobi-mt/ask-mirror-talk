import gc
import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.ingestion.rss import fetch_feed, normalize_entries
from app.ingestion.audio import download_audio
from app.ingestion.transcription import transcribe_audio
from app.indexing.chunking import chunk_segments
from app.indexing.tagging import tag_chunk
from app.indexing.embeddings import embed_text
from app.storage import repository

logger = logging.getLogger(__name__)


def run_ingestion(db: Session):
    if not settings.rss_url:
        raise ValueError("RSS URL is not configured")

    run = repository.create_ingest_run(db, status="started")
    feed = fetch_feed(settings.rss_url)
    entries = normalize_entries(feed)
    processed = 0

    try:
        for entry in entries:
            if processed >= settings.max_episodes_per_run:
                break

            if not entry["audio_url"]:
                logger.warning("Skipping entry with no audio URL: %s", entry["title"])
                continue

            existing = repository.get_episode_by_guid(db, entry["guid"])
            if existing:
                continue

            episode = repository.create_episode(db, **entry)
            audio_filename = f"episode_{episode.id}.mp3"
            audio_path = download_audio(entry["audio_url"], settings.audio_dir, audio_filename)

            transcript = transcribe_audio(
                audio_path,
                provider=settings.transcription_provider,
                model_name=settings.whisper_model,
            )

            repository.create_transcript(
                db,
                episode_id=episode.id,
                provider=settings.transcription_provider,
                raw_text=transcript["raw_text"],
                segments=transcript["segments"],
            )

            chunks = chunk_segments(
                transcript["segments"],
                max_chars=settings.max_chunk_chars,
                min_chars=settings.min_chunk_chars,
            )

            enriched_chunks = []
            for chunk in chunks:
                topic, tone, domain = tag_chunk(chunk["text"])
                embedding = embed_text(chunk["text"])
                enriched_chunks.append(
                    {
                        "start": chunk["start"],
                        "end": chunk["end"],
                        "text": chunk["text"],
                        "topic": topic,
                        "emotional_tone": tone,
                        "growth_domain": domain,
                        "embedding": embedding,
                    }
                )

            repository.create_chunks(db, episode_id=episode.id, chunks=enriched_chunks)
            processed += 1
            
            # Force garbage collection after each episode to free memory
            gc.collect()

        repository.finish_ingest_run(db, run.id, status="success", message=f"processed={processed}")
        return {"processed": processed}
    except Exception as exc:
        repository.finish_ingest_run(db, run.id, status="failed", message=str(exc))
        raise
