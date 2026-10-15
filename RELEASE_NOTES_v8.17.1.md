# Mirror Talk 8.17.1 — Emergency-safe Migration Dashboard

- Confirms 8.17.0 is active on production and removes the remaining request-time legacy payload work.
- The Elementor Migration dashboard no longer loads or decodes `_elementor_data` JSON—not even for its 12 visible rows.
- Removes synchronous conversion previews from the dashboard request.
- Moves residual shortcode scans into a guarded background job with a six-hour cached result.
- Moves aggregate migration counts into a guarded background job; the first dashboard request now renders a safe shell instead of waiting for database-wide counts.
- Uses ID-only, metadata-cache-disabled dashboard queries.
- Keeps actual analysis, conversion, verification and rollback inside isolated workers.
- Includes all runtime containment, trust-page and previous migration corrections.
