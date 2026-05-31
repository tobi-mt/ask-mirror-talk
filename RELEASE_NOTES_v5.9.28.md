# Ask Mirror Talk v5.9.28 - Retrieval + Analytics Lift

Released: 2026-05-31  
Status: Draft

## Summary
v5.9.28 improves answer quality on weak matches, warms the cache daily using real analytics signals, and adds per-origin cohort visibility for latency and weak-match tracking.

## Highlights

1. Low-match auto-rewrite fallback
- Added a second-pass retrieval fallback when first-pass confidence is low.
- Applies to both standard and streaming answer flows.
- Uses the rewritten retrieval query only when confidence improves.

2. Analytics-driven daily weak-match prewarm
- Added weak-match question mining from recent qa_logs.
- Added startup weak-match prewarm and a daily background prewarm loop.
- Keeps hard questions warm to reduce slow and low-quality responses.

3. Per-origin cohort dashboards
- Added origin-cohort analytics endpoint.
- Added origin cohort metrics to summary payload and admin dashboard.
- Tracks origin-level total questions, avg/p95 latency, cache hit %, and weak-match %.

## Version + Packaging
- Project/theme/widget version markers bumped to 5.9.28.
- Service worker cache key bumped to amt-v5.9.28.
- Release artifact: ask-mirror-talk_v5.9.28.zip

## Validation Snapshot
- Focused regression tests passed for routes, service logging, preprocessing, cache, and rate limits.
- Python compile checks passed for updated backend modules.

## Notes
- This is a short draft intended for deployment comms and handoff.