# Mirror Talk 8.32.3

## YouTube runtime reliability correction

- Fixes a live YouTube IFrame API timing race discovered during production verification of 8.32.2.
- Uses the callback's initialized player controller as the authoritative object before reading mute or playback state.
- Guards every player method used by autoplay, visibility, sound and podcast-coordination handlers.
- Restores reliable playing-status text and `youtube_video_start` Intelligence collection.
- Formats numeric RSS durations into reader-friendly minutes or hours instead of exposing raw seconds.
- Preserves all compact Listen & Connect Studio functionality introduced in 8.32.2.
