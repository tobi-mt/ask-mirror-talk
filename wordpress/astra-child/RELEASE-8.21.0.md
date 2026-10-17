# Mirror Talk 8.21.0

Platform-health release focused on Intelligence aggregation and background reliability.

- Replaces the monolithic Intelligence refresh with isolated quality, recommendation and knowledge-graph stages.
- Adds per-stage runtime state, timestamps, failure evidence and stale-job recovery.
- Dispatches explicit administrator refreshes only after the admin response has completed.
- Adds a System Health panel showing pipeline freshness, event-table readiness, last collection time and recovery state.
- Preserves completed artifacts when another stage needs a retry.
- Bounds command-centre analysis on shared hosting and avoids redundant search-history scans for pages without search evidence.
- Retains all public experience, listening, conversion, SEO, Composer, migration and safety features from 8.20.1.

Certification requires the local release gate plus a complete live pipeline run after activation. The dashboard deliberately reports “Queued”, “Running” or “Attention” until that production proof exists; it does not claim health optimistically.
