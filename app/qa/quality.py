"""
Answer Quality Validation and Scoring

Provides comprehensive quality checks for generated answers to ensure:
- Completeness (no truncation, proper ending)
- Coherence (logical flow, proper structure)
- Citation support (answer grounded in provided sources)
- Relevance (actually addresses the question)
- Hallucination detection (stays within source material)
"""

import re
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class QualityScore:
    """Comprehensive quality assessment of an answer."""
    overall_score: float  # 0-100
    completeness: float  # 0-100
    coherence: float  # 0-100
    citation_support: float  # 0-100
    relevance: float  # 0-100
    issues: list[str]
    passed: bool
    
    @property
    def grade(self) -> str:
        """Letter grade for the answer quality."""
        if self.overall_score >= 90:
            return "A"
        elif self.overall_score >= 80:
            return "B"
        elif self.overall_score >= 70:
            return "C"
        elif self.overall_score >= 60:
            return "D"
        else:
            return "F"


def validate_answer_quality(
    question: str,
    answer: str,
    citations: list[dict],
    min_score: float = 70.0
) -> QualityScore:
    """
    Comprehensive quality validation of a generated answer.
    
    Args:
        question: The user's original question
        answer: The generated answer text
        citations: List of citation chunks used
        min_score: Minimum acceptable quality score (default 70)
    
    Returns:
        QualityScore with detailed assessment
    """
    issues = []
    
    # Check completeness
    completeness = _check_completeness(answer, issues)
    
    # Check coherence
    coherence = _check_coherence(answer, issues)
    
    # Check citation support
    citation_support = _check_citation_support(answer, citations, issues)
    
    # Check relevance to question
    relevance = _check_relevance(question, answer, issues)
    
    # Calculate overall score (weighted average)
    overall_score = (
        completeness * 0.30 +  # 30% - answer must be complete
        coherence * 0.25 +      # 25% - must be well-structured
        citation_support * 0.25 + # 25% - must be grounded
        relevance * 0.20        # 20% - must address the question
    )
    
    passed = overall_score >= min_score and completeness >= 80
    
    logger.info(
        "Answer quality: overall=%.1f, completeness=%.1f, coherence=%.1f, "
        "citation_support=%.1f, relevance=%.1f, grade=%s, passed=%s",
        overall_score, completeness, coherence, citation_support, relevance,
        _get_grade(overall_score), passed
    )
    
    if issues:
        logger.warning("Quality issues found: %s", "; ".join(issues))
    
    return QualityScore(
        overall_score=overall_score,
        completeness=completeness,
        coherence=coherence,
        citation_support=citation_support,
        relevance=relevance,
        issues=issues,
        passed=passed
    )


def _check_completeness(answer: str, issues: list[str]) -> float:
    """
    Check if answer is complete (not truncated, proper ending).
    Returns score 0-100.
    """
    score = 100.0
    
    if not answer or not isinstance(answer, str):
        issues.append("Answer is empty or invalid")
        return 0.0
    
    text = answer.strip()
    
    # Minimum length check
    if len(text) < 100:
        issues.append(f"Answer too short ({len(text)} chars)")
        score -= 30
    
    # Check for proper sentence ending
    if not text or text[-1] not in '.!?':
        issues.append("Answer does not end with proper punctuation")
        score -= 25
    
    # Check for mid-sentence cut-off patterns
    if _has_incomplete_ending(text):
        issues.append("Answer appears truncated or incomplete")
        score -= 30
    
    # Check for minimum sentence count (should have at least 3-4 sentences)
    sentence_count = len([s for s in re.split(r'[.!?]+', text) if len(s.strip()) > 20])
    if sentence_count < 3:
        issues.append(f"Too few sentences ({sentence_count})")
        score -= 15
    
    return max(0.0, score)


def _check_coherence(answer: str, issues: list[str]) -> float:
    """
    Check logical flow and structure of the answer.
    Returns score 0-100.
    """
    score = 100.0
    text = answer.strip()
    
    # Check for paragraph structure (should have line breaks for longer answers)
    if len(text) > 400 and '\n' not in text:
        issues.append("Long answer lacks paragraph breaks")
        score -= 10
    
    # Check for excessive repetition
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 20]
    if len(sentences) > 1:
        # Check for repeated sentence patterns
        for i in range(len(sentences) - 1):
            similarity = _sentence_similarity(sentences[i], sentences[i + 1])
            if similarity > 0.7:
                issues.append("Excessive repetition detected")
                score -= 15
                break
    
    # Check for generic filler phrases (should be minimal)
    filler_phrases = [
        "it's important to",
        "it's worth noting",
        "at the end of the day",
        "the fact of the matter",
        "in other words",
        "to put it simply",
    ]
    filler_count = sum(1 for phrase in filler_phrases if phrase in text.lower())
    if filler_count > 2:
        issues.append(f"Too much filler language ({filler_count} phrases)")
        score -= 10
    
    # Check for proper flow indicators
    has_transitions = any(word in text.lower() for word in [
        'however', 'therefore', 'moreover', 'furthermore', 'additionally',
        'meanwhile', 'instead', 'rather', 'similarly', 'likewise'
    ])
    
    # Longer answers should have some transitions
    if len(text) > 300 and not has_transitions:
        score -= 5  # Minor deduction, not critical
    
    return max(0.0, score)


def _check_citation_support(answer: str, citations: list[dict], issues: list[str]) -> float:
    """
    Check if answer is properly supported by citations.
    Returns score 0-100.
    """
    score = 100.0
    
    # Must have citations
    if not citations:
        issues.append("No citations provided")
        return 0.0
    
    # Should have at least 2-3 citations for credibility
    if len(citations) < 2:
        issues.append("Too few citations (need at least 2)")
        score -= 20
    
    # Extract key claims from the answer
    claims = _extract_key_claims(answer)
    
    # Check if citations contain relevant content
    citation_texts = [c.get('text', '') for c in citations]
    all_citation_text = ' '.join(citation_texts).lower()
    
    # Check for orphaned claims (statements not supported by citations)
    unsupported_claims = 0
    for claim in claims:
        # Simple heuristic: check if key words from claim appear in citations
        claim_words = set(re.findall(r'\b\w+\b', claim.lower()))
        # Remove stopwords
        claim_words = claim_words - {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been'
        }
        
        # Check overlap
        if claim_words:
            matches = sum(1 for word in claim_words if word in all_citation_text)
            overlap = matches / len(claim_words)
            if overlap < 0.3:  # Less than 30% of key words found
                unsupported_claims += 1
    
    if unsupported_claims > len(claims) / 2:
        issues.append(f"Many claims lack citation support ({unsupported_claims}/{len(claims)})")
        score -= 30
    
    return max(0.0, score)


def _check_relevance(question: str, answer: str, issues: list[str]) -> float:
    """
    Check if answer actually addresses the question.
    Returns score 0-100.
    """
    score = 100.0
    
    # Extract key words from question
    question_words = set(re.findall(r'\b\w{4,}\b', question.lower()))
    # Remove common question words
    question_words = question_words - {
        'what', 'when', 'where', 'which', 'who', 'whom', 'whose', 'why', 'how',
        'does', 'can', 'could', 'would', 'should', 'will', 'about', 'help', 'tell'
    }
    
    # Check if answer addresses question terms
    answer_lower = answer.lower()
    matching_words = sum(1 for word in question_words if word in answer_lower)
    
    if question_words:
        relevance_ratio = matching_words / len(question_words)
        if relevance_ratio < 0.3:  # Less than 30% of key question words in answer
            issues.append(f"Low relevance to question ({relevance_ratio:.0%} term overlap)")
            score -= 40
        elif relevance_ratio < 0.5:
            score -= 20
    
    # Check if answer starts with generic deflection
    deflection_starts = [
        "i'm not sure",
        "i cannot",
        "i don't have enough",
        "based on the available",
        "unfortunately",
    ]
    
    answer_start = answer.lower()[:100]
    if any(deflection in answer_start for deflection in deflection_starts):
        issues.append("Answer starts with deflection/uncertainty")
        score -= 15
    
    return max(0.0, score)


def _has_incomplete_ending(text: str) -> bool:
    """Check if text ends mid-sentence or with incomplete pattern."""
    # Get last few words
    last_sentence = text.split('.')[-2] if '.' in text[:-1] else text
    last_words = last_sentence.strip().split()[-3:] if last_sentence else []
    
    if not last_words:
        return True
    
    # Common incomplete endings
    incomplete_patterns = {
        'is', 'are', 'was', 'were', 'been', 'being',
        'that', 'which', 'who', 'what', 'when', 'where', 'why', 'how',
        'a', 'an', 'the',
        'and', 'or', 'but', 'so', 'yet',
        'to', 'for', 'of', 'in', 'on', 'at', 'by', 'with',
        'can', 'could', 'will', 'would', 'should', 'may', 'might', 'must',
        'this', 'these', 'those', 'their', 'them',
    }
    
    return last_words[-1].lower() in incomplete_patterns


def _extract_key_claims(text: str) -> list[str]:
    """Extract key claims/statements from text."""
    # Split into sentences
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 30]
    
    # Filter out questions and very short statements
    claims = []
    for sentence in sentences:
        # Skip questions
        if sentence.endswith('?'):
            continue
        # Skip meta-statements about the podcast
        if any(word in sentence.lower() for word in ['episode', 'podcast', 'mirror talk']):
            continue
        claims.append(sentence)
    
    return claims


def _sentence_similarity(s1: str, s2: str) -> float:
    """Simple word-overlap similarity between two sentences."""
    words1 = set(re.findall(r'\b\w+\b', s1.lower()))
    words2 = set(re.findall(r'\b\w+\b', s2.lower()))
    
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    
    return intersection / union if union > 0 else 0.0


def _get_grade(score: float) -> str:
    """Convert numeric score to letter grade."""
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"


def should_retry_generation(quality: QualityScore, attempt: int, max_attempts: int = 2) -> bool:
    """
    Determine if answer generation should be retried based on quality.
    
    Args:
        quality: QualityScore from validation
        attempt: Current attempt number (0-indexed)
        max_attempts: Maximum retry attempts
    
    Returns:
        True if should retry, False otherwise
    """
    # Don't retry if we've hit max attempts
    if attempt >= max_attempts:
        return False
    
    # Retry if completeness is very low (likely truncation)
    if quality.completeness < 70:
        logger.info("Retrying generation due to low completeness (%.1f)", quality.completeness)
        return True
    
    # Retry if overall quality is poor
    if quality.overall_score < 60:
        logger.info("Retrying generation due to poor quality (%.1f)", quality.overall_score)
        return True
    
    return False
