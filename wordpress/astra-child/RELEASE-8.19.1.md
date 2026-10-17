# Mirror Talk 8.19.1

## Story Studio runtime repair

- Fixes the Story Studio asset eligibility check so it no longer asks whether WordPress is inside the content loop during the earlier script-enqueue phase.
- Restores the privacy-enhanced YouTube play control, podcast play/completion measurement, Composer navigation measurement and CTA measurement on composed posts.
- Keeps the script excluded from the homepage, reflection flows, trust documents, preserved-format documents and explicitly disabled Story Studio pages.
- Adds an automated regression check that rejects any future loop-dependent enqueue condition.
- Keeps on-page navigation to meaningful H2 sections instead of utility headings such as sharing controls.
- Formats numeric RSS durations as readable times.
- Removes duplicated related-content and listening-platform panels when Story Studio already provides the same next step.

The visible Composer HTML and stored source content are unchanged. No URL, quotation, transcript, embed or factual statement is rewritten.
