# Local Ingestion of Large Files (>25MB)

## Overview

Railway deployment skips audio files larger than 25MB due to OpenAI Whisper API limits. This guide shows you how to ingest these large files locally using your own machine, where you have more memory and can use alternative transcription methods.

## Why Files Are Skipped on Railway

1. **OpenAI Whisper API Limit**: 25MB maximum file size
2. **Memory Constraints**: Railway containers have limited RAM (~512MB-1GB)
3. **Cost Optimization**: Large file processing can timeout or crash containers

## Solution: Local Ingestion

Process large files on your local machine, then the transcriptions and embeddings are stored in the Neon Postgres database, making them immediately available to your Railway API.

---

## Prerequisites

1. **Python 3.9+** installed locally
2. **Database Access**: Your local environment configured to connect to the Neon database
3. **OpenAI API Key**: For Whisper API (or use faster-whisper for local processing)
4. **Sufficient RAM**: At least 4GB available for processing large files

---

## Setup Instructions

### 1. Clone the Repository (if not already done)

```bash
cd ~/PycharmProjects/pythonProject/ask-mirror-talk
```

### 2. Create Local Environment File

Create a `.env` file in the project root with your production database credentials:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Database - Use your Neon production database
DATABASE_URL=postgresql://neondb_owner:your-password@your-neon-host/neondb

# OpenAI API Key
OPENAI_API_KEY=sk-your-openai-api-key

# RSS Feed
RSS_URL=https://your-podcast-feed-url.com/feed

# Transcription Provider
TRANSCRIPTION_PROVIDER=openai  # or faster_whisper for local processing

# Whisper Model (only used if TRANSCRIPTION_PROVIDER=faster_whisper)
WHISPER_MODEL=base  # Options: tiny, base, small, medium, large

# Embedding Provider
EMBEDDING_PROVIDER=local

# Answer Generation
ANSWER_GENERATION_PROVIDER=openai  # Use OpenAI for intelligent answers
OPENAI_ANSWER_MODEL=gpt-3.5-turbo
OPENAI_ANSWER_MAX_TOKENS=500
OPENAI_ANSWER_TEMPERATURE=0.7

# Environment
ENVIRONMENT=dev
```

**Important**: Use your **production Neon database URL** so that ingested data is immediately available to the Railway API.

### 3. Install Python Dependencies

```bash
# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Verify Database Connection

Test that you can connect to the Neon database:

```bash
python -c "from app.core.db import init_db; init_db(); print('✅ Database connection successful!')"
```

---

## Method 1: Using OpenAI Whisper API (Recommended for Files Up To 25MB)

This is what Railway uses, but won't work for files >25MB.

**Skip to Method 2 for large files.**

---

## Method 2: Using faster-whisper for Local Processing (No File Size Limit!)

This method runs Whisper models locally on your machine, bypassing the 25MB limit entirely.

### Step 1: Install faster-whisper

```bash
pip install faster-whisper
```

### Step 2: Update Your `.env`

```env
TRANSCRIPTION_PROVIDER=faster_whisper
WHISPER_MODEL=base  # Options: tiny, base, small, medium, large
```

**Model Selection**:
- `tiny`: Fastest, lowest accuracy (~1GB RAM)
- `base`: Good balance (~1GB RAM) - **Recommended**
- `small`: Better accuracy (~2GB RAM)
- `medium`: High accuracy (~5GB RAM)
- `large`: Best accuracy (~10GB RAM)

### Step 3: Identify Large Episodes to Ingest

Run a dry-run to see which episodes are too large:

```bash
python scripts/bulk_ingest.py --dry-run
```

Look for messages like:
```
⚠️  SKIPPED: Episode "XYZ" - Audio file too large: 35.2MB > 25MB
```

### Step 4: Ingest All Episodes (Including Large Ones)

```bash
python scripts/bulk_ingest.py
```

This will:
- Process all episodes from your RSS feed
- Use faster-whisper to transcribe large files locally
- Store transcriptions and embeddings in Neon database
- Make them immediately available to your Railway API

### Step 5: Monitor Progress

Watch the console output for:
```
✅ Successfully transcribed: episode-title.mp3 (35.2MB)
✅ Indexed 45 chunks from: episode-title.mp3
✅ Episode ingested successfully: episode-title
```

---

## Method 3: Ingest Specific Episodes Only

If you only want to ingest a few specific large episodes:

### Option A: Use the Bulk Ingest Script with Filters

Edit `scripts/bulk_ingest.py` temporarily to filter by title:

```python
# Around line 110, after fetching feed entries
entries = [e for e in entries if "specific-episode-title" in e.get("title", "").lower()]
```

Then run:
```bash
python scripts/bulk_ingest.py
```

### Option B: Create a Custom Script

Create `scripts/ingest_single_episode.py`:

```python
#!/usr/bin/env python3
"""Ingest a single episode by URL or title"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.db import SessionLocal, init_db
from app.core.config import settings
from app.core.logging import setup_logging
from app.ingestion.pipeline_optimized import run_ingestion_optimized
from app.ingestion.rss import fetch_feed, normalize_entries

setup_logging()
import logging
logger = logging.getLogger(__name__)

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/ingest_single_episode.py <episode-title-keyword>")
        sys.exit(1)
    
    search_term = sys.argv[1].lower()
    
    init_db()
    logger.info(f"Fetching RSS feed...")
    feed = fetch_feed(settings.rss_url)
    entries = normalize_entries(feed)
    
    # Find matching episode
    matched = [e for e in entries if search_term in e.get("title", "").lower()]
    
    if not matched:
        logger.error(f"No episodes found matching: {search_term}")
        return 1
    
    if len(matched) > 1:
        logger.info(f"Found {len(matched)} matching episodes:")
        for e in matched:
            logger.info(f"  - {e.get('title')}")
        logger.info("Please be more specific.")
        return 1
    
    episode = matched[0]
    logger.info(f"Found episode: {episode.get('title')}")
    
    with SessionLocal() as db:
        success = run_ingestion_optimized(db, episode)
        if success:
            logger.info("✅ Episode ingested successfully!")
            return 0
        else:
            logger.error("❌ Ingestion failed")
            return 1

if __name__ == "__main__":
    sys.exit(main())
```

Make it executable and run:
```bash
chmod +x scripts/ingest_single_episode.py
python scripts/ingest_single_episode.py "episode keyword"
```

---

## Method 4: Manual Download + Ingest

For very large files or special cases:

### Step 1: Download Audio Manually

```bash
mkdir -p data/audio
cd data/audio
curl -L -o episode.mp3 "https://direct-audio-url.com/episode.mp3"
```

### Step 2: Create a Manual Ingest Script

Create `scripts/ingest_local_file.py`:

```python
#!/usr/bin/env python3
"""Ingest a locally downloaded audio file"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.db import SessionLocal, init_db
from app.core.config import settings
from app.core.logging import setup_logging
from app.ingestion.transcription_openai import transcribe_audio_openai
from app.ingestion.transcription import transcribe_audio as transcribe_faster_whisper
from app.indexing.chunker import chunk_text
from app.indexing.embeddings import get_embedding_function
from app.storage import repository

setup_logging()
import logging
logger = logging.getLogger(__name__)

def main():
    if len(sys.argv) < 4:
        print("Usage: python scripts/ingest_local_file.py <audio_file_path> <episode_title> <episode_url>")
        sys.exit(1)
    
    audio_file = Path(sys.argv[1])
    episode_title = sys.argv[2]
    episode_url = sys.argv[3]
    
    if not audio_file.exists():
        logger.error(f"Audio file not found: {audio_file}")
        return 1
    
    init_db()
    
    logger.info(f"Processing: {audio_file}")
    logger.info(f"Title: {episode_title}")
    logger.info(f"URL: {episode_url}")
    
    # Transcribe
    if settings.transcription_provider == "openai":
        transcript = transcribe_audio_openai(str(audio_file))
    else:
        transcript = transcribe_faster_whisper(str(audio_file), settings.whisper_model)
    
    logger.info(f"✅ Transcription complete: {len(transcript)} chars")
    
    # Chunk
    chunks = chunk_text(
        transcript,
        max_chars=settings.max_chunk_chars,
        min_chars=settings.min_chunk_chars
    )
    logger.info(f"✅ Created {len(chunks)} chunks")
    
    # Embed and store
    embed_fn = get_embedding_function()
    
    with SessionLocal() as db:
        # Create episode
        episode = repository.create_episode(
            db,
            title=episode_title,
            audio_url=episode_url,
            transcript=transcript
        )
        
        # Store chunks
        for i, chunk_text in enumerate(chunks):
            embedding = embed_fn([chunk_text])[0]
            repository.create_chunk(
                db,
                episode_id=episode.id,
                content=chunk_text,
                embedding=embedding,
                chunk_index=i,
                start_time=0.0,
                end_time=0.0
            )
        
        db.commit()
        logger.info(f"✅ Successfully ingested episode: {episode_title}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

Run it:
```bash
python scripts/ingest_local_file.py \
    data/audio/episode.mp3 \
    "Episode Title" \
    "https://your-podcast.com/episodes/123"
```

---

## Verification

After local ingestion, verify the episodes are available:

### 1. Check Database Directly

```bash
python -c "
from app.core.db import SessionLocal
from app.storage.models import Episode

with SessionLocal() as db:
    episodes = db.query(Episode).all()
    print(f'Total episodes in database: {len(episodes)}')
    
    # Show largest episodes
    for ep in sorted(episodes, key=lambda x: len(x.transcript or ''), reverse=True)[:5]:
        print(f'  - {ep.title}: {len(ep.transcript or 0)} chars')
"
```

### 2. Test API Locally

Start the API locally:
```bash
uvicorn app.api.main:app --reload --port 8000
```

Test a query:
```bash
curl -X POST "http://localhost:8000/api/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "test query from large episode"}'
```

### 3. Test Production API

Once data is in Neon, it's immediately available to Railway:

```bash
curl -X POST "https://your-railway-app.railway.app/api/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "test query from large episode"}'
```

---

## Troubleshooting

### Issue: "Audio file too large" even with faster-whisper

**Solution**: Make sure your `.env` has:
```env
TRANSCRIPTION_PROVIDER=faster_whisper
```

Not `openai`. Restart your Python process after changing.

### Issue: Out of memory during local processing

**Solutions**:
1. Use a smaller Whisper model: `WHISPER_MODEL=tiny` or `base`
2. Process episodes one at a time instead of bulk
3. Close other applications to free up RAM
4. Use the manual download + ingest method (Method 4)

### Issue: Database connection fails locally

**Solutions**:
1. Verify DATABASE_URL in `.env` matches your Neon credentials
2. Check Neon dashboard for connection string
3. Ensure your IP is not blocked (Neon allows all IPs by default)
4. Test with: `psql "postgresql://user:pass@host/db"`

### Issue: Episodes ingested but not showing in API results

**Solutions**:
1. Check that embeddings were created: Query the `chunks` table
2. Verify `embedding_dim` matches between local and Railway (both should be 384)
3. Clear any caching if present
4. Check Railway logs for errors

---

## Cost Considerations

### OpenAI Whisper API (for files ≤25MB)
- Cost: ~$0.006 per minute of audio
- Example: 60-minute episode = ~$0.36

### faster-whisper (local, no file size limit)
- Cost: **FREE** (uses your own machine)
- Trade-off: Uses your local CPU/GPU and RAM

### Recommendation
Use **faster-whisper** locally for:
- Large files (>25MB)
- Bulk processing of many episodes
- When you want to minimize API costs

Use **OpenAI Whisper API** for:
- Quick processing of individual files <25MB
- When you don't have local compute resources
- Automated cron jobs (Railway can handle <25MB files)

---

## Automation: Scheduled Local Ingestion

To automatically process new large episodes:

### Create a Cron Job (macOS/Linux)

```bash
# Edit crontab
crontab -e

# Add this line to run daily at 2 AM
0 2 * * * cd /Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk && source venv/bin/activate && python scripts/bulk_ingest.py --no-confirm >> /tmp/ingestion.log 2>&1
```

### Create a Launch Agent (macOS)

Create `~/Library/LaunchAgents/com.mirrortalk.ingestion.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.mirrortalk.ingestion</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk/venv/bin/python</string>
        <string>/Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk/scripts/bulk_ingest.py</string>
        <string>--no-confirm</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>2</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/tmp/mirrortalk-ingestion.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/mirrortalk-ingestion-error.log</string>
    <key>WorkingDirectory</key>
    <string>/Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
```

Load it:
```bash
launchctl load ~/Library/LaunchAgents/com.mirrortalk.ingestion.plist
```

---

## Summary

**For large files (>25MB):**
1. Install faster-whisper locally: `pip install faster-whisper`
2. Configure `.env` with Neon database and `TRANSCRIPTION_PROVIDER=faster_whisper`
3. Run: `python scripts/bulk_ingest.py`
4. Data is immediately available in Railway API (shared database)

**Quick Reference:**
```bash
# Setup (one-time)
cp .env.example .env
# Edit .env with Neon credentials
pip install -r requirements.txt
pip install faster-whisper

# Ingest all episodes (including large ones)
python scripts/bulk_ingest.py

# Verify
python -c "from app.core.db import SessionLocal; from app.storage.models import Episode; print(f'{SessionLocal().query(Episode).count()} episodes in database')"
```

**Result:** Large episodes processed locally are stored in Neon and instantly queryable via your Railway API! 🎉

---

## Questions?

- Check Railway logs: `railway logs`
- Check ingestion logs: Look at console output during local runs
- Test API: `curl https://your-app.railway.app/api/ask -X POST -d '{"question":"test"}' -H "Content-Type: application/json"`

For more help, see:
- `INGESTION_COMPLETE_GUIDE.md` - Comprehensive ingestion documentation
- `QUICK_REFERENCE.md` - Quick command reference
- `TROUBLESHOOTING.md` - Common issues and solutions
