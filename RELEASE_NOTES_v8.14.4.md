# Mirror Talk 8.14.4

This is a focused performance and intelligence-integrity follow-up to 8.14.3.

## Improvements

- Replaces legacy Elementor YouTube autoplay widgets with a fast, accessible click-to-load facade.
- Loads legacy videos from YouTube's privacy-enhanced domain only after an explicit visitor action.
- Removes unrelated form-plugin and starter-template assets independently instead of retaining every form stack when one valid form exists.
- Prevents WordPress administration and login destinations from entering first-party journey analytics.
- Filters previously recorded private administration paths from journey reports.

## Safety

- Stored post and page content is not rewritten.
- Existing forms keep the assets belonging to their actual form family.
- Mirror Talk's modern YouTube Studio and Editorial Composer video components are unchanged.
- URL structures, canonical URLs and editor-authored taxonomy are unchanged.

## Verification

- Local release quality gate: passed.
- Focused WordPress/theme regression suite: 89 passed.
- JavaScript syntax checks: passed.
- Full repository pytest collection is currently blocked by an unrelated local dependency mismatch (`httpx.BaseTransport` absent from the installed mixed Python packages).
