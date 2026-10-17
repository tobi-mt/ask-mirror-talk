# Mirror Talk 8.20.0

## Consolidated reliability release

This release includes the complete Story Studio runtime repair from 8.19.1 and folds it into a broader release gate so it can be validated as one candidate.

- Restores Story Studio JavaScript, podcast and video interactions, and Intelligence event collection.
- Keeps Composer navigation focused on meaningful H2 sections.
- Removes redundant listening and related-content panels when the Composer already supplies the same journey.
- Formats RSS durations for people rather than exposing raw seconds.
- Prunes obsolete link-health records when an anchor no longer exists, preventing repaired historical links from remaining in the broken-link count.
- Continues conservative link repair only after a definitive repeated failure, preserving anchor text and WordPress revisions.
- Adds live runtime probes for both Composer HTML and the Story Studio JavaScript asset.
- Automatically schedules a fresh quality and command-centre analysis after the release background repairs begin.
- Formats Core Web Vitals predictably in the Intelligence dashboard.

No URL, quotation, transcript, embed or factual statement is rewritten by the Composer. Existing editor opt-outs and rollback history remain intact.
