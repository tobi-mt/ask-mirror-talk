# Mirror Talk 8.13.1 — Fast authenticated previews

- Adds a dedicated fast path for authenticated WordPress post and page previews.
- Prevents preview requests from spawning WP-Cron or competing with background composition on resource-constrained hosting.
- Omits the unrelated persistent player, global YouTube studio, Ask dock, subscription dialogs, analytics consent and personalization script from editor previews.
- Keeps the actual article, Composer layout, Story Studio inline media, featured image and editorial typography visible for review.
- Adds `X-Mirror-Talk-Preview-Mode: fast` to successful preview responses for diagnosis.
- Does not change the public published experience.

