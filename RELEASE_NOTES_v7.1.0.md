# Mirror Talk 7.1.0

## Homepage

- Featured conversations now run as a fully automated editorial sequence with no visible control buttons.
- The slider is substantially shorter on desktop and explicitly rendered at a compact 420px mobile height.
- Autoplay still pauses when off-screen, when the tab is hidden and for reduced-motion visitors.
- The time-aware homepage greeting now appears on first visits and returning visits across desktop and mobile layouts.

## Newsletter

- Newsletter invitations now open a direct name-and-email form inside the existing calm modal.
- Submissions are validated, nonce-protected, honeypot-protected, consent-stamped and stored as private `mt_subscriber` records in WordPress.
- Existing emails are deduplicated and administrators receive a new-subscriber notification.
- No contact-page redirect remains.

## Insights

- The Insights page is restored as the visitor's private Ask Mirror Talk archive.
- It reads the same `amt_saved_insights` browser library used by Ask Mirror Talk and never substitutes blog posts.
- An empty state explains how to save the first insight.

## Blog

- Astra's inherited posts-page title/banner is disabled on the blog index.
- Additional compatibility CSS removes legacy archive/page-builder headers above the native dark blog experience.
