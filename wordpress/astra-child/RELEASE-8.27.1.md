# Mirror Talk 8.27.1

## Live-verification refinement

- Refreshes the cached Migration Centre automatically after queue transitions while keeping the admin request fast.
- Shows every active migration document in the cached queue instead of only the first twelve.
- Prevents a duplicate queue control from appearing during `preview_ready` or `preview_verified` stages.
- Expands the retained audit ledger to 2,000 global events and 100 events per document.
- States how many retained audit events are currently displayed.
- Correctly classifies migrated landing pages as pages rather than episodes.
- Rejects short headings and navigation labels as generated takeaways.

## Production evidence from 8.27.0

- A live Elementor page completed prepare, private preview, desktop verification, mobile verification, commit and public verification.
- Both live verification profiles returned HTTP 200 with no structural issues.
- The automatic queue reduced the actionable pending count without a 504 or quarantined document.
