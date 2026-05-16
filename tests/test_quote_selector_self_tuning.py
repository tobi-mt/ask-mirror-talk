"""
Test: QuoteSelector self-tuning and explainability
"""
from app.core.quote_selector import QuoteSelector, QuoteCandidate
from app.core.monitoring import monitoring_logger

def test_self_tuning_and_explainability():
    candidates = [
        QuoteCandidate("You are enough."),
        QuoteCandidate("Keep pushing forward."),
        QuoteCandidate("Embrace your journey."),
    ]
    context = {'user_id': 'user123', 'recent_texts': ["You are enough."]}
    selector = QuoteSelector(monitoring_logger=monitoring_logger)
    selector.weights['semantic'] = 1.0
    selector.weights['quality'] = 1.0
    selector.weights['redundancy_penalty'] = 1.0
    selector.weights['diversity_penalty'] = 1.0
    selector.score_candidates(candidates, context)
    best = selector.select_best(candidates, context)
    assert best is not None
    print("Best candidate:", best.text)
    print("Explainability:", getattr(best, 'explain', {}))
    # Simulate feedback
    feedback_data = [
        {'quote_id': 1, 'feedback_type': 'share', 'score': 1.0},
        {'quote_id': 2, 'feedback_type': 'like', 'score': 1.0},
        {'quote_id': 3, 'feedback_type': 'skip', 'score': 0.0},
    ]
    selector.update_feedback_weights(feedback_data)
    print("Updated weights:", selector.weights)
