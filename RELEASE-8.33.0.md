# Mirror Talk 8.33.0

Question of the Day reliability and experience release.

## What changed

- Replaces the conflicting site service-worker lifecycle with one root-scoped, cache-free push worker. It handles notifications only and cannot cache or intercept page requests.
- Adds consent-safe subscription recovery. A browser is recovered only when notification permission is already granted and the browser still has a subscription or a local record of prior consent. Explicit opt-outs are never reactivated.
- Adds subscription lifecycle health, delivery status, failure counts and a privacy-preserving audit ledger to the Railway backend.
- Makes QOTD job output distinguish total, active, eligible and currently due subscriptions.
- Adds **The Living Question** to the homepage and at a safe editorial boundary in eligible posts and pages.
- Keeps the card useful during API or page-cache delays with server-rendered fallback content and a small live refresh from the QOTD API.
- Adds a direct Living Mirror answer path, daily reminder control and first-party Intelligence events.
- Excludes sensitive, policy, contact, listening and Ask Mirror Talk flows from automatic insertion.
- Includes responsive, high-contrast and reduced-motion presentation for desktop and mobile.

## Deployment order

1. Deploy the Railway/API changes and run `scripts/migrate_push_subscription_health.py` once. The migration is additive and idempotent.
2. Activate `astra-child-v8.33.0.zip` in WordPress.
3. Purge host/CDN/page caches once so every browser receives the new worker URL and markup.

The production database migration was run successfully on 24 October 2026. Historical inactive subscriptions were left inactive; the site recovers only browser-confirmed prior consent.
