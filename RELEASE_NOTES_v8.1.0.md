# Mirror Talk Theme 8.1.0 — Live Staging Audit Corrections

This release addresses defects found by testing the deployed v8.0.2 staging runtime rather than relying only on local fixtures.

## Corrected

- Makes the editorial Mirror Talk homepage the owned front-page template automatically, restoring the welcome, atmospheric hero, journey rail, adaptive slider and topic pathways on every browser without a manual page-template assignment.
- Creates a resilient `/blog/` route and renders the real conversations archive instead of redirecting visitors to the homepage.
- Serves the main, Google News and video sitemaps even when host rewrite rules have not refreshed correctly.
- Removes duplicate canonical, description, Open Graph, Twitter and JSON-LD output from parallel SEO suites and emits one authoritative Mirror Talk SEO graph.
- Gives Ask Mirror Talk a real semantic H1 while preserving its appearance.
- Sets intentional front-page, blog and topic search titles independent of legacy SEO-plugin filters.

## Performance hardening

- Stops loading the redundant Astra parent `style.css` request because Astra already provides its generated theme stylesheet.
- Removes legacy page-builder, contact-form, MediaElement and Jetpack podcast assets from the owned homepage, where none of those components are rendered.
- Preserves the native Mirror Talk player, slider, analytics and consent-aware YouTube module.

## Live audit findings that require deployment verification

The deployed v8.0.2 homepage returned successfully but still rendered the legacy page, `/blog/` redirected to home, three sitemap routes returned 404, duplicate SureRank/Mirror Talk metadata was present, and the legacy homepage delivered dozens of unnecessary assets. Version 8.1.0 directly corrects those findings. A final field audit must be run after v8.1.0 is active on staging.
