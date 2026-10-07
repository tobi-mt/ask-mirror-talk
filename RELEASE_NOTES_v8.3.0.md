# Mirror Talk Theme 8.3.0

## Mirror Talk Intelligence

This release adds a separate, native WordPress administration dashboard at **Mirror Talk Intelligence**.

### Reporting

- Page views, consented unique visitors and top pages
- Referrer and campaign acquisition
- Internal page-to-page journeys
- Newsletter and contact conversions
- Device mix and privacy-safe country reporting when the host supplies a country header
- Podcast plays, completions, completion rate and episode performance
- Core Web Vitals distributions and averages
- Broken-resource observations
- Google and Bing clicks, impressions, queries and average position
- SEO link health, redirect counts and audit status
- AI readiness, crawler observations and recognizable AI referrals
- 7, 30, 90 and 365-day filters with equal-period comparisons
- Responsive charts, filterable tables and a complete CSV export
- Stored weekly reports plus an administrator-triggered “Generate report now” action

### First-party collection and privacy

- Analytics events now go to the website's own WordPress REST endpoint and dedicated database table.
- Only allow-listed events and fields are accepted.
- Visitor identifiers are irreversibly HMAC-hashed before storage.
- Raw IP addresses are used only for a one-minute abuse-control transient and are never written to the analytics table.
- No questions, reflection text, email addresses or page contents are accepted.
- Existing consent remains authoritative: collection stays off until a visitor chooses **Allow insights**.
- Data older than 400 days is removed automatically.

Historical events held by the previous remote collector are not silently copied into WordPress. Native reporting starts accumulating after this version is activated.
