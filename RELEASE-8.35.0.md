# Mirror Talk 8.35.0

Intentional featured-image fallback release.

- Replaces the homepage archive cards’ blank beige placeholders with actual Mirror Talk artwork.
- Uses the same stable per-document fallback selection for homepage cards, featured sliders, article heroes and social previews.
- Adds the podcast cover art to the fallback rotation and removes the visually pale reflection asset from card/social fallback selection.
- Keeps editor-supplied featured images authoritative.
- Supplies meaningful fallback alt text, intrinsic dimensions, lazy loading, asynchronous decoding and low fetch priority for archive cards.
- Retains a CSS artwork fallback if the PHP image helper is unavailable.
- Verified the live 8.34.2 QOTD is present inside `.mt-composer-document`, outside **At a glance**, and placed between an ordinary paragraph and the next article section.
