# Mirror Talk Theme 8.8.1

This staging hardening release follows the live 8.8.0 runtime audit.

## Fixes

- Keeps right-side desktop navigation submenus inside the viewport, removing hidden horizontal overflow.
- Restores one semantic page heading on the first-party Contact experience even when discarded legacy page-builder content contains an H1.
- Hides the floating Ask control while the mobile Living Mirror player is expanded, preventing it from covering player actions.
- Makes Automatic Editorial Composer coverage resilient when a host disables or delays loopback WP-Cron:
  - the current public post or page is composed on its first visit;
  - a small locked batch advances whenever an editor enters WordPress administration;
  - the existing scheduled batch remains the primary backfill mechanism.

## Verification

- Public 8.8.0 staging runtime confirmed across the home, blog, Ask Mirror Talk, contact, editorial-standards and corrections routes.
- Canonical URLs, descriptions, Open Graph images, Twitter cards, JSON-LD and release markers verified.
- Mobile homepage verified at 390 × 844 with the greeting, player and Ask control visible and no horizontal overflow.
- Desktop audit identified and resolved the closed-submenu overflow documented above.
