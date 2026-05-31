# Ask Mirror Talk v5.9.31 - Reflection Card Headline Reliability

Released: 2026-05-31  
Status: Draft

## Summary
v5.9.31 improves reflection card headline selection so cards stay grounded in the actual answer and question instead of falling back too early to generic theme lines.

## Highlights

1. Question-aware headline ranking
- Increased the influence of question relevance during share-headline scoring.
- Helps answer-derived lines outrank polished but off-topic candidates.

2. Safer fallback behavior
- Synthetic theme fallback lines no longer compete with answer-derived headline candidates during normal selection.
- Theme fallback remains available as a true last resort.

3. Editorial family consistency
- Editorial and editorial_serene card families now use the shared fit-aware selector.
- Prevents those families from drifting into generic relationship or healing slogans when stronger source-grounded text fits.

4. Sanitization hardening
- Narrowed attribution cleanup so valid lines like "Failure teaches us..." are preserved.
- Keeps backend and frontend headline cleanup behavior aligned.

## Version + Packaging
- Project/theme/widget version markers bumped to 5.9.31.
- Service worker cache key bumped to amt-v5.9.31.
- WordPress release artifact: astra-child-v5.9.31.zip

## Validation Snapshot
- Focused headline, sanitization, and cache tests passed.
- Reflection card fixture validation passed for auto and editorial families after the selector change.
- JavaScript syntax checks passed for the child theme widget.

## Notes
- This release is specifically aimed at better reflection-card relevance and more trustworthy share output.
