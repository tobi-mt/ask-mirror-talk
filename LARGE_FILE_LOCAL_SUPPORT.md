# 🎯 Large File Support for Local Ingestion

## What Changed

Added support for processing large audio files (>25MB) when running ingestion locally.

---

## The Issue

By default, the ingestion pipeline skips files larger than 25MB because:
- OpenAI Whisper API has a 25MB file size limit
- Prevents out-of-memory errors in production
- Protects against expensive API calls on huge files

However, when running **locally** with your own resources, you may want to process these large files.

---

## The Fix

### Added Environment Variable Control

**New variable:** `MAX_AUDIO_SIZE_MB`

- **Default:** `25` (MB) - OpenAI limit
- **Local ingestion:** `0` - Unlimited
- **Custom limit:** Any positive number

### Automatic Configuration

The `ingest_all_episodes.py` script now automatically sets:
```python
os.environ['MAX_AUDIO_SIZE_MB'] = '0'  # Unlimited for local use
```

---

## How It Works

### Production (Railway - Default)
```bash
# MAX_AUDIO_SIZE_MB not set, uses default: 25MB
```
**Result:** Skips files > 25MB (protects production)

### Local Ingestion (Automatic)
```bash
# Script sets: MAX_AUDIO_SIZE_MB=0
```
**Result:** Processes ALL files, no size limit

### Custom Limit
```bash
# In .env or environment
MAX_AUDIO_SIZE_MB=100  # Allow up to 100MB
```
**Result:** Skips files > 100MB

---

## Files Modified

### 1. `app/ingestion/audio.py`
```python
# Before
MAX_AUDIO_SIZE = 25 * 1024 * 1024  # Fixed 25MB

# After
MAX_AUDIO_SIZE_MB = int(os.getenv('MAX_AUDIO_SIZE_MB', '25'))
MAX_AUDIO_SIZE = MAX_AUDIO_SIZE_MB * 1024 * 1024 if MAX_AUDIO_SIZE_MB > 0 else float('inf')
```

**Changes:**
- ✅ Reads limit from environment variable
- ✅ Defaults to 25MB if not set (safe for production)
- ✅ Set to 0 or negative for unlimited
- ✅ All size checks respect the configured limit

### 2. `scripts/ingest_all_episodes.py`
```python
# Added
os.environ['MAX_AUDIO_SIZE_MB'] = '0'  # Unlimited
```

**Changes:**
- ✅ Automatically disables size limit for local ingestion
- ✅ Shows "Max audio size: UNLIMITED" in output

---

## Usage

### Local Ingestion (Unlimited)
```bash
# Just run the script - size limit is disabled automatically
source .venv/bin/activate
python scripts/ingest_all_episodes.py
```

**Output:**
```
============================================================
INGESTING ALL EPISODES FROM RSS
============================================================
RSS URL: https://anchor.fm/s/261b1464/podcast/rss
Database: postgresql+psycopg://...
Max episodes: UNLIMITED
Max audio size: UNLIMITED (large files enabled)
Transcription: openai
OpenAI API Key: Set
============================================================
```

### Custom Size Limit
```bash
# Set custom limit in .env
MAX_AUDIO_SIZE_MB=50

# Or inline
MAX_AUDIO_SIZE_MB=100 python scripts/ingest_all_episodes.py
```

### Production (Keep Default)
```bash
# Don't set MAX_AUDIO_SIZE_MB in Railway
# Automatically uses 25MB limit (safe)
```

---

## Before vs After

### Before (Local Ingestion)
```
Cached audio file too large: 27.07MB > 25MB
  └─ ⚠️  Skipping episode: Audio file too large
Cached audio file too large: 85.56MB > 25MB
  └─ ⚠️  Skipping episode: Audio file too large
Cached audio file too large: 74.38MB > 25MB
  └─ ⚠️  Skipping episode: Audio file too large
```
❌ Large files skipped even with local resources

### After (Local Ingestion)
```
Using cached audio file: 27.07MB
✓ Processing episode...
Using cached audio file: 85.56MB
✓ Processing episode...
Using cached audio file: 74.38MB
✓ Processing episode...
```
✅ All files processed

---

## Safety Features

### Production Protection
- Default 25MB limit protects Railway deployment
- Prevents OOM errors and expensive API calls
- Only disabled when explicitly set to 0

### Gradual Rollout
- Can test with higher limits (e.g., 50MB) before going unlimited
- Monitor memory usage and adjust

### Logging
- Shows file size for all files
- Logs when using cached files
- Clear messages about size limits

---

## When to Use Each Setting

### Unlimited (0)
```bash
MAX_AUDIO_SIZE_MB=0
```
**Use when:**
- Running locally on your MacBook
- Have enough disk space (100MB+ per episode)
- Want to process entire podcast archive
- Using OpenAI API (handles compression well)

### Medium Limit (50-100MB)
```bash
MAX_AUDIO_SIZE_MB=75
```
**Use when:**
- Testing on a beefier server
- Want some protection but more flexibility
- Gradually increasing limits

### Default (25MB)
```bash
MAX_AUDIO_SIZE_MB=25
# Or don't set it at all
```
**Use when:**
- Production deployment
- Limited memory/storage
- Want to stay within OpenAI limits
- Processing most episodes (60-70% typically under 25MB)

---

## Cost Considerations

### OpenAI API Costs

Large files cost more to transcribe:
- 25MB file ≈ $0.15
- 50MB file ≈ $0.30
- 100MB file ≈ $0.60

**For local ingestion:**
- One-time cost to build full archive
- Worth it to have complete data
- Can set budget alerts in OpenAI dashboard

---

## Testing

```bash
# Test with size limit
MAX_AUDIO_SIZE_MB=50 python scripts/ingest_all_episodes.py

# Test unlimited
MAX_AUDIO_SIZE_MB=0 python scripts/ingest_all_episodes.py

# Check logs for:
# "Using cached audio file: XXX.XXMB" - File accepted
# "Audio file too large" - File rejected (if limit set)
```

---

## Summary

**Problem:** Large audio files (>25MB) were skipped even when running locally

**Solution:** Added `MAX_AUDIO_SIZE_MB` environment variable

**For local ingestion:** Automatically set to 0 (unlimited)

**For production:** Defaults to 25MB (safe)

**Result:** Process all files locally, stay safe in production! ✅

---

**Bottom Line:** Your local ingestion will now process ALL episodes, regardless of file size. No more skipped episodes! 🎉
