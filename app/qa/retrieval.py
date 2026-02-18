from sqlalchemy.orm import Session
from sqlalchemy import select
from pgvector.sqlalchemy import Vector

from app.storage.models import Chunk, Episode
from app.core.config import settings


def retrieve_chunks(db: Session, query_embedding: list[float]):
    """
    Retrieve relevant chunks with deduplication to avoid showing 
    multiple chunks from the same episode.
    """
    distance = Chunk.embedding.cosine_distance(query_embedding)
    stmt = (
        select(Chunk, distance.label("distance"))
        .order_by(distance.asc())
        .limit(settings.top_k * 3)  # Get 3x to allow for deduplication
    )
    results = db.execute(stmt).all()

    # Deduplicate: Keep only the best (most similar) chunk per episode
    seen_episodes = set()
    filtered = []
    
    for chunk, dist in results:
        similarity = 1 - float(dist)
        
        # Only include chunks above similarity threshold
        if similarity < settings.min_similarity:
            continue
            
        # Skip if we already have a chunk from this episode
        if chunk.episode_id in seen_episodes:
            continue
            
        # Add this chunk and mark the episode as seen
        seen_episodes.add(chunk.episode_id)
        filtered.append((chunk, similarity))
        
        # Stop once we have enough unique episodes
        if len(filtered) >= settings.top_k:
            break
    
    return filtered


def load_episode_map(db: Session, episode_ids: list[int]):
    rows = db.execute(select(Episode).where(Episode.id.in_(episode_ids))).scalars().all()
    return {row.id: row for row in rows}
