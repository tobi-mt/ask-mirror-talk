# Mirror Talk 8.29.0

Elementor migration completion and recovery release.

## What changed

- Counts provisional and quarantined migration jobs even after Elementor source metadata has been removed.
- Repairs heading-level jumps deterministically and retries the document through the full preview and live verification stages.
- Preserves rollback snapshots without WordPress slash corruption and recognizes the exact legacy escaping transformation used by earlier releases.
- Rechecks recoverable live-stage snapshot failures automatically after deployment.
- Converts residual template shortcodes, then retires only templates proven to be unreferenced.
- Protects templates with Theme Builder conditions or references from active content.
- Recalculates residual dependencies and refreshes the dashboard after cleanup.
- Marks automatic migration complete only after documents, template shortcodes, and safe template retirement all pass.

## Deployment behaviour

The migration engine version bump automatically resumes its guarded background workflow. Elementor must remain active until the Migration Centre reports **SAFE TO DEACTIVATE**.

## Validation

- 227 tests passed; 3 skipped.
- Release quality gate passed.
- All 40 PHP files parsed successfully.
