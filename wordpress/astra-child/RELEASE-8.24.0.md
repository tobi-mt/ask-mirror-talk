# Mirror Talk 8.24.0

This release adds a guarded semantic formatting layer for existing and future
posts and pages.

- Repairs high-confidence bold-only legacy section labels as real H2 headings.
- Converts consecutive bullet and numbered paragraphs into semantic lists.
- Converts timestamp sequences into accessible episode chapter lists with
  machine-readable durations.
- Handles Classic Editor lists stored in a single paragraph with line breaks.
- Runs before the Editorial Composer, allowing real repaired headings to power
  on-page navigation instead of generic generated sections.
- Leaves canonical `post_content`, quotations, transcripts, embeds, URLs and
  factual wording unchanged.
- Supports the existing `mirror-talk:preserve-format` document opt-out.
- Adds an individual Composer decision that administrators can disable or
  re-enable per post or page.
- Records detected heading, list and chapter repairs in each Composer report.
- Starts a bounded Composer 2.3 backfill for report metadata while public
  formatting works immediately, without waiting for the queue.
- Adds responsive, high-contrast presentation for headings, lists and chapters.

The formatter deliberately refuses ambiguous transformations: it requires
short bold-only labels or at least two consecutive items of the same verified
type. Stored editorial content is never rewritten by this feature.
