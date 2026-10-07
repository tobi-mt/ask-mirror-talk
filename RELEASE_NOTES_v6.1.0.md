# Mirror Talk 6.1.0 — Editorial Sanctuary Foundation

Release date: 2026-10-02

## Outcome

This release establishes the new Mirror Talk WordPress design system and the
first opt-in editorial homepage while preserving Astra compatibility and the
existing Ask Mirror Talk feature set.

## WordPress theme

- Added `theme.json` with the Mirror Talk color, typography, spacing and layout tokens.
- Added `mirror-talk-site.css` for the global brand system and responsive homepage.
- Added the opt-in **Mirror Talk Editorial Home** page template.
- Added the seven-step Listen → Read → Explore → Reflect → Ask → Connect → Return journey rail.
- Added a coordinated abstract artwork system for the homepage, Ask Mirror Talk and topic discovery, with no synthetic people or embedded text.
- Added responsive AVIF artwork with optimized JPEG fallbacks and stronger text-legibility overlays.
- Added native, indexable category templates that turn WordPress categories into topic hubs.
- Added contextual episode reflection panels and a lightweight site-wide Ask entry point.
- Added editable contextual Ask prefill; content links never auto-submit a question.
- Replaced the API-driven public answer archive with an editor-curated Insights Library so private questions cannot be published automatically.
- Added a WordPress administrator warning when AIOSEO and SureRank are active together.
- Enabled responsive embeds, editor styles, wide alignment, post thumbnails and semantic HTML5 support.

## Ask Mirror Talk

- Brought the question flow substantially higher on mobile by compressing the hero and hiding statistics from the default Ask view.
- Added a native privacy and safety disclosure beside the question field.
- Changed product analytics from automatic collection to explicit opt-in consent.
- Replaced inaccurate anonymity language with a precise explanation of question processing, local notes and analytics.
- Removed personalized FAQ structured-data injection from private answers.
- Preserved reduced-motion and increased-contrast behavior.

## Safety

- Added detection for direct acute-distress language such as “I want to die” and “I can’t go on.”
- Replaced terse self-harm blocking copy with immediate, compassionate human-support guidance.
- Removed raw blocked-question content from application log messages.
- Added regression tests for crisis detection and privacy-conscious logging.

## Validation

- Full Python suite: 155 passed, 3 skipped.
- JavaScript syntax: passed for core, premium, analytics and service-worker files.
- Theme JSON: parsed successfully.
- Desktop and 390 × 844 mobile visual reviews completed for the homepage and Ask interface.
- PHP CLI was not installed in the local environment, so PHP lint remains a staging check.

## Deployment package

`wordpress/astra-child-v6.1.0.zip`

The homepage template is intentionally opt-in. Install the package on staging,
select **Mirror Talk Editorial Home** for a draft page, review content and links,
then make it the static homepage only after approval.
