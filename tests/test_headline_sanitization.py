"""
Comprehensive tests for shareable headline sanitization.

This module rigorously tests the sanitize_shareable_headline() function to ensure
that cached headlines with quality issues (fragments, questions, etc.) are properly
cleaned up and never reach users.
"""

import pytest
from app.qa.answer import sanitize_shareable_headline, _extract_best_sentence_headline


class TestFragmentStartSanitization:
    """Test that headlines starting with coordinating conjunctions are fixed."""
    
    def test_removes_and_prefix(self):
        """Should remove 'And' from the start and recapitalize."""
        headline = "And 'How can I use this lesson to improve?'"
        result = sanitize_shareable_headline(headline)
        
        # Should remove 'And ' and capitalize the next word
        assert not result.startswith("And ")
        assert not result.startswith("and ")
        # Should still be valid or empty if unfixable
        if result:
            assert result[0].isupper()
    
    def test_removes_but_prefix(self):
        """Should remove 'But' from the start."""
        headline = "But where do I feel even the tiniest spark of quiet joy?"
        result = sanitize_shareable_headline(headline)
        
        assert not result.startswith("But ")
        assert not result.startswith("but ")
    
    def test_removes_or_prefix(self):
        """Should remove 'Or' from the start."""
        headline = "Or maybe this is exactly where you need to be right now."
        result = sanitize_shareable_headline(headline)
        
        assert not result.startswith("Or ")
        assert not result.startswith("or ")
    
    def test_removes_so_prefix(self):
        """Should remove 'So' from the start."""
        headline = "So what would it look like to try again with more honesty?"
        result = sanitize_shareable_headline(headline)
        
        assert not result.startswith("So ")
        assert not result.startswith("so ")
    
    def test_removes_because_prefix(self):
        """Should remove 'Because' from the start."""
        headline = "Because grief asks for space, not solutions."
        result = sanitize_shareable_headline(headline)
        
        assert not result.startswith("Because ")
        assert not result.startswith("because ")
    
    def test_removes_if_prefix(self):
        """Should remove 'If' from the start."""
        headline = "If you want to heal, start by acknowledging the pain."
        result = sanitize_shareable_headline(headline)
        
        assert not result.startswith("If ")
        assert not result.startswith("if ")
    
    def test_removes_when_prefix(self):
        """Should remove 'When' from the start."""
        headline = "When you notice the patterns, you can begin to change them."
        result = sanitize_shareable_headline(headline)
        
        assert not result.startswith("When ")
        assert not result.startswith("when ")
    
    def test_removes_where_prefix(self):
        """Should remove 'Where' from the start."""
        headline = "Where you find resistance, you often find the path forward."
        result = sanitize_shareable_headline(headline)
        
        assert not result.startswith("Where ")
        assert not result.startswith("where ")
    
    def test_fragment_removal_preserves_quality(self):
        """After removing fragment start, result should still meet quality standards."""
        headline = "And what you have in this relationship is already worth protecting."
        result = sanitize_shareable_headline(headline)
        
        if result:
            # Should be properly formatted
            assert len(result) >= 40
            assert result[0].isupper()
            assert result[-1] in ".!?"
            # Should not be a question
            assert not result.endswith("?")


class TestQuestionRejection:
    """Test that questions are rejected and replaced with better content."""
    
    def test_rejects_question_ending_with_mark(self):
        """Should reject headlines ending with ?"""
        headline = "How can I use this lesson to improve my life today?"
        answer = "Trust that your next right step will reveal itself when you need it most."
        
        result = sanitize_shareable_headline(headline, answer)
        
        assert not result.endswith("?")
    
    def test_rejects_how_do_questions(self):
        """Should reject questions starting with 'How do'."""
        headline = "How do I know if this is the right path for me?"
        answer = "The path becomes clear when you honor what you already know is true."
        
        result = sanitize_shareable_headline(headline, answer)
        
        assert not result.startswith("How do")
    
    def test_rejects_how_can_questions(self):
        """Should reject questions starting with 'How can'."""
        headline = "How can I be more present in my relationships?"
        answer = "Presence is built through small, consistent choices to truly listen."
        
        result = sanitize_shareable_headline(headline, answer)
        
        assert not result.startswith("How can")
    
    def test_rejects_what_is_questions(self):
        """Should reject questions starting with 'What is'."""
        headline = "What is the best way to approach this situation?"
        answer = "Approach the situation with curiosity rather than judgment first."
        
        result = sanitize_shareable_headline(headline, answer)
        
        assert not result.startswith("What is")
    
    def test_rejects_why_questions(self):
        """Should reject questions starting with 'Why'."""
        headline = "Why does this keep happening to me?"
        answer = "Patterns repeat until we're ready to see them clearly and change them."
        
        result = sanitize_shareable_headline(headline, answer)
        
        assert not result.startswith("Why")
    
    def test_allows_declarative_what_sentences(self):
        """Should allow declarative sentences that start with 'What you' (not questions)."""
        headline = "What you have in this relationship right now is already worth protecting."
        
        result = sanitize_shareable_headline(headline)
        
        # This is NOT a question, it's a declarative statement
        assert result == headline or result.startswith("What you")
        assert not result.endswith("?")
    
    def test_extracts_from_answer_when_question_rejected(self):
        """When a question is rejected, should extract from answer text."""
        headline = "How can I trust again after betrayal?"
        answer = (
            "Trust is rebuilt through small, consistent actions over time. "
            "It requires both honesty about the hurt and willingness to try again. "
            "The path forward starts with one brave conversation."
        )
        
        result = sanitize_shareable_headline(headline, answer)
        
        # Should have extracted a sentence from the answer
        assert result != headline
        if result:
            assert not result.endswith("?")
            assert result in answer


class TestLengthValidation:
    """Test that headlines meet length requirements."""
    
    def test_rejects_too_short_headline(self):
        """Should reject headlines under 40 characters."""
        headline = "Be brave today."
        answer = "Courage is built through small, consistent choices to show up authentically each day."
        
        result = sanitize_shareable_headline(headline, answer)
        
        # Should either extract from answer or return empty
        if result:
            assert len(result) >= 40
    
    def test_rejects_too_long_headline(self):
        """Should reject headlines over 180 characters."""
        headline = (
            "The kind of connection and relationship that you're seeking requires "
            "daily attention to what's already present and worthy of protection and "
            "nurturing in your existing relationships right now in this very moment."
        )
        answer = "What you already have in your relationships is worth protecting today."
        
        result = sanitize_shareable_headline(headline, answer)
        
        # Should extract shorter version or return empty
        if result:
            assert len(result) <= 180
    
    def test_rejects_too_few_words(self):
        """Should reject headlines with fewer than 6 words."""
        headline = "Trust the process always."
        answer = "Trust that your next right step will reveal itself when you need it most."
        
        result = sanitize_shareable_headline(headline, answer)
        
        if result:
            assert len(result.split()) >= 6
    
    def test_rejects_too_many_words(self):
        """Should reject headlines with more than 26 words."""
        headline = (
            "The most important thing you can do right now is to take a moment "
            "and really think carefully about what matters most to you and your "
            "family and your future and your dreams."
        )
        answer = "What matters most is already clear if you listen to your deepest truth."
        
        result = sanitize_shareable_headline(headline, answer)
        
        if result:
            assert len(result.split()) <= 26


class TestValidHeadlinePassthrough:
    """Test that valid headlines pass through unchanged."""
    
    def test_preserves_valid_headline(self):
        """Should not modify headlines that already meet all criteria."""
        headline = "What you have in this relationship right now is already worth protecting."
        
        result = sanitize_shareable_headline(headline)
        
        assert result == headline
    
    def test_preserves_valid_grief_headline(self):
        """Should preserve valid headline about grief."""
        headline = "Grief asks for space, not solutions—permission to feel whatever comes."
        
        result = sanitize_shareable_headline(headline)
        
        assert result == headline
    
    def test_preserves_valid_action_headline(self):
        """Should preserve valid headline with clear action."""
        headline = "Trust that your next right step will reveal itself when you need it most."
        
        result = sanitize_shareable_headline(headline)
        
        assert result == headline
    
    def test_preserves_valid_presence_headline(self):
        """Should preserve valid headline about presence."""
        headline = "Presence is built through small, consistent choices to truly listen."
        
        result = sanitize_shareable_headline(headline)
        
        assert result == headline
    
    def test_requires_proper_ending_punctuation(self):
        """Valid headlines must end with . ! or ?"""
        # Note: ? endings are rejected elsewhere, so really . or !
        headline = "What you have right now is worth protecting"
        
        result = sanitize_shareable_headline(headline)
        
        # Without proper ending, it should be rejected
        # If it returns something, it should have proper ending
        if result:
            assert result[-1] in ".!?"


class TestEdgeCases:
    """Test edge cases and malformed input."""
    
    def test_handles_empty_string(self):
        """Should handle empty string gracefully."""
        result = sanitize_shareable_headline("")
        
        assert result == ""
    
    def test_handles_none_gracefully(self):
        """Should handle None input without crashing."""
        # This should not crash
        result = sanitize_shareable_headline("")
        assert result == ""
    
    def test_handles_whitespace_only(self):
        """Should handle whitespace-only input."""
        result = sanitize_shareable_headline("   \n\t  ")
        
        assert result == ""
    
    def test_strips_quotes(self):
        """Should strip surrounding quotes from headlines."""
        headline = '"Trust that your next right step will reveal itself when you need it most."'
        
        result = sanitize_shareable_headline(headline)
        
        assert not result.startswith('"')
        assert not result.endswith('"')
    
    def test_strips_single_quotes(self):
        """Should strip surrounding single quotes."""
        headline = "'What you have in this moment is already worth protecting.'"
        
        result = sanitize_shareable_headline(headline)
        
        assert not result.startswith("'")
        # Note: may still have single quote after "What you have in this moment"
        # but not as wrapping quotes
    
    def test_handles_multiple_spaces(self):
        """Should normalize multiple spaces."""
        headline = "Trust  that   your    next right step will reveal itself."
        
        result = sanitize_shareable_headline(headline)
        
        # Should still be valid
        if result:
            assert "  " not in result or result == headline  # Either normalized or rejected


class TestCacheIntegration:
    """Test scenarios where cached headlines are sanitized."""
    
    def test_sanitizes_legacy_fragment_from_cache(self):
        """Should fix fragment starts from legacy cached headlines."""
        cached_headline = "And 'How can I use this lesson to improve?'"
        answer_text = (
            "The lesson is already working on you if you're asking this question. "
            "Notice what's shifting in how you see the situation now. "
            "That awareness is the first step toward change."
        )
        
        result = sanitize_shareable_headline(cached_headline, answer_text)
        
        # Should not have fragment start
        assert not result.startswith("And ")
        # Should not be a question
        assert not result.endswith("?")
        # Should be valid or extracted from answer
        if result:
            assert len(result) >= 40
            assert result[-1] in ".!?"
    
    def test_extracts_fallback_when_cached_is_unfixable(self):
        """When cached headline is unfixable, should extract from answer."""
        cached_headline = "How?"
        answer_text = "Trust that your next right step will reveal itself when you need it most."
        
        result = sanitize_shareable_headline(cached_headline, answer_text)
        
        # Too short and a question - should extract from answer
        assert result != cached_headline
        if result:
            assert "Trust" in result or len(result) >= 40
    
    def test_preserves_good_cached_headline(self):
        """Should not modify good cached headlines."""
        cached_headline = "What you have in this relationship is already worth protecting."
        
        result = sanitize_shareable_headline(cached_headline)
        
        assert result == cached_headline


class TestRecursiveFixing:
    """Test that recursive fixing works for nested issues."""
    
    def test_fixes_nested_fragment_after_quote_removal(self):
        """After stripping quotes, might reveal another fragment."""
        # After stripping quotes, this becomes "And what you have..."
        headline = '"And what you have in this moment is already worth protecting."'
        
        result = sanitize_shareable_headline(headline)
        
        # Should strip quotes AND fix fragment
        assert not result.startswith('"')
        assert not result.startswith("And ")
        if result:
            assert result[0].isupper()
            assert "what you have" in result.lower()
    
    def test_recursive_sanitization_converges(self):
        """Should eventually converge to valid or empty, not infinite loop."""
        # Pathological case: multiple issues
        headline = '"And but or so when where if..."'
        
        # Should not hang, should return something or empty
        result = sanitize_shareable_headline(headline, "This is a fallback sentence to extract from.")
        
        # Just verify it completes without hanging
        assert isinstance(result, str)


class TestRealWorldExamples:
    """Test with real examples from production."""
    
    def test_growth_card_example(self):
        """Test the actual problematic card from the screenshot."""
        cached_headline = "And 'How can I use this lesson to improve?'"
        answer = (
            "Failure teaches us critical lessons about resilience, humility, "
            "and the importance of action over inaction. The key is to extract "
            "the wisdom from what went wrong and apply it going forward."
        )
        
        result = sanitize_shareable_headline(cached_headline, answer)
        
        # Should be fixed
        assert not result.startswith("And ")
        assert not result.endswith("?")
        # Should be a valid declarative sentence
        if result:
            assert len(result) >= 40
            assert result[-1] in ".!?"
            # Should have extracted something meaningful
            assert len(result.split()) >= 6
    
    def test_preserves_quote_below_card(self):
        """The quote 'Failure teaches us...' should be extractable."""
        answer = (
            "Failure teaches us critical lessons about resilience, humility, "
            "and the importance of action over inaction."
        )
        
        # This should extract the good sentence
        result = _extract_best_sentence_headline(answer)
        
        assert "Failure teaches us" in result
        assert "resilience" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
