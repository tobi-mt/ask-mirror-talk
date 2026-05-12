"""
Integration test for headline sanitization in cache retrieval flow.

This ensures that when cached responses are served (both exact match and similarity match),
the shareable headlines are properly sanitized before being sent to users.
"""

import pytest
from unittest.mock import Mock, patch
from app.qa.service import answer_question_stream


class TestCacheHeadlineSanitization:
    """Test that cached headlines are sanitized when served."""
    
    @patch('app.qa.service.get_answer_cache')
    @patch('app.qa.service._log_qa_with_fresh_session')
    def test_exact_cache_sanitizes_fragment_headline(self, mock_log, mock_cache):
        """When serving exact cached response, should sanitize fragment headlines."""
        # Set up mock cache with bad headline
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance
        
        bad_headline = "And 'How can I use this lesson to improve?'"
        cached_response = {
            "answer": "Trust that your next right step will reveal itself when you need it most.",
            "citations": [{"episode_id": 1, "text": "some text", "timestamp_seconds": 100}],
            "follow_up_questions": ["Q1?", "Q2?", "Q3?"],
            "shareable_headline": bad_headline,
            "answer_source": "openai",
            "answer_status": "generated"
        }
        
        mock_cache_instance.get_exact.return_value = cached_response
        mock_log.return_value = 12345
        
        # Mock database
        mock_db = Mock()
        
        # Call answer_question_stream
        result_chunks = list(answer_question_stream(
            db=mock_db,
            question="test question",
            user_ip="127.0.0.1",
            bypass_cache=False,
            log_interaction=True
        ))
        
        # Find the headline chunk
        headline_chunks = [
            chunk for chunk in result_chunks 
            if '"type": "headline"' in chunk
        ]
        
        assert len(headline_chunks) == 1
        headline_chunk = headline_chunks[0]
        
        # Should not contain the bad headline
        assert "And '" not in headline_chunk
        # Should not contain question marks in headline
        assert not ('"text": "' in headline_chunk and '?"' in headline_chunk.split('"text": "')[1].split('"')[0])
    
    @patch('app.qa.service.embed_text')
    @patch('app.qa.service.get_answer_cache')
    @patch('app.qa.service._log_qa_with_fresh_session')
    def test_similarity_cache_sanitizes_fragment_headline(self, mock_log, mock_cache, mock_embed):
        """When serving similarity cached response, should sanitize fragment headlines."""
        # Set up mock cache
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance
        mock_cache_instance.get_exact.return_value = None  # No exact match
        
        bad_headline = "But where do I feel even the tiniest spark of quiet joy?"
        cached_response = {
            "answer": "What you already have in your relationships is worth protecting today.",
            "citations": [{"episode_id": 2, "text": "citation text", "timestamp_seconds": 200}],
            "follow_up_questions": ["Q1?", "Q2?", "Q3?"],
            "shareable_headline": bad_headline,
            "answer_source": "openai",
            "answer_status": "generated"
        }
        
        mock_cache_instance.get.return_value = cached_response
        mock_embed.return_value = [0.1] * 1536  # Mock embedding
        mock_log.return_value = 67890
        
        # Mock database
        mock_db = Mock()
        
        # Call answer_question_stream
        result_chunks = list(answer_question_stream(
            db=mock_db,
            question="test question about joy",
            user_ip="127.0.0.1",
            bypass_cache=False,
            log_interaction=True
        ))
        
        # Find the headline chunk
        headline_chunks = [
            chunk for chunk in result_chunks 
            if '"type": "headline"' in chunk
        ]
        
        assert len(headline_chunks) == 1
        headline_chunk = headline_chunks[0]
        
        # Should not contain fragment start
        assert "But where" not in headline_chunk
        # Should not be a question
        assert not ('"text": "' in headline_chunk and '?"' in headline_chunk.split('"text": "')[1].split('"')[0])
    
    @patch('app.qa.service.get_answer_cache')
    @patch('app.qa.service._log_qa_with_fresh_session')
    def test_preserves_good_cached_headline(self, mock_log, mock_cache):
        """Should not modify good headlines from cache."""
        # Set up mock cache with good headline
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance
        
        good_headline = "What you have in this relationship right now is already worth protecting."
        cached_response = {
            "answer": "Your relationships need attention more than they need perfection.",
            "citations": [{"episode_id": 3, "text": "some text", "timestamp_seconds": 300}],
            "follow_up_questions": ["Q1?", "Q2?", "Q3?"],
            "shareable_headline": good_headline,
            "answer_source": "openai",
            "answer_status": "generated"
        }
        
        mock_cache_instance.get_exact.return_value = cached_response
        mock_log.return_value = 11111
        
        # Mock database
        mock_db = Mock()
        
        # Call answer_question_stream
        result_chunks = list(answer_question_stream(
            db=mock_db,
            question="test question",
            user_ip="127.0.0.1",
            bypass_cache=False,
            log_interaction=True
        ))
        
        # Find the headline chunk
        headline_chunks = [
            chunk for chunk in result_chunks 
            if '"type": "headline"' in chunk
        ]
        
        assert len(headline_chunks) == 1
        headline_chunk = headline_chunks[0]
        
        # Should contain the original good headline
        assert good_headline in headline_chunk
    
    @patch('app.qa.service.get_answer_cache')
    @patch('app.qa.service._log_qa_with_fresh_session')
    def test_replaces_unfixable_cached_headline(self, mock_log, mock_cache):
        """When cached headline is unfixable, should extract from answer."""
        # Set up mock cache with terrible headline
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance
        
        terrible_headline = "How?"  # Too short and a question
        cached_response = {
            "answer": "Trust that your next right step will reveal itself when you need it most.",
            "citations": [{"episode_id": 4, "text": "some text", "timestamp_seconds": 400}],
            "follow_up_questions": ["Q1?", "Q2?", "Q3?"],
            "shareable_headline": terrible_headline,
            "answer_source": "openai",
            "answer_status": "generated"
        }
        
        mock_cache_instance.get_exact.return_value = cached_response
        mock_log.return_value = 22222
        
        # Mock database
        mock_db = Mock()
        
        # Call answer_question_stream
        result_chunks = list(answer_question_stream(
            db=mock_db,
            question="test question",
            user_ip="127.0.0.1",
            bypass_cache=False,
            log_interaction=True
        ))
        
        # Find the headline chunk
        headline_chunks = [
            chunk for chunk in result_chunks 
            if '"type": "headline"' in chunk
        ]
        
        assert len(headline_chunks) == 1
        headline_chunk = headline_chunks[0]
        
        # Should not contain the terrible headline
        assert '"How?"' not in headline_chunk
        # Should extract from answer OR return empty
        # If it extracted, should contain something from the answer
        if '"text": ""' not in headline_chunk:
            assert ("Trust" in headline_chunk or 
                    "next right step" in headline_chunk or
                    "reveal itself" in headline_chunk)


class TestRealWorldScenario:
    """Test the exact scenario from the user's screenshot."""
    
    @patch('app.qa.service.get_answer_cache')
    @patch('app.qa.service._log_qa_with_fresh_session')
    def test_growth_card_scenario(self, mock_log, mock_cache):
        """Test the actual problematic 'Growth' card from production."""
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance
        
        # Exact cached response that was causing the issue
        problematic_cached = {
            "answer": (
                "Failure teaches us critical lessons about resilience, humility, "
                "and the importance of action over inaction. The key is to extract "
                "the wisdom from what went wrong and apply it going forward."
            ),
            "citations": [
                {
                    "episode_id": 123,
                    "text": "We learn from failure",
                    "timestamp_seconds": 500
                }
            ],
            "follow_up_questions": [
                "How can I learn from my mistakes?",
                "What patterns do I see in my failures?",
                "How can I be more resilient?"
            ],
            "shareable_headline": "And 'How can I use this lesson to improve?'",
            "answer_source": "openai",
            "answer_status": "generated"
        }
        
        mock_cache_instance.get_exact.return_value = problematic_cached
        mock_log.return_value = 99999
        
        mock_db = Mock()
        
        # Stream the answer
        result_chunks = list(answer_question_stream(
            db=mock_db,
            question="how do I grow from failure",
            user_ip="127.0.0.1",
            bypass_cache=False,
            log_interaction=True
        ))
        
        # Extract headline
        headline_chunks = [
            chunk for chunk in result_chunks 
            if '"type": "headline"' in chunk
        ]
        
        assert len(headline_chunks) == 1
        headline_chunk = headline_chunks[0]
        
        # CRITICAL ASSERTIONS - The fix for the reported bug
        assert "And 'How can I use this lesson to improve?'" not in headline_chunk
        assert "And " not in headline_chunk or '"text": ""' in headline_chunk
        
        # If a headline was returned (not empty), verify it's valid
        if '"text": ""' not in headline_chunk:
            # Should extract something from the answer
            assert ("Failure teaches us" in headline_chunk or
                    "resilience" in headline_chunk or
                    "wisdom" in headline_chunk)
            # Should not end with ?
            import json
            # Parse to verify
            data_part = headline_chunk.split("data: ")[1].strip()
            parsed = json.loads(data_part)
            if parsed.get("text"):
                assert not parsed["text"].endswith("?")
                assert len(parsed["text"]) >= 40


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
