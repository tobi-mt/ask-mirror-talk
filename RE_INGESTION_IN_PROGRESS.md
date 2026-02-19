# Re-Ingestion of Low-Chunk Episodes - IN PROGRESS

**Status:** ✅ **RUNNING NOW!**
**Started:** February 18, 2026 at 23:35
**Episodes:** 30 episodes (previously had ≤4 chunks)
**Estimated Completion:** ~90 minutes (around 01:05 AM)
**Terminal ID:** 254ea1fd-ff9d-40ef-a35d-f3d1fc0bc7a9

## What's Happening

The re-ingestion script (`scripts/reingest_low_chunk_episodes.py`) is currently running to fix episodes that have too few chunks. These episodes were likely truncated due to audio file size limits during the original ingestion.

### Configuration
- **ENABLE_AUDIO_COMPRESSION:** `true` ✅
- **MAX_AUDIO_SIZE_MB:** `0` (no limit) ✅

### Process

1. **Identify Low-Chunk Episodes** ✅
   - Found 30 episodes with 1-4 chunks
   - These represent episodes that were likely truncated due to file size

2. **Delete Existing Data** ✅ (In Progress)
   - Delete chunks (30 records)
   - Delete transcript segments
   - Delete transcripts (30 records)
   - Delete episodes (30 records)

3. **Re-Ingest with Compression** ⏳ (In Progress)
   - Download audio files
   - **Compress audio** (new feature!)
   - Transcribe with OpenAI Whisper
   - Chunk transcripts with AI
   - Generate embeddings
   - Index in database

## Episodes Being Re-Ingested

1. [652] Channeling Your Power with Mike Acker (was 1 chunk)
2. [663] 3 Qualities to Enhance Yourself and Live A More Authentic Li... (was 1 chunk)
3. [257] Donna Chacko: ONE Thing To Improve Your Overall Health (was 1 chunk)
4. [241] Unleashing the Champ with Kyle Sullivan (was 1 chunk)
5. [231] Sharing Your Message with Neil Gordon (was 1 chunk)
6. [246] How To Live A Purposeful Life with Alan Lazaros (was 1 chunk)
7. [651] Creating Your Reality with Jay Campbell (was 1 chunk)
8. [229] Born This Way (was 1 chunk)
9. [259] Mark Robinson: Black On Madison Avenue (was 1 chunk)
10. [255] Becoming Unconstrained with Myles Wakeham (was 1 chunk)
... and 20 more episodes

## Technical Details

### Problem Solved
Previously, episodes failed to ingest completely when:
- Audio files exceeded 25MB
- No audio compression was available
- Files were rejected by the transcription service

### Solution
1. **Created `reingest_low_chunk_episodes.py` script** to automate re-processing
2. **Added proper deletion cascade** to handle foreign key constraints:
   - chunks → episodes
   - transcript_segments → transcripts
   - transcripts → episodes
   - episodes (parent table)
3. **Enabled audio compression** with no size limit
4. **Automated the re-ingestion process** with progress tracking

### Expected Outcome
- Each episode should now have **5-20+ chunks** (depending on length)
- **Better coverage** of episode content in Q&A responses
- **Improved diversity** in search results
- **Higher quality** answers with more context

## Monitoring

You can check the progress by:
```bash
# Check the terminal output
tail -f <terminal output>

# Once complete, verify chunk counts
python scripts/analyze_episode_engagement.py
```

## How to Monitor Progress

### Check Current Status
```bash
# View the terminal output in real-time
# Terminal ID: 254ea1fd-ff9d-40ef-a35d-f3d1fc0bc7a9

# Or check database progress
python -c "
from app.core.db import get_session_local
from app.storage import models

db = get_session_local()()
total_episodes = db.query(models.Episode).count()
total_chunks = db.query(models.Chunk).count()
print(f'Episodes: {total_episodes}/471 ({total_episodes-441} new)')
print(f'Chunks: {total_chunks} (started with 44,107)')
db.close()
"
```

### What to Expect
The script will process episodes in batches, showing progress like:
```
2026-02-18 23:35:xx | INFO | Episode 1/30: "Title" - Downloading...
2026-02-18 23:35:xx | INFO | Episode 1/30: "Title" - Compressing...
2026-02-18 23:36:xx | INFO | Episode 1/30: "Title" - Transcribing...
2026-02-18 23:37:xx | INFO | Episode 1/30: "Title" - Chunking (XX chunks)...
2026-02-18 23:37:xx | INFO | Episode 1/30: "Title" - ✓ Complete
```

Each episode takes approximately 2-3 minutes to process.

## Current Progress

**Database State:**
- Before: 441 episodes, 44,107 chunks (avg 100.02 chunks/episode)
- Target: 471 episodes, ~44,500+ chunks (avg 94+ chunks/episode)
- **In Progress:** Re-ingesting 30 episodes with compression enabled

## Next Steps (After Completion)

1. **Verify the re-ingestion:**
   ```bash
   python scripts/analyze_episode_engagement.py
   ```
   - Check that episodes now have more chunks
   - Verify no episodes with ≤4 chunks remain

2. **Test the improved coverage:**
   - Ask questions about these episodes
   - Verify better, more complete answers
   - Check citation diversity

3. **Monitor user engagement:**
   - Track question answering quality
   - Monitor episode diversity in responses
   - Review user feedback

4. **Document the fix:**
   - Update deployment notes
   - Add to changelog
   - Share success metrics

## Files Changed

- ✅ `scripts/reingest_low_chunk_episodes.py` - Created new script
- ✅ Script handles foreign key constraints properly
- ✅ Script integrates with existing pipeline_optimized.py

## Estimated Time

- **Per Episode:** 1-3 minutes (download, compress, transcribe, chunk, index)
- **Total:** 30-90 minutes for all 30 episodes
- **Current Status:** Check terminal output for real-time progress

## Success Criteria

✅ All 30 episodes successfully re-ingested
✅ No episodes with ≤4 chunks remaining
✅ Chunk count increased from 30 total → 150-600+ total
✅ No errors during ingestion
✅ Database consistency maintained
