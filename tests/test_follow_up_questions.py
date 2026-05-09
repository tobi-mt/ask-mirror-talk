from app.qa.answer import _fallback_follow_up_questions, _polish_follow_up_question


def test_legacy_episode_title_followups_become_complete_questions():
    broken = 'Tell me more about "Unlocking the Secrets of Attachment Theory in Dating & Relat"'

    polished = _polish_follow_up_question(broken)

    assert polished == "How can I understand my relationship patterns with more honesty?"
    assert polished.endswith("?")
    assert "Relat" not in polished


def test_fallback_followups_are_theme_based_complete_questions():
    questions = _fallback_follow_up_questions("What's the first step to breaking a bad habit?", [])

    assert len(questions) == 3
    assert all(question.endswith("?") for question in questions)
    assert questions[0] == "What is the smallest wise step I can take to interrupt this habit?"
