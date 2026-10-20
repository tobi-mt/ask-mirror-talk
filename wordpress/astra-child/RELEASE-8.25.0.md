# Mirror Talk 8.25.0

This release adds guarded automatic hyperlinks for plain-text website addresses
in existing and future posts and pages.

- Recognizes HTTP, HTTPS, `www.` and common bare-domain web addresses.
- Requires WordPress public-URL validation before creating a link.
- Leaves URLs already classified as definitively broken by the scheduled link
  crawler as plain text.
- Never changes URLs inside existing links, code, preformatted text, scripts,
  styles, buttons, textareas or SVG content.
- Preserves surrounding punctuation and the author's displayed address.
- Opens generated links in a new tab with `noopener noreferrer external`.
- Supplies an accessible warning that the link opens in a new tab.
- Styles generated links with visible hover and keyboard-focus states.
- Leaves stored `post_content` unchanged and supports per-document rollback via
  the Editorial Composer's “Valid plain-text website links” decision.
- Records the number of generated links in the Composer report and starts the
  normal bounded metadata backfill.

No synchronous network requests are introduced into page rendering. Actual
link health remains the responsibility of the existing scheduled crawler, so
the feature does not slow down public pages.
