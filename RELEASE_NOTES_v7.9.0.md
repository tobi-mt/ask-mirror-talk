# Mirror Talk Theme 7.9.0 — Native SEO Authority

Mirror Talk Intelligence & SEO is now the default and authoritative SEO system.

## Shared-link previews

- Posts and pages automatically use their WordPress featured image on Facebook, LinkedIn, WhatsApp, X and other Open Graph consumers.
- The theme outputs the image URL, secure URL, MIME type, width, height and meaningful alt text.
- Pages without a featured image receive the branded 1600 × 900 Mirror Talk atmospheric fallback.
- The editor's Mirror Talk SEO panel now shows the image that will represent the shared link.
- `summary_large_image` Twitter cards include the same title, description, image and alt text.

## Native premium SEO coverage

- Editable search/social titles and meta descriptions.
- Canonical URLs, including paginated archive canonicals.
- Open Graph site, locale, page and article metadata.
- Article publication, modification, section and tag metadata.
- Article, PodcastEpisode, VideoObject, Organization, WebSite and Breadcrumb structured data.
- Featured images represented as full `ImageObject` schema.
- Search-engine directives supporting large image previews and unrestricted snippet/video previews.
- Per-page noindex controls that also exclude the page from the Mirror Talk sitemap.
- Image-aware XML sitemap entries.
- Existing first-party analytics, Core Web Vitals, broken-link monitoring, content guidance and weekly SEO audits remain active.

## AIOSEO transition

- Mirror Talk no longer suppresses itself when AIOSEO is installed.
- The official `aioseo_disable` master filter suppresses AIOSEO frontend output during staging verification, preventing duplicate canonical, social and schema markup.
- The previous administrator conflict warning has been removed.
- Once staging is verified, AIOSEO can be deactivated. It should not be deleted until any historical settings or redirects you want to preserve have been reviewed.
