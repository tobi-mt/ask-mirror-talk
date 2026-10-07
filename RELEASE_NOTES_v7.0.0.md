# Mirror Talk 7.0.0 — Intelligence & SEO

This release introduces a first-party measurement and native SEO layer spanning the WordPress theme and Ask Mirror Talk backend.

## Measurement

- Consent-gated page views, visitors, referrals, campaigns and internal journeys
- Podcast plays, pauses, 25/50/75% progress and completions
- Episode discovery events and protected listening reports
- LCP, CLS and INP field measurements
- Resource failure and weekly priority-link monitoring
- Strict event and metadata allow lists; private questions and page content are rejected

## Native SEO

- Search titles and editable descriptions
- Canonical URLs, Open Graph and large Twitter cards
- Organization, WebSite, Article, PodcastEpisode and Breadcrumb structured data
- XML sitemap for posts, pages, categories, tags and all `/explore/` topic hubs
- `robots.txt` sitemap discovery
- WordPress editor content-quality and internal-link prompts
- Weekly email audit of priority URLs, redirects and failures

## Safe migration

When AIOSEO, SureRank, Yoast or Rank Math is active, Mirror Talk suppresses its own head metadata to prevent duplicates. Deactivate the external suite only after verifying the native output in staging. Analytics and the proprietary sitemap remain available during migration.

## External truth sources

The dashboard reports first-party behavior immediately. Verified Google/Bing impressions, queries, positions and indexing coverage still require connecting their webmaster APIs because those data originate inside the search engines.

The backend exposes protected connector endpoints at `/api/intelligence/search-performance/import` and `/api/intelligence/search-performance`. Set a strong `ANALYTICS_HASH_SALT` in production before deploying; website analytics store a rotating one-way network token rather than a raw visitor IP.

## Deployment order

1. Deploy the updated backend so the intelligence collector and reporting routes are live.
2. Set `ANALYTICS_HASH_SALT` and confirm `ALLOWED_ORIGINS` contains the production and staging WordPress origins.
3. Upload and activate `astra-child-v7.0.0.zip` in staging.
4. Save **Settings → Permalinks** once, then verify `/mirror-talk-sitemap.xml`.
5. Verify consent accept/decline, page-view collection, podcast milestones and `/admin/intelligence`.
6. Keep the existing SEO plugin active during comparison. When native titles, canonical URLs, social cards and schema pass staging inspection, deactivate the external SEO plugin; Mirror Talk then becomes authoritative automatically.
