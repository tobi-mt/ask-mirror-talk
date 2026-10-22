# Mirror Talk 8.30.1 — Clean Link Guardian

- Confirms every apparent HEAD failure with a bounded GET request before changing content.
- Uses verified internal redirects, old slugs, canonical published URLs and approved platform replacements when available.
- Removes only the dead hyperlink when no safe replacement exists, preserving its readable anchor content.
- Cleans dead internal and external links after two independent definitive failures.
- Tracks the same destination separately in every source document so no duplicate occurrence is hidden.
- Processes the existing broken-link backlog automatically in bounded background batches.
- Records each repair in the SEO automation history; WordPress revisions retain the prior article body for rollback.
- Never treats blocked, rate-limited, timed-out or server-error responses as definitively broken.
