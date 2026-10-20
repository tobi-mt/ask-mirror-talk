# Mirror Talk 8.22.0

## RSS Editorial Pipeline

- Inventories the complete official podcast feed in bounded, restartable background batches.
- Reconciles episodes using an RSS identity, exact audio URL, or exact normalized title; ambiguous records are never guessed.
- Creates review-only WordPress drafts for confidently missing episodes, either individually or through an explicit background import.
- Preserves the official title, audio, publisher notes, publication evidence, transcript declaration, chapter declaration and source URL.
- Never publishes automatically and never generates transcript text, quotations, guests, credentials or factual claims.
- Hands new drafts to the Editorial Composer and Story Studio with the exact episode audio and a compact, editorial or deep-dive presentation profile.
- Provides an Intelligence submenu with progress, evidence, state, review links and safe controls.

## Reliability

- The scan performs no post mutations.
- Imports are idempotent and duplicate-protected.
- Work is isolated from editor requests and split into batches of 20 episodes.
- A failed feed request stops cleanly and records the reason without affecting the public website.
