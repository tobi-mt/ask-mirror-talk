# Mirror Talk 6.3.0 — Listen Everywhere

Release date: 2026-10-02

## Listening companion

- Added a persistent Listen control opposite Ask Mirror Talk on every public page.
- Reads the latest episodes from the official podcast RSS feed and caches the normalized queue for six hours.
- Opens with the latest episode selected and expands into an eight-episode queue.
- Supports native audio controls, play-from-queue behavior and browser Media Session metadata.
- Uses metadata-only audio preloading; no episode is downloaded or played before visitor interaction.
- Responsive panel is scroll-contained and remains usable at 390 px mobile width.

## Intentional invitations

- Ask Mirror Talk now opens a calm explanatory invitation before entering the reflection experience; the original link remains the no-JavaScript fallback.
- Added accessible newsletter and podcast-platform dialogs.
- Added verified Apple Podcasts, Spotify, YouTube, WhatsApp Channel and Patreon destinations.
- Newsletter invitations appear only on individual posts after both 45 seconds and 55% reading depth.
- The automatic newsletter invitation is frequency-capped to once every 21 days and never competes with an open player or dialog.
- All dialogs use native modal semantics, visible close controls, Escape support and backdrop dismissal.

## Configuration

Go to **Appearance → Customise → Mirror Talk listening & connections** to set:

- Podcast RSS feed URL
- Newsletter signup URL

The newsletter destination defaults to the Contact page until the production newsletter form URL is configured.

## Validation

- Full Python suite: 157 passed, 3 skipped.
- JavaScript syntax: passed.
- Desktop and 390 × 844 mobile player checks: passed with no horizontal overflow.
- Queue expansion and five-destination follow dialog: visually and interactively verified.
- PHP CLI is not installed locally, so PHP lint remains a staging check.

## Deployment package

`wordpress/astra-child-v6.3.0.zip`
