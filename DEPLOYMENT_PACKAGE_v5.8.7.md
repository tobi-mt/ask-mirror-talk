# Deployment Package v5.8.7

Release date: 2026-05-15
Package: astra-child-v5.8.7.zip

## What This Release Fixes

- OpenAI compat hardening for GPT-5/o-series models:
  - Avoids unsafe downgrade to max_tokens when SDK cannot handle max_completion_tokens.
  - Prevents recurring 400 errors caused by max_tokens on GPT-5.x models.
- Follow-up and headline generation now use safe model fallback chains.
  - If the primary follow-up/headline model fails, fallback models are attempted automatically.
- Reflection card quality tightened safely:
  - Backend headline sanitation now strips weak starters and speaker-attribution lead-ins.
  - Frontend ignores weak SSE headline candidates before card rendering.

## Version Bumps

- pyproject.toml -> 5.8.7
- wordpress/astra-child/style.css -> 5.8.7
- wordpress/astra-child/ask-mirror-talk.php -> 5.8.7
- wordpress/astra-child/ask-mirror-talk.js -> v5.8.7 marker
- wordpress/astra-child/ask-mirror-talk-premium.js -> v5.8.7 marker
- wordpress/astra-child/analytics-addon.js -> v5.8.7 marker
- wordpress/astra-child/sw.js -> CACHE_VERSION amt-v5.8.7
- wordpress/astra-child/sw.js -> BUILD_TIMESTAMP 2026-05-15T01:00:00.000Z

## Verification Summary

- tests/test_openai_compat.py: 7 passed
- tests/test_shareable_headline.py: 17 passed
- Existing unrelated baseline failures still present in tests/test_qa_quality_improvements.py:
  - test_filter_low_quality_citations
  - test_citation_relevance_scoring

## Deployment Checklist

1. Upload astra-child-v5.8.7.zip.
2. Purge WordPress/CDN cache.
3. Verify service worker version update on mobile and desktop.
4. Confirm no new max_tokens warnings for GPT-5.x in logs.
