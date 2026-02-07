TOPIC_KEYWORDS = {
    "faith": ["faith", "god", "prayer", "spiritual", "church"],
    "relationships": ["relationship", "marriage", "partner", "family", "friend"],
    "leadership": ["leader", "team", "vision", "responsibility"],
    "inner life": ["anxiety", "fear", "peace", "identity", "shame"],
}

TONE_KEYWORDS = {
    "encouraging": ["hope", "encourage", "lift"],
    "reflective": ["reflect", "consider", "think"],
    "challenging": ["challenge", "hard", "difficult"],
    "comforting": ["comfort", "safe", "secure"],
}

DOMAIN_KEYWORDS = {
    "faith": ["faith", "god", "spiritual"],
    "relationships": ["relationship", "marriage", "family"],
    "leadership": ["leader", "team", "purpose"],
    "inner life": ["anxiety", "peace", "identity"],
}


def _match_keyword(text: str, mapping: dict, default: str):
    lowered = text.lower()
    for label, keywords in mapping.items():
        if any(keyword in lowered for keyword in keywords):
            return label
    return default


def tag_chunk(text: str):
    topic = _match_keyword(text, TOPIC_KEYWORDS, "general")
    tone = _match_keyword(text, TONE_KEYWORDS, "grounded")
    domain = _match_keyword(text, DOMAIN_KEYWORDS, "general")
    return topic, tone, domain
