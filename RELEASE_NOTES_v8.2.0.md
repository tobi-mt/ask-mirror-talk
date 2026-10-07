# Mirror Talk Theme 8.2.0

## First-party forms

- Replaces the SureForms output on Contact and Join Us with a responsive Mirror Talk form.
- Stores each accepted message privately under **Tools → Contact messages** and emails the WordPress administrator with a direct reply address.
- Protects submissions with WordPress nonces, signed form age, dual-window rate limiting, a honeypot, strict validation and excessive-link filtering.
- Removes SureForms and Contact Form 7 frontend assets from the owned contact experience.
- Preserves the existing first-party newsletter, double opt-in and subscriber management, while making signed forms safe for normal page-cache lifetimes.

## AI and source discovery

- Explicitly permits OAI-SearchBot, ChatGPT-User, GPTBot, ClaudeBot, PerplexityBot, Googlebot and Bingbot to crawl public content while keeping `/wp-admin/` unavailable.
- Adds `/mirror-talk-ai-guide/`, a concise first-party source map with entity context, authoritative collections, recent articles and citation guidance.
- Advertises that guide in page metadata without depending on AIOSEO's intercepted `/llms.txt` route.

## Important limitations

- Search and AI providers decide whether a page is indexed, ranked or cited; technical eligibility cannot guarantee a citation.
- Google Search Console OAuth, Bing ownership/API access and verification tokens require the site owner's accounts and cannot be completed safely by a theme alone.
- Reliable outbound email still depends on the hosting mail system or an authenticated SMTP/transactional email provider.

## Validation

- 22 PHP files parsed successfully.
- All theme JavaScript passed syntax validation.
- 185 tests passed and 3 were skipped.
