# Deployment Package v5.8.8

Release date: 2026-05-15
Package: astra-child-v5.8.8.zip

## What This Release Includes

- Version refresh for the Ask Mirror Talk backend and WordPress child theme.
- Service worker cache/version bump to force clients onto the latest static assets.
- Packaging refresh for deployment as a new zip artifact.

## Version Bumps

- pyproject.toml -> 5.8.8
- wordpress/astra-child/style.css -> 5.8.8
- wordpress/astra-child/ask-mirror-talk.php -> 5.8.8
- wordpress/astra-child/ask-mirror-talk.js -> v5.8.8 marker
- wordpress/astra-child/ask-mirror-talk-premium.js -> v5.8.8 marker
- wordpress/astra-child/analytics-addon.js -> v5.8.8 marker
- wordpress/astra-child/sw.js -> CACHE_VERSION amt-v5.8.8
- wordpress/astra-child/sw.js -> BUILD_TIMESTAMP 2026-05-15T02:30:00.000Z

## Deployment Checklist

1. Upload astra-child-v5.8.8.zip.
2. Purge WordPress/CDN cache.
3. Confirm service worker update on mobile and desktop.
4. Confirm Ask flow still returns answer, follow-ups, and shareable headline.
