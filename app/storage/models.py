from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.core.db import Base


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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
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
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(50))
    message: Mapped[str] = mapped_column(Text, default="")


class QALog(Base):
    __tablename__ = "qa_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    episode_ids: Mapped[str] = mapped_column(String(500))
    latency_ms: Mapped[int] = mapped_column(Integer)
    user_ip: Mapped[str] = mapped_column(String(100))
