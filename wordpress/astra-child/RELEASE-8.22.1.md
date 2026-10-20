# Mirror Talk 8.22.1

## Autonomous RSS editorial workflow

The manual scan, comparison, draft and publication sequence is now a guarded
background state machine.

- Runs a full reconciliation every day and can also be started immediately.
- Processes at most five write operations per batch to protect the host and the editor.
- Creates only evidence-backed drafts and sends them through the Editorial Composer.
- Preserves the original feed publication timestamp and exact episode audio.
- Publishes automatically only when source identity, title completeness, source depth,
  metadata, Composer preservation and placeholder checks all pass.
- Keeps ambiguous, thin or incomplete episodes private and records each failed gate.
- Never modifies or auto-publishes an editor-owned draft merely because its title is similar.
- Displays published, quarantined, drafted, matched, missing and error totals in the
  RSS Editorial Pipeline dashboard.

Automatic publication remains deterministic. It does not invent transcripts, quotes,
people, credentials, summaries or facts to force an episode through the gate.
