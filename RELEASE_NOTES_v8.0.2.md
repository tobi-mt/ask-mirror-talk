# Mirror Talk Theme 8.0.2 — Release Hardening

This release supersedes v8.0.0 and v8.0.1.

- Includes the v8.0.1 LocalBusiness PHP parse correction.
- Validates every PHP file in the child theme before packaging.
- Makes podcast-player state storage non-fatal when a browser disables local storage.
- Guards the dialog fallback for older browser engines.
- Changes the full-site link crawler to persistent batches of 30 URLs with shorter timeouts, preventing long WordPress requests on constrained hosting.
- Adds a fallback when the optional PHP `mbstring` extension is unavailable.
- Preserves link-health history while capping stored records.

Staging must be restored with this package before visual, interactive and field-performance sign-off can be completed against the real WordPress runtime.
