# 🚨 CRITICAL: Railway Using Wrong Dockerfile for Ingestion

## The Real Problem

Railway is using the **same Dockerfile** for BOTH services:
- ✅ `mirror-talk-api` - Should use `Dockerfile` (web server with healthcheck)
- ❌ `mirror-talk-ingestion` - Should use `Dockerfile.worker` (no healthcheck, different CMD)

But both services are using `Dockerfile` because there's only one `railway.toml`.

### Evidence from Build Logs
```
Step 5: RUN pip install ... cached
Step 6: COPY app /app/app cached
Step 7: COPY scripts /app/scripts cached
Step 8: RUN pip install -e . cached
```
All cached! ENV variable didn't help.

### Evidence from Deploy Logs
The ingestion service tries to start but:
1. Runs `ingest_all_episodes.py` (correct)
2. But Docker has CMD for uvicorn (wrong!)
3. Healthcheck tries /health endpoint (doesn't exist in ingestion)
4. Healthcheck fails → container marked unhealthy → restarts

## The Fix: Configure Each Service Separately in Railway

Since we can't have two `railway.toml` files, we need to configure each service in Railway Dashboard.

### Option 1: Use Custom Start Command (RECOMMENDED)

#### For `mirror-talk-ingestion` service:

1. Go to Railway Dashboard
2. Select `mirror-talk-ingestion` service
3. Click **Settings** tab
4. Scroll to **Deploy** section
5. Set **Custom Start Command**:
   ```bash
   python scripts/bulk_ingest.py --max-episodes 50 --no-confirm
   ```
6. Scroll to **Health Check** section
7. **Disable Health Check** (toggle off)
8. Click **Deploy**

This makes the ingestion service:
- Use the same Dockerfile (cached is fine)
- Override the CMD with bulk_ingest.py
- Skip healthcheck
- Just run ingestion and exit

#### For `mirror-talk-api` service:

1. Go to Railway Dashboard
2. Select `mirror-talk-api` service  
3. Verify **Health Check** is enabled
4. Health Check Path: `/health`
5. Keep default CMD (uvicorn)

### Option 2: Use Dockerfile.worker (MORE COMPLEX)

Create separate railway config for worker, but this requires Railway CLI or JSON config.

## Immediate Fix Steps

### Step 1: Fix Ingestion Service Start Command

In Railway Dashboard for `mirror-talk-ingestion`:

**Settings → Deploy → Custom Start Command:**
```bash
python scripts/bulk_ingest.py --max-episodes 20 --no-confirm
```

**Settings → Health Check:**
- Toggle OFF (disable healthcheck)

**Settings → Deploy:**
- Click "Redeploy"

### Step 2: Set WHISPER_MODEL=tiny

In Railway Dashboard for `mirror-talk-ingestion`:

**Variables → Add Variable:**
```
WHISPER_MODEL=tiny
```

### Step 3: Verify Both Services

**API Service (`mirror-talk-api`):**
- ✅ Uses Dockerfile
- ✅ Starts uvicorn
- ✅ Has /health endpoint
- ✅ Healthcheck enabled

**Ingestion Service (`mirror-talk-ingestion`):**
- ✅ Uses Dockerfile (same image)
- ✅ Custom start command overrides CMD
- ✅ Runs bulk_ingest.py
- ✅ No healthcheck
- ✅ Exits when done

## Why Healthcheck Fails for Ingestion

The Dockerfile has:
```dockerfile
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

CMD ["sh", "-c", "exec uvicorn app.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

When ingestion service starts:
1. Runs `ingest_all_episodes.py` (from custom start command or Dockerfile.worker)
2. No web server running
3. Healthcheck tries curl to /health
4. Connection refused → healthcheck fails
5. Railway marks container unhealthy
6. Restarts container
7. Repeat forever

## Solution Summary

### Configuration in Railway Dashboard

**mirror-talk-api:**
```
Dockerfile: Dockerfile (default)
Start Command: (none - use Dockerfile CMD)
Health Check: Enabled
Health Check Path: /health
Health Check Timeout: 300s
Environment Variables:
  DATABASE_URL=...
  RSS_URL=...
  All other vars...
```

**mirror-talk-ingestion:**
```
Dockerfile: Dockerfile (same as API)
Start Command: python scripts/bulk_ingest.py --max-episodes 20 --no-confirm
Health Check: DISABLED
Environment Variables:
  DATABASE_URL=...
  RSS_URL=...
  WHISPER_MODEL=tiny  ← Important!
  MAX_EPISODES_PER_RUN=20  ← Optional
  All other vars...
```

## Alternative: Use Dockerfile.worker

If you want ingestion to use a different Dockerfile:

### Create railway-worker.toml

```toml
[build]
builder = "dockerfile"
dockerfilePath = "Dockerfile.worker"

[deploy]
# No healthcheck for worker
```

But Railway doesn't support per-service config files. You'd need to use Railway CLI:

```bash
railway up --service mirror-talk-ingestion --dockerfile Dockerfile.worker
```

## Cache Busting - Why ENV Didn't Work

Railway caches at multiple levels:
1. Docker layer cache (ENV should bust this)
2. Railway build cache (persists across deployments)
3. Registry cache

To force complete rebuild:
1. Railway Dashboard → Service → Deployments
2. Click "..." menu on failed deployment
3. Select "Redeploy"
4. Check ✅ "Rebuild without cache"
5. Deploy

But honestly, since dependencies ARE working (based on earlier logs showing transcription starting), the cache is fine. The real issue is the healthcheck.

## Expected Behavior After Fix

### mirror-talk-ingestion logs:
```
Starting Container
============================================================
BULK INGESTION SCRIPT
============================================================
RSS Feed: https://anchor.fm/s/261b1464/podcast/rss
Max Episodes: 20
Whisper Model: tiny
============================================================
✓ Database initialized
✓ Fetching RSS feed...
✓ Found 470 episodes
✓ Already ingested: 44 episodes
✓ New episodes to process: 20

Processing episode 45/470: ...
  ├─ Transcribing (model=tiny)...
  ├─ Transcription complete
  └─ ✓ Episode complete

Processing episode 46/470: ...
  └─ ✓ Episode complete

...

✓ INGESTION COMPLETE
Processed: 20 episodes
Skipped: 44 episodes
Total chunks: 2,500

Container exits successfully (exit code 0)
```

### mirror-talk-api logs:
```
Starting Container
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
✓ Health check passed
Container running (healthy)
```

## Quick Fix Checklist

For `mirror-talk-ingestion` service in Railway:

- [ ] Settings → Deploy → Custom Start Command:
  - `python scripts/bulk_ingest.py --max-episodes 20 --no-confirm`
- [ ] Settings → Health Check → Disable (toggle off)
- [ ] Variables → Add `WHISPER_MODEL=tiny`
- [ ] Settings → Deploy → Redeploy

For `mirror-talk-api` service:

- [ ] Verify Health Check is enabled
- [ ] Verify Health Check Path is `/health`
- [ ] No custom start command needed

---

**The Fix:** Disable healthcheck and set custom start command for ingestion service!
