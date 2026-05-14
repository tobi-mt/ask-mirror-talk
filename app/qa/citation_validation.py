"""
Citation Relevance Validation

Validates that citations actually support the generated answer:
- Checks semantic relevance between citation and answer
- Detects unsupported claims
- Filters low-quality or generic citations
- Ranks citations by relevance
"""

import re
import math
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CitationScore:
    """Relevance score for a citation."""
    citation_id: int
    relevance_score: float  # 0-100
    supports_answer: bool
    quality_score: float  # 0-100
    issues: list[str]
    

def validate_citations(
    answer: str,
    citations: list[dict],
    min_relevance: float = 60.0
) -> tuple[list[dict], list[CitationScore]]:
    """
    Validate and filter citations based on relevance to answer.
    
    Args:
        answer: Generated answer text
        citations: List of citation dicts
        min_relevance: Minimum relevance score to keep citation
    
    Returns:
        (filtered_citations, scores) tuple
    """
    if not citations:
        return [], []
    
    scores = []
    filtered = []
    
    # Extract key phrases from answer for matching
    answer_phrases = _extract_key_phrases(answer)
    answer_lower = answer.lower()
    
    for i, citation in enumerate(citations):
        citation_text = citation.get('text', '')
        citation_id = citation.get('episode_id', i)
        
        # Score the citation
        score = _score_citation(
            answer=answer_lower,
            answer_phrases=answer_phrases,
            citation_text=citation_text,
            citation_id=citation_id
        )
        
        scores.append(score)
        
        # Keep if relevance is above threshold
        if score.relevance_score >= min_relevance and score.supports_answer:
            filtered.append(citation)
        else:
            logger.info(
                f"Filtered out citation {citation_id} "
                f"(relevance={score.relevance_score:.1f}, issues={score.issues})"
            )
    
    logger.info(
        f"Citation validation: {len(filtered)}/{len(citations)} passed "
        f"(min_relevance={min_relevance})"
    )
    
    return filtered, scores


def _score_citation(
    answer: str,
    answer_phrases: set[str],
    citation_text: str,
    citation_id: int
) -> CitationScore:
    """Calculate comprehensive relevance score for a citation."""
    issues = []
    
    # Check basic quality
    quality_score = _check_citation_quality(citation_text, issues)
    
    # Check semantic relevance
    relevance_score = _check_semantic_relevance(
        answer, answer_phrases, citation_text, issues
    )
    
    # Determine if it supports the answer
    supports_answer = (
        relevance_score >= 60.0 and 
        quality_score >= 50.0 and
        len(issues) < 3
    )
    
    return CitationScore(
        citation_id=citation_id,
        relevance_score=relevance_score,
        supports_answer=supports_answer,
        quality_score=quality_score,
        issues=issues
    )


def _check_citation_quality(text: str, issues: list[str]) -> float:
    """
    Check intrinsic quality of citation text.
    Returns score 0-100.
    """
    score = 100.0
    
    if not text or len(text.strip()) < 50:
        issues.append("Citation too short")
        return 0.0
    
    text_lower = text.lower()
    
    # Check for meta/filler content
    meta_patterns = [
        'welcome back',
        'thank you for',
        'subscribe',
        'support the show',
        'hit that',
        'add a little sparkle',
        'friendly nudge',
        'tell us',
        'can you talk about',
        'before we get started',
        'let me ask you',
    ]
    
    for pattern in meta_patterns:
        if pattern in text_lower:
            issues.append(f"Contains meta/filler: '{pattern}'")
            score -= 30
            break
    
    # Check for host questions (should cite guest answers, not host questions)
    if text_lower.count('?') > text_lower.count('.'):
        issues.append("Mostly questions, not substantive content")
        score -= 25
    
    # Check for promotional content
    promo_words = ['website', 'book', 'podcast', 'follow me', 'contact']
    promo_count = sum(1 for word in promo_words if word in text_lower)
    if promo_count >= 2:
        issues.append("Contains promotional content")
        score -= 20
    
    return max(0.0, score)


def _check_semantic_relevance(
    answer: str,
    answer_phrases: set[str],
    citation_text: str,
    issues: list[str]
) -> float:
    """
    Check how relevant citation is to the answer content.
    Returns score 0-100.
    """
    citation_lower = citation_text.lower()
    
    # Extract key phrases from citation
    citation_phrases = _extract_key_phrases(citation_text)
    
    # Calculate phrase overlap
    if not answer_phrases or not citation_phrases:
        issues.append("No key phrases extracted")
        return 0.0
    
    overlap = answer_phrases & citation_phrases
    overlap_ratio = len(overlap) / len(answer_phrases)
    
    # Base score from phrase overlap
    score = overlap_ratio * 100
    
    # Extract key words from answer (important concepts)
    answer_words = set(re.findall(r'\b\w{5,}\b', answer))
    citation_words = set(re.findall(r'\b\w{5,}\b', citation_lower))
    
    # Remove common words
    stopwords = {
        'about', 'after', 'before', 'being', 'could', 'would', 'should',
        'their', 'there', 'these', 'those', 'through', 'where', 'which',
        'while', 'still', 'other', 'people', 'person', 'thing', 'things',
        'something', 'someone', 'really', 'think', 'feels', 'right'
    }
    answer_words -= stopwords
    citation_words -= stopwords
    
    # Word-level overlap boost
    word_overlap = answer_words & citation_words
    if answer_words:
        word_overlap_ratio = len(word_overlap) / len(answer_words)
        score += word_overlap_ratio * 50  # Up to 50 bonus points
    
    # Penalty for citations with no overlap
    if overlap_ratio < 0.1:
        issues.append(f"Low phrase overlap ({overlap_ratio:.0%})")
    
    if len(word_overlap) < 2:
        issues.append(f"Few shared key terms ({len(word_overlap)})")
    
    # Check for direct quotes or paraphrasing
    # Look for longer matching sequences (3+ words)
    answer_trigrams = _get_ngrams(answer, 3)
    citation_trigrams = _get_ngrams(citation_lower, 3)
    
    matching_trigrams = answer_trigrams & citation_trigrams
    if matching_trigrams:
        # Boost for direct quotes/close paraphrasing
        quote_bonus = min(20, len(matching_trigrams) * 5)
        score += quote_bonus
        logger.debug(f"Found {len(matching_trigrams)} matching trigrams, bonus={quote_bonus}")
    
    return min(100.0, score)


def _extract_key_phrases(text: str) -> set[str]:
    """
    Extract meaningful 2-3 word phrases from text.
    
    These capture key concepts better than individual words.
    """
    text_lower = text.lower()
    
    # Common stopwords to exclude
    stopwords = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
        'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
    }
    
    # Extract bigrams and trigrams
    words = re.findall(r'\b\w+\b', text_lower)
    phrases = set()
    
    # Bigrams (2-word phrases)
    for i in range(len(words) - 1):
        w1, w2 = words[i], words[i + 1]
        # Skip if either word is stopword or too short
        if w1 not in stopwords and w2 not in stopwords:
            if len(w1) >= 4 or len(w2) >= 4:
                phrases.add(f"{w1} {w2}")
    
    # Trigrams (3-word phrases) - more specific
    for i in range(len(words) - 2):
        w1, w2, w3 = words[i], words[i + 1], words[i + 2]
        # Allow one stopword in middle
        if w1 not in stopwords and w3 not in stopwords:
            if len(w1) >= 4 or len(w3) >= 4:
                phrases.add(f"{w1} {w2} {w3}")
    
    return phrases


def _get_ngrams(text: str, n: int) -> set[str]:
    """Extract n-grams from text."""
    words = re.findall(r'\b\w+\b', text.lower())
    ngrams = set()
    
    for i in range(len(words) - n + 1):
        ngram = ' '.join(words[i:i+n])
        ngrams.add(ngram)
    
    return ngrams


def rank_citations_by_relevance(
    citations: list[dict],
    scores: list[CitationScore]
) -> list[dict]:
    """
    Re-rank citations by relevance score.
    
    Returns citations sorted by relevance (highest first).
    """
    if len(citations) != len(scores):
        logger.warning(
            f"Citation count mismatch: {len(citations)} citations, "
            f"{len(scores)} scores. Returning original order."
        )
        return citations
    
    # Combine citations with scores
    paired = list(zip(citations, scores))
    
    # Sort by relevance score (descending)
    paired.sort(key=lambda x: x[1].relevance_score, reverse=True)
    
    # Return just the citations
    ranked = [citation for citation, _ in paired]
    
    logger.info(
        "Ranked citations: scores=%s",
        [f"{s.relevance_score:.0f}" for _, s in paired[:5]]
    )
    
    return ranked


def ensure_citation_quality(
    answer: str,
    citations: list[dict],
    min_count: int = 2,
    min_relevance: float = 60.0
) -> tuple[list[dict], bool]:
    """
    Ensure citations meet minimum quality standards.
    
    Args:
        answer: Generated answer
        citations: List of citations
        min_count: Minimum number of citations needed
        min_relevance: Minimum relevance score
    
    Returns:
        (filtered_citations, quality_ok) where quality_ok indicates
        if we have enough high-quality citations
    """
    if not citations:
        return [], False
    
    # Validate and filter citations
    filtered, scores = validate_citations(answer, citations, min_relevance)
    
    # Check if we have enough quality citations
    quality_ok = len(filtered) >= min_count
    
    if not quality_ok:
        logger.warning(
            f"Insufficient quality citations: {len(filtered)}/{min_count} needed. "
            f"Keeping original {len(citations)} citations."
        )
        # Fall back to original citations if filtering was too aggressive
        return citations, False
    
    # Rank by relevance
    ranked = rank_citations_by_relevance(filtered, [s for s in scores if s.supports_answer])
    
    return ranked, True
