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
import re

from app.storage.models import Chunk, Episode, Transcript, TranscriptSegment
from app.core.config import settings

logger = logging.getLogger(__name__)

_STOPWORDS = {
    "the", "and", "that", "this", "with", "from", "your", "have", "what", "when",
    "where", "which", "about", "into", "them", "they", "their", "there", "would",
    "could", "should", "being", "been", "were", "will", "than", "then", "because",
    "while", "through", "after", "before", "over", "under", "between", "today",
    "still", "just", "more", "most", "some", "such", "really", "very", "does",
    "mean", "look", "like", "life", "mirror", "talk",
}


def _tokenize_for_overlap(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z'-]{2,}", (text or "").lower())
    return {word for word in words if word not in _STOPWORDS}


def _overlap_score(source_tokens: set[str], candidate_text: str) -> float:
    if not source_tokens:
        return 0.0
    candidate_tokens = _tokenize_for_overlap(candidate_text)
    if not candidate_tokens:
        return 0.0
    overlap = source_tokens & candidate_tokens
    return len(overlap) / max(1, min(len(source_tokens), 12))


def _score_candidate_text(
    *,
    text_value: str,
    question_tokens: set[str],
    answer_tokens: set[str],
    semantic: float = 0.0,
) -> tuple[float, float, float]:
    question_overlap = _overlap_score(question_tokens, text_value)
    answer_overlap = _overlap_score(answer_tokens, text_value)
    score = (
        semantic * 0.55 +
        question_overlap * 0.25 +
        answer_overlap * 0.20
    )
    if len((text_value or "").strip()) < 90:
        score -= 0.05
    return score, question_overlap, answer_overlap


def rerank_citation_moments(
    question: str,
    answer_text: str,
    answer_chunks: list[dict],
    candidate_episode_ids: list[int],
) -> list[dict]:
    """
    Refine the chosen citation timestamp for each already-selected episode.

    The initial episode selection is good at picking which episodes matter.
    This pass sharpens *where* inside those episodes we point by scoring each
    candidate chunk against both the user question and the final answer text.
    """
    if not answer_chunks or not candidate_episode_ids:
        return []

    question_tokens = _tokenize_for_overlap(question)
    answer_tokens = _tokenize_for_overlap(answer_text)

    chunks_by_episode: dict[int, list[dict]] = defaultdict(list)
    for chunk in answer_chunks:
        episode = (chunk or {}).get("episode") or {}
        episode_id = episode.get("id")
        if episode_id:
            chunks_by_episode[int(episode_id)].append(chunk)

    refined: list[dict] = []
    for episode_id in candidate_episode_ids:
        candidates = chunks_by_episode.get(int(episode_id), [])
        if not candidates:
            continue

        best_chunk = None
        best_score = float("-inf")

        for chunk in candidates:
            text_value = chunk.get("text", "")
            semantic = float(chunk.get("similarity", 0.0) or 0.0)
            score, question_overlap, answer_overlap = _score_candidate_text(
                text_value=text_value,
                question_tokens=question_tokens,
                answer_tokens=answer_tokens,
                semantic=semantic,
            )

            if score > best_score:
                best_score = score
                best_chunk = dict(chunk)
                best_chunk["citation_precision_score"] = round(score, 4)
                best_chunk["citation_question_overlap"] = round(question_overlap, 4)
                best_chunk["citation_answer_overlap"] = round(answer_overlap, 4)
                best_chunk["citation_semantic_score"] = round(semantic, 4)

        if best_chunk:
            refined.append(best_chunk)

    refined.sort(
        key=lambda chunk: float(chunk.get("citation_precision_score", 0.0) or 0.0),
        reverse=True,
    )

    filtered: list[dict] = []
    for idx, chunk in enumerate(refined):
        precision = float(chunk.get("citation_precision_score", 0.0) or 0.0)
        question_overlap = float(chunk.get("citation_question_overlap", 0.0) or 0.0)
        answer_overlap = float(chunk.get("citation_answer_overlap", 0.0) or 0.0)
        semantic = float(chunk.get("citation_semantic_score", 0.0) or 0.0)

        # Keep the strongest few by default, but avoid padding with weak,
        # generic episode moments that only barely match semantically.
        if idx < 3:
            filtered.append(chunk)
            continue

        has_lexical_support = max(question_overlap, answer_overlap) >= 0.08
        has_strong_semantic_support = semantic >= 0.62
        has_good_precision = precision >= 0.34

        if has_good_precision and (has_lexical_support or has_strong_semantic_support):
            filtered.append(chunk)
        else:
            logger.info(
                "Dropping weak citation moment for episode %s (precision=%.3f, q_overlap=%.3f, a_overlap=%.3f, semantic=%.3f)",
                (chunk.get("episode") or {}).get("id"),
                precision,
                question_overlap,
                answer_overlap,
                semantic,
            )

    if filtered:
        top_score = float(filtered[0].get("citation_precision_score", 0.0) or 0.0)
        second_score = float(filtered[1].get("citation_precision_score", 0.0) or 0.0) if len(filtered) > 1 else 0.0
        top_chunk = filtered[0]
        top_question_overlap = float(top_chunk.get("citation_question_overlap", 0.0) or 0.0)
        top_answer_overlap = float(top_chunk.get("citation_answer_overlap", 0.0) or 0.0)
        confidence_gap = top_score - second_score
        has_clear_support = top_score >= 0.38 and max(top_question_overlap, top_answer_overlap) >= 0.10
        has_clear_lead = confidence_gap >= 0.035 or len(filtered) == 1
        top_chunk["is_strongest_match"] = bool(has_clear_support and has_clear_lead)

    return filtered


def refine_citation_segments(
    db: Session,
    *,
    question: str,
    answer_text: str,
    citation_chunks: list[dict],
    padding_seconds: int = 12,
) -> list[dict]:
    """
    Improve citation precision by picking the best transcript segment inside each
    already-selected chunk window when transcript segments are available.
    """
    if not citation_chunks:
        return []

    question_tokens = _tokenize_for_overlap(question)
    answer_tokens = _tokenize_for_overlap(answer_text)
    refined_chunks: list[dict] = []

    for chunk in citation_chunks:
        episode = (chunk or {}).get("episode") or {}
        episode_id = episode.get("id")
        if not episode_id:
            refined_chunks.append(chunk)
            continue

        start_time = float(chunk.get("start_time", 0.0) or 0.0)
        end_time = float(chunk.get("end_time", start_time) or start_time)
        search_start = max(0.0, start_time - padding_seconds)
        search_end = max(search_start, end_time + padding_seconds)

        stmt = (
            select(TranscriptSegment)
            .join(Transcript, Transcript.id == TranscriptSegment.transcript_id)
            .where(Transcript.episode_id == int(episode_id))
            .where(TranscriptSegment.end_time >= search_start)
            .where(TranscriptSegment.start_time <= search_end)
            .order_by(TranscriptSegment.start_time.asc())
        )
        segments = db.execute(stmt).scalars().all()
        if not segments:
            refined_chunks.append(chunk)
            continue

        base_precision = float(chunk.get("citation_precision_score", chunk.get("similarity", 0.0)) or 0.0)
        best_segment = None
        best_score = float("-inf")

        for segment in segments:
            seg_text = (segment.text or "").strip()
            if len(seg_text) < 35:
                continue

            lexical_score, question_overlap, answer_overlap = _score_candidate_text(
                text_value=seg_text,
                question_tokens=question_tokens,
                answer_tokens=answer_tokens,
                semantic=0.0,
            )
            score = base_precision * 0.45 + lexical_score * 0.55
            if score > best_score:
                best_score = score
                best_segment = {
                    **chunk,
                    "text": seg_text,
                    "start_time": float(segment.start_time),
                    "end_time": float(segment.end_time),
                    "citation_precision_score": round(max(base_precision, score), 4),
                    "citation_question_overlap": round(question_overlap, 4),
                    "citation_answer_overlap": round(answer_overlap, 4),
                }

        refined_chunks.append(best_segment or chunk)

    return refined_chunks


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
