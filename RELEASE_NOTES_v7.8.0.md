# Mirror Talk Theme 7.8.0 — From the Mirror Talk Studio

This release introduces a lightweight, context-aware latest-YouTube experience immediately before the owned Mirror Talk footer.

## Experience

- Homepage: cinematic presentation without taking over the viewport.
- Blog, topic and taxonomy archives: compact landscape presentation.
- Individual posts: an editorial watch-next section after the article.
- Standard pages: compact presentation.
- Ask Mirror Talk and Insights: intentionally excluded to protect focused reflection flows.
- Mobile: media runs edge to edge while copy retains safe, readable gutters.
- Feed failure: degrades to a calm channel invitation instead of leaving a broken player.

## Intelligent playback

- Resolves the newest upload or Short from the official channel feed.
- Caches successful results for three hours and failures for fifteen minutes.
- Loads no YouTube iframe, API or thumbnail before external-media consent.
- Remembers media consent on the visitor's device.
- On later visits, starts muted only when at least half the player is visible.
- Pauses outside the viewport, in hidden tabs and when the podcast starts.
- Unmuting video pauses the podcast, preventing competing audio.
- Respects reduced-motion and Data Saver preferences.
- Provides an ordinary player and direct YouTube links when autoplay is blocked.

## Performance, SEO and control

- The YouTube API is requested only when the media is about to be used.
- WordPress Customizer controls allow the module to be disabled, the channel ID to be changed, or a specific video to be pinned temporarily.
- Mirror Talk Intelligence can record consent-gated video impressions, starts, 25/50/75% progress, completion, sound choices, autoplay blocking and errors.
- Native Mirror Talk SEO adds `VideoObject` data when the theme is authoritative; external SEO plugins remain protected from duplicate schema.

## Verification

- JavaScript syntax checks passed.
- Git whitespace validation passed.
- Full automated suite: 175 passed, 3 skipped.
- Live channel feed verified and currently resolves both standard uploads and Shorts.
- PHP CLI is not installed in this workspace, so final WordPress/PHP execution remains part of staging verification after upload.
