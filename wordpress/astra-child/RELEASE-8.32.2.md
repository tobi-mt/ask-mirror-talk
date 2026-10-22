# Mirror Talk 8.32.2

## Compact YouTube Studio for Listen & Connect

- Adds the latest YouTube upload directly after the podcast player on `/listen-connect/`.
- Uses a thumbnail-first facade and loads the privacy-enhanced YouTube player only after consent.
- Starts eligible playback muted, respects reduced-motion and data-saver preferences, and preserves native controls when autoplay is blocked.
- Handles landscape videos and portrait Shorts responsively without introducing the large cinematic section used elsewhere.
- Coordinates audio so podcast and video playback do not compete.
- Records Studio visibility, consent, playback, progress, completion, sound and error events in Mirror Talk Intelligence.
- Repairs the shared Intelligence event receiver so feature events emitted from either `document` or `window` are collected once, eliminating a silent YouTube-event reporting gap.
- Hides the module cleanly when YouTube is disabled or no valid video is available.
- Preserves the global YouTube Studio suppression on the link hub, preventing duplicate players.
