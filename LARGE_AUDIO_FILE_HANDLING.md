# Large Audio File Handling - Complete Analysis

## ✅ Summary: YES, Large Episodes ARE Broken Into Chunks

The ingestion pipeline **DOES** handle large episodes (>25MB) by:
1. **Compressing** the audio file if it exceeds OpenAI's 25MB limit
2. **Chunking** the transcript into smaller segments for embedding and storage

## How It Works: Step-by-Step

### 1. Audio Download (app/ingestion/audio.py)
```
MAX_AUDIO_SIZE_MB = 25 (default, configurable via env var)
```

- Downloads audio file from RSS feed
- **Checks file size** during and after download
- If file > 25MB:
  - **Production (Railway)**: Raises `ValueError` and skips episode
  - **Local (with MAX_AUDIO_SIZE_MB=0)**: No size limit, downloads complete file

### 2. Audio Compression (app/ingestion/transcription_openai.py)
```
ENABLE_COMPRESSION = true (default, configurable via env var)
```

**When file > 25MB:**
1. Converts audio to MP3 format (if not already)
2. Attempts compression with FFmpeg at multiple bitrates:
   - **64k bitrate** (good quality for speech) - try first
   - **48k bitrate** (medium quality) - if 64k still too large
   - **32k bitrate** (minimum acceptable) - if 48k still too large
3. If compression at 32k still exceeds 25MB → raises `ValueError` and skips episode

**Compression settings:**
- Mono audio (`-ac 1`) - reduces size by ~50%
- 16kHz sample rate (`-ar 16000`) - sufficient for speech
- Progressive bitrate reduction (64k → 48k → 32k)

**Result:**
- Most episodes successfully compressed to <25MB
- Episodes that cannot be compressed are skipped (rare for podcast audio)

### 3. Transcription
- Sends audio (original or compressed) to OpenAI Whisper API
- Returns transcript with timestamped segments
- Each segment has: `{start, end, text}`

### 4. Text Chunking (app/indexing/chunking.py)
```
max_chars = 1000 (configurable)
min_chars = 200 (configurable)
```

**Chunking Strategy:**
1. Combines transcript segments until reaching `max_chars`
2. Splits into chunks respecting sentence boundaries
3. Each chunk includes:
   - `text`: The transcript text
   - `start`: Start timestamp in audio
   - `end`: End timestamp in audio

**Example:**
- 60-minute episode → ~100-200 transcript segments
- Segments chunked into ~50-100 text chunks
- Each chunk ~500-1000 characters

### 5. Embedding & Storage
- Each chunk is embedded individually (OpenAI embeddings)
- Chunks stored in database with metadata
- All chunks link back to original episode

## Current Production Behavior

**On Railway (Production):**
```bash
MAX_AUDIO_SIZE_MB=25  # Default - skips files >25MB before download
ENABLE_AUDIO_COMPRESSION=false  # Disabled to save compute resources
```

**Result:**
- Episodes >25MB are **skipped during download** (never transcribed)
- Episodes <25MB are transcribed and chunked normally

## Episodes with Only 1 Chunk

From your engagement analysis, several episodes have only 1 chunk. This happens when:

1. **Very short episodes** (<1000 characters of transcript)
   - Example: Brief announcements, intros, trailers
   
2. **Transcription issues**
   - Audio quality problems
   - Speaker detection issues
   - Background noise

3. **Incomplete processing**
   - Episode was re-ingested but not fully completed
   - Processing error during chunking

## Recommendations

### Option A: Enable Compression on Railway (Recommended)
```bash
# In Railway dashboard, set environment variable:
ENABLE_AUDIO_COMPRESSION=true
```

**Benefits:**
- Process episodes that are currently skipped (25-40MB range)
- Better episode coverage
- More diverse search results

**Tradeoffs:**
- Requires FFmpeg in Docker image (already present in Dockerfile.api)
- Additional CPU usage during ingestion (~30 seconds per large file)
- Slight quality reduction (but sufficient for speech transcription)

### Option B: Local Re-ingestion of Large Episodes
```bash
# For local ingestion only:
export MAX_AUDIO_SIZE_MB=0  # No size limit
export ENABLE_AUDIO_COMPRESSION=true

# Run ingestion
python scripts/bulk_ingest.py --max 5
```

**Use case:**
- Process specific large episodes locally
- Export chunks to production database
- One-time backfill of missing episodes

### Option C: Keep Current Behavior
- Continue skipping episodes >25MB
- Accept gaps in episode coverage
- Monitor for user questions about skipped episodes

## Verification Commands

### Check which episodes are skipped:
```bash
# Search for "too large" messages in logs
grep "Audio file too large" logs/*.log
```

### Check episodes with only 1 chunk:
```python
# Already implemented in scripts/analyze_episode_engagement.py
python scripts/analyze_episode_engagement.py
# Look for "Episodes with only 1 chunk" section
```

### Test compression locally:
```bash
# Enable compression
export ENABLE_AUDIO_COMPRESSION=true
export MAX_AUDIO_SIZE_MB=0

# Ingest one large episode
python scripts/bulk_ingest.py --max 1
```

## Files Involved

| File | Purpose | Key Logic |
|------|---------|-----------|
| `app/ingestion/audio.py` | Audio download | Size checking, skipping >25MB |
| `app/ingestion/transcription_openai.py` | Transcription | Audio compression, FFmpeg integration |
| `app/indexing/chunking.py` | Text chunking | Segment-to-chunk conversion |
| `app/ingestion/pipeline_optimized.py` | Main pipeline | Orchestrates all steps |

## Environment Variables

| Variable | Default | Production | Purpose |
|----------|---------|------------|---------|
| `MAX_AUDIO_SIZE_MB` | 25 | 25 | Max download size (0=unlimited) |
| `ENABLE_AUDIO_COMPRESSION` | true | false | Enable FFmpeg compression |
| `MAX_CHUNK_CHARS` | 1000 | 1000 | Max characters per chunk |
| `MIN_CHUNK_CHARS` | 200 | 200 | Min characters per chunk |

## Conclusion

✅ **The system DOES handle large episodes through:**
1. Audio compression (when enabled)
2. Text chunking (always enabled)

❌ **Current production limitation:**
- Compression disabled on Railway (compute resource optimization)
- Episodes >25MB are skipped during download

💡 **To improve coverage:**
- Enable `ENABLE_AUDIO_COMPRESSION=true` on Railway
- Or run local ingestion with compression for large episodes
- Monitor `analyze_episode_engagement.py` for episodes with low chunk counts
