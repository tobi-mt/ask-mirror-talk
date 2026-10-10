# Mirror Talk 8.11.0 — Request-path performance release

- Removes synchronous Editorial Composer processing from public page requests.
- Removes archive backfill work from ordinary WordPress administrator requests.
- Makes post and page saves non-blocking: Composer v2 is queued after the save response instead of running inside it, preventing editor 504 timeouts.
- Retires all automatic legacy Composer triggers so a draft is never analyzed twice; historical reports and rollback data remain available.
- Continues Composer migration in smaller scheduled batches without resetting completed 2.1.1 work.
- Uses stale-while-revalidate podcast RSS data so an expired feed cache cannot hold up the page.
- Uses stale-while-revalidate YouTube metadata for the same reason.
- Removes anonymous admin-bar and Dashicons styles and unused Jetpack PayPal styling.
- Defers below-the-fold rendering with progressive `content-visibility` support.
- Keeps the persistent player, greeting, slider, Composer enhancements, analytics, SEO metadata and responsive design intact.
