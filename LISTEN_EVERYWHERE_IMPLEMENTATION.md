# Listen Everywhere implementation checklist

This checklist converts the Master Website Builder Prompt into a guarded Mirror
Talk release plan. `/listen/` is the listening and platform hub;
`/podcast-episodes/` remains the editorial episode archive.

## Phase 1 — identity, routes and verified data

- [x] Preserve `/podcast-episodes/` and give `/listen/` a distinct purpose.
- [x] Register a stable `/listen/` rewrite and canonical route.
- [x] Create one sanitized platform registry shared by every public component.
- [x] Seed only the already approved Apple Podcasts, Spotify, YouTube and RSS destinations as public.
- [x] Keep all other proposed destinations disabled and unverified until reviewed.
- [x] Record status, verification method, last checked date and health separately.

## Phase 2 — listener experience

- [x] Build a native, responsive `/listen/` page.
- [x] Reuse the existing RSS feed cache and accessible native audio controls.
- [x] Add prioritized platform cards and a progressive “More ways” group.
- [x] Provide a browser-safe RSS fallback without claiming native availability.
- [x] Add a homepage listening invitation.
- [x] Add a reusable episode-page listening component.
- [x] Drive the footer and follow modal from the same registry.

## Phase 3 — privacy-conscious intelligence

- [x] Reorder—not hide—compatible services using coarse device information.
- [x] Never claim that an application is installed.
- [x] Remember only an explicitly chosen preferred platform on the device.
- [x] Keep every verified service accessible regardless of recommendation.
- [x] Record platform selections through the existing consent-gated first-party analytics.
- [x] Avoid fingerprinting, precise location and silent redirects.

## Phase 4 — administration and maintenance

- [x] Add a protected WordPress platform-management screen.
- [x] Sanitize URLs, labels, capabilities, statuses, order and enablement.
- [x] Add guarded server-side GET validation with timeouts and redirect limits.
- [x] Treat bot-blocking responses as review-needed, not automatically broken.
- [x] Never automatically disable a public destination.
- [x] Add a daily scheduled validation event and a manual “check now” control.

## Phase 5 — SEO, accessibility and regression gates

- [x] Add a unique title, description and canonical URL for `/listen/`.
- [x] Extend the existing PodcastSeries graph with only public verified profiles.
- [x] Use one H1 and semantic section headings.
- [x] Preserve reduced-motion, keyboard, focus and touch-target support.
- [x] Keep the page server-rendered and usable without JavaScript.
- [x] Keep trademark imagery optional until an approved icon asset is supplied.
- [ ] Verify every additional platform against the RSS feed or podcast GUID.
- [ ] Add approved official platform icon assets after trademark review.
- [ ] Run staging checks in current Safari, Chrome, Firefox, Edge, iOS and Android.
- [ ] Validate public schema after staging deployment.
- [ ] Record field Core Web Vitals after sufficient real-user traffic.

Items left unchecked require external platform evidence or deployed-browser data;
the theme must not fabricate those results.
