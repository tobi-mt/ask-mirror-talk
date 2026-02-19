# Complete Analysis: Large Episode Handling

## Executive Summary

**Question:** Does `bulk_ingest.py` handle breaking down large episodes (>25MB) into smaller chunks?

**Answer:** ✅ YES, but with important caveats:

1. **Audio Level:** Large files (>25MB) are COMPRESSED (not split) to fit OpenAI's API limit
   - Currently DISABLED in production to prevent memory issues
   - Results in episodes >25MB being SKIPPED

2. **Text Level:** All transcripts are CHUNKED into smaller segments for embedding
   - Always enabled, works for all processed episodes
   - Creates 50-200+ chunks per episode on average

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         INGESTION PIPELINE                          │
└─────────────────────────────────────────────────────────────────────┘

1. RSS FEED
   ├─ Parse episodes metadata
   └─ Extract audio URLs

2. AUDIO DOWNLOAD (app/ingestion/audio.py)
   ├─ Stream download with size checking
   ├─ MAX_AUDIO_SIZE_MB=25 (default, configurable)
   ├─ If >25MB in production → SKIP episode
   └─ If >25MB locally with MAX_AUDIO_SIZE_MB=0 → CONTINUE

3. AUDIO COMPRESSION (app/ingestion/transcription_openai.py)
   ├─ Check if file >25MB (OpenAI limit)
   ├─ If ENABLE_AUDIO_COMPRESSION=true:
   │  ├─ Convert to MP3 (if needed)
   │  ├─ Compress with FFmpeg:
   │  │  ├─ Try 64k bitrate (good quality)
   │  │  ├─ Try 48k bitrate (if still too large)
   │  │  └─ Try 32k bitrate (minimum acceptable)
   │  └─ If still >25MB → SKIP episode
   └─ If ENABLE_AUDIO_COMPRESSION=false:
      └─ SKIP episode immediately

4. TRANSCRIPTION (OpenAI Whisper API)
   ├─ Send audio (original or compressed) to OpenAI
   ├─ Receive transcript with timestamps
   └─ ~100-300 segments per 60-min episode

5. TEXT CHUNKING (app/indexing/chunking.py)
   ├─ Combine segments until max_chars (1000)
   ├─ Split at sentence boundaries
   ├─ Create 50-200+ chunks per episode
   └─ Each chunk: {text, start, end, topic, tone, domain}

6. EMBEDDING & STORAGE
   ├─ Batch embed all chunks (OpenAI embeddings)
   └─ Save to PostgreSQL with pgvector
```

## Current Production Configuration

### Railway Worker Service

**Dockerfile.worker:**
```dockerfile
# FFmpeg IS installed (line 15)
ffmpeg \

# Comment indicates compression disabled (line 3)
# "DISABLE compression to prevent OOM"
```

**Assumed Environment Variables:**
```bash
ENABLE_AUDIO_COMPRESSION=false  # Disabled to prevent OOM
MAX_AUDIO_SIZE_MB=25           # Skip files >25MB
MAX_CHUNK_CHARS=1000           # Text chunk size
MIN_CHUNK_CHARS=200            # Minimum chunk size
```

### Why Compression is Disabled

From Docker comments and documentation:
- Railway worker has limited memory (512MB-1GB)
- FFmpeg compression uses significant RAM
- OOM (Out of Memory) crashes occurred
- **Solution:** Disable compression, skip large files

## Current Database State

From `analyze_episode_engagement.py`:

```
Total Episodes: 471
Episodes with chunks: 471 (100%)
Average chunks/episode: 93.7

Chunk Distribution:
  1-4 chunks:    30 episodes  (6.4%)  ← PROBLEM
  5-9 chunks:     7 episodes  (1.5%)
  10-19 chunks:  67 episodes  (14.2%)
  20-49 chunks:  22 episodes  (4.7%)
  50+ chunks:   345 episodes  (73.2%) ← HEALTHY
```

### Episodes with Only 1 Chunk (Examples)

1. "Mark Robinson: Black On Madison Avenue"
2. "Born This Way"
3. "Creating Your Reality with Jay Campbell"
4. "How To Live A Purposeful Life with Alan Lazaros"
5. "Unleashing the Champ with Kyle Sullivan"
... (25 more)

**Likely Causes:**
- Very short episodes (trailers, announcements)
- Large file size (>25MB, skipped)
- Poor audio quality (transcription failed)
- Processing errors (incomplete ingestion)

## Detailed Code Flow

### 1. Size Checking (audio.py)

```python
MAX_AUDIO_SIZE_MB = int(os.getenv('MAX_AUDIO_SIZE_MB', '25'))
MAX_AUDIO_SIZE = MAX_AUDIO_SIZE_MB * 1024 * 1024 if MAX_AUDIO_SIZE_MB > 0 else float('inf')

# During download:
if MAX_AUDIO_SIZE_MB > 0 and downloaded_size > MAX_AUDIO_SIZE:
    raise ValueError(f"Audio file too large: >{downloaded_size / 1024 / 1024:.2f}MB")
```

**Result:**
- Production: Files >25MB raise ValueError → episode skipped
- Local (MAX_AUDIO_SIZE_MB=0): No limit → download complete

### 2. Compression (transcription_openai.py)

```python
ENABLE_COMPRESSION = os.getenv('ENABLE_AUDIO_COMPRESSION', 'true').lower() == 'true'

if file_size > OPENAI_MAX_SIZE:  # 25MB
    if not ENABLE_COMPRESSION:
        raise ValueError("Audio file too large, compression disabled")
    
    # Try compression at 64k, 48k, 32k bitrates
    compress_audio_ffmpeg(audio_path, temp_path, target_bitrate="64k")
    
    if compressed_size > OPENAI_MAX_SIZE:
        # Try lower bitrates...
        # If still too large:
        raise ValueError("Unable to compress below 25MB limit")
```

**Result:**
- Compression enabled: Most episodes compressed successfully
- Compression disabled: All >25MB episodes skipped
- Very long episodes (>2 hours): May fail even with compression

### 3. Text Chunking (chunking.py)

```python
def chunk_segments(segments, max_chars=1000, min_chars=200):
    chunks = []
    current_text = []
    
    for seg in segments:
        current_text.append(seg["text"])
        
        if sum(len(t) for t in current_text) >= max_chars:
            # Create chunk and reset
            chunks.append(finalize_chunk(current_text, start, end))
            current_text = []
    
    return chunks
```

**Result:**
- 60-min episode → ~100-300 segments → ~50-100 chunks
- 90-min episode → ~150-450 segments → ~75-150 chunks
- 120-min episode → ~200-600 segments → ~100-200 chunks

## Solutions Comparison

### Option 1: Local Re-ingestion (RECOMMENDED)

**What:**
- Run re-ingestion locally for 30 low-chunk episodes
- Enable compression locally
- No production changes

**How:**
```bash
export ENABLE_AUDIO_COMPRESSION=true
export MAX_AUDIO_SIZE_MB=0
python scripts/reingest_low_chunk_episodes.py
```

**Pros:**
- ✅ No production risk
- ✅ No cost increase
- ✅ Immediate improvement
- ✅ One-time operation

**Cons:**
- ❌ Manual execution needed
- ❌ Future large episodes still skipped
- ❌ Requires local resources

**Time:** 15-30 minutes
**Cost:** Free (uses local compute)

---

### Option 2: Enable Production Compression

**What:**
- Enable compression on Railway worker
- Increase memory allocation
- Handle all large episodes automatically

**How:**
```bash
# In Railway Dashboard:
ENABLE_AUDIO_COMPRESSION=true
# Increase memory to 2GB
```

**Pros:**
- ✅ Automatic processing
- ✅ Future episodes handled
- ✅ No manual intervention

**Cons:**
- ❌ OOM risk (crashes)
- ❌ Higher costs (~$10-20/month)
- ❌ Requires monitoring

**Time:** 5 minutes setup + ongoing monitoring
**Cost:** +$10-20/month

---

### Option 3: Hybrid Approach

**What:**
- Local re-ingestion for backfill
- Keep production compression disabled
- Monitor and manually process large episodes

**Pros:**
- ✅ Best of both worlds
- ✅ Low risk
- ✅ Cost effective

**Cons:**
- ❌ Ongoing manual work
- ❌ Two-step process

**Time:** 30 minutes initial + 10 minutes/month
**Cost:** Free

## Implementation Guide: Option 1 (Recommended)

### Prerequisites

1. **Install FFmpeg:**
```bash
brew install ffmpeg  # macOS
# or
apt-get install ffmpeg  # Linux
```

2. **Set Environment Variables:**
```bash
# Enable compression
export ENABLE_AUDIO_COMPRESSION=true

# Remove size limit
export MAX_AUDIO_SIZE_MB=0

# OpenAI API key
export OPENAI_API_KEY="your-key-here"

# Production database URL
export DATABASE_URL="your-production-db-url"
```

### Step 1: Analyze Current State

```bash
cd /Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk

python scripts/analyze_episode_engagement.py
```

Output shows 30 episodes with 1-4 chunks.

### Step 2: Run Re-ingestion

```bash
python scripts/reingest_low_chunk_episodes.py
```

This will:
1. Query database for episodes with ≤4 chunks
2. Show list of episodes to re-ingest
3. Ask for confirmation
4. Re-process each episode with compression enabled
5. Report results

### Step 3: Verify Results

```bash
# Re-run analysis
python scripts/analyze_episode_engagement.py

# Check for improvements:
# - Episodes with 1-4 chunks should decrease from 30 to <10
# - Average chunks/episode should increase from 93.7 to 95+
```

### Step 4: Test Search Quality

```bash
# Test a query that might use previously low-chunk episodes
curl -X POST "https://your-api.railway.app/api/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "topic from low-chunk episode"}'

# Check if citations now include more chunks from those episodes
```

## Expected Results

### Before Re-ingestion

```
Episodes with 1-4 chunks: 30
Episodes with 5-9 chunks: 7
Average chunks/episode: 93.7
```

Example episode:
- "Mark Robinson: Black On Madison Avenue": 1 chunk
- Likely 60-min episode, file >25MB, skipped

### After Re-ingestion

```
Episodes with 1-4 chunks: 5-10 (only true shorts/trailers)
Episodes with 5-9 chunks: 3
Average chunks/episode: 95-100
```

Same episode after re-ingestion:
- "Mark Robinson: Black On Madison Avenue": 80-120 chunks
- Successfully compressed from 35MB → 18MB
- Transcribed and chunked normally

## Monitoring & Maintenance

### Weekly Monitoring

```bash
# Run engagement analysis
python scripts/analyze_episode_engagement.py > reports/engagement_$(date +%Y%m%d).txt

# Check for new low-chunk episodes
grep "1 chunks" reports/engagement_*.txt
```

### Monthly Review

1. Check skipped episodes in logs:
```bash
grep "Audio file too large" logs/*.log
```

2. Decide if new large episodes need processing:
```bash
# If yes, run local re-ingestion again
python scripts/reingest_low_chunk_episodes.py
```

### Alerting (Optional)

Add to weekly report:
```python
# In weekly_engagement_report.py
if low_chunk_count > 10:
    print("⚠️  WARNING: More than 10 episodes with <5 chunks")
    print("   Consider running re-ingestion")
```

## FAQs

### Q: Why not just split large audio files into parts?

**A:** Complexity and quality concerns:
- Would need to split at silence points (complex)
- Would create artificial boundaries in transcripts
- Would complicate chunk timestamp management
- Compression is simpler and maintains episode integrity

### Q: What's the maximum episode length supported?

**A:** With compression:
- **Up to ~2 hours** at reasonable quality (64k bitrate)
- **Up to ~3 hours** at lower quality (32k bitrate)
- **Beyond 3 hours:** Would need splitting (very rare for podcasts)

### Q: Will compression affect transcription quality?

**A:** Minimal impact:
- 64k bitrate: Excellent quality for speech
- 48k bitrate: Good quality for speech
- 32k bitrate: Acceptable quality for speech
- OpenAI Whisper is robust to compression artifacts

### Q: How much does re-ingestion cost?

**A:** OpenAI API costs:
- Transcription: $0.006/minute
- Embeddings: $0.0001/1K tokens
- 60-min episode: ~$0.36 transcription + ~$0.10 embeddings = ~$0.46
- 30 episodes: ~$13.80 total

### Q: Can this be automated?

**A:** Yes, but requires:
- Scheduled job (cron/GitHub Actions)
- Secure credential management
- Error handling and retry logic
- Cost monitoring

For now, manual execution is simpler and gives more control.

## Files Reference

| File | Purpose | Key Functions |
|------|---------|---------------|
| `app/ingestion/audio.py` | Audio download | Size checking, stream download |
| `app/ingestion/transcription_openai.py` | Transcription | Compression, OpenAI API calls |
| `app/indexing/chunking.py` | Text chunking | Segment-to-chunk conversion |
| `app/ingestion/pipeline_optimized.py` | Main pipeline | Orchestrates all steps |
| `scripts/bulk_ingest.py` | Batch ingestion | Fetches RSS, calls pipeline |
| `scripts/reingest_low_chunk_episodes.py` | Re-ingestion | Processes low-chunk episodes |
| `scripts/analyze_episode_engagement.py` | Analytics | Episode/chunk statistics |

## Environment Variables Reference

| Variable | Default | Production | Local (Re-ingestion) | Purpose |
|----------|---------|------------|----------------------|---------|
| `MAX_AUDIO_SIZE_MB` | 25 | 25 | 0 | Max download size |
| `ENABLE_AUDIO_COMPRESSION` | true | false | true | Enable FFmpeg compression |
| `MAX_CHUNK_CHARS` | 1000 | 1000 | 1000 | Max characters per chunk |
| `MIN_CHUNK_CHARS` | 200 | 200 | 200 | Min characters per chunk |
| `OPENAI_API_KEY` | - | Set | Required | OpenAI API access |
| `DATABASE_URL` | - | Set | Required | PostgreSQL connection |

## Conclusion

### Does `bulk_ingest.py` break down large episodes?

**YES** - in two ways:

1. **Audio Level (Compression):**
   - Large files (>25MB) are compressed with FFmpeg
   - Currently disabled in production (memory constraints)
   - Can be enabled locally for re-ingestion

2. **Text Level (Chunking):**
   - All transcripts are chunked into smaller segments
   - Always enabled, works for all episodes
   - Creates 50-200+ chunks per episode

### Current State:
- ✅ 471 episodes ingested (100% coverage)
- ⚠️ 30 episodes with only 1-4 chunks (6.4%)
- ✅ Chunking works well for processed episodes
- ❌ Some large episodes skipped due to disabled compression

### Recommended Action:
- ✅ Run local re-ingestion for 30 low-chunk episodes
- ✅ Use `scripts/reingest_low_chunk_episodes.py`
- ✅ Enable compression locally (no production changes)
- ✅ Monitor weekly for new low-chunk episodes

### Next Steps:
1. Review this document
2. Set up local environment (FFmpeg, env vars)
3. Run re-ingestion script
4. Verify improvements
5. Set up monitoring schedule

**Time required:** 30-60 minutes
**Cost:** ~$13-15 (OpenAI API usage)
**Risk:** Low (local execution only)
**Impact:** High (improves 30 episodes, ~6% of database)
