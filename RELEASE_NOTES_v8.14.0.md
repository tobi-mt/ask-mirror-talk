# Mirror Talk 8.14.0 — Listen Everywhere

## Listener experience

- Adds a dedicated, server-rendered `/listen/` hub without replacing the
  `/podcast-episodes/` archive.
- Adds a native RSS-powered latest-episode player and recent-episode selector.
- Adds verified platform cards, an RSS fallback, mobile layouts and a calm
  Ask Mirror Talk bridge.
- Adds the same listening invitation to the homepage and individual posts.
- Makes the footer and existing follow dialog use the central platform registry.

## Trust and intelligence

- Adds a protected **Mirror Talk Intelligence → Listening platforms** screen.
- Public output is limited to enabled destinations with confirmed statuses.
- Proposed services remain disabled and unverified until a human verifies them.
- Adds guarded daily GET-based health checks; bot-blocking results require
  review and never automatically disable a destination.
- Adds coarse device-compatible ordering without app detection, fingerprinting,
  location inference, silent redirects or hidden options.
- Remembers only a visitor's explicit platform selection locally and records
  platform selections only through the existing consent-gated analytics.

## SEO and discovery

- Adds a unique title, description and canonical URL for `/listen/`.
- Adds the route to the XML sitemap, weekly priority audit, `llms.txt` and the
  AI source guide.
- Extends PodcastSeries `sameAs` from the public verified registry only.
- Queues `/listen/` for IndexNow when the release refreshes rewrite rules.

## Release safety

- No existing content or episode URL is changed.
- No unverified third-party URL is published.
- No autoplay is introduced.
- Official platform artwork remains optional until an approved asset is supplied.
- Local release gate, eight dedicated tests, JavaScript parsing, CSS parsing and
  PHP AST parsing pass. Deployed browser, schema and field-performance checks
  remain staging acceptance steps because they require the running WordPress site.
