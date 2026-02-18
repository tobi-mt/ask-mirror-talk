from sqlalchemy.orm import Session
from sqlalchemy import select
from pgvector.sqlalchemy import Vector
import logging

from app.storage.models import Chunk, Episode
from app.core.config import settings

logger = logging.getLogger(__name__)


def retrieve_chunks(db: Session, query_embedding: list[float], diversity_lambda: float = None):
    """
    Retrieve relevant chunks using MMR (Maximal Marginal Relevance) for diversity.
    
    This balances relevance to the query with diversity across episodes, preventing
    the same episodes from dominating every response.
    
    Args:
        db: Database session
        query_embedding: Query embedding vector
        diversity_lambda: Balance between relevance (1.0) and diversity (0.0)
                         If None, uses settings.diversity_lambda (default 0.7)
                         0.7 = 70% relevance, 30% diversity
    
    Returns:
        List of (chunk, similarity) tuples with diverse episodes
    """
    # Use config value if not specified
    if diversity_lambda is None:
        diversity_lambda = settings.diversity_lambda
    # Get more candidates to allow for diversity selection
    # 5x gives us 30 candidates for 6 final results
    distance = Chunk.embedding.cosine_distance(query_embedding)
    stmt = (
        select(Chunk, distance.label("distance"))
        .order_by(distance.asc())
        .limit(settings.top_k * 5)  # Increased from 3x to 5x for more diversity
    )
    results = db.execute(stmt).all()
    
    # Convert to (chunk, similarity) and filter by threshold
    candidates = []
    for chunk, dist in results:
        similarity = 1 - float(dist)
        if similarity >= settings.min_similarity:
            candidates.append((chunk, similarity))
    
    if not candidates:
        logger.warning("No chunks found above similarity threshold")
        return []
    
    # MMR Algorithm: Balance relevance and diversity
    selected = []
    seen_episodes = set()
    
    # Always pick the most relevant chunk first
    best_chunk, best_similarity = candidates[0]
    selected.append((best_chunk, best_similarity))
    seen_episodes.add(best_chunk.episode_id)
    
    logger.info(f"MMR: Selected most relevant - Episode {best_chunk.episode_id} (similarity: {best_similarity:.3f})")
    
    # For remaining slots, balance relevance with diversity
    while len(selected) < settings.top_k:
        best_mmr_score = -1
        best_candidate = None
        best_candidate_similarity = 0
        
        for chunk, similarity in candidates:
            # Skip if already from a selected episode
            if chunk.episode_id in seen_episodes:
                continue
            
            # Calculate diversity: penalize episodes similar to already selected ones
            # In simple implementation, just ensure it's a different episode
            # More advanced: calculate embedding distance to selected chunks
            diversity_bonus = 0.3  # Fixed bonus for being a different episode
            
            # MMR score combines relevance and diversity
            # Higher lambda = more weight on relevance
            # Lower lambda = more weight on diversity
            mmr_score = (diversity_lambda * similarity) + ((1 - diversity_lambda) * diversity_bonus)
            
            if mmr_score > best_mmr_score:
                best_mmr_score = mmr_score
                best_candidate = (chunk, similarity)
                best_candidate_similarity = similarity
        
        # If we found a good diverse candidate, add it
        if best_candidate:
            selected.append(best_candidate)
            seen_episodes.add(best_candidate[0].episode_id)
            logger.info(f"MMR: Selected diverse - Episode {best_candidate[0].episode_id} "
                       f"(similarity: {best_candidate_similarity:.3f}, MMR score: {best_mmr_score:.3f})")
        else:
            # No more candidates available
            logger.info(f"MMR: Stopped at {len(selected)} results (no more diverse candidates)")
            break
    
    logger.info(f"MMR: Final selection - {len(selected)} unique episodes from {len(candidates)} candidates")
    
    return selected


def load_episode_map(db: Session, episode_ids: list[int]):
    rows = db.execute(select(Episode).where(Episode.id.in_(episode_ids))).scalars().all()
    return {row.id: row for row in rows}
