# Mirror Talk 8.26.0

## RSS Editorial intelligence

- Replaces the fixed 180-word RSS-note rejection with a media-aware factual quality gate.
- Enriches concise official notes into structured episode pages without presenting generated text as a transcript.
- Reprocesses pipeline-owned drafts and quarantined episodes during the automatic workflow.
- Preserves editor-owned changes and keeps a ten-entry content rollback history.
- Re-runs the Editorial Composer, SEO metadata, guarded taxonomy and discovery workflow before publication.
- Keeps episodes quarantined when identity, primary media, composition or protected editor content cannot be verified.

## Listening and video

- Requires the exact RSS audio player on ingested episode pages.
- Uses a verified episode-specific YouTube URL when present and the latest channel video as the controlled fallback.
- Repairs missing automatic podcast and YouTube decisions across legacy posts in bounded background batches.
- Preserves explicit editorial media overrides.

## Verification

- WordPress experience regression suite: 79 passed.
- Release quality gate: passed with no failures.
- PHP CLI syntax validation was unavailable in the local runtime; production deployment should retain the normal staging activation and fatal-error smoke check.
