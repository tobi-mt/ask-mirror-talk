from app.qa.cache import AnswerCache, normalize_question


def test_exact_cache_hit_returns_without_similarity_scan():
    cache = AnswerCache(ttl_seconds=60)
    norm_q = normalize_question("How do I heal?")
    cache.put(norm_q, [0.1, 0.2], {"answer": "cached", "citations": []})

    result = cache.get_exact(norm_q)

    assert result is not None
    assert result["answer"] == "cached"
    assert result["cached"] is True
    assert result["cache_similarity"] == 1.0
    assert result["cache_match_type"] == "exact"
