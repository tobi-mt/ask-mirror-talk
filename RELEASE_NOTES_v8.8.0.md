# Mirror Talk Theme 8.8.0

Automatic Editorial Composer release.

## Content-in, polished-page-out workflow

- Automatically analyses every saved or published post and page.
- Detects article, episode, interview, reflection and resource content types.
- Repairs duplicate and skipped heading levels at render time without rewriting stored editorial copy.
- Applies the existing responsive editorial system to paragraphs, lists, quotations, tables, embeds and media.
- Adds a concise supplied-content introduction when a document starts without readable context.
- Adds a generated “What you will explore” block to long, well-structured documents when appropriate.
- Calculates reading time and content-quality score.

## Zero-configuration SEO

- Generates a bounded search title and search description when the editor has not provided one.
- Derives a clearly labelled provisional focus topic from the supplied content.
- Automatically replaces the provisional source label when verified Google/Bing evidence becomes available.
- Selects the appropriate Mirror Talk topic category when a post has no meaningful category.
- Reuses matching existing tags without manufacturing taxonomy spam.
- Records the relevant `/explore/` topic hub and contextual internal-link opportunities.
- Uses the featured image when supplied and the established branded social fallback otherwise.
- Repairs deterministic featured-image alt text without guessing people, identity or scene details.
- Reuses canonical, Open Graph, Twitter, Article/Podcast and citation schema systems.
- Queues materially composed public URLs for IndexNow.

## Editorial safety and control

- Never silently rewrites stored body content.
- Displays possible spelling, punctuation, accessibility, structural and internal-link issues as review items.
- Stores composition snapshots, taxonomy state and SEO metadata history.
- Adds “Recompose now” and one-click “Restore previous composition” controls to the editor.
- Publishes composer results through protected WordPress REST fields.
- Supports `<!-- mirror-talk:preserve-format -->` for intentionally bespoke documents.
- Backfills the existing public archive in safe 25-document background batches.

## Validation

- Adds composer requirements to the permanent release-quality gate.
- Includes deterministic tests for content detection, SEO generation, taxonomy, IndexNow, revision history, rollback, non-destructive behavior and responsive presentation.
