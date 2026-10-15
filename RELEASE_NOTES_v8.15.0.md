# Mirror Talk 8.15.0 — Owned Content Migration

## Elementor Migration Centre

Adds **Mirror Talk Intelligence → Elementor Migration**, a guarded migration workspace that:

- Inventories Elementor-authored posts and pages.
- Classifies each document as ready, review required, invalid or migrated.
- Lists widget dependencies and unsupported components.
- Generates a semantic conversion preview without changing the public page.
- Converts headings, text, images, videos, buttons, lists, dividers, shortcodes and social links into owned WordPress/Mirror Talk components.
- Replaces Elementor YouTube widgets with Mirror Talk's privacy-first player.
- Creates a complete checksum-protected snapshot before every migration.
- Preserves URLs, titles, publication details, authors, taxonomies, featured images and SEO history.
- Sends migrated content through the Editorial Composer, guarded taxonomy engine, SEO metadata system and IndexNow queue.
- Migrates only fully supported documents in guarded batches of ten.
- Provides individual restore controls.
- Detects remaining Elementor templates and `[elementor-template]` dependencies.
- Shows a strict **safe to deactivate Elementor** release gate only when no public dependency remains.

## Safety rules

- Unknown widgets, custom HTML, Elementor forms, sliders and complex plugin widgets are never silently discarded.
- Documents with unsupported widgets are held for review.
- Migration never changes a slug, permalink or canonical URL.
- Original Elementor JSON remains in the protected migration snapshot.
- An inline migrated video disables the Composer's additional video insertion to avoid duplicate players.

## Verification

- Local release quality gate: passed.
- Focused theme and WordPress regression suite: 92 passed.
- JavaScript syntax checks: passed.
