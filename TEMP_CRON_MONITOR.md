# ⏰ Temporary Cron Schedule - Monitoring Guide

## What Just Happened

✅ **Deployed temporary cron schedule**: Runs every 10 minutes
✅ **Added --no-confirm flag**: Runs automatically without prompts
✅ **Purpose**: Load initial podcast data into database

---

## Timeline

| Time | Action | Expected Result |
|------|--------|-----------------|
| **Now** | Git push completed | Render starts deploying |
| **+2-3 min** | Deployment complete | Cron job schedule updated |
| **+10 min** | First cron run | Starts ingesting 3 episodes |
| **+20-25 min** | Ingestion complete | Data loaded, ready=true |

---

## Monitoring Steps

### 1. Check Deployment Status (Now - 3 minutes)

Go to: https://dashboard.render.com

- Find **`mirror-talk-ingestion`** cron job
- Verify it shows schedule: `*/10 * * * *`
- Wait for "Live" status

### 2. Watch for First Run (~10 minutes from now)

The cron job will automatically trigger within 10 minutes.

**Check cron job logs** for output like:
```
Fetching RSS feed...
Found X episodes in feed
New episodes to process: 3
Starting ingestion...
Downloading audio...
Transcribing...
✓ INGESTION COMPLETE
Processed: 3 episodes
```

⏱️ **Duration**: ~9-15 minutes per run (3-5 min per episode)

### 3. Verify Data Loaded (~25 minutes from now)

Test the status endpoint:

```bash
curl https://ask-mirror-talk.onrender.com/status
```

**Before ingestion:**
```json
{"status":"ok","episodes":0,"chunks":0,"ready":false}
```

**After successful ingestion:**
```json
{"status":"ok","episodes":3,"chunks":150,"ready":true}
```

### 4. Test from WordPress

Once `ready: true`, go to https://mirrortalkpodcast.com and ask:
- "What topics are discussed in the podcast?"
- "Who are the guests?"

Should get real answers! 🎉

---

## Troubleshooting

### If Cron Job Fails with OOM

The cron job runs in its own container and might hit memory limits.

**Solution 1**: Process one episode at a time

Edit `render.yaml`:
```yaml
dockerCommand: python scripts/bulk_ingest.py --max-episodes 1 --no-confirm
```

Then run 3 times (wait 10 min between each).

**Solution 2**: Use smaller Whisper model

Edit `render.yaml` (in cron job section):
```yaml
- key: WHISPER_MODEL
  value: tiny  # Change from 'base'
```

**Solution 3**: Temporarily upgrade to Standard plan

Only for the cron job during initial load:
```yaml
- type: cron
  plan: standard  # Add this line (2GB RAM)
```

Cost: ~$25 for one month, then remove after initial load.

### If Episodes Still 0 After 30 Minutes

1. **Check cron job logs** for errors
2. **Verify schedule updated** - should show `*/10 * * * *`
3. **Check if cron is running** - look for recent log entries
4. **Try manual trigger** - some Render plans have "Run Now" button

---

## ⚠️ IMPORTANT: Revert to Weekly Schedule

**After data is loaded successfully**, you MUST change the schedule back to avoid:
- Unnecessary runs every 10 minutes
- Wasted resources
- Potential rate limiting

### Revert Steps

1. Edit `render.yaml`:

```yaml
- type: cron
  name: mirror-talk-ingestion
  # ...
  schedule: "0 4 * * 3"  # Change back to weekly
  dockerCommand: python scripts/bulk_ingest.py --max-episodes 3 --no-confirm
```

2. Commit and push:

```bash
git add render.yaml
git commit -m "Revert cron to weekly schedule after initial load"
git push origin main
```

3. Verify in Render dashboard that schedule shows: `0 4 * * 3`

---

## Current Configuration

**Temporary (for initial load):**
```yaml
schedule: "*/10 * * * *"  # Every 10 minutes
dockerCommand: python scripts/bulk_ingest.py --max-episodes 3 --no-confirm
```

**Production (after initial load):**
```yaml
schedule: "0 4 * * 3"  # Wednesdays at 4 AM UTC (5 AM CET)
dockerCommand: python scripts/bulk_ingest.py --max-episodes 3 --no-confirm
```

---

## Expected Memory Usage During Ingestion

| Component | Memory |
|-----------|--------|
| Python runtime | ~80MB |
| Whisper base model | ~200MB |
| Audio download | ~30MB |
| Local embeddings | ~0MB |
| **Total** | **~310MB** |

Should fit in 512MB with room to spare. If OOM occurs, use solutions above.

---

## Next Steps Checklist

- [ ] Wait 10 minutes for first cron run
- [ ] Check cron job logs for success
- [ ] Verify status shows episodes > 0
- [ ] Test WordPress widget with real question
- [ ] **Revert schedule to weekly after success**
- [ ] Delete Background Worker if still exists

---

**Deployment Time**: Commit 98ae285  
**Next Cron Run**: Within 10 minutes of deployment  
**Expected Completion**: ~25 minutes from now  
**Action Required**: Revert schedule after first successful run
