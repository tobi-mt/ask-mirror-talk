# Mirror Talk 8.17.5 — Bounded Migration Inventory

- Replaces WordPress's slow OR-meta dashboard query with an index-friendly `EXISTS` query.
- Fetches no more than 12 post IDs and never hydrates Elementor JSON.
- Allows the progressive snapshot worker to commit document rows before residual scanning.
- Retains the resolved 504, recursion, diagnostic-log and progressive-snapshot protections.
