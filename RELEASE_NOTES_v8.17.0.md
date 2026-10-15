# Mirror Talk 8.17.0 — Runtime Resilience

## Request isolation

- Introduces a shared guarded-job runtime with locks, exception containment, duration logging and bounded history.
- Records fatal background failures for administrators without exposing them to visitors.
- Shows queued-work and recent-background-failure notices only inside Mirror Talk administration screens.
- Forces queued work to spawn promptly while keeping the initiating browser request short.

## Non-blocking administration

- Queues SEO learning, intelligence refreshes, weekly reports, connector synchronization and link crawls.
- Keeps Composer, Elementor migration, verification, backfill, media repair and metadata work behind guarded background execution.
- Splits weekly work into independent jobs so one provider cannot delay the others.

## Public performance containment

- Never fetches podcast RSS or YouTube feeds during a visitor or editor-page request.
- Uses last-known-good or bundled fallbacks while refreshing feeds asynchronously.
- Limits crawler batches to eight links, shortens remote timeouts and resumes from a cursor.
- Limits runtime probes and response sizes so unavailable services cannot monopolize PHP workers.

## Included corrections

- Contains the Elementor Migration Centre 504 fix from 8.16.2.
- Contains the dedicated Corrections and Editorial Standards presentation from 8.16.1.
