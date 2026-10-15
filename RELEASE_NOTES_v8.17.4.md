# Mirror Talk 8.17.4 — Clean Recovery and Progressive Snapshots

- Removes the resolved historic recursion failure from administrator notices immediately.
- Makes migration dashboard snapshots progressive: counts and rows are committed before residual dependency work begins.
- Isolates the unindexed legacy-shortcode scan in its own background event.
- Updates the cached dashboard automatically when the residual scan finishes.
- Prevents a host-level worker termination from discarding already completed dashboard progress.
