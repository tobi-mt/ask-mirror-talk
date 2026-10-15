# Mirror Talk Theme 8.14.2

Release 8.14.2 is a regression and performance hardening update for 8.14.0.

## Fixed

- Restored the **Mirror Talk Intelligence** top-level dashboard and made its
  Overview page the stable parent for Listening Platforms, Editorial Composer,
  and Taxonomy Intelligence.
- Corrected the Listening Platforms menu so it no longer replaces or redirects
  the Intelligence parent item.
- Restored WhatsApp and Patreon links to the public follow dialog.

## Performance hardening

- Removed an accidental database write from the cached podcast-feed path.
- Moved cron recovery checks from every public request to theme activation and
  authenticated admin requests.
- Added a short-lived coherent cache for the Intelligence dashboard's grouped
  analytics queries.
- Capped the initial Quality Guardian table to the 50 highest-priority issues,
  while retaining the full stored audit, to reduce admin-page DOM and rendering
  work.
- Removed Contact Form 7, Hostinger Reach, MediaElement, Spectra/UAGB, Jetpack
  form, and WordPress block-library assets from Mirror Talk-owned routes where
  those components are not rendered.
- Kept the Editorial Composer asynchronous on post save and moved its backfill
  recovery check out of public traffic.
- Added a truthful generic accessible title to legacy iframes that omitted one,
  without rewriting stored content or inventing media details.

## Discovery and listening

- Added the canonical `/listen/` destination to titles, descriptions, sitemap,
  weekly checks, `llms.txt`, and AI discovery output.
- Kept platform destinations in one verified registry used by the website,
  footer, dialogs, and admin health screen.

## Verification

- 211 automated tests passed; 3 skipped.
- Focused WordPress experience and Listen Everywhere tests: 80 passed.
- Release quality gate passed.
- All JavaScript files passed `node --check`.
- All 34 PHP files parsed successfully.
- CSS structural validation passed.

## Deployment note

Upload and activate `astra-child-v8.14.2.zip`, then clear every cache layer
(WordPress/cache plugin, Hostinger/CDN, and browser cache). No content migration
or template reassignment is required.
