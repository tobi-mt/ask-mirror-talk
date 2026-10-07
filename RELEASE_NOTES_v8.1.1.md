# Mirror Talk Theme 8.1.1

## Sitemap compatibility hotfix

- Moves the native main, Google News and video sitemap feeds to stable extensionless routes so external SEO suites cannot intercept them as their own `.xml` requests.
- Publishes the new sitemap routes in `robots.txt`, the SEO dashboard and the weekly SEO report.
- Removes the duplicate main-sitemap declaration previously added by two theme modules.
- Keeps the existing query-variable endpoints as resilient fallbacks.

## Public endpoints

- `/mirror-talk-sitemap/`
- `/mirror-talk-news-sitemap/`
- `/mirror-talk-video-sitemap/`
- `/llms.txt`

The response body and content type remain valid XML for all three sitemap routes; an `.xml` filename suffix is not required by search engines.

## Verification

- 21 PHP files parsed successfully.
- All theme JavaScript passed Node syntax checks.
- 39 focused WordPress experience tests passed.
