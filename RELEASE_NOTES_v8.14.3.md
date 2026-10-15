# Mirror Talk Theme 8.14.3

This is a narrowly scoped performance and contrast follow-up discovered during
the production verification of 8.14.2.

## Improvements

- Prevents Contact Form 7, Hostinger Reach, Jetpack form and Prosopo captcha
  front-end assets from loading on ordinary posts and pages that contain no
  supported form.
- Preserves every form asset when an actual shortcode, block or form container
  is present.
- Prevents primary and quiet buttons from inheriting lower-contrast global link
  colours.
- Caches the large XML sitemaps and AI discovery catalogues inside WordPress,
  with automatic invalidation after public content or taxonomy changes.
- Moves listen and topic rewrite recovery to activation and wp-admin recovery
  so public visits never trigger release-maintenance rewrite flushes.
- Stops Spectra from injecting per-post generated scripts into Mirror Talk-owned
  home, blog and topic templates, eliminating repeated missing-runtime errors.

## Production evidence behind the patch

- Homepage warm-cache Lighthouse: Performance 94, Accessibility 100,
  Best Practices 100, SEO 100.
- Listen page warm-cache Lighthouse: Performance 87, Accessibility 100,
  Best Practices 100, SEO 100.
- A representative legacy post exposed a globally enqueued captcha runtime that
  consumed roughly 3.3 seconds of main-thread work despite the post containing
  no form. Version 8.14.3 removes that runtime only from form-free documents.

## Verification

- 204 applicable automated tests passed, 3 skipped; one unrelated API test was
  deselected because this workstation has an incompatible global HTTPX package.
- Release quality gate passed.
- All 34 PHP files parsed successfully.
- JavaScript and CSS structural validation passed.
