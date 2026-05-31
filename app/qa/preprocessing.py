"""
Query Preprocessing and Optimization

Enhances user questions before retrieval to improve search quality:
- Spell correction for common typos
- Query expansion with synonyms
- Clarification detection (vague/ambiguous questions)
- Intent classification
- Key term extraction
"""

import re
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ProcessedQuery:
    """Result of query preprocessing."""
    original: str
    normalized: str
    expanded: Optional[str]  # Query with synonyms/expansions
    key_terms: list[str]
    intent: str  # 'advice', 'definition', 'example', 'reflection'
    is_clear: bool  # False if query is too vague
    suggestions: list[str]  # Clarification suggestions if vague


# Common misspellings in emotional/psychological topics
_SPELLING_CORRECTIONS = {
    'boundries': 'boundaries',
    'boundry': 'boundary',
    'greif': 'grief',
    'releationship': 'relationship',
    'releationships': 'relationships',
    'forgivness': 'forgiveness',
    'dissapointment': 'disappointment',
    'anxious': 'anxiety',
    'jelousy': 'jealousy',
    'jelous': 'jealous',
    'seperating': 'separating',
    'seperation': 'separation',
}


# Synonym expansion for key emotional concepts
_SYNONYM_GROUPS = {
    'grief': ['loss', 'mourning', 'bereavement', 'sorrow'],
    'anxiety': ['worry', 'fear', 'nervousness', 'stress'],
    'boundaries': ['limits', 'saying no', 'protection'],
    'forgiveness': ['letting go', 'release', 'pardon'],
    'love': ['affection', 'care', 'compassion'],
    'relationship': ['connection', 'partnership', 'bond'],
    'courage': ['bravery', 'boldness', 'strength'],
    'trust': ['faith', 'confidence', 'belief'],
    'healing': ['recovery', 'restoration', 'growth'],
    'shame': ['guilt', 'embarrassment', 'humiliation'],
}


_BRAND_LEAD_PATTERNS = [
    re.compile(r"^\s*what does mirror talk (?:teach|say) about\s+", re.IGNORECASE),
    re.compile(r"^\s*mirror talk (?:teaches|says)\s+", re.IGNORECASE),
    re.compile(r"^\s*according to mirror talk[,:\s]+", re.IGNORECASE),
]


def preprocess_query(question: str) -> ProcessedQuery:
    """
    Preprocess and optimize a user query for better retrieval.
    
    Args:
        question: Raw user question
    
    Returns:
        ProcessedQuery with normalized and expanded versions
    """
    # Normalize the question
    normalized = _normalize_query(question)

    # Strip product-brand lead-ins that add little retrieval value
    normalized = _strip_brand_lead(normalized)
    
    # Correct common spelling errors
    corrected = _correct_spelling(normalized)
    
    # Extract key terms
    key_terms = _extract_key_terms(corrected)
    
    # Detect intent
    intent = _detect_intent(corrected)
    
    # Check if query is clear enough
    is_clear, suggestions = _check_clarity(corrected, key_terms)
    
    # Expand with synonyms if we have key emotional terms
    expanded = _expand_query(corrected, key_terms, intent=intent) if key_terms else None
    
    logger.info(
        "Query preprocessing: original='%s', normalized='%s', "
        "key_terms=%s, intent=%s, is_clear=%s",
        question[:50], corrected[:50], key_terms, intent, is_clear
    )
    
    return ProcessedQuery(
        original=question,
        normalized=corrected,
        expanded=expanded,
        key_terms=key_terms,
        intent=intent,
        is_clear=is_clear,
        suggestions=suggestions
    )


def _strip_brand_lead(query: str) -> str:
    """Remove brand-heavy lead-ins so retrieval embeds the actual user intent."""
    for pattern in _BRAND_LEAD_PATTERNS:
        stripped = pattern.sub("", query).strip()
        if stripped and stripped != query and len(stripped.split()) >= 3:
            # Preserve terminal punctuation from the original normalization step.
            if query.endswith("?") and not stripped.endswith("?"):
                stripped += "?"
            logger.info("Stripped brand lead-in for retrieval: '%s' -> '%s'", query[:60], stripped[:60])
            return stripped
    return query


def _normalize_query(query: str) -> str:
    """Basic normalization of query text."""
    # Strip whitespace
    q = query.strip()
    
    # Remove excessive punctuation
    q = re.sub(r'[?!.]+$', '?', q) if q.endswith(('?', '!', '.')) else q
    
    # Remove multiple spaces
    q = re.sub(r'\s+', ' ', q)
    
    # Ensure it ends with question mark if it's a question
    question_words = ['what', 'when', 'where', 'who', 'why', 'how', 'can', 'should', 'do', 'does']
    if any(q.lower().startswith(word) for word in question_words) and not q.endswith('?'):
        q = q + '?'
    
    return q


def _correct_spelling(query: str) -> str:
    """Correct common spelling mistakes."""
    words = query.split()
    corrected_words = []
    
    for word in words:
        word_lower = word.lower().strip('?!.,;:')
        if word_lower in _SPELLING_CORRECTIONS:
            # Preserve original capitalization
            corrected = _SPELLING_CORRECTIONS[word_lower]
            if word[0].isupper():
                corrected = corrected.capitalize()
            # Add back punctuation
            for char in '?!.,;:':
                if word.endswith(char):
                    corrected = corrected + char
            corrected_words.append(corrected)
            logger.info(f"Corrected spelling: '{word}' -> '{corrected}'")
        else:
            corrected_words.append(word)
    
    return ' '.join(corrected_words)


def _extract_key_terms(query: str) -> list[str]:
    """
    Extract key emotional/psychological terms from query.
    
    These are the most important concepts that should guide retrieval.
    """
    query_lower = query.lower()
    key_terms = []
    
    # Check for terms in synonym groups (these are important concepts)
    for term, synonyms in _SYNONYM_GROUPS.items():
        if term in query_lower:
            key_terms.append(term)
        for syn in synonyms:
            if syn in query_lower and syn not in key_terms:
                key_terms.append(syn)
    
    # Extract other meaningful words (4+ characters, not stopwords)
    stopwords = {
        'what', 'when', 'where', 'which', 'who', 'whom', 'whose', 'why', 'how',
        'does', 'do', 'did', 'can', 'could', 'would', 'should', 'will', 'won',
        'about', 'after', 'before', 'from', 'into', 'through', 'during',
        'with', 'without', 'for', 'of', 'by', 'on', 'at', 'to', 'in',
        'the', 'a', 'an', 'and', 'or', 'but', 'if', 'because', 'as', 'until',
        'this', 'that', 'these', 'those', 'then', 'so', 'than', 'such',
        'even', 'most', 'other', 'some', 'very', 'just', 'help', 'tell', 'talk'
    }
    
    words = re.findall(r'\b\w{4,}\b', query_lower)
    for word in words:
        if word not in stopwords and word not in key_terms:
            # Check if it's a meaningful term (contains vowel, not just numbers)
            if any(v in word for v in 'aeiou') and not word.isdigit():
                key_terms.append(word)
    
    return key_terms[:5]  # Limit to top 5 terms


def _detect_intent(query: str) -> str:
    """
    Detect the intent behind the query.
    
    Returns: 'advice', 'definition', 'example', 'reflection', 'general'
    """
    query_lower = query.lower()

    # Example-seeking patterns (check before definition so
    # "what does ... look like" is treated as example intent).
    if any(pattern in query_lower for pattern in [
        'example', 'look like', 'sound like', 'instance',
        'case of', 'scenario', 'situation where'
    ]):
        return 'example'
    
    # Advice-seeking patterns
    if any(pattern in query_lower for pattern in [
        'how do i', 'how can i', 'what should i', 'how to',
        'what can i do', 'help me', 'need to', 'want to',
        'struggling with', 'dealing with', 'handle', 'cope'
    ]):
        return 'advice'
    
    # Definition-seeking patterns
    if any(pattern in query_lower for pattern in [
        'what is', 'what does', 'what are', 'define',
        'meaning of', 'mean by', 'definition', 'explain'
    ]):
        return 'definition'
    
    # Reflection/understanding patterns
    if any(pattern in query_lower for pattern in [
        'why do', 'why is', 'why are', 'why does',
        'understand', 'make sense', 'learn about', 'know about'
    ]):
        return 'reflection'
    
    return 'general'


def _check_clarity(query: str, key_terms: list[str]) -> tuple[bool, list[str]]:
    """
    Check if query is clear enough for good retrieval.
    
    Returns:
        (is_clear, suggestions) where suggestions are for clarification
    """
    suggestions = []
    
    # Too short
    if len(query) < 15:
        suggestions.append("Could you provide a bit more context about what you're looking for?")
        return False, suggestions
    
    # No key terms extracted
    if not key_terms:
        suggestions.append("Try including specific topics like 'grief', 'boundaries', or 'relationships'")
        return False, suggestions
    
    # Too vague/generic
    vague_patterns = [
        'tell me about',
        'what about',
        'talk about',
        'something about',
        'anything on',
        'info on',
        'stuff about',
    ]
    
    query_lower = query.lower()
    if any(pattern in query_lower for pattern in vague_patterns):
        suggestions.append("What specific aspect would you like to explore?")
        return False, suggestions
    
    # Very generic single-word questions
    if len(query.split()) <= 2 and not any(c in query for c in '?,.!'):
        suggestions.append("Could you rephrase that as a question?")
        return False, suggestions
    
    return True, []


def _expand_query(query: str, key_terms: list[str], intent: str = "general") -> Optional[str]:
    """
    Expand query with synonyms for better retrieval.
    
    Returns expanded query or None if no expansion needed.
    """
    expansions = []
    
    for term in key_terms:
        # Check if term has synonyms
        term_lower = term.lower()
        if term_lower in _SYNONYM_GROUPS:
            # Add up to 2 synonyms
            synonyms = _SYNONYM_GROUPS[term_lower][:2]
            expansions.extend(synonyms)
    
    query_lower = query.lower()

    # Add intent-aware context for "what does X look like" style questions.
    if intent == "example":
        expansions.extend(["practical example", "real life"])

    # Add phrase-level expansions for high-frequency weak-match phrasings.
    if "everyday life" in query_lower or "daily life" in query_lower:
        expansions.extend(["daily practice", "real world"])
    if "without feeling guilty" in query_lower:
        expansions.extend(["self-compassion", "healthy limits"])
    if "without shutting down" in query_lower:
        expansions.extend(["emotional regulation", "staying open"])

    # Keep insertion order while removing duplicates.
    deduped_expansions = list(dict.fromkeys(expansions))

    if not deduped_expansions:
        return None
    
    # Create expanded query: "original query [synonym1 synonym2]"
    expanded = f"{query} {' '.join(deduped_expansions)}"
    logger.info(f"Query expanded with synonyms: {deduped_expansions}")
    return expanded


def optimize_for_retrieval(query: ProcessedQuery) -> str:
    """
    Get the best query version for retrieval.
    
    Returns:
        The optimal query string to use for embedding/search
    """
    # If we have an expanded query and the original is clear, use expanded
    if query.is_clear and query.expanded:
        return query.expanded
    
    # Otherwise use normalized
    return query.normalized


def build_low_match_rewrite(query: ProcessedQuery) -> Optional[str]:
    """
    Build a second-pass retrieval query when first-pass confidence is low.

    The rewrite keeps the user's intent but adds concrete retrieval hints so
    semantic search can recover stronger supporting chunks.
    """
    if not query or not query.normalized:
        return None

    base = query.normalized.strip().rstrip("?")
    if not base:
        return None

    hints: list[str] = []
    if query.key_terms:
        hints.append("focus on " + ", ".join(query.key_terms[:3]))

    if query.intent == "example":
        hints.append("practical real-life examples and steps")
    elif query.intent == "advice":
        hints.append("grounded practical guidance")
    elif query.intent == "reflection":
        hints.append("clear reflective perspective")

    if "everyday life" in query.normalized.lower() or "daily life" in query.normalized.lower():
        hints.append("daily practice")

    if not hints:
        return None

    rewritten = f"{base}; {'; '.join(dict.fromkeys(hints))}?"
    if rewritten.lower() == query.normalized.lower():
        return None
    return rewritten


def get_clarification_response(query: ProcessedQuery) -> Optional[str]:
    """
    Generate a clarification request if query is too vague.
    
    Returns:
        Clarification message or None if query is clear
    """
    if query.is_clear:
        return None
    
    message = "I'd love to help you explore that. "
    
    if query.suggestions:
        message += query.suggestions[0]
    
    # Add example based on key terms if we have any
    if query.key_terms:
        term = query.key_terms[0]
        message += f" For example, are you wondering about {term} in relationships, at work, or something else?"
    
    return message
