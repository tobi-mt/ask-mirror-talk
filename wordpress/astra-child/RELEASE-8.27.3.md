# Mirror Talk 8.27.3

## Semantic legacy-list repair

- Repairs prose-length H2–H6 elements nested inside numbered or bulleted list items at render time.
- Preserves every word while rendering the item as readable body copy rather than an oversized heading.
- Retains a short colon-delimited label as bold lead-in text when one is present.
- Leaves legitimate concise headings and stored WordPress content untouched.

## Production evidence

- Version 8.27.2 successfully recovered and publicly verified document #6795 after its earlier template-validation quarantine.
- Verified migrations increased from 10 to 11 and the quarantine count returned to zero.
- The recovered page returned a complete semantic document, podcast player, privacy-respecting video, valid external links and responsive site navigation.
