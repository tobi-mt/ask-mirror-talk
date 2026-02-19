# Quick Reference: Large Episode Handling

## TL;DR

**Q: Does bulk_ingest.py break down large episodes (>25MB)?**

**A: YES ✅ - Two ways:**
1. **Audio compression** (FFmpeg) - compresses files >25MB to fit OpenAI's API limit
2. **Text chunking** - splits transcripts into ~50-200 chunks per episode

**BUT:** Compression is currently **DISABLED** in production (memory constraints), so large files are **SKIPPED**.

---

## Quick Stats

```
Total Episodes: 471 (100% coverage)
Average Chunks/Episode: 93.7

Problem: 30 episodes with only 1-4 chunks (6.4%)
Cause: Large files (>25MB) skipped OR very short episodes
```

---

## Quick Fix (Recommended)

### Re-ingest Low-Chunk Episodes Locally

```bash
# 1. Set up environment
export ENABLE_AUDIO_COMPRESSION=true
export MAX_AUDIO_SIZE_MB=0
export OPENAI_API_KEY="your-key"
export DATABASE_URL="your-db-url"

# 2. Install FFmpeg (if needed)
brew install ffmpeg  # macOS

# 3. Run re-ingestion
cd /Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk
python scripts/reingest_low_chunk_episodes.py

# 4. Verify results
python scripts/analyze_episode_engagement.py
```

**Time:** 15-30 minutes  
**Cost:** ~$13-15 (OpenAI API)  
**Risk:** Low (local only)  
**Impact:** Fixes 30 episodes

---

## How It Works

### 1. Audio Compression (`transcription_openai.py`)

```python
# If audio file > 25MB:
if ENABLE_AUDIO_COMPRESSION == true:
    # Try compression at 64k, 48k, 32k bitrates
    compress_audio_ffmpeg(audio_path, "64k")
    # If still too large after 32k → skip
else:
    # Skip episode immediately
```

**Production:** Compression disabled → files >25MB skipped  
**Local:** Compression enabled → files compressed and processed

### 2. Text Chunking (`chunking.py`)

```python
# Always enabled
# Combines transcript segments until max_chars (1000)
# Splits at sentence boundaries
# Result: 50-200+ chunks per episode
```

**Works for all processed episodes**

---

## Production vs Local

| Setting | Production | Local Re-ingestion |
|---------|-----------|-------------------|
| `MAX_AUDIO_SIZE_MB` | 25 | 0 (unlimited) |
| `ENABLE_AUDIO_COMPRESSION` | false | true |
| FFmpeg installed | Yes | Yes |
| Result for >25MB files | Skip | Compress & Process |

---

## Files Created

1. **`LARGE_EPISODE_ANALYSIS_COMPLETE.md`** - Full analysis (this is the main doc)
2. **`ACTION_PLAN_LOW_CHUNK_EPISODES.md`** - Detailed action plan with 3 solutions
3. **`LARGE_AUDIO_FILE_HANDLING.md`** - Technical deep dive
4. **`scripts/reingest_low_chunk_episodes.py`** - Re-ingestion script
5. **`LARGE_EPISODE_QUICK_REFERENCE.md`** - This file (quick lookup)

---

## Decision Tree

```
Do you want to process episodes >25MB?
│
├─ YES, automatically → Enable compression in production
│  ├─ Set ENABLE_AUDIO_COMPRESSION=true on Railway
│  ├─ Increase worker memory to 2GB
│  └─ Cost: +$10-20/month, Risk: OOM crashes
│
├─ YES, manually → Local re-ingestion (RECOMMENDED)
│  ├─ Run scripts/reingest_low_chunk_episodes.py
│  ├─ No production changes needed
│  └─ Cost: ~$15 once, Risk: None
│
└─ NO, keep current → Skip large episodes
   └─ Accept gaps in coverage
```

---

## Common Questions

**Q: Why are 30 episodes only 1-4 chunks?**  
A: Either very short (trailers) OR large files (>25MB) that were skipped.

**Q: Will re-ingestion help?**  
A: Yes! Large episodes that were skipped will be compressed and processed, creating 50-200+ chunks each.

**Q: What's the risk?**  
A: Very low. Re-ingestion runs locally, doesn't affect production.

**Q: How much does it cost?**  
A: ~$0.46 per episode (OpenAI API). For 30 episodes: ~$13-15 total.

**Q: How long does it take?**  
A: ~30-60 seconds per episode. For 30 episodes: ~15-30 minutes total.

---

## Monitoring

```bash
# Weekly: Check for low-chunk episodes
python scripts/analyze_episode_engagement.py | grep "1 chunks"

# Monthly: Check if new re-ingestion needed
python scripts/reingest_low_chunk_episodes.py
```

---

## Success Metrics

**Before:**
- 30 episodes with 1-4 chunks
- Average: 93.7 chunks/episode

**After (Expected):**
- 5-10 episodes with 1-4 chunks (only true shorts)
- Average: 95-100 chunks/episode
- Better citation diversity

---

## Next Steps

1. ✅ Review this quick reference
2. ⬜ Read full analysis: `LARGE_EPISODE_ANALYSIS_COMPLETE.md`
3. ⬜ Read action plan: `ACTION_PLAN_LOW_CHUNK_EPISODES.md`
4. ⬜ Run re-ingestion: `python scripts/reingest_low_chunk_episodes.py`
5. ⬜ Verify results: `python scripts/analyze_episode_engagement.py`

---

## Key Takeaway

✅ **The system CAN handle large episodes through compression**  
⚠️ **Production has compression disabled (memory constraints)**  
💡 **Solution: Run local re-ingestion for backfill**  
🎯 **Result: Better coverage, more diverse citations**
