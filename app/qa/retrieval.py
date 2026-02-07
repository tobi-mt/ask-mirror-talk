from sqlalchemy.orm import Session
from sqlalchemy import select
from pgvector.sqlalchemy import Vector

from app.storage.models import Chunk, Episode
from app.core.config import settings


def retrieve_chunks(db: Session, query_embedding: list[float]):
    distance = Chunk.embedding.cosine_distance(query_embedding)
    stmt = (
        select(Chunk, distance.label("distance"))
        .order_by(distance.asc())
        .limit(settings.top_k)
    )
    results = db.execute(stmt).all()

    filtered = []
    for chunk, dist in results:
        similarity = 1 - float(dist)
        if similarity >= settings.min_similarity:
            filtered.append((chunk, similarity))
    return filtered


def load_episode_map(db: Session, episode_ids: list[int]):
    rows = db.execute(select(Episode).where(Episode.id.in_(episode_ids))).scalars().all()
    return {row.id: row for row in rows}
