from sqlalchemy.orm import Session
from sqlalchemy import select

from app.storage import models


def get_episode_by_guid(db: Session, guid: str):
    return db.scalar(select(models.Episode).where(models.Episode.guid == guid))


def create_episode(db: Session, **kwargs) -> models.Episode:
    episode = models.Episode(**kwargs)
    db.add(episode)
    db.commit()
    db.refresh(episode)
    return episode


def create_transcript(db: Session, episode_id: int, provider: str, raw_text: str, segments: list[dict]):
    transcript = models.Transcript(
        episode_id=episode_id,
        provider=provider,
        raw_text=raw_text,
    )
    db.add(transcript)
    db.flush()

    for segment in segments:
        db.add(
            models.TranscriptSegment(
                transcript_id=transcript.id,
                start_time=segment["start"],
                end_time=segment["end"],
                text=segment["text"],
            )
        )
    db.commit()
    db.refresh(transcript)
    return transcript


def create_chunks(db: Session, episode_id: int, chunks: list[dict]):
    for chunk in chunks:
        db.add(
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
        )
    db.commit()


def log_qa(db: Session, question: str, answer: str, episode_ids: list[int], latency_ms: int, user_ip: str):
    log = models.QALog(
        question=question,
        answer=answer,
        episode_ids=",".join(str(eid) for eid in episode_ids),
        latency_ms=latency_ms,
        user_ip=user_ip,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def log_citation_click(db: Session, qa_log_id: int, episode_id: int, user_ip: str, timestamp: float = None):
    """Log when a user clicks on a cited episode"""
    click = models.CitationClick(
        qa_log_id=qa_log_id,
        episode_id=episode_id,
        user_ip=user_ip,
        timestamp=timestamp,
    )
    db.add(click)
    db.commit()
    return click


def log_user_feedback(db: Session, qa_log_id: int, feedback_type: str, user_ip: str, rating: int = None, comment: str = None):
    """Log user feedback on an answer"""
    feedback = models.UserFeedback(
        qa_log_id=qa_log_id,
        feedback_type=feedback_type,
        rating=rating,
        comment=comment,
        user_ip=user_ip,
    )
    db.add(feedback)
    db.commit()
    return feedback


def create_ingest_run(db: Session, status: str, message: str = "") -> models.IngestRun:
    run = models.IngestRun(status=status, message=message)
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def finish_ingest_run(db: Session, run_id: int, status: str, message: str = ""):
    run = db.get(models.IngestRun, run_id)
    if not run:
        return
    run.status = status
    run.message = message
    run.finished_at = __import__("datetime").datetime.utcnow()
    db.commit()
