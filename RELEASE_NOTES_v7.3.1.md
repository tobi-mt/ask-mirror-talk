# Mirror Talk Theme 7.3.1

## Cross-browser staging delivery fix

The staging origin was correctly updated to v7.3.0, but Hostinger LiteSpeed and CDN edges were serving different cached HTML releases by browser user agent: v6.3.1, v7.2.0, and v7.3.0 were all observed simultaneously.

- Disables full-page caching specifically on `calm.mirrortalkpodcast.com`.
- Emits browser, CDN, surrogate, and LiteSpeed no-cache headers on staging.
- Purges LiteSpeed and WordPress caches automatically when the installed theme version changes.
- Fingerprints the core theme CSS and JavaScript using both the release version and each file's modification time.
- Removes a hard-coded `6.1.0` PWA version that could repeatedly register or retain the wrong service-worker URL.
- Advances the service-worker cache namespace to `amt-v7.3.1`.
- Removes optional-chaining syntax from the homepage/slider and listening companion runtimes for broader Safari and older mobile-browser compatibility.
- Keeps production caching unchanged; these no-cache rules are scoped only to the staging hostname.

After uploading the theme, opening any WordPress admin screen runs the release cache purge. Test the clean staging URL without adding query parameters.
