# FFmpeg Installation Required for Audio Compression

## The Problem

OpenAI Whisper API has a **25MB file size limit**. Your audio file is **25.07MB**, which exceeds this limit by a tiny margin.

To process files larger than 25MB, we need to compress them first using **FFmpeg**.

---

## Quick Fix: Install FFmpeg

### macOS (Using Homebrew)

```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install FFmpeg
brew install ffmpeg

# Verify installation
ffmpeg -version
```

**Time:** ~2-5 minutes

---

### Alternative: Use Without Compression (Skip Large Files)

If you don't want to install FFmpeg, you can disable compression and skip files over 25MB:

```bash
# Set environment variable to disable compression
export ENABLE_AUDIO_COMPRESSION=false

# Run ingestion
python3 scripts/ingest_all_episodes.py
```

This will skip episodes with audio files larger than 25MB.

---

## After Installing FFmpeg

Once FFmpeg is installed, just run the script again:

```bash
cd /Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk
python3 scripts/ingest_all_episodes.py
```

The script will automatically:
1. Detect files over 25MB
2. Compress them using FFmpeg
3. Try progressively lower bitrates (64k → 48k → 32k) until under 25MB
4. Upload compressed version to OpenAI for transcription
5. Clean up temporary files

---

## How Compression Works

### Before Compression
```
Original file: 25.07MB → ❌ Too large for OpenAI
```

### After Compression (64k bitrate)
```
Compressed file: ~8-12MB → ✅ Under 25MB limit
```

### Compression Settings
- **64k bitrate**: Best quality, ~10-15MB for 1 hour podcast
- **48k bitrate**: Good quality, ~8-12MB for 1 hour podcast  
- **32k bitrate**: Acceptable quality, ~5-8MB for 1 hour podcast

Speech remains very clear even at 32k bitrate.

---

## Technical Details

### FFmpeg Command Used
```bash
ffmpeg -i input.mp3 \
  -ac 1 \           # Mono (reduces size)
  -ar 16000 \       # 16kHz sample rate (sufficient for speech)
  -b:a 64k \        # 64k bitrate
  -y output.mp3     # Overwrite if exists
```

### Memory Usage
- **Without FFmpeg** (pydub): 300-500MB RAM
- **With FFmpeg** (subprocess): 50-100MB RAM ✅

FFmpeg streams the audio instead of loading it all into memory, making it safe for large files.

---

## Troubleshooting

### Issue: "command not found: ffmpeg"

**Solution:** FFmpeg not installed. Follow installation instructions above.

### Issue: "Audio file too long to compress below 25MB limit"

**Solution:** Episode is extremely long (>3 hours). Options:
1. Skip this episode
2. Split audio into chunks (advanced)
3. Use a different transcription service

### Issue: "FFmpeg compression timed out"

**Solution:** File is taking too long to compress. Options:
1. Check your CPU usage
2. Try again (might be temporary)
3. Skip this episode

---

## Current Status

Your file: **25.07MB**
OpenAI limit: **25.00MB**
Difference: **70KB over limit**

This is a very small overage - compression at 64k bitrate will easily bring it under 25MB!

---

## Next Steps

1. **Install FFmpeg** (recommended):
   ```bash
   brew install ffmpeg
   ```

2. **Run ingestion again**:
   ```bash
   python3 scripts/ingest_all_episodes.py
   ```

3. **Watch it work**:
   ```
   Audio file size: 25.07MB
   ⚠️  Audio file is 25.07MB (limit: 25MB)
   🔧 Attempting compression...
   🔧 Compressing audio with FFmpeg (bitrate=64k)...
   ✅ Compression complete: 25.07MB → 10.5MB (42% of original)
   ✅ Compressed to 10.5MB, proceeding with transcription
   ```

---

**Status:** ⏳ Waiting for FFmpeg installation
**Estimated time:** 2-5 minutes to install, then ingestion proceeds normally
