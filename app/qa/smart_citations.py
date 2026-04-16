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
    "thank you so much for sharing that",
    "i really appreciate you",
    "i appreciate you taking",
    "this is what i do on a daily basis",
    "the language that i speak on a daily basis",
    "i have 450 employees",
    "i pray all the time",
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
    "thank you so much for sharing",
    "i really appreciate you",
    "i appreciate you taking",
    "this is what i do on a daily basis",
    "the language that i speak on a daily basis",
)

_META_QUESTION_MARKERS = (
    "citation",
    "quoted source",
    "source moment",
    "prove the answer",
    "verify the answer",
    "supporting the answer",
    "supports the answer",
    "supports an answer",
    "citation genuinely supports",
    "citation is actually supporting",
    "quoted source really proves",
    "really supporting",
    "episode reference",
    "references",
    "grounding",
    "evidence",
    "answer itself",
    "just nearby",
    "sounding related",
    "actually supporting",
)

_PERSONAL_STORY_MARKERS = (
    "my fiance",
    "my fiancée",
    "at the time",
    "every time i get angry",
    "every time i feel",
    "every time i was",
    "i know exactly where it's coming from",
    "left me",
    "when i was",
    "when i got",
    "when i went",
    "when i started",
    "when i stopped",
    "in my life",
    "in my marriage",
    "in my relationship",
    "i had to",
    "i used to",
    "i remember",
    "i was working",
    "i had 450 employees",
    "my employees",
    "my company",
    "my business",
    "my childhood",
)

_PROGRESS_TIME_MARKERS = (
    "daily",
    "practice",
    "over time",
    "with time",
    "day by day",
    "step by step",
    "habit",
    "habits",
    "consistent",
    "consistently",
    "repetition",
    "repeated",
    "repeat",
    "track",
    "tracking",
    "change",
    "changing",
    "growth",
    "progress",
    "gradually",
    "gradual",
)

_COURAGE_THEME_MARKERS = (
    "courage",
    "courageous",
    "fear",
    "fearful",
    "brave",
    "bravery",
    "bold",
    "risk",
    "risks",
    "challenge",
    "challenging",
    "discomfort",
    "growth",
    "resilience",
    "resilient",
)

_VAGUE_EXAMPLE_MARKERS = (
    "for example",
    "maybe",
    "also in the past",
    "it could also be about",
    "or maybe",
    "in one way or the other",
    "for instance",
)

_DECLARATIVE_GUIDANCE_MARKERS = (
    "we have to",
    "we need to",
    "you can",
    "you have to",
    "you need to",
    "it's about",
    "it is about",
    "it's not about",
    "it takes",
    "it requires",
    "the key is",
    "the goal is",
    "what matters is",
    "it's okay to",
    "boundaries are",
    "forgiveness is",
    "grief is",
    "trust is",
)

_BOUNDARY_THEME_MARKERS = (
    "boundary",
    "boundaries",
    "personal space",
    "what i need",
    "healthy boundaries",
)

_FORGIVENESS_THEME_MARKERS = (
    "forgive",
    "forgiveness",
    "release",
    "resentment",
    "trust",
    "betrayal",
    "justice",
)

_GRIEF_THEME_MARKERS = (
    "grief",
    "grieving",
    "loss",
    "mourning",
    "honor how you're feeling",
    "feelings",
    "sadness",
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


def _overlap_count(source_tokens: set[str], candidate_text: str) -> int:
    if not source_tokens:
        return 0
    candidate_tokens = _tokenize_for_overlap(candidate_text)
    if not candidate_tokens:
        return 0
    return len(source_tokens & candidate_tokens)


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
        question_overlap * 0.30 +
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


def _looks_bridge_or_polite_exchange(text_value: str) -> bool:
    lower = (text_value or "").strip().lower()
    if not lower:
        return True
    if sum(1 for pattern in _HOST_BRIDGE_PATTERNS if pattern in lower) >= 1:
        return True
    if lower.startswith("thank you") or lower.startswith("i appreciate you"):
        return True
    if "for sharing that" in lower or "thanks for sharing" in lower:
        return True
    return False


def _looks_conversational_or_setup(text_value: str) -> bool:
    lower = (text_value or "").strip().lower()
    if not lower:
        return True
    if _looks_bridge_or_polite_exchange(lower):
        return True
    if lower.count("?") >= 1:
        return True
    if any(marker in lower for marker in _VAGUE_EXAMPLE_MARKERS):
        return True
    if lower.startswith("so ") or lower.startswith("and ") or lower.startswith("because ") or lower.startswith("cause "):
        return True
    return False


def _has_declarative_guidance_shape(text_value: str) -> bool:
    lower = (text_value or "").strip().lower()
    if not lower:
        return False
    if any(marker in lower for marker in _DECLARATIVE_GUIDANCE_MARKERS):
        return True
    sentences = [part.strip() for part in re.split(r"[.!?]+", lower) if part.strip()]
    if not sentences:
        return False
    first = sentences[0]
    return (
        first.startswith("you ")
        or first.startswith("your ")
        or first.startswith("forgiveness ")
        or first.startswith("grief ")
        or first.startswith("boundaries ")
        or first.startswith("trust ")
        or first.startswith("healing ")
    )


def _trim_conversational_tail(text_value: str) -> str:
    text_value = (text_value or "").strip()
    if not text_value:
        return ""
    sentences = [part.strip() for part in re.split(r'(?<=[.!?])\s+', text_value) if part.strip()]
    kept: list[str] = []
    for sentence in sentences:
        lower = sentence.lower()
        if _looks_bridge_or_polite_exchange(lower):
            break
        if _looks_conversational_or_setup(lower) and kept:
            break
        kept.append(sentence)
    trimmed = " ".join(kept).strip()
    return trimmed or text_value


def _split_quote_sentences(text_value: str) -> list[str]:
    text_value = (text_value or "").strip()
    if not text_value:
        return []
    return [part.strip() for part in re.split(r'(?<=[.!?])\s+', text_value) if part.strip()]


def _sentence_quality_for_question(question: str, sentence: str) -> float:
    lower = (sentence or "").strip().lower()
    if not lower:
        return -1.0
    score = 0.0
    if _has_declarative_guidance_shape(sentence):
        score += 0.45
    if _looks_conversational_or_setup(sentence):
        score -= 0.50
    if _looks_bridge_or_polite_exchange(sentence):
        score -= 0.60
    if _looks_generic_source_moment(sentence):
        score -= 0.20
    score += _topic_specific_alignment_score(question, sentence) * 0.45
    score += _progress_alignment_score(question, sentence) * 0.20
    score += _courage_theme_alignment_score(question, sentence) * 0.20
    if len(sentence) < 45:
        score -= 0.12
    return score


def _polish_quote_for_question(question: str, text_value: str) -> str:
    text_value = _trim_conversational_tail(text_value)
    sentences = _split_quote_sentences(text_value)
    if len(sentences) <= 1:
        return text_value

    scored = [(idx, _sentence_quality_for_question(question, sentence), sentence) for idx, sentence in enumerate(sentences)]
    best_idx, best_score, _ = max(scored, key=lambda item: item[1])
    if best_score < 0.15:
        return text_value

    selected = [sentences[best_idx]]
    next_idx = best_idx + 1
    while next_idx < len(sentences):
        next_score = _sentence_quality_for_question(question, sentences[next_idx])
        if next_score < 0.05:
            break
        if len(" ".join(selected + [sentences[next_idx]])) > 260:
            break
        selected.append(sentences[next_idx])
        next_idx += 1

    polished = " ".join(selected).strip()
    return polished or text_value


def _topic_specific_alignment_score(question: str, text_value: str) -> float:
    lower_q = (question or "").strip().lower()
    lower_t = (text_value or "").strip().lower()
    if not lower_q or not lower_t:
        return 0.0
    marker_groups = []
    if "boundar" in lower_q:
        marker_groups.append(_BOUNDARY_THEME_MARKERS)
    if "forgiv" in lower_q or "trust" in lower_q or "betray" in lower_q:
        marker_groups.append(_FORGIVENESS_THEME_MARKERS)
    if "grief" in lower_q or "loss" in lower_q:
        marker_groups.append(_GRIEF_THEME_MARKERS)
    if not marker_groups:
        return 0.0
    best = 0.0
    for group in marker_groups:
        hits = sum(1 for marker in group if marker in lower_t)
        best = max(best, min(1.0, hits / 2.0))
    return best


def _question_has_topic_specific_expectation(question: str) -> bool:
    lower_q = (question or "").strip().lower()
    return any(word in lower_q for word in ("boundar", "forgiv", "trust", "betray", "grief", "loss"))


def _is_standalone_evidence(text_value: str) -> bool:
    lower = (text_value or "").strip().lower()
    if not lower:
        return False
    if _looks_generic_source_moment(lower):
        return False
    if _looks_bridge_or_polite_exchange(lower):
        return False
    if _looks_conversational_or_setup(lower):
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


def _looks_self_contained_quote(text_value: str) -> bool:
    """
    Prefer windows that can stand alone on a card or citation rail without
    sounding like a clipped transcript fragment.
    """
    text_value = (text_value or "").strip()
    if not text_value:
        return False
    if len(text_value) < 120:
        return False

    starts_clean = bool(re.match(r'^[A-Z0-9"“\'(]', text_value))
    ends_clean = text_value[-1] in ".!?”\"'"
    if starts_clean and ends_clean:
        return True

    # Allow a slightly looser fallback if the window is otherwise strong and
    # clearly sentence-like.
    sentence_count = len(re.findall(r'[.!?]', text_value))
    return starts_clean and sentence_count >= 2


def _is_abstract_or_meta_question(question: str) -> bool:
    lower = (question or "").strip().lower()
    if not lower:
        return False
    if any(marker in lower for marker in _META_QUESTION_MARKERS):
        return True
    tokens = _tokenize_for_overlap(lower)
    if "citation" in tokens or "citations" in tokens:
        return True
    if "reference" in tokens or "references" in tokens:
        return True
    if ("answer" in tokens or "question" in tokens) and any(word in tokens for word in {"evidence", "proof", "support", "supporting", "related", "nearby"}):
        return True
    if any(phrase in lower for phrase in ("really proves", "genuinely supports", "just sounding related", "just sounds related", "actually supporting", "actually supports")):
        return True
    if len(tokens) <= 5 and any(word in tokens for word in {"truth", "meaning", "proof", "evidence", "answer"}):
        return True
    return False


def _question_wants_personal_example(question: str) -> bool:
    lower = (question or "").strip().lower()
    if not lower:
        return False
    return any(
        marker in lower
        for marker in (
            "for example",
            "an example",
            "example of",
            "share a story",
            "share a personal story",
            "personal story",
            "personal example",
            "real example",
            "real life example",
            "real-life example",
            "tell me a story",
            "tell me about a time",
            "what happened when",
        )
    )


def _is_reflective_guidance_question(question: str) -> bool:
    lower = (question or "").strip().lower()
    if not lower or _is_abstract_or_meta_question(lower):
        return False
    return (
        lower.startswith("how do i ")
        or lower.startswith("how can i ")
        or lower.startswith("how do we ")
        or lower.startswith("what does ")
        or lower.startswith("what can i ")
        or lower.startswith("how should i ")
        or lower.startswith("how will i ")
        or lower.startswith("how do you know")
    )


def _looks_anecdotal_personal_story(text_value: str) -> bool:
    lower = (text_value or "").strip().lower()
    if not lower:
        return False
    if any(marker in lower for marker in _PERSONAL_STORY_MARKERS):
        return True
    pronoun_hits = len(re.findall(r"\b(i|me|my|mine)\b", lower))
    narrative_hits = len(
        re.findall(
            r"\b(was|were|had|did|left|worked|started|stopped|felt|realized|remember|grew|grew up|went)\b",
            lower,
        )
    )
    emotion_hits = len(re.findall(r"\b(angry|sad|hurt|afraid|fearful|anxious|lonely|upset)\b", lower))
    if pronoun_hits >= 2 and emotion_hits >= 1 and narrative_hits >= 1:
        return True
    return pronoun_hits >= 4 and narrative_hits >= 2


def _question_wants_progress_evidence(question: str) -> bool:
    lower = (question or "").strip().lower()
    if not lower:
        return False
    return any(marker in lower for marker in _PROGRESS_TIME_MARKERS)


def _progress_alignment_score(question: str, text_value: str) -> float:
    if not _question_wants_progress_evidence(question):
        return 0.0
    lower = (text_value or "").strip().lower()
    if not lower:
        return 0.0
    hits = sum(1 for marker in _PROGRESS_TIME_MARKERS if marker in lower)
    return min(1.0, hits / 4.0)


def _question_wants_courage_theme(question: str) -> bool:
    lower = (question or "").strip().lower()
    if not lower:
        return False
    return any(marker in lower for marker in _COURAGE_THEME_MARKERS)


def _courage_theme_alignment_score(question: str, text_value: str) -> float:
    if not _question_wants_courage_theme(question):
        return 0.0
    lower = (text_value or "").strip().lower()
    if not lower:
        return 0.0
    hits = sum(1 for marker in _COURAGE_THEME_MARKERS if marker in lower)
    return min(1.0, hits / 3.0)


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
    wants_personal_example = _question_wants_personal_example(question)
    reflective_guidance = _is_reflective_guidance_question(question)
    wants_progress_evidence = _question_wants_progress_evidence(question)
    wants_courage_theme = _question_wants_courage_theme(question)

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
        text_value = _polish_quote_for_question(question, (chunk.get("text") or "").strip())
        chunk["text"] = text_value
        anecdotal_story = _looks_anecdotal_personal_story(text_value)
        progress_alignment = _progress_alignment_score(question, text_value)
        courage_alignment = _courage_theme_alignment_score(question, text_value)
        conversational_setup = _looks_conversational_or_setup(text_value)
        declarative_guidance = _has_declarative_guidance_shape(text_value)
        topic_alignment = _topic_specific_alignment_score(question, text_value)

        has_lexical_support = max(question_overlap, answer_overlap) >= 0.10
        has_good_precision = precision >= 0.36
        has_min_semantic_support = semantic >= 0.50
        looks_generic = _looks_generic_source_moment(text_value)
        looks_bridgey = _looks_bridge_or_polite_exchange(text_value)
        story_penalty = reflective_guidance and not wants_personal_example and anecdotal_story
        weak_progress_alignment = wants_progress_evidence and progress_alignment < 0.25
        weak_courage_alignment = wants_courage_theme and courage_alignment < 0.25
        weak_guidance_shape = reflective_guidance and not declarative_guidance
        weak_topic_alignment = topic_alignment < 0.25 if topic_alignment or any(word in (question or "").lower() for word in ("boundar", "forgiv", "trust", "betray", "grief", "loss")) else False

        if (
            has_good_precision
            and has_lexical_support
            and question_overlap >= 0.08
            and has_min_semantic_support
            and not looks_generic
            and not looks_bridgey
            and not conversational_setup
            and not story_penalty
            and not weak_progress_alignment
            and not weak_courage_alignment
            and not weak_guidance_shape
            and not weak_topic_alignment
        ):
            filtered.append(chunk)
        else:
            logger.info(
                "Dropping weak citation moment for episode %s (precision=%.3f, q_overlap=%.3f, a_overlap=%.3f, semantic=%.3f, generic=%s, story=%s)",
                (chunk.get("episode") or {}).get("id"),
                precision,
                question_overlap,
                answer_overlap,
                semantic,
                looks_generic or looks_bridgey,
                anecdotal_story,
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
    wants_personal_example = _question_wants_personal_example(question)
    reflective_guidance = _is_reflective_guidance_question(question)
    wants_progress_evidence = _question_wants_progress_evidence(question)
    wants_courage_theme = _question_wants_courage_theme(question)
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
                window_text = _polish_quote_for_question(question, window_text)
                if len(window_text) < 60:
                    continue

                lexical_score, question_overlap, answer_overlap = _score_candidate_text(
                    text_value=window_text,
                    question_tokens=question_tokens,
                    answer_tokens=answer_tokens,
                    semantic=0.0,
                )
                progress_alignment = _progress_alignment_score(question, window_text)
                courage_alignment = _courage_theme_alignment_score(question, window_text)
                topic_alignment = _topic_specific_alignment_score(question, window_text)
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
                if _looks_bridge_or_polite_exchange(window_text):
                    score -= 0.28
                if _looks_conversational_or_setup(window_text):
                    score -= 0.32
                if reflective_guidance and not wants_personal_example and _looks_anecdotal_personal_story(window_text):
                    score -= 0.22
                if wants_progress_evidence:
                    score += progress_alignment * 0.12
                    if progress_alignment < 0.25:
                        score -= 0.12
                if wants_courage_theme:
                    score += courage_alignment * 0.14
                    if courage_alignment < 0.25:
                        score -= 0.14
                if topic_alignment > 0.0:
                    score += topic_alignment * 0.16
                    if topic_alignment < 0.25:
                        score -= 0.16
                if reflective_guidance and _has_declarative_guidance_shape(window_text):
                    score += 0.08
                elif reflective_guidance:
                    score -= 0.10

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
        chosen_text = _polish_quote_for_question(question, (chosen.get("text") or "").strip())
        chosen["text"] = chosen_text

        weak_overlap = max(chosen_question_overlap, chosen_answer_overlap) < 0.10
        weak_question_overlap = chosen_question_overlap < 0.08
        weak_precision = chosen_precision < 0.38
        generic_window = _looks_generic_source_moment(chosen_text)
        bridge_window = _looks_bridge_or_polite_exchange(chosen_text)
        conversational_window = _looks_conversational_or_setup(chosen_text)
        anecdotal_window = (
            reflective_guidance
            and not wants_personal_example
            and _looks_anecdotal_personal_story(chosen_text)
        )
        weak_progress_alignment = wants_progress_evidence and _progress_alignment_score(question, chosen_text) < 0.25
        weak_courage_alignment = wants_courage_theme and _courage_theme_alignment_score(question, chosen_text) < 0.25
        weak_guidance_shape = reflective_guidance and not _has_declarative_guidance_shape(chosen_text)
        topic_alignment = _topic_specific_alignment_score(question, chosen_text)
        weak_topic_alignment = topic_alignment < 0.25 if topic_alignment or any(word in (question or "").lower() for word in ("boundar", "forgiv", "trust", "betray", "grief", "loss")) else False
        suspicious_intro = chosen_start < 45 and max(chosen_question_overlap, chosen_answer_overlap) < 0.16

        if (
            (weak_precision and weak_overlap)
            or weak_question_overlap
            or generic_window
            or bridge_window
            or conversational_window
            or anecdotal_window
            or weak_progress_alignment
            or weak_courage_alignment
            or weak_guidance_shape
            or weak_topic_alignment
            or suspicious_intro
        ):
            logger.info(
                "Dropping low-trust citation segment for episode %s (precision=%.3f, q_overlap=%.3f, a_overlap=%.3f, start=%.1f, anecdotal=%s)",
                episode_id,
                chosen_precision,
                chosen_question_overlap,
                chosen_answer_overlap,
                chosen_start,
                anecdotal_window,
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
    wants_personal_example = _question_wants_personal_example(question)
    reflective_guidance = _is_reflective_guidance_question(question)
    wants_progress_evidence = _question_wants_progress_evidence(question)
    wants_courage_theme = _question_wants_courage_theme(question)
    min_question_overlap_count = 2 if reflective_guidance and not wants_personal_example else 1

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
                window_text = _polish_quote_for_question(question, window_text)
                if not _is_standalone_evidence(window_text):
                    continue

                _, question_overlap, answer_overlap = _score_candidate_text(
                    text_value=window_text,
                    question_tokens=question_tokens,
                    answer_tokens=answer_tokens,
                    semantic=0.0,
                )
                question_overlap_count = _overlap_count(question_tokens, window_text)
                progress_alignment = _progress_alignment_score(question, window_text)
                courage_alignment = _courage_theme_alignment_score(question, window_text)
                topic_alignment = _topic_specific_alignment_score(question, window_text)
                overlap = max(question_overlap, answer_overlap)
                if overlap < 0.12:
                    continue
                min_question_overlap = 0.10 if reflective_guidance and not wants_personal_example else 0.08
                if question_overlap < min_question_overlap:
                    continue
                if question_overlap_count < min_question_overlap_count:
                    continue
                if wants_progress_evidence and progress_alignment < 0.25:
                    continue
                if wants_courage_theme and courage_alignment < 0.25:
                    continue
                if topic_alignment > 0.0 and topic_alignment < 0.25:
                    continue
                if reflective_guidance and _looks_conversational_or_setup(window_text):
                    continue
                if reflective_guidance and not _has_declarative_guidance_shape(window_text):
                    continue

                score = (
                    min(episode_boost, 1.0) * 0.35 +
                    question_overlap * 0.42 +
                    answer_overlap * 0.23
                )

                if 130 <= len(window_text) <= 320:
                    score += 0.05
                if _looks_self_contained_quote(window_text):
                    score += 0.06
                else:
                    score -= 0.07
                if _looks_bridge_or_polite_exchange(window_text):
                    score -= 0.40
                if reflective_guidance and not wants_personal_example and _looks_anecdotal_personal_story(window_text):
                    score -= 0.28
                if reflective_guidance and question_overlap_count >= 2:
                    score += 0.05
                if wants_progress_evidence:
                    score += progress_alignment * 0.14
                if wants_courage_theme:
                    score += courage_alignment * 0.16
                if topic_alignment > 0.0:
                    score += topic_alignment * 0.18
                if window_start < 60 and overlap < 0.18:
                    score -= 0.25
                if sum(1 for pattern in _GENERIC_SEGMENT_MARKERS if pattern in window_text.lower()) >= 1:
                    score -= 0.30
                if window_text[:1].islower():
                    score -= 0.05
                if window_text.endswith(",") or window_text.endswith(";") or window_text.endswith(":"):
                    score -= 0.05

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
                        "citation_question_overlap_count": question_overlap_count,
                        "citation_answer_overlap": round(answer_overlap, 4),
                        "citation_progress_alignment": round(progress_alignment, 4),
                        "citation_courage_alignment": round(courage_alignment, 4),
                        "citation_topic_alignment": round(topic_alignment, 4),
                        "is_strongest_match": False,
                    }

        if (
            best_candidate
            and float(best_candidate["citation_precision_score"]) >= 0.44
            and float(best_candidate.get("citation_question_overlap", 0.0) or 0.0) >= (0.12 if reflective_guidance and not wants_personal_example else 0.10)
            and int(best_candidate.get("citation_question_overlap_count", 0) or 0) >= min_question_overlap_count
            and float(best_candidate.get("citation_progress_alignment", 0.0) or 0.0) >= (0.25 if wants_progress_evidence else 0.0)
            and float(best_candidate.get("citation_courage_alignment", 0.0) or 0.0) >= (0.25 if wants_courage_theme else 0.0)
            and float(best_candidate.get("citation_topic_alignment", 0.0) or 0.0) >= (0.25 if float(best_candidate.get("citation_topic_alignment", 0.0) or 0.0) > 0 else 0.0)
            and _looks_self_contained_quote(best_candidate.get("text", ""))
            and not _looks_bridge_or_polite_exchange(best_candidate.get("text", ""))
            and not (
                reflective_guidance
                and not wants_personal_example
                and _looks_anecdotal_personal_story(best_candidate.get("text", ""))
            )
        ):
            best_per_episode.append(best_candidate)

    best_per_episode.sort(
        key=lambda item: float(item.get("citation_precision_score", 0.0) or 0.0),
        reverse=True,
    )

    strong = [
        item for item in best_per_episode
        if float(item.get("citation_precision_score", 0.0) or 0.0) >= 0.46
        and max(
            float(item.get("citation_question_overlap", 0.0) or 0.0),
            float(item.get("citation_answer_overlap", 0.0) or 0.0),
        ) >= 0.14
        and float(item.get("citation_question_overlap", 0.0) or 0.0) >= (0.12 if reflective_guidance and not wants_personal_example else 0.10)
        and int(item.get("citation_question_overlap_count", 0) or 0) >= min_question_overlap_count
        and float(item.get("citation_progress_alignment", 0.0) or 0.0) >= (0.25 if wants_progress_evidence else 0.0)
        and float(item.get("citation_courage_alignment", 0.0) or 0.0) >= (0.25 if wants_courage_theme else 0.0)
        and float(item.get("citation_topic_alignment", 0.0) or 0.0) >= (0.25 if float(item.get("citation_topic_alignment", 0.0) or 0.0) > 0 else 0.0)
    ]

    calibrated_single = [
        item for item in best_per_episode
        if float(item.get("citation_precision_score", 0.0) or 0.0) >= 0.39
        and float(item.get("citation_question_overlap", 0.0) or 0.0) >= 0.08
        and int(item.get("citation_question_overlap_count", 0) or 0) >= 1
        and _has_declarative_guidance_shape(item.get("text", ""))
        and _looks_self_contained_quote(item.get("text", ""))
        and not _looks_bridge_or_polite_exchange(item.get("text", ""))
        and not _looks_conversational_or_setup(item.get("text", ""))
        and not _looks_generic_source_moment(item.get("text", ""))
        and not _looks_anecdotal_personal_story(item.get("text", ""))
        and float(item.get("citation_topic_alignment", 0.0) or 0.0) >= (0.15 if float(item.get("citation_topic_alignment", 0.0) or 0.0) > 0 else 0.0)
    ]

    reflective_single = [
        item for item in best_per_episode
        if float(item.get("citation_precision_score", 0.0) or 0.0) >= 0.34
        and float(item.get("citation_question_overlap", 0.0) or 0.0) >= 0.06
        and _looks_self_contained_quote(item.get("text", ""))
        and not _looks_bridge_or_polite_exchange(item.get("text", ""))
        and not _looks_conversational_or_setup(item.get("text", ""))
        and not _looks_generic_source_moment(item.get("text", ""))
        and not _looks_anecdotal_personal_story(item.get("text", ""))
        and (
            _has_declarative_guidance_shape(item.get("text", ""))
            or float(item.get("citation_topic_alignment", 0.0) or 0.0) >= 0.25
        )
        and float(item.get("citation_topic_alignment", 0.0) or 0.0) >= (
            0.15 if _question_has_topic_specific_expectation(question) else 0.0
        )
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
        selected = strong[:(2 if reflective_guidance and not wants_personal_example else max_citations)]
    elif (
        reflective_guidance
        and not wants_personal_example
        and not wants_progress_evidence
        and not wants_courage_theme
        and len(calibrated_single) >= 1
    ):
        selected = calibrated_single[:1]
    elif (
        reflective_guidance
        and not wants_personal_example
        and not wants_progress_evidence
        and not wants_courage_theme
        and len(reflective_single) >= 1
    ):
        selected = reflective_single[:1]
    else:
        selected = best_per_episode[:(2 if reflective_guidance and not wants_personal_example else max_citations)]

    if not is_meta_question:
        # For normal questions, still refuse citations if we can't find at least
        # one clearly solid supporting moment.
        if not strong and not calibrated_single and not reflective_single and len(selected) > 0:
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
