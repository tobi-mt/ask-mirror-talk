# Mirror Talk 6.4.0 — Real-Content Correction

Release date: 2026-10-02

This release responds to staging screenshots of the homepage, blog, Contact page, post pages, slider and invitation dialogs.

## Corrections

- Removed legacy page-builder content that was being appended beneath the new homepage.
- Neutralised Astra's article widths, floats, margins and large internal padding inside the blog grid.
- Restored balanced three-column desktop, two-column tablet and one-column mobile blog layouts.
- Forced single-post article surfaces to remain dark so ivory text can never appear on a white Astra background.
- Added compatibility colors for legacy Elementor headings, body copy, links, forms and buttons.
- Reduced feature-slider heading and episode-title scales, added safe wrapping and increased the responsive stage height.
- Reset modal close controls to a consistent accessible 40 × 40 px circle.
- Forced the text-based site title and description to use readable light colors in the dark header.

## Topic intelligence

- Replaced general-blog fallbacks with six real routes: `/explore/purpose/`, `/explore/resilience/`, `/explore/relationships/`, `/explore/faith/`, `/explore/healing/` and `/explore/leadership/`.
- Added virtual topic collections that classify existing posts using titles, excerpts, article content and assigned categories.
- No manual recategorisation is required before the collections become useful.

## Continuous listening

- Added **Keep playing while I browse** to the inline player.
- The action opens a compact same-origin player window that survives normal WordPress navigation.
- Selected episode, timestamp and playing state transfer through same-origin browser storage.
- The inline player restores the last selected episode and timestamp when a new page loads.
- Continuous playback is explicitly user initiated to comply with browser autoplay and popup restrictions.

## Validation

- Full automated suite: 160 passed, 3 skipped.
- JavaScript syntax and theme JSON: passed.
- Blog cards: 437 px each at 1440 px; one 368 px column at 390 px.
- Article background and text contrast: visually and programmatically verified.
- Modal close control: verified at 40 × 40 px with zero inherited padding.
- No horizontal overflow in verified desktop or mobile views.
- PHP CLI remains unavailable locally; PHP lint remains a staging check.

## Deployment package

`wordpress/astra-child-v6.4.0.zip`
