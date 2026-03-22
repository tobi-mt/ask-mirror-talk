from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, Text, Float, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.core.db import Base


def _utcnow():
    return datetime.now(timezone.utc)



class Episode(Base):
    __tablename__ = "episodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    guid: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)
    published_at: Mapped[datetime] = mapped_column(DateTime)
    audio_url: Mapped[str] = mapped_column(String(1000))

    transcripts: Mapped[list["Transcript"]] = relationship(back_populates="episode")
    chunks: Mapped[list["Chunk"]] = relationship(back_populates="episode")


class Transcript(Base):
    __tablename__ = "transcripts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    episode_id: Mapped[int] = mapped_column(ForeignKey("episodes.id"))
    provider: Mapped[str] = mapped_column(String(50))
    language: Mapped[str] = mapped_column(String(20), default="en")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    raw_text: Mapped[str] = mapped_column(Text)

    episode: Mapped[Episode] = relationship(back_populates="transcripts")
    segments: Mapped[list["TranscriptSegment"]] = relationship(back_populates="transcript")


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transcript_id: Mapped[int] = mapped_column(ForeignKey("transcripts.id"))
    start_time: Mapped[float] = mapped_column(Float)
    end_time: Mapped[float] = mapped_column(Float)
    text: Mapped[str] = mapped_column(Text)

    transcript: Mapped[Transcript] = relationship(back_populates="segments")


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    episode_id: Mapped[int] = mapped_column(ForeignKey("episodes.id"))
    start_time: Mapped[float] = mapped_column(Float)
    end_time: Mapped[float] = mapped_column(Float)
    text: Mapped[str] = mapped_column(Text)
    topic: Mapped[str] = mapped_column(String(200))
    emotional_tone: Mapped[str] = mapped_column(String(200))
    growth_domain: Mapped[str] = mapped_column(String(200))
    embedding: Mapped[list[float]] = mapped_column(Vector(384))

    episode: Mapped[Episode] = relationship(back_populates="chunks")


class IngestRun(Base):
    __tablename__ = "ingest_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(50))
    message: Mapped[str] = mapped_column(Text, default="")


class QALog(Base):
    __tablename__ = "qa_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    episode_ids: Mapped[str] = mapped_column(String(500))
    latency_ms: Mapped[int] = mapped_column(Integer)
    user_ip: Mapped[str] = mapped_column(String(100))


class CitationClick(Base):
    """Track when users click on episode citations"""
    __tablename__ = "citation_clicks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    qa_log_id: Mapped[int] = mapped_column(ForeignKey("qa_logs.id"))
    episode_id: Mapped[int] = mapped_column(ForeignKey("episodes.id"))
    clicked_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    user_ip: Mapped[str] = mapped_column(String(100))
    timestamp: Mapped[float | None] = mapped_column(Float, nullable=True)  # Specific timestamp in episode if clicked


class UserFeedback(Base):
    """Track user feedback on answers (thumbs up/down, ratings, comments)"""
    __tablename__ = "user_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    qa_log_id: Mapped[int] = mapped_column(ForeignKey("qa_logs.id"))
    feedback_type: Mapped[str] = mapped_column(String(20))  # 'positive', 'negative', 'neutral'
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-5 stars (optional)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)  # Optional user comment
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    user_ip: Mapped[str] = mapped_column(String(100))


class PushSubscription(Base):
    """Store Web Push notification subscriptions from PWA users."""
    __tablename__ = "push_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    endpoint: Mapped[str] = mapped_column(Text, unique=True, index=True)
    p256dh_key: Mapped[str] = mapped_column(String(200))
    auth_key: Mapped[str] = mapped_column(String(100))
    user_ip: Mapped[str] = mapped_column(String(100))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_qotd: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_new_episodes: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class PushMotivationMessage(Base):
    """Pool of midday motivation messages — seeded from static list, expanded by AI.

    Generic messages are shared across all subscribers (source='static'|'generated').
    Personalized messages (source='personalized') are generated on-the-fly from a
    subscriber's recent qa_logs questions and are also stored here for history tracking.
    """
    __tablename__ = "push_motivation_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    theme: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source: Mapped[str] = mapped_column(String(20), default="static")  # 'static' | 'generated' | 'personalized'
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class PushQotdHistory(Base):
    """Track which QOTD questions have been sent to each push subscriber.

    Enables no-repeat delivery: each subscriber gets the next question from the
    global push_qotd_questions pool that they haven't seen yet. New questions are
    AI-generated and appended to the pool before it can be exhausted.
    """
    __tablename__ = "push_qotd_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subscription_id: Mapped[int] = mapped_column(Integer, index=True)
    qotd_id: Mapped[int] = mapped_column(Integer)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class PushQotdQuestion(Base):
    """Pool of QOTD questions — seeded from static list, expanded by AI generation.

    New questions are generated via GPT and appended whenever any subscriber is
    within REFILL_THRESHOLD questions of exhausting the pool, so the pool never
    runs dry and questions are never repeated.
    """
    __tablename__ = "push_qotd_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    theme: Mapped[str] = mapped_column(String(100))
    emoji: Mapped[str] = mapped_column(String(20))
    hook: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(20), default="static")  # "static" | "generated"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
