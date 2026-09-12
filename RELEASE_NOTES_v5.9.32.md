# Ask Mirror Talk v5.9.32 - 10k DAU Measurement Foundation

This release makes the 10,000 daily-active-user milestone measurable and restores a clean release gate.

## Added

- Anonymous `app_opened` telemetry with persistent device IDs and web/PWA entry context.
- Authenticated `/api/analytics/growth` scorecard with daily active users, askers, answered users, value users, referrers, conversion rates, and day-1 retention.
- A focused 30-day execution plan and scale gates in `MILESTONE_10000_DAU.md`.
- Direct access to the growth scorecard from the admin dashboard.

## Improved

- Citation relevance now recognizes concise semantic paraphrases instead of depending too heavily on exact phrase overlap.
- Admin dashboard analytics data remains backward-compatible when origin cohorts are unavailable.
- Product-event tests cover device-ID propagation.
- Heavy widget assets load only on the Ask Mirror Talk page or pages that contain its shortcode.
- Blocked-notification instructions appear only when a user deliberately opens notification settings.
- Onboarding privacy language now accurately distinguishes local notes from anonymously processed questions.
- Programmatic onboarding questions update the counter and question coach immediately.
- Question-coach suggestions and singular citation-support copy use natural grammar.
- Audio previews request metadata first instead of eagerly preloading the full episode.

## Verification

- 137 tests passed and 3 skipped.
- Python compilation, JavaScript syntax validation, and `git diff --check` passed.
