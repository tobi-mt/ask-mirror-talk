# Mirror Talk 8.27.4

## Reliable mobile YouTube playback

- Fixes an author-style collision that overrode the native `hidden` attribute and left the poster button covering the YouTube iframe.
- Uses `playsinline=1`, `mute=1`, an explicit autoplay permission and privacy-enhanced YouTube embeds for mobile-safe playback.
- Treats the first explicit play action as external-media consent and shares that choice with the site-wide YouTube Studio.
- After consent, loads videos only when at least half visible and requests muted autoplay.
- Respects reduced-motion and Data Saver preferences by loading normal controls without automatic playback.
- Keeps a visible, ordinary play control before consent and does not contact YouTube until consent exists.
