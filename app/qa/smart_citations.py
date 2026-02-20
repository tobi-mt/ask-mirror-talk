"""
Smart Episode Reference Selection

This module implements intelligent episode selection for citations,
ensuring that referenced episodes are highly relevant to the user's question.

Key Features:
1. Answer generation uses ALL relevant chunks (comprehensive context)
2. Episode references are selected based on episode-level relevance
3. Top 5 most relevant episodes are cited (not random chunks)
4. Each episode shows its most relevant timestamp
"""

from sqlalchemy.orm import Session
from sqlalchemy import select, func
from collections import defaultdict
import logging

from app.storage.models import Chunk, Episode
from app.core.config import settings

logger = logging.getLogger(__name__)


def select_top_episodes_for_citation(
    chunks_with_similarity: list[tuple],
    max_episodes: int = 5
) -> list[dict]:
    """
    Select the top N most relevant episodes for citation from retrieved chunks.
    
    This ensures that the cited episodes are truly the most relevant to the question,
    even if many chunks were used to generate the answer.
    
    Args:
        chunks_with_similarity: List of (chunk, similarity) tuples
        max_episodes: Maximum number of episodes to cite (default: 5)
        
    Returns:
        List of episode citations with best timestamps
    """
    # Group chunks by episode and calculate episode-level relevance
    episode_groups = defaultdict(list)
    
    for chunk, similarity in chunks_with_similarity:
        episode_groups[chunk.episode_id].append((chunk, similarity))
    
    # Calculate episode relevance scores
    episode_scores = []
    for episode_id, chunk_list in episode_groups.items():
        # Score based on:
        # 1. Best chunk similarity (most important)
        # 2. Average similarity across all chunks (consistency)
        # 3. Number of relevant chunks (coverage)
        
        best_similarity = max(sim for _, sim in chunk_list)
        avg_similarity = sum(sim for _, sim in chunk_list) / len(chunk_list)
        chunk_count = len(chunk_list)
        
        # Weighted score: 60% best match, 30% average, 10% coverage
        relevance_score = (
            0.6 * best_similarity +
            0.3 * avg_similarity +
            0.1 * min(chunk_count / 5, 1.0)  # Cap coverage bonus at 5 chunks
        )
        
        episode_scores.append({
            'episode_id': episode_id,
            'chunks': chunk_list,
            'relevance_score': relevance_score,
            'best_similarity': best_similarity,
            'chunk_count': chunk_count
        })
    
    # Sort by relevance score and take top N
    episode_scores.sort(key=lambda x: x['relevance_score'], reverse=True)
    top_episodes = episode_scores[:max_episodes]
    
    logger.info(f"Selected top {len(top_episodes)} episodes from {len(episode_groups)} candidates")
    
    # For each top episode, select the best timestamp(s)
    episode_citations = []
    for ep_data in top_episodes:
        # Sort chunks by similarity to find best segments
        sorted_chunks = sorted(ep_data['chunks'], key=lambda x: x[1], reverse=True)
        
        # Take the best chunk for this episode
        best_chunk, best_sim = sorted_chunks[0]
        
        # Optionally, if there are multiple high-quality chunks in different
        # parts of the episode, we could include multiple timestamps
        # For now, we'll just use the single best one
        
        episode_citations.append({
            'episode_id': best_chunk.episode_id,
            'chunk': best_chunk,
            'similarity': best_sim,
            'relevance_score': ep_data['relevance_score'],
            'total_relevant_chunks': ep_data['chunk_count']
        })
    
    return episode_citations


def retrieve_chunks_two_tier(
    db: Session,
    query_embedding: list[float],
    diversity_lambda: float = None
):
    """
    Two-tier retrieval strategy:
    1. Retrieve many chunks for comprehensive answer generation
    2. Select top episodes for focused citations
    
    Args:
        db: Database session
        query_embedding: Query embedding vector
        diversity_lambda: Balance between relevance and diversity (for answer context)
        
    Returns:
        dict with 'answer_chunks' (all relevant) and 'citation_episodes' (top episodes)
    """
    from app.qa.retrieval import retrieve_chunks
    
    # Get diverse chunks for answer generation (uses MMR)
    # This ensures comprehensive coverage for the answer
    answer_chunks = retrieve_chunks(db, query_embedding, diversity_lambda)
    
    # Now select top episodes for citations based on pure relevance
    # We want the MOST relevant episodes, not necessarily diverse ones
    citation_episodes = select_top_episodes_for_citation(
        answer_chunks,
        max_episodes=settings.max_cited_episodes
    )
    
    logger.info(f"Two-tier retrieval: {len(answer_chunks)} chunks for answer, "
                f"{len(citation_episodes)} episodes for citations")
    
    return {
        'answer_chunks': answer_chunks,  # All chunks for comprehensive answer
        'citation_episodes': citation_episodes  # Top relevant episodes only
    }


def get_multiple_timestamps_per_episode(
    chunks_with_similarity: list[tuple],
    max_timestamps_per_episode: int = 3,
    min_time_gap_seconds: int = 120  # 2 minutes minimum gap between timestamps
) -> dict:
    """
    For each episode, identify multiple relevant timestamps if the episode
    has several distinct relevant segments.
    
    This is useful for long episodes that discuss the topic in multiple places.
    
    Args:
        chunks_with_similarity: List of (chunk, similarity) tuples
        max_timestamps_per_episode: Max timestamps to show per episode
        min_time_gap_seconds: Minimum time gap between selected segments
        
    Returns:
        Dict mapping episode_id to list of timestamp dicts
    """
    episode_timestamps = defaultdict(list)
    
    for chunk, similarity in chunks_with_similarity:
        episode_id = chunk.episode_id
        episode_timestamps[episode_id].append({
            'chunk': chunk,
            'similarity': similarity,
            'start_time': chunk.start_time,
            'end_time': chunk.end_time
        })
    
    # For each episode, select diverse timestamps
    result = {}
    for episode_id, timestamps in episode_timestamps.items():
        # Sort by similarity
        timestamps.sort(key=lambda x: x['similarity'], reverse=True)
        
        selected = []
        for ts in timestamps:
            # Check if this timestamp is far enough from already selected ones
            if len(selected) >= max_timestamps_per_episode:
                break
                
            if not selected:
                # Always add the best one
                selected.append(ts)
            else:
                # Check time gap from existing selections
                too_close = False
                for existing in selected:
                    time_gap = abs(ts['start_time'] - existing['start_time'])
                    if time_gap < min_time_gap_seconds:
                        too_close = True
                        break
                
                if not too_close:
                    selected.append(ts)
        
        result[episode_id] = selected
    
    return result
