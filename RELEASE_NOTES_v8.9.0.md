# Mirror Talk Theme 8.9.0

## Automatic Editorial Composer 2

Composer 2 converts the earlier invisible analysis layer into a visible,
server-rendered editorial presentation without rewriting canonical WordPress
body content.

### Visible reader and crawler experience

- Extractive introduction generated only from supplied content.
- Content-type, topic and reading-time context.
- Extractive “At a glance” takeaway panel.
- Neutral accessible section headings when a long article lacks structure.
- Contextual related-conversation links rendered in the initial HTML.
- Responsive, dark editorial styling for legacy posts and ordinary pages.
- Existing citation briefs and related-conversation source guides retained.

Homepage, Ask Mirror Talk, Contact, Join Us and Insights are explicitly
excluded from automatic composition because they have dedicated interaction
designs.

### Editorial safety

- Stored `post_content` remains untouched.
- Quotations, transcripts, figures, code, audio, video and embeds are never
  rewritten.
- Manually authored SEO titles and descriptions are detected and preserved.
- Weak or ambiguous topics are rejected instead of published confidently.
- Generic keywords receive reduced weight during topic classification.
- Search titles cannot end with dangling punctuation or connector words.
- Validated search evidence continues to supersede provisional topics.

### Administrator controls

- Full Composer decision report in each post/page editor.
- Global report under **Mirror Talk Intelligence → Editorial Composer**.
- Editor-accessible report under **Tools → Mirror Talk Composer**.
- Per-decision Enable/Revert controls.
- Approve, Recompose, Preview and Restore actions.
- Post/page list shortcut to Composer decisions.
- Twenty historical Composer snapshots per document.
- REST representation for auditable Composer results.

### Migration

- All published posts and pages are reprocessed in controlled batches.
- WP-Cron, administrator visits and first public visits provide redundant
  migration paths.
- IndexNow receives materially recomposed URLs.

## Validation

- 205 automated tests passed; 3 integration-dependent tests skipped.
- 30 PHP files parsed without syntax errors.
- All theme JavaScript files passed syntax validation.
