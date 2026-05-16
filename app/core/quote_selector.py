"""
quote_selector.py
A standalone utility for smart, context-aware quote selection using semantic analysis and quality metrics.
"""
from typing import List, Dict, Optional, Any

class QuoteCandidate:
    def __init__(self, text: str, meta: Optional[Dict[str, Any]] = None):
        self.text = text
        self.meta = meta or {}
        self.score = 0.0


class QuoteSelector:
    def __init__(
        self,
        nlp_model=None,
        feedback_logger=None,
        weights=None,
        user_profiles=None,
        monitoring_logger=None,
        *,
        max_weight_delta: float = 0.03,
        min_weight: float = 0.1,
        max_weight: float = 3.0,
    ):
        """
        nlp_model: Optional callable for semantic scoring (e.g., OpenAI, HuggingFace pipeline, etc.)
        feedback_logger: Optional callable for logging user feedback (shares, likes, skips)
        weights: Dict of scoring weights for self-tuning
        user_profiles: Dict or callable for per-user personalization
        monitoring_logger: Optional callable for error/quality monitoring
        """
        self.nlp_model = nlp_model
        self.feedback_logger = feedback_logger
        self.weights = weights or {
            'semantic': 1.0,
            'quality': 1.0,
            'advanced_quality': 1.0,
            'contextual': 1.0,
            'improved_contextual': 1.0,
            'redundancy_penalty': 1.0,
            'diversity_penalty': 1.0,
        }
        self.user_profiles = user_profiles or {}
        self.monitoring_logger = monitoring_logger
        self.max_weight_delta = max_weight_delta
        self.min_weight = min_weight
        self.max_weight = max_weight

    def score_candidates(self, candidates: List[QuoteCandidate], context: Optional[Dict[str, Any]] = None) -> None:
        """
        Assigns a score to each candidate based on semantic, contextual, and quality metrics.
        Applies per-user personalization and logs explainability info.
        """
        user_id = context.get('user_id') if context else None
        user_profile = self.user_profiles.get(user_id) if user_id and self.user_profiles else None
        explainability = []
        for candidate in candidates:
            score = 0.0
            details = {}
            try:
                s = self.weights['semantic'] * self.semantic_score(candidate, context)
                score += s
                details['semantic'] = s
                q = self.weights['quality'] * self.quality_score(candidate, context)
                score += q
                details['quality'] = q
                aq = self.weights['advanced_quality'] * self.advanced_quality_score(candidate, context)
                score += aq
                details['advanced_quality'] = aq
                cx = self.weights['contextual'] * self.contextual_score(candidate, context)
                score += cx
                details['contextual'] = cx
                icx = self.weights['improved_contextual'] * self.improved_contextual_score(candidate, context)
                score += icx
                details['improved_contextual'] = icx
                rp = self.weights['redundancy_penalty'] * self.redundancy_penalty(candidate, candidates)
                score -= rp
                details['redundancy_penalty'] = rp
                dp = self.weights['diversity_penalty'] * self.diversity_penalty(candidate, candidates)
                score -= dp
                details['diversity_penalty'] = dp
                # Personalization: boost if user liked similar quotes
                if user_profile and 'liked_phrases' in user_profile:
                    for phrase in user_profile['liked_phrases']:
                        if phrase in candidate.text.lower():
                            score += 0.2
                            details['personalization'] = details.get('personalization', 0) + 0.2
                candidate.score = score
                candidate.explain = details
                explainability.append({'text': candidate.text, 'score': score, 'details': details})
            except (TypeError, ValueError, RuntimeError) as e:
                if self.monitoring_logger:
                    self.monitoring_logger(f"Scoring error: {e}")
                candidate.score = 0.0
                candidate.explain = {'error': str(e)}
        # Optionally log explainability for admin/analytics
        if self.monitoring_logger:
            self.monitoring_logger({'explainability': explainability})

    def semantic_score(self, candidate: QuoteCandidate, context: Optional[Dict[str, Any]]) -> float:
        """
        Use NLP model to score for emotional resonance, clarity, etc.
        """
        _ = context
        if self.nlp_model:
            # Example: return self.nlp_model(candidate.text, context)
            return float(self.nlp_model(candidate.text))
        return 0.0

    def quality_score(self, candidate: QuoteCandidate, context: Optional[Dict[str, Any]]) -> float:
        """
        Score for shareability, completeness, uniqueness, etc.
        """
        _ = context
        score = 0.0
        text = candidate.text
        if 40 <= len(text) <= 180:
            score += 0.5  # Prefer concise, complete quotes
        if text.endswith(('.', '!', '?')):
            score += 0.2
        if len(set(text.lower().split())) > 8:
            score += 0.2  # Prefer more unique words
        return score

    def advanced_quality_score(self, candidate: QuoteCandidate, context: Optional[Dict[str, Any]]) -> float:
        """
        Advanced scoring for shareability, emotional resonance, uniqueness, etc.
        """
        _ = context
        score = 0.0
        text = candidate.text
        # Shareability: concise, memorable, emotionally clear
        if 40 <= len(text) <= 140:
            score += 0.7
        # Emotional resonance: presence of feeling words
        feeling_words = ["love", "hope", "courage", "grief", "gratitude", "peace", "healing", "growth", "faith", "connection", "loneliness", "tender", "gentle", "wisdom", "honest", "truth", "care", "support", "strength", "resilience"]
        if any(word in text.lower() for word in feeling_words):
            score += 0.5
        # Uniqueness: penalize generic phrases
        generic_phrases = ["embrace your journey", "be your best self", "level up", "unlock your potential", "keep pushing", "trust the process"]
        if any(phrase in text.lower() for phrase in generic_phrases):
            score -= 0.7
        # Completeness: ends with punctuation
        if text and text[-1] in '.!?':
            score += 0.2
        return score

    def contextual_score(self, candidate: QuoteCandidate, context: Optional[Dict[str, Any]]) -> float:
        """
        Score based on theme, user intent, recent interactions, etc.
        """
        score = 0.0
        if context:
            theme = context.get('theme')
            if theme and theme.lower() in candidate.text.lower():
                score += 0.3
            # Add more context-based logic as needed
        return score

    def improved_contextual_score(self, candidate: QuoteCandidate, context: Optional[Dict[str, Any]]) -> float:
        """
        Improved scoring based on theme, user history, and intent.
        """
        score = 0.0
        if context:
            theme = context.get('theme')
            if theme and theme.lower() in candidate.text.lower():
                score += 0.4
            user_ip = context.get('user_ip')
            if user_ip:
                score += 0.1  # Slight boost for personalized context
            recent_theme = context.get('recent_theme')
            if recent_theme and recent_theme.lower() in candidate.text.lower():
                score += 0.2
            # Add more advanced context logic as needed
        return score

    def redundancy_penalty(self, candidate: QuoteCandidate, candidates: List[QuoteCandidate]) -> float:
        """
        Penalize repetitive or overly generic quotes.
        """
        penalty = 0.0
        for other in candidates:
            if other is not candidate and other.text.strip().lower() == candidate.text.strip().lower():
                penalty += 0.5
        return penalty

    def diversity_penalty(self, candidate: QuoteCandidate, candidates: List[QuoteCandidate]) -> float:
        """
        Penalize lack of diversity (e.g., too similar to other candidates).
        """
        penalty = 0.0
        for other in candidates:
            if other is not candidate:
                # Simple similarity: overlap of words
                words1 = set(candidate.text.lower().split())
                words2 = set(other.text.lower().split())
                overlap = len(words1 & words2) / max(1, len(words1 | words2))
                if overlap > 0.7:
                    penalty += 0.3
        return penalty


    def select_best(self, candidates: List[QuoteCandidate], context: Optional[Dict[str, Any]] = None) -> Optional[QuoteCandidate]:
        """
        Main entry point: scores all candidates and returns the best one.
        Enforces explicit diversity constraints and logs selection.
        """
        if not candidates:
            return None
        self.score_candidates(candidates, context)
        # Diversity constraint: do not select if too similar to recent selections
        recent_texts = context.get('recent_texts', []) if context else []
        for candidate in sorted(candidates, key=lambda c: c.score, reverse=True):
            if all(self._is_diverse(candidate.text, t) for t in recent_texts):
                if self.monitoring_logger:
                    self.monitoring_logger({'selected': candidate.text, 'explain': getattr(candidate, 'explain', {})})
                return candidate
        # Fallback: return highest scoring
        best = max(candidates, key=lambda c: c.score)
        if self.monitoring_logger:
            self.monitoring_logger({'selected': best.text, 'explain': getattr(best, 'explain', {})})
        return best

    def _is_diverse(self, text1: str, text2: str) -> bool:
        """Return True if two texts are sufficiently different (semantic or Jaccard)."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        overlap = len(words1 & words2) / max(1, len(words1 | words2))
        return overlap < 0.5

    def log_feedback(self, candidate: QuoteCandidate, feedback_type: str, user_context: Optional[Dict[str, Any]] = None):
        """
        Log user feedback (e.g., 'share', 'like', 'skip') for a candidate.
        """
        if self.feedback_logger:
            self.feedback_logger(candidate, feedback_type, user_context)

    def update_feedback_weights(self, feedback_data: list[dict]) -> dict[str, Any]:
        """
        Update scoring weights or logic based on aggregated user feedback.
        Uses engagement depth and bounded deltas for safe self-tuning.
        """
        if not feedback_data:
            return {
                "updated": False,
                "reason": "no_feedback",
                "weights": dict(self.weights),
                "average_feedback_score": 0.0,
                "feedback_count": 0,
            }

        old_weights = dict(self.weights)
        engagement_weights = {"share": 2.0, "like": 1.0, "skip": -1.0}
        total_weighted_score = 0.0
        total_abs_weight = 0.0

        raw_deltas = {k: 0.0 for k in self.weights}
        for entry in feedback_data:
            ftype = entry.get("feedback_type")
            score = float(entry.get("score", 1.0) or 0.0)
            weight = engagement_weights.get(ftype, 0.5)

            if ftype == "share":
                raw_deltas["semantic"] += 0.02
                raw_deltas["quality"] += 0.01
            elif ftype == "like":
                raw_deltas["quality"] += 0.01
                raw_deltas["advanced_quality"] += 0.005
            elif ftype == "skip":
                raw_deltas["redundancy_penalty"] += 0.015
                raw_deltas["diversity_penalty"] += 0.01
            else:
                raw_deltas["contextual"] += 0.002

            total_weighted_score += score * weight
            total_abs_weight += abs(weight)

        for key, delta in raw_deltas.items():
            bounded_delta = max(-self.max_weight_delta, min(self.max_weight_delta, delta))
            self.weights[key] = self._clamp_weight(self.weights[key] + bounded_delta)

        average_feedback_score = (
            total_weighted_score / total_abs_weight if total_abs_weight > 0 else 0.0
        )

        if self.monitoring_logger:
            self.monitoring_logger(
                {
                    "weights_old": old_weights,
                    "weights_new": dict(self.weights),
                    "average_feedback_score": average_feedback_score,
                    "feedback_count": len(feedback_data),
                }
            )

        return {
            "updated": True,
            "weights_old": old_weights,
            "weights_new": dict(self.weights),
            "average_feedback_score": average_feedback_score,
            "feedback_count": len(feedback_data),
        }

    def _clamp_weight(self, value: float) -> float:
        return max(self.min_weight, min(self.max_weight, value))
    # --- Continuous model training hook ---
    def train_model_on_feedback(self, feedback_data: list[dict]):
        """
        Placeholder for continuous model fine-tuning on feedback data.
        """
        # Hook for external ML pipeline integration.
        if self.monitoring_logger:
            self.monitoring_logger({'train_model_called': len(feedback_data)})
