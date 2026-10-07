# Mirror Talk Theme 7.6.0 — Cross-browser Consistency Release

This release addresses the root cause of devices rendering different generations of staging.

## What the audit proved

- Staging HTML was still serving release **6.1.0**.
- The child-theme file on the same server was **7.4.1**.
- A cache-bypassing query still returned the old HTML.
- Therefore Hostinger's full-page/CDN layer—not responsive CSS—was serving an obsolete document.

## Durable safeguards

- Adds `X-Mirror-Talk-Release` to WordPress responses.
- Adds `<meta name="mirror-talk-release">` to every public page.
- Adds the uncached `/mirror-talk-release.json` diagnostic endpoint.
- Retires full-site service workers and deletes historical `amt-*` browser caches.
- Performs one controlled reload when a page is still controlled by a retired worker.
- Keeps asset versions tied to both the theme release and file modification time.
- Removes the old global cream PWA paint override that could flash before the dark theme.
- Retains the staging no-store response policy and automatic LiteSpeed purge hooks.
- Restores browser zoom by removing the inaccessible `maximum-scale=1` viewport restriction.
- Corrects the dark-footer copyright contrast.
- Preloads the homepage atmosphere artwork and adds responsive image sizing to episode cards.
- Re-flushes topic and sitemap routes on every theme release instead of relying on a stale one-time flag.
- Hides the obsolete blog-page heading when the editorial archive owns the page title.

## Baseline staging audit

Before deployment, Lighthouse measured the cached staging homepage at **94 desktop performance** but only **48 mobile performance**. Mobile LCP was 5.4 seconds and total blocking time was 2.46 seconds. The cached document also failed zoom accessibility, footer contrast and crawlability checks. The crawlability result is acceptable only while staging is intentionally blocked from indexing; it must be rechecked before production launch.

## Required deployment step

After replacing the installed child theme with v7.6.0, purge **all** Hostinger CDN/cache-manager caches once. The audit shows the CDN currently serves old HTML before WordPress executes, so PHP cannot purge that already-intercepted request by itself.

Verify deployment at `/mirror-talk-release.json`. It must report `"release":"7.6.0"` before cross-device acceptance testing begins.
