# Mirror Talk Theme 7.9.2 — Whole-Word Responsive Typography

This release corrects mid-word heading breaks and applies the fix across the complete owned website experience.

- Replaces forced `overflow-wrap: anywhere` behavior in YouTube Studio, featured slides and post cards.
- Adds a global whole-word heading policy across pages, posts, archives, topic hubs, Insights, dialogs, the Living Mirror and the footer.
- Disables automatic heading hyphenation so editorial titles remain intentional and readable.
- Preserves safe `break-word` behavior for prose only when a genuinely unbroken token would otherwise escape the viewport.
- Replaces clipping on the primary site frame and homepage with horizontal-only containment.
- Tightens mobile hero, article, archive, feature and footer heading scales.
- Retains balanced line wrapping where supported, with ordinary whole-word wrapping as the cross-browser fallback.
- Shortens the homepage studio statement to “Watch what moves you.” for a calmer, better-proportioned composition.
- Keeps grid children at `min-width: 0` so content reflows inside its column instead of pushing beneath adjacent media.

The automated typography audit now rejects `overflow-wrap: anywhere` and `word-break: break-all` in the owned site system.
