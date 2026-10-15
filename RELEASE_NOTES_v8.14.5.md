# Mirror Talk 8.14.5

Focused follow-up discovered during the live 8.14.4 verification.

## Fix

- Detects legacy Elementor YouTube widgets in Elementor's `_elementor_data` metadata as well as ordinary WordPress post content.
- Ensures the 8.14.4 privacy-first, click-to-load legacy-video guard is actually enqueued on Elementor-authored posts.

No post content, URLs, SEO metadata, forms, layouts or taxonomies are rewritten.

## Verification

- Local release quality gate: passed.
- Focused WordPress/theme regression suite: 89 passed.
- JavaScript syntax checks: passed.
