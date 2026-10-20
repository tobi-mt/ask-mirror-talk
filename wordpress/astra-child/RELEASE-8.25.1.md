# Mirror Talk 8.25.1

Production verification of 8.25.0 found one Classic Editor edge case: a
non-breaking-space entity placed immediately after a plain-text URL could be
captured as part of the generated destination.

This maintenance release keeps `&nbsp;`, `&#160;` and equivalent hexadecimal
non-breaking-space entities outside the hyperlink. Display spacing is preserved,
while the generated destination remains the exact validated website address.

All 8.25.0 security, crawler-health, accessibility, rollback and non-destructive
content protections remain unchanged.
