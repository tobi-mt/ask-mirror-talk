# Complete Ingestion Guide

This guide covers all methods to ingest podcast episodes into Ask Mirror Talk.

## Quick Start

```bash
# In Railway shell
railway run bash
python scripts/ingest_all_episodes.py
```

## Ingestion Methods

### Method 1: Railway Shell (Recommended for Initial Load)

Use this for the first-time ingestion of all episodes:

```bash
# Open Railway shell
railway run bash

# Run the script that ingests ALL episodes
python scripts/ingest_all_episodes.py
```

**What it does:**
- Fetches all episodes from RSS feed
- Downloads audio files
- Transcribes using Faster Whisper
- Generates embeddings
- Stores in database
- Sets `MAX_EPISODES_PER_RUN=999` to process all episodes

**Duration:** ~5-10 minutes per episode (depends on episode length)

### Method 2: GitHub Actions (Automatic Updates)

Use this for ongoing automatic updates:

**Setup:**

1. Add secrets in GitHub → Settings → Secrets and variables → Actions:
   - `DATABASE_URL` - Your Neon Postgres connection string
   - `RSS_URL` - Your podcast RSS feed URL

2. The workflow at `.github/workflows/update-episodes.yml` will:
   - Run every 6 hours automatically
   - Check for new episodes
   - Ingest only new episodes (max 10 per run)
   - Can be triggered manually from GitHub UI

**Manual trigger:**
1. Go to GitHub → Actions → "Update Latest Episodes"
2. Click "Run workflow"

### Method 3: Railway Cron Job

Create a scheduled service in Railway:

1. **Create New Service** in your Railway project
2. **Service Type:** Cron Job
3. **Schedule:** `0 */6 * * *` (every 6 hours)
4. **Repository:** Same as main service
5. **Start Command:** `python scripts/update_latest_episodes.py`
6. **Variables:** Share all variables from main service

### Method 4: API Endpoint

Call the ingestion endpoint directly:

```bash
# Using curl with basic auth
curl -X POST "https://your-app.railway.app/admin/ingest" \
  -H "Authorization: Basic $(echo -n 'tobi:@GoingPlaces#2026' | base64)"

# Or visit in browser (will prompt for login)
https://your-app.railway.app/admin/ingest
```

**Notes:**
- Requires admin credentials
- Limited by Railway's request timeout (~30 seconds)
- Best for triggering background ingestion
- Use for manual updates only

### Method 5: Local Development

Run ingestion from your local machine:

```bash
# Set environment variables
export DATABASE_URL="postgresql://..."
export RSS_URL="https://anchor.fm/s/261b1464/podcast/rss"

# Run ingestion
python scripts/ingest_all_episodes.py

# Or update with latest only
python scripts/update_latest_episodes.py
```

## Scripts Comparison

| Script | Purpose | Episodes Processed | Use Case |
|--------|---------|-------------------|----------|
| `ingest_all_episodes.py` | Initial load | ALL episodes (999 max) | First-time setup |
| `update_latest_episodes.py` | Incremental updates | 10 most recent | Scheduled updates |

## Ingestion Process

Each episode goes through these steps:

1. **RSS Parsing** - Fetch episode metadata from RSS feed
2. **Audio Download** - Download MP3 file to temp storage
3. **Transcription** - Convert audio to text using Faster Whisper
4. **Chunking** - Split transcript into semantic chunks
5. **Embedding** - Generate vector embeddings for each chunk
6. **Storage** - Save to database with metadata

## Configuration

Environment variables that affect ingestion:

```bash
# How many episodes to process per run
MAX_EPISODES_PER_RUN=10

# Transcription settings
WHISPER_MODEL=base  # Options: tiny, base, small, medium, large
TRANSCRIPTION_PROVIDER=faster_whisper

# Embedding settings
EMBEDDING_PROVIDER=local  # Use sentence-transformers

# RSS settings
RSS_URL=https://anchor.fm/s/261b1464/podcast/rss
```

## Monitoring Ingestion

### Check Status

```bash
# Via API
curl https://your-app.railway.app/status

# Via admin dashboard
https://your-app.railway.app/admin
```

### View Logs

```bash
# Railway logs
railway logs

# Follow logs in real-time
railway logs -f
```

### Check Database

```bash
# In Railway shell
railway run bash

# Connect to database
python -c "
from app.core.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) FROM episodes'))
    print(f'Episodes: {result.scalar()}')
    
    result = conn.execute(text('SELECT COUNT(*) FROM chunks'))
    print(f'Chunks: {result.scalar()}')
"
```

## Troubleshooting

### Ingestion Fails Midway

**Symptoms:** Process stops after a few episodes

**Solutions:**
1. **Memory limit:** Upgrade Railway plan for more memory
2. **Timeout:** Use `update_latest_episodes.py` with smaller batches
3. **Network issues:** Retry failed episodes

```bash
# Process in smaller batches
MAX_EPISODES_PER_RUN=5 python scripts/update_latest_episodes.py
```

### Duplicate Episodes

**Symptoms:** Same episode appears multiple times

**Solution:** The scripts check for existing episodes before ingesting
```python
# Both scripts use this check
existing_episode = session.query(Episode).filter_by(
    title=episode_data['title']
).first()

if existing_episode:
    print(f"✓ Episode already exists: {title}")
    continue
```

### Transcription Errors

**Symptoms:** Transcription fails or produces garbled text

**Solutions:**
1. Check audio file is valid MP3
2. Try different Whisper model:
   ```bash
   WHISPER_MODEL=small python scripts/ingest_all_episodes.py
   ```
3. Check audio URL is accessible

### Embedding Errors

**Symptoms:** Error generating embeddings

**Solutions:**
1. Ensure sentence-transformers is installed:
   ```bash
   pip install sentence-transformers
   ```
2. Check model is downloaded:
   ```python
   from sentence_transformers import SentenceTransformer
   model = SentenceTransformer('all-MiniLM-L6-v2')
   ```

## Performance Tips

### Speed Up Ingestion

1. **Use faster Whisper model:**
   ```bash
   WHISPER_MODEL=tiny  # Fastest, less accurate
   WHISPER_MODEL=base  # Good balance (default)
   ```

2. **Reduce chunk size:**
   - Fewer chunks = faster processing
   - Edit `app/indexing/chunking.py`

3. **Parallel processing:**
   - Current scripts are sequential
   - Could be parallelized for multiple episodes

### Reduce Costs

1. **Use local providers:**
   ```bash
   TRANSCRIPTION_PROVIDER=faster_whisper  # Free
   EMBEDDING_PROVIDER=local  # Free
   ```

2. **Ingest only recent episodes:**
   ```bash
   MAX_EPISODES_PER_RUN=10
   python scripts/update_latest_episodes.py
   ```

3. **Schedule updates less frequently:**
   - Change cron to `0 0 * * *` (daily)
   - Or `0 0 * * 0` (weekly)

## Validation

After ingestion, validate the data:

```bash
# Check episode count
curl https://your-app.railway.app/status

# Test search
curl -X POST "https://your-app.railway.app/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Mirror Talk about?"}'

# Should return relevant chunks from episodes
```

## Best Practices

1. **Initial Load:**
   - Use `ingest_all_episodes.py` in Railway shell
   - Do this during off-peak hours
   - Monitor logs for errors

2. **Ongoing Updates:**
   - Use GitHub Actions or Railway Cron
   - Check for new episodes every 6 hours
   - Automatic, no manual intervention

3. **Error Handling:**
   - Scripts log errors but continue processing
   - Check logs regularly for issues
   - Re-run script to process failed episodes

4. **Data Backup:**
   - Neon provides automatic backups
   - Export database periodically:
     ```bash
     pg_dump $DATABASE_URL > backup.sql
     ```

## Complete Workflow

### First-Time Setup

```bash
# 1. Deploy to Railway
railway up

# 2. Add environment variables (see RAILWAY_SETUP_GUIDE.md)

# 3. Run initial ingestion
railway run bash
python scripts/ingest_all_episodes.py

# 4. Verify ingestion
curl https://your-app.railway.app/status

# 5. Test search
curl -X POST "https://your-app.railway.app/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "test question"}'
```

### Ongoing Maintenance

```bash
# Option A: GitHub Actions (recommended)
# - Set up secrets in GitHub
# - Workflow runs automatically every 6 hours

# Option B: Manual update
railway run bash
python scripts/update_latest_episodes.py

# Option C: API endpoint
curl -X POST "https://your-app.railway.app/admin/ingest" \
  -H "Authorization: Basic $(echo -n 'tobi:@GoingPlaces#2026' | base64)"
```

## Next Steps

- [ ] Run initial ingestion with `ingest_all_episodes.py`
- [ ] Set up GitHub Actions for automatic updates
- [ ] Verify all episodes are searchable
- [ ] Monitor logs for any errors
- [ ] Test the `/ask` endpoint thoroughly
- [ ] Update WordPress widget
- [ ] Set up monitoring/alerts for failed ingestions
