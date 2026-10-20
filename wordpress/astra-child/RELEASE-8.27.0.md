# Mirror Talk 8.27.0

## Elementor Migration 2.0

- Replaces direct conversion with a resumable `prepare → preview → commit → live verification` state machine.
- Shows pending, in-progress, quarantined, verified and stale-metadata totals separately.
- Excludes empty or obsolete Elementor metadata from the actionable migration count and removes that debris in a bounded background task.
- Normalizes duplicate H1 elements, heading jumps, plain URLs and legacy content structure before a candidate can proceed.
- Creates a private, no-index conversion preview and validates both desktop and mobile responses before committing.
- Creates a checksum-protected snapshot immediately before every mutation.
- Rolls back any conversion that fails public verification and retries recoverable failures with bounded backoff.
- Quarantines only the affected document after the retry ceiling; the remaining queue continues automatically.
- Recovers lost scheduled stages after PHP termination, cron interruption or host restart.
- Marks a document migrated only after its public URL renders the owned document marker successfully in desktop and mobile checks.
- Adds per-document preview, retry and restoration controls plus a retained global and per-document audit ledger.

## Editorial presentation

- Reduces oversized long-form titles and prevents broken mid-word wrapping across desktop and mobile layouts.
- Improves introduction extraction by reading real prose paragraphs instead of concatenating headings, controls and body text.
- Advances Editorial Composer to 2.5.0 so existing content is refreshed through the guarded background backfill.

## Verification

- PHP parser validation: passed for the migration engine and Editorial Composer.
- WordPress experience regression suite: 80 passed.
- Release quality gate: passed with no failures.
