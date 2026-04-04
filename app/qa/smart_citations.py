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

_GENERIC_SEGMENT_MARKERS = {
    "well,",
    "you know",
    "i mean",
    "right.",
    "right?",
    "that's right",
    "uh",
    "um",
    "tell us",
    "welcome back",
    "thanks for having me",
    "thank you for having me",
    "before we get started",
    "in this episode",
    "for joining us",
    "podcast enthusiasts",
    "add a little sparkle",
    "friendly nudge",
    "if you're loving",
    "captivating stories",
    "let's take a quick break",
    "we'll be right back",
    "support the show",
    "share this episode",
    "politicians in d.c.",
}

_HOST_BRIDGE_PATTERNS = (
    "tell us",
    "can you talk about",
    "can you share",
    "what does that mean",
    "how does that feel",
    "let me ask you",
    "i'd like to know",
    "welcome back",
    "before we continue",
    "after the break",
    "we'll be right back",
    "hit that subscribe",
    "friendly nudge",
    "support the show",
)

_META_QUESTION_MARKERS = (
    "citation",
    "quoted source",
    "source moment",
    "prove the answer",
    "verify the answer",
    "supporting the answer",
    "really supporting",
    "episode reference",
    "references",
    "grounding",
    "evidence",
    "answer itself",
)


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


def _looks_generic_source_moment(text_value: str) -> bool:
    lower = (text_value or "").strip().lower()
    if not lower:
        return True
    if len(lower) < 70:
        return True
    marker_hits = sum(1 for marker in _GENERIC_SEGMENT_MARKERS if marker in lower[:140])
    if marker_hits >= 2:
        return True
    token_count = len(_tokenize_for_overlap(lower))
    return token_count < 4


def _is_standalone_evidence(text_value: str) -> bool:
    lower = (text_value or "").strip().lower()
    if not lower:
        return False
    if _looks_generic_source_moment(lower):
        return False
    if len(lower) < 110:
        return False
    if len(lower) > 460:
        return False
    if len(_tokenize_for_overlap(lower)) < 7:
        return False
    if sum(1 for pattern in _HOST_BRIDGE_PATTERNS if pattern in lower) >= 1:
        return False
    if lower.count("?") >= 2:
        return False
    if re.match(r"^(so|and|but|well|right)\b", lower) and len(lower) < 180:
        return False
    return True


def _is_abstract_or_meta_question(question: str) -> bool:
    lower = (question or "").strip().lower()
    if not lower:
        return False
    if any(marker in lower for marker in _META_QUESTION_MARKERS):
        return True
    tokens = _tokenize_for_overlap(lower)
    if len(tokens) <= 5 and any(word in tokens for word in {"truth", "meaning", "proof", "evidence", "answer"}):
        return True
    return False


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
    for chunk in refined:
        precision = float(chunk.get("citation_precision_score", 0.0) or 0.0)
        question_overlap = float(chunk.get("citation_question_overlap", 0.0) or 0.0)
        answer_overlap = float(chunk.get("citation_answer_overlap", 0.0) or 0.0)
        semantic = float(chunk.get("citation_semantic_score", 0.0) or 0.0)
        text_value = (chunk.get("text") or "").strip()

        has_lexical_support = max(question_overlap, answer_overlap) >= 0.10
        has_good_precision = precision >= 0.36
        has_min_semantic_support = semantic >= 0.50
        looks_generic = _looks_generic_source_moment(text_value)

        if has_good_precision and has_lexical_support and has_min_semantic_support and not looks_generic:
            filtered.append(chunk)
        else:
            logger.info(
                "Dropping weak citation moment for episode %s (precision=%.3f, q_overlap=%.3f, a_overlap=%.3f, semantic=%.3f, generic=%s)",
                (chunk.get("episode") or {}).get("id"),
                precision,
                question_overlap,
                answer_overlap,
                semantic,
                looks_generic,
            )

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
    Improve citation precision by picking the best transcript window inside each
    already-selected chunk when transcript segments are available.
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

        for start_idx, segment in enumerate(segments):
            for end_idx in range(start_idx, min(start_idx + 3, len(segments))):
                window_segments = segments[start_idx:end_idx + 1]
                window_start = float(window_segments[0].start_time)
                window_end = float(window_segments[-1].end_time)
                if window_end - window_start > 42:
                    break

                window_text = " ".join((seg.text or "").strip() for seg in window_segments).strip()
                if len(window_text) < 60:
                    continue

                lexical_score, question_overlap, answer_overlap = _score_candidate_text(
                    text_value=window_text,
                    question_tokens=question_tokens,
                    answer_tokens=answer_tokens,
                    semantic=0.0,
                )
                score = base_precision * 0.40 + lexical_score * 0.60

                # Prefer self-contained, quoteable moments over tiny fragments.
                if 110 <= len(window_text) <= 320:
                    score += 0.04
                elif len(window_text) < 90:
                    score -= 0.08
                elif len(window_text) > 420:
                    score -= 0.04

                if _looks_generic_source_moment(window_text):
                    score -= 0.18

                # Early-episode snippets are often intros; only allow them when they
                # show unmistakable lexical support for the actual topic.
                if window_start < 45 and max(question_overlap, answer_overlap) < 0.16:
                    score -= 0.18

                # Very late snippets can also be outro-like or summary-like.
                if window_start >= max(0.0, end_time - 15) and max(question_overlap, answer_overlap) < 0.12:
                    score -= 0.06

                if score > best_score:
                    best_score = score
                    best_segment = {
                        **chunk,
                        "text": window_text,
                        "start_time": window_start,
                        "end_time": window_end,
                        "citation_precision_score": round(max(base_precision, score), 4),
                        "citation_question_overlap": round(question_overlap, 4),
                        "citation_answer_overlap": round(answer_overlap, 4),
                    }

        chosen = best_segment or chunk
        chosen_precision = float(chosen.get("citation_precision_score", 0.0) or 0.0)
        chosen_question_overlap = float(chosen.get("citation_question_overlap", 0.0) or 0.0)
        chosen_answer_overlap = float(chosen.get("citation_answer_overlap", 0.0) or 0.0)
        chosen_start = float(chosen.get("start_time", 0.0) or 0.0)
        chosen_text = (chosen.get("text") or "").strip()

        weak_overlap = max(chosen_question_overlap, chosen_answer_overlap) < 0.08
        weak_precision = chosen_precision < 0.34
        generic_window = _looks_generic_source_moment(chosen_text)
        suspicious_intro = chosen_start < 45 and max(chosen_question_overlap, chosen_answer_overlap) < 0.16

        if (weak_precision and weak_overlap) or generic_window or suspicious_intro:
            logger.info(
                "Dropping low-trust citation segment for episode %s (precision=%.3f, q_overlap=%.3f, a_overlap=%.3f, start=%.1f)",
                episode_id,
                chosen_precision,
                chosen_question_overlap,
                chosen_answer_overlap,
                chosen_start,
            )
            continue

        refined_chunks.append(chosen)

    return refined_chunks


def finalize_citation_confidence(citation_chunks: list[dict]) -> list[dict]:
    """
    Re-evaluate badge confidence after segment refinement / filtering.
    Ensures only the final top citation can carry the strongest-match badge.
    """
    if not citation_chunks:
        return []

    ordered = sorted(
        [dict(chunk) for chunk in citation_chunks],
        key=lambda chunk: float(chunk.get("citation_precision_score", chunk.get("similarity", 0.0)) or 0.0),
        reverse=True,
    )

    for chunk in ordered:
        chunk["is_strongest_match"] = False

    # Temporarily disable the badge until production testing shows the top
    # citation is consistently trustworthy enough to merit the claim.
    return ordered


def select_citation_segments(
    db: Session,
    *,
    question: str,
    answer_text: str,
    candidate_episodes: list[dict],
    min_citations: int = 2,
    max_citations: int = 3,
) -> list[dict]:
    """
    Select citations from transcript segments first, not from chunk timestamps.
    Only keep 2-3 strong, self-contained source moments.
    """
    if not candidate_episodes:
        return []

    question_tokens = _tokenize_for_overlap(question)
    answer_tokens = _tokenize_for_overlap(answer_text)
    is_meta_question = _is_abstract_or_meta_question(question)

    episode_meta = {
        int(item["episode"]["id"]): item
        for item in candidate_episodes
        if item.get("episode", {}).get("id")
    }
    episode_ids = list(episode_meta.keys())
    if not episode_ids:
        return []

    stmt = (
        select(Transcript.episode_id, TranscriptSegment)
        .join(Transcript, Transcript.id == TranscriptSegment.transcript_id)
        .where(Transcript.episode_id.in_(episode_ids))
        .order_by(Transcript.episode_id.asc(), TranscriptSegment.start_time.asc())
    )
    rows = db.execute(stmt).all()

    segments_by_episode: dict[int, list[TranscriptSegment]] = defaultdict(list)
    for episode_id, segment in rows:
        segments_by_episode[int(episode_id)].append(segment)

    best_per_episode: list[dict] = []
    for episode_id, segments in segments_by_episode.items():
        episode_context = episode_meta.get(int(episode_id))
        if not episode_context or not segments:
            continue

        episode_boost = max(
            float(episode_context.get("relevance_score", 0.0) or 0.0),
            float(episode_context.get("similarity", 0.0) or 0.0),
        )

        best_candidate = None
        best_score = float("-inf")
        for start_idx in range(len(segments)):
            for end_idx in range(start_idx, min(start_idx + 4, len(segments))):
                window_segments = segments[start_idx:end_idx + 1]
                window_start = float(window_segments[0].start_time)
                window_end = float(window_segments[-1].end_time)
                if window_end - window_start > 55:
                    break

                window_text = " ".join((seg.text or "").strip() for seg in window_segments).strip()
                if not _is_standalone_evidence(window_text):
                    continue

                _, question_overlap, answer_overlap = _score_candidate_text(
                    text_value=window_text,
                    question_tokens=question_tokens,
                    answer_tokens=answer_tokens,
                    semantic=0.0,
                )
                overlap = max(question_overlap, answer_overlap)
                if overlap < 0.12:
                    continue

                score = (
                    min(episode_boost, 1.0) * 0.35 +
                    question_overlap * 0.35 +
                    answer_overlap * 0.30
                )

                if 130 <= len(window_text) <= 320:
                    score += 0.05
                if window_start < 60 and overlap < 0.18:
                    score -= 0.25
                if sum(1 for pattern in _GENERIC_SEGMENT_MARKERS if pattern in window_text.lower()) >= 1:
                    score -= 0.30

                if score > best_score:
                    best_score = score
                    best_candidate = {
                        "text": window_text,
                        "start_time": window_start,
                        "end_time": window_end,
                        "episode": episode_context["episode"],
                        "similarity": float(episode_context.get("similarity", 0.0) or 0.0),
                        "relevance_score": float(episode_context.get("relevance_score", 0.0) or 0.0),
                        "citation_precision_score": round(score, 4),
                        "citation_question_overlap": round(question_overlap, 4),
                        "citation_answer_overlap": round(answer_overlap, 4),
                        "is_strongest_match": False,
                    }

        if best_candidate and float(best_candidate["citation_precision_score"]) >= 0.34:
            best_per_episode.append(best_candidate)

    best_per_episode.sort(
        key=lambda item: float(item.get("citation_precision_score", 0.0) or 0.0),
        reverse=True,
    )

    strong = [
        item for item in best_per_episode
        if float(item.get("citation_precision_score", 0.0) or 0.0) >= 0.40
        and max(
            float(item.get("citation_question_overlap", 0.0) or 0.0),
            float(item.get("citation_answer_overlap", 0.0) or 0.0),
        ) >= 0.14
    ]

    very_strong = [
        item for item in best_per_episode
        if float(item.get("citation_precision_score", 0.0) or 0.0) >= 0.48
        and max(
            float(item.get("citation_question_overlap", 0.0) or 0.0),
            float(item.get("citation_answer_overlap", 0.0) or 0.0),
        ) >= 0.18
    ]

    if is_meta_question:
        if len(very_strong) >= 2:
            return finalize_citation_confidence(very_strong[:max_citations])
        logger.info("Meta/abstract question detected; refusing weak citations for question: %s", question[:140])
        return []

    if len(strong) >= min_citations:
        selected = strong[:max_citations]
    else:
        selected = best_per_episode[:max_citations]

    if not is_meta_question:
        # For normal questions, still refuse citations if we can't find at least
        # one clearly solid supporting moment.
        if not strong and len(selected) > 0:
            logger.info("No strong citation support found; returning broader reflection for question: %s", question[:140])
            return []

    return finalize_citation_confidence(selected)


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
