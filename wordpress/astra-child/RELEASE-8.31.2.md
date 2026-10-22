# Mirror Talk 8.31.2 — Deterministic YouTube Detection

- Extracts the video ID directly from current post/page source instead of reparsing a matched URL.
- Handles watch URLs, Shorts, embeds, `youtu.be` links and HTML-encoded query parameters.
- Adds a non-personal `data-video-source` marker (`document` or `latest`) for reliable production QA.
- Keeps current-content, provided-URL, legacy-Elementor and latest-upload priority in that order.
