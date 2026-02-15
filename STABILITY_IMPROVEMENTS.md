# Stability Improvements - Preventing Container Crashes

## Date: 2024

## Problem
Railway ingestion container was crashing when processing large audio files, even after implementing the 25MB skip logic.

## Root Causes Identified

### 1. **Memory Accumulation**
- Audio files were not being cleaned up immediately after processing
- Memory was accumulating across multiple episodes
- Garbage collection wasn't sufficient for large batches

### 2. **Database Connection Idle Timeout**
- Long transcription times (especially with OpenAI API) could cause the database connection to timeout
- Connection errors would crash the entire ingestion run

### 3. **Late File Size Detection**
- Files were being fully downloaded before size checks
- Large files (>25MB) were consuming disk space and memory even though they couldn't be transcribed
- No early abort mechanism during download

### 4. **Incomplete Error Handling**
- Audio files weren't cleaned up when errors occurred
- Failed episodes left orphaned files on disk

## Solutions Implemented

### 1. **Early File Size Detection in Download** (`app/ingestion/audio.py`)
```python
# Check Content-Length header BEFORE downloading
if content_length and int(content_length) > MAX_AUDIO_SIZE:
    raise ValueError(f"Audio file too large: {size_mb:.2f}MB > 25MB")

# Abort download if size exceeds limit during streaming
if downloaded_size > MAX_AUDIO_SIZE:
    file_path.unlink()  # Delete partial file
    raise ValueError("Audio file too large...")
```

**Benefits:**
- Prevents downloading files that are too large
- Saves bandwidth and disk space
- Avoids wasting time and resources on files that will be skipped

### 2. **Immediate Audio File Cleanup** (`app/ingestion/pipeline_optimized.py`)
```python
# Clean up audio file immediately after successful processing
if audio_path and audio_path.exists():
    audio_path.unlink()
    audio_path = None

# Clean up on errors too
except Exception:
    if audio_path and audio_path.exists():
        audio_path.unlink()
```

**Benefits:**
- Frees disk space immediately
- Prevents disk full errors
- Reduces memory pressure from cached file handles

### 3. **Database Connection Keep-Alive**
```python
# Refresh database connection before each episode
try:
    db.execute("SELECT 1")
except Exception:
    logger.warning("Database connection lost, refreshing...")
    db.rollback()
```

**Benefits:**
- Prevents connection timeout errors
- Ensures database is always ready
- Auto-recovers from transient connection issues

### 4. **Comprehensive Error Handling**
```python
try:
    # Process episode
except ValueError as e:
    # Known errors (file too large, etc.)
    logger.warning("Skipping episode: %s", str(e))
    skipped += 1
    # Clean up
except Exception as e:
    # Unexpected errors
    logger.error("Episode failed: %s", str(e))
    skipped += 1
    # Clean up
finally:
    gc.collect()  # Force garbage collection
```

**Benefits:**
- Prevents single episode failures from crashing entire run
- Proper resource cleanup on all code paths
- Detailed error logging for debugging

## File Size Strategy

### Current Implementation
- **25MB Hard Limit** (OpenAI Whisper API restriction)
- Files are checked at **3 stages**:
  1. During download (Content-Length header)
  2. During download (streaming size check)
  3. Before transcription (file size on disk)

### Why No Compression?
Previous attempts to compress files >25MB caused:
- **Out of Memory (OOM) crashes** - FFmpeg processes consumed too much RAM
- **Container crashes** - Railway killed containers due to memory limits
- **Unpredictable behavior** - Compression ratios varied widely

**Current approach is safer:**
- Skip large files with clear warning
- No memory spikes
- Predictable resource usage
- Container stability

## Expected Behavior

### Successful Episode Processing
```
[1/50] Processing episode: Episode Title
  ├─ Created episode (id=123)
  ├─ Downloaded audio: episode_123.mp3
  ├─ Downloaded audio: 18.5MB
  ├─ Audio file size: 18.50MB (within 25MB limit)
  ├─ Transcribing (model=whisper-1)...
  ├─ Transcription complete (142 segments)
  ├─ Created 28 chunks
  ├─ Embedding 28 chunks (batch mode)...
  ├─ Saving 28 chunks to database...
  └─ ✓ Episode complete (id=123)
  └─ Cleaned up audio file
```

### Skipped Episode (Too Large)
```
[2/50] Processing episode: Very Long Episode
  ├─ Created episode (id=124)
  └─ ⚠️  Skipping episode: Audio file too large: 32.45MB > 25MB. Episode will be skipped.
```

### Error Recovery
```
[3/50] Processing episode: Problematic Episode
  ├─ Created episode (id=125)
  ├─ Downloaded audio: episode_125.mp3
  └─ ❌ Episode failed: OpenAI API error: Rate limit exceeded
```

## Monitoring

### Key Metrics to Watch
1. **Processed vs Skipped** - How many episodes are being skipped?
2. **Memory Usage** - Should stay stable across episodes
3. **Disk Usage** - Should not grow during ingestion
4. **Error Rate** - What % of episodes fail?

### Railway Dashboard
- Check Memory usage graph - should be relatively flat
- Check CPU usage - spikes during transcription are normal
- Check Logs - look for warnings about skipped episodes

## Future Optimizations

### If Many Episodes Are >25MB
1. **Pre-process audio files** - Use a separate service to compress before ingestion
2. **Split long episodes** - Break into chunks <25MB
3. **Alternative transcription** - Use a service without file size limits
4. **Direct streaming** - Stream audio directly to transcription API without downloading

### If Container Still Crashes
1. **Reduce max_episodes_per_run** - Process fewer episodes per run
2. **Add delays** - Sleep between episodes to let system recover
3. **Increase Railway memory** - Upgrade to larger container
4. **Implement checkpointing** - Resume from last successful episode

## Testing Recommendations

### Local Testing
```bash
# Test with single episode
python scripts/bulk_ingest.py --max-episodes 1

# Test with dry run to see what would be processed
python scripts/bulk_ingest.py --dry-run

# Test with known large file
python scripts/bulk_ingest.py --max-episodes 1  # manually select large episode
```

### Railway Testing
1. Deploy and watch logs in real-time
2. Monitor memory usage in Railway dashboard
3. Start with `--max-episodes 5` to test stability
4. Gradually increase batch size if stable

## Deployment Checklist

- [x] File size detection in download phase
- [x] Immediate audio file cleanup after processing
- [x] Database connection keep-alive
- [x] Comprehensive error handling with cleanup
- [x] Garbage collection after each episode
- [x] Clear logging for skipped episodes
- [x] Documentation updated

## Quick Reference

### Environment Variables
```bash
# Required
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://...
RSS_URL=https://...

# Optional tuning
MAX_EPISODES_PER_RUN=10  # Lower = more stable
TRANSCRIPTION_PROVIDER=openai
```

### Manual Episode Cleanup (if needed)
```python
# Remove all audio files
rm -rf data/audio/*.mp3

# Check disk usage
du -sh data/audio/
```

### Check Railway Logs
```bash
railway logs --service mirror-talk-ingestion
```

## Summary

These improvements make the ingestion service **much more stable** by:
1. ✅ Detecting file size issues **before** wasting resources
2. ✅ Cleaning up resources **immediately** after use
3. ✅ Keeping database connection **alive** during long operations
4. ✅ Handling errors **gracefully** without crashing
5. ✅ Providing **clear visibility** into what's happening

The service should now handle mixed episode sizes gracefully, skipping large episodes with warnings while successfully processing all episodes ≤25MB.
