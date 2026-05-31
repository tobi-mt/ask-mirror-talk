"""
Test Suite for QA Service Quality Improvements

Run with: pytest tests/test_qa_quality_improvements.py -v
"""

import pytest
from app.qa.quality import validate_answer_quality, should_retry_generation
from app.qa.preprocessing import preprocess_query, optimize_for_retrieval, build_low_match_rewrite
from app.qa.citation_validation import validate_citations, ensure_citation_quality
from app.qa.resilience import CircuitBreaker, CircuitBreakerConfig, is_transient_error


class TestAnswerQualityValidation:
    """Test answer quality scoring and validation."""
    
    def test_complete_quality_answer(self):
        """Test that a complete, quality answer scores well."""
        question = "How do I deal with grief?"
        answer = """
        Grief is a deeply personal journey that requires patience and self-compassion. 
        According to Mirror Talk, the key is to allow yourself to feel the emotions 
        without rushing the process. Create space for both the pain and the healing, 
        understanding that they often coexist. One practical step is to find small 
        rituals that honor your loss while also nurturing your present self.
        """
        citations = [
            {"episode_id": 1, "text": "Grief requires patience and allowing yourself to feel..."},
            {"episode_id": 2, "text": "Create space for both pain and healing..."},
        ]
        
        quality = validate_answer_quality(question, answer, citations)
        
        assert quality.passed is True
        assert quality.overall_score >= 70.0
        assert quality.completeness >= 80.0
        assert len(quality.issues) == 0
    
    def test_incomplete_answer(self):
        """Test that incomplete answers are detected."""
        question = "How do I deal with grief?"
        answer = "Grief is a deeply personal journey that requires"  # Incomplete!
        citations = []
        
        quality = validate_answer_quality(question, answer, citations)
        
        assert quality.passed is False
        assert quality.completeness < 70.0
        assert any("incomplete" in issue.lower() or "end" in issue.lower() for issue in quality.issues)
    
    def test_no_citations(self):
        """Test that answers without citations score poorly."""
        question = "How do I deal with grief?"
        answer = "This is a complete answer with proper structure and length."
        citations = []
        
        quality = validate_answer_quality(question, answer, citations)
        
        assert quality.citation_support == 0.0
        assert any("no citations" in issue.lower() for issue in quality.issues)
    
    def test_should_retry_low_quality(self):
        """Test retry logic for low quality answers."""
        question = "Test"
        answer = "Short"
        citations = []
        
        quality = validate_answer_quality(question, answer, citations)
        
        should_retry = should_retry_generation(quality, attempt=0, max_attempts=2)
        assert should_retry is True


class TestQueryPreprocessing:
    """Test query preprocessing and optimization."""
    
    def test_spell_correction(self):
        """Test spelling correction."""
        query = "How do I deal with greif and boundries?"
        processed = preprocess_query(query)
        
        assert "grief" in processed.normalized.lower()
        assert "boundaries" in processed.normalized.lower()
    
    def test_key_term_extraction(self):
        """Test key term extraction."""
        query = "How do I set boundaries without feeling guilty?"
        processed = preprocess_query(query)
        
        assert "boundaries" in processed.key_terms or "boundary" in processed.key_terms
        assert len(processed.key_terms) > 0
    
    def test_intent_detection(self):
        """Test intent classification."""
        advice_query = "How do I deal with grief?"
        definition_query = "What is emotional resilience?"
        
        advice_processed = preprocess_query(advice_query)
        definition_processed = preprocess_query(definition_query)
        
        assert advice_processed.intent == "advice"
        assert definition_processed.intent == "definition"
    
    def test_query_expansion(self):
        """Test synonym expansion."""
        query = "How do I handle grief?"
        processed = preprocess_query(query)
        
        # Should have expanded query with synonyms
        if processed.expanded:
            assert "grief" in processed.expanded.lower()
            # May include synonyms like loss, mourning
    
    def test_clarity_detection(self):
        """Test vague query detection."""
        clear_query = "How do I set boundaries with my family without feeling guilty?"
        vague_query = "Tell me about stuff"
        
        clear_processed = preprocess_query(clear_query)
        vague_processed = preprocess_query(vague_query)
        
        assert clear_processed.is_clear is True
        assert vague_processed.is_clear is False
        assert len(vague_processed.suggestions) > 0

    def test_brand_lead_in_stripping(self):
        """Brand boilerplate should be removed from retrieval query text."""
        query = "What does Mirror Talk teach about carrying inner peace with more honesty and peace?"
        processed = preprocess_query(query)

        assert processed.normalized.lower().startswith("carrying inner peace")
        assert "mirror talk" not in processed.normalized.lower()

    def test_example_query_gets_practical_expansion(self):
        """Example-seeking prompts should get practical-context expansion."""
        query = "What does courage look like in everyday life?"
        processed = preprocess_query(query)
        retrieval_query = optimize_for_retrieval(processed)

        assert processed.intent == "example"
        assert "daily practice" in retrieval_query.lower()

    def test_low_match_rewrite_builder(self):
        """Low-match rewrites should preserve intent and add practical hints."""
        query = "What does courage look like in everyday life?"
        processed = preprocess_query(query)
        rewritten = build_low_match_rewrite(processed)

        assert rewritten is not None
        assert "practical real-life examples and steps" in rewritten.lower()
        assert rewritten.endswith("?")


class TestCitationValidation:
    """Test citation quality and relevance validation."""
    
    def test_filter_low_quality_citations(self):
        """Test that low quality citations are filtered."""
        answer = "The key to healing is self-compassion and patience."
        citations = [
            {
                "episode_id": 1,
                "text": "Self-compassion is essential for healing and growth...",
            },
            {
                "episode_id": 2,
                "text": "Welcome back to the show! Don't forget to subscribe!",  # Meta content
            },
            {
                "episode_id": 3,
                "text": "What does that mean to you? Can you tell us more?",  # Host question
            },
        ]
        
        filtered, scores = validate_citations(answer, citations, min_relevance=60.0)
        
        # Should filter out the meta and host question citations
        assert len(filtered) < len(citations)
        assert filtered[0]["episode_id"] == 1  # Keep the good one
    
    def test_citation_relevance_scoring(self):
        """Test citation relevance scoring."""
        answer = "Grief requires patience, self-compassion, and allowing yourself to feel."
        citations = [
            {
                "episode_id": 1,
                "text": "Grief is a journey that requires patience and self-compassion.",  # High relevance
            },
            {
                "episode_id": 2,
                "text": "The weather is nice today and I like coffee.",  # No relevance
            },
        ]
        
        filtered, scores = validate_citations(answer, citations, min_relevance=60.0)
        
        assert len(scores) == 2
        assert scores[0].relevance_score > scores[1].relevance_score
        assert len(filtered) == 1  # Only high-relevance citation
    
    def test_ensure_minimum_citations(self):
        """Test minimum citation count requirement."""
        answer = "This is a good answer."
        citations = [{"episode_id": 1, "text": "Some relevant text here."}]
        
        filtered, quality_ok = ensure_citation_quality(
            answer, citations, min_count=2, min_relevance=60.0
        )
        
        # Should recognize we don't have enough citations
        assert quality_ok is False


class TestResilience:
    """Test resilience features."""
    
    def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after threshold failures."""
        config = CircuitBreakerConfig(failure_threshold=3, timeout=1.0)
        breaker = CircuitBreaker("test", config)
        
        # Simulate failures
        for i in range(3):
            try:
                breaker.call(lambda: 1 / 0)  # Will raise ZeroDivisionError
            except ZeroDivisionError:
                pass
        
        # Circuit should now be open
        from app.qa.resilience import CircuitBreakerOpenError
        with pytest.raises(CircuitBreakerOpenError):
            breaker.call(lambda: "success")
    
    def test_circuit_breaker_resets(self):
        """Test circuit breaker can be manually reset."""
        config = CircuitBreakerConfig(failure_threshold=1)
        breaker = CircuitBreaker("test", config)
        
        # Cause failure
        try:
            breaker.call(lambda: 1 / 0)
        except ZeroDivisionError:
            pass
        
        # Reset
        breaker.reset()
        
        # Should work now
        result = breaker.call(lambda: "success")
        assert result == "success"
    
    def test_transient_error_detection(self):
        """Test detection of transient vs permanent errors."""
        # Transient errors
        assert is_transient_error(Exception("Connection timeout"))
        assert is_transient_error(Exception("Rate limit exceeded (429)"))
        assert is_transient_error(Exception("502 Bad Gateway"))
        
        # Permanent errors
        assert is_transient_error(Exception("Invalid API key")) is False
        assert is_transient_error(Exception("Not found")) is False


class TestEndToEndQuality:
    """Integration tests for complete QA flow with improvements."""
    
    @pytest.mark.skip(reason="Requires database and OpenAI API")
    def test_answer_generation_with_quality_checks(self):
        """Test complete answer generation with quality validation."""
        # This would test the full flow but requires:
        # - Database connection
        # - OpenAI API key
        # - Sample episodes in DB
        pass
    
    @pytest.mark.skip(reason="Requires database and OpenAI API")
    def test_retry_on_poor_quality(self):
        """Test that poor quality answers trigger retry."""
        # This would test retry logic but requires:
        # - Ability to mock OpenAI responses
        # - Control over answer quality
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
