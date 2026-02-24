# Initial Data Load Guide

## Problem: Empty Database

The API is working, but returns: *"I could not find anything in the Mirror Talk episodes..."*

**Reason**: No episodes have been ingested yet.

---

## Solution: Manually Trigger Initial Ingestion

### Method 1: Trigger Cron Job (Easiest)

1. Go to https://dashboard.render.com
2. Navigate to your **`mirror-talk-ingestion`** Cron Job
3. Click **"Trigger Run"** or **"Run Now"** button
4. Monitor logs - should see:
   ```
   Found X episodes in feed
   New episodes to process: 3
   Starting ingestion...
   ✓ INGESTION COMPLETE
   ```

⏱️ **Time**: ~3-5 minutes per episode (9-15 minutes total for 3 episodes)

---

### Method 2: Run Command in Web Service Shell

If cron job trigger isn't available:

1. Go to https://dashboard.render.com
2. Navigate to your **`ask-mirror-talk`** Web Service
3. Click **"Shell"** tab (opens terminal in running container)
4. Run this command:

```bash
python scripts/bulk_ingest.py --max-episodes 3
```

5. When prompted "Proceed? [y/N]:", type `y` and press Enter
6. Wait for completion (~9-15 minutes)

---

### Method 3: Increase Max Episodes in Cron Job (For Future)

To ingest more episodes automatically on the next Wednesday run:

1. Edit `render.yaml`:
```yaml
- type: cron
  name: mirror-talk-ingestion
  # ...
  dockerCommand: python scripts/bulk_ingest.py --max-episodes 10  # Change from 3 to 10
```

2. Commit and push:
```bash
git add render.yaml
git commit -m "Increase cron job to process 10 episodes"
git push origin main
```

---

## What Happens During Ingestion

The script will:

1. ✅ Fetch RSS feed from Anchor.fm
2. ✅ Download audio for each episode
3. ✅ Transcribe with Whisper (this is the slow part)
4. ✅ Split transcript into chunks
5. ✅ Generate embeddings (with `local` provider, very fast)
6. ✅ Store in PostgreSQL database

---

## Verify Data Was Loaded

After ingestion completes, test the status endpoint:

```bash
curl https://ask-mirror-talk.onrender.com/status
```

**Expected response:**
```json
{
  "status": "ok",
  "episode_count": 3,
  "total_chunks": 150  // or similar number
}
```

---

## Test from WordPress

Once `episode_count > 0`, try asking a question:

```javascript
fetch('https://ask-mirror-talk.onrender.com/api/ask', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({question: "What topics are discussed?"})
})
.then(r => r.json())
.then(data => console.log(data))
```

You should now get real answers with sources!

---

## Memory Considerations

**With local embeddings (current setup):**
- ✅ Ingestion: ~200-300MB RAM
- ✅ Transcription (Whisper base): ~200MB RAM
- ✅ Should work fine on starter plan

**If you see OOM errors during ingestion:**
1. Use `--max-episodes 1` (one at a time)
2. Or upgrade to Standard plan temporarily
3. Or use `WHISPER_MODEL=tiny` (faster, less accurate)

---

## Troubleshooting

### "Ran out of memory" during ingestion

**Option A**: Process fewer episodes at once
```bash
python scripts/bulk_ingest.py --max-episodes 1
```

**Option B**: Use smaller Whisper model

Edit `render.yaml`:
```yaml
- key: WHISPER_MODEL
  value: tiny  # Change from 'base' to 'tiny'
```

Then trigger ingestion again.

**Option C**: Upgrade to Standard plan ($25/month, 2GB RAM)

Edit `render.yaml`:
```yaml
- type: web
  plan: standard  # Change from 'starter'
```

### Ingestion Takes Forever

**Expected**: ~3-5 minutes per episode
- Downloading audio: 10-30 seconds
- Transcription: 2-4 minutes (depends on episode length)
- Chunking + embeddings: 10-30 seconds

**For 3 episodes**: 9-15 minutes total

### "No chunks created"

Check logs for errors during:
- Audio download (network issues?)
- Transcription (Whisper errors?)
- Database writes (connection issues?)

---

## Ongoing Automatic Ingestion

After initial load, the cron job runs automatically:
- **Schedule**: Every Wednesday at 4 AM UTC (5 AM CET)
- **Command**: `python scripts/bulk_ingest.py --max-episodes 3`
- **Purpose**: Process up to 3 new episodes released that week

No manual intervention needed after initial setup! 🎉

---

## Cost Optimization

If you need to ingest many episodes (e.g., 50+ episodes):

1. **Temporarily upgrade** to Standard plan for initial load
2. **Process all episodes** at once (faster, no memory issues)
3. **Downgrade back** to Starter plan after initial load
4. Cron job will handle weekly updates on Starter plan

**Total extra cost**: ~$25 for one month, saves hours of time

---

**Next Step**: Trigger the ingestion using Method 1 or Method 2 above! ⚡
