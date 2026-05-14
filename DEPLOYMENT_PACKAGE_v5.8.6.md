# Deployment Package v5.8.6

Release date: 2026-05-15
Package: astra-child-v5.8.6.zip

## Included Version Bumps

- wordpress/astra-child/style.css -> 5.8.6
- wordpress/astra-child/ask-mirror-talk.php -> 5.8.6
- wordpress/astra-child/ask-mirror-talk.js -> v5.8.6 log marker
- wordpress/astra-child/ask-mirror-talk-premium.js -> v5.8.6 log marker
- wordpress/astra-child/analytics-addon.js -> v5.8.6 markers
- wordpress/astra-child/sw.js -> CACHE_VERSION amt-v5.8.6
- wordpress/astra-child/sw.js -> BUILD_TIMESTAMP 2026-05-15T00:00:00.000Z
- pyproject.toml -> 5.8.6

## Sanity Verification Summary

- Editor diagnostics: no errors in all modified files.
- JavaScript syntax checks: could not run because node is not installed in this environment.
- PHP lint checks: could not run because php is not installed in this environment.
- Python test run:
  - Collection issue when running full repo: scripts/test_openai_compat.py name collision with tests/test_openai_compat.py.
  - tests/ suite run: 121 passed, 2 failed, 3 skipped.
  - Failing tests:
    - tests/test_qa_quality_improvements.py::TestCitationValidation::test_filter_low_quality_citations
    - tests/test_qa_quality_improvements.py::TestCitationValidation::test_citation_relevance_scoring

## Package Artifact

- wordpress/astra-child-v5.8.6.zip (created)

## Deployment Notes

1. Upload astra-child-v5.8.6.zip in WordPress theme uploader.
2. Purge WordPress/CDN caches after deployment.
3. Validate service worker update on a fresh browser session.
