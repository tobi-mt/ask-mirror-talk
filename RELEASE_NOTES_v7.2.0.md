# Mirror Talk 7.2.0 — Anti-spam hardening

No public form can honestly promise absolute immunity from automated abuse. This release adds layered controls so a single bypass does not create a valid subscription or an unbounded database-write path.

## Newsletter protection

- WordPress nonce verification
- Signed, time-limited form proof tied to the rendered page
- Two-second minimum form age and six-hour expiry
- Hidden honeypot with a neutral response
- Strict name, email and explicit-consent validation
- HMAC-anonymised network rate limits: 3 attempts/minute and 10/day
- Duplicate-address suppression without account-enumeration responses
- Cryptographically random, hashed, 48-hour confirmation tokens
- Double opt-in: records remain unconfirmed until the inbox link is opened
- Confirmation tokens are deleted immediately after successful use
- Administrator notifications occur only after inbox confirmation

## Analytics collector protection

- Strict event-name and metadata allow lists
- Configured-origin enforcement
- 120 events/minute per rotating anonymous network identifier
- Bounded in-memory limiter cleanup
- Maximum field lengths and rejection of nested arbitrary payloads
- Daily rotating HMAC network identifiers instead of raw IP storage

## Infrastructure still required

Set strong production values for `ALLOWED_ORIGINS` and `ANALYTICS_HASH_SALT`. Enable host/CDN request-size limits and rate limiting. Cloudflare Turnstile or another challenge should be reserved as an adaptive escalation if the WAF detects sustained abuse, rather than burdening every legitimate visitor.
