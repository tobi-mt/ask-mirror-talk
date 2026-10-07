# Mirror Talk Theme 8.2.2

## Complete search data connections

- Replaces raw access-token fields with a complete Google Search Console OAuth 2.0 authorization-code flow.
- Requests offline access, encrypts client credentials and refresh tokens with authenticated AES-256-GCM, renews expired access automatically and validates OAuth state.
- Discovers verified Search Console properties, selects the matching Mirror Talk domain or URL-prefix property, synchronizes final query/page/date performance rows and submits all Mirror Talk sitemaps.
- Connects Bing Webmaster Tools using its account API key, discovers and verifies the matching site, synchronizes query performance and submits all Mirror Talk sitemaps through Bing's supported JSON/HTTP API.
- Adds connection health, last synchronization, verified property, row counts, actionable errors, manual sync and disconnect/credential-erasure controls.
- Migrates a previously stored Bing key into encrypted storage and removes obsolete raw Google/Bing secret fields.
- Scheduled synchronization continues twice daily after the one-time owner authorization.

## Setup required by the providers

- Google requires a Web application OAuth client with the Search Console API enabled and the exact callback URL shown in the Mirror Talk SEO dashboard.
- Bing requires an API key generated under Bing Webmaster Tools → Settings → API Access.
- Mirror Talk cannot create either provider credential or grant itself account access; the site owner completes each provider's one-time consent.
