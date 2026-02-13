# 🚨 CRITICAL: Railway Service Configuration Required

## The Problem
Your ingestion service is failing with:
```
ModuleNotFoundError: No module named 'feedparser'
```

**Root Cause:** Railway is using the **wrong Dockerfile** (the lightweight `Dockerfile` instead of `Dockerfile.worker`).

---

## ✅ THE FIX (Do This Now!)

### Step 1: Configure Dockerfile Path in Railway Dashboard

1. **Open Railway Dashboard:** https://railway.app/dashboard
2. **Select the `mirror-talk-ingestion` service**
3. Click **Settings** (left sidebar)
4. Scroll to **Build** section
5. Find **Dockerfile Path** field
6. Enter: `Dockerfile.worker`
7. Click **Save**

### Step 2: Verify Configuration

The Settings page should show:
```
Build
├─ Builder: Dockerfile
└─ Dockerfile Path: Dockerfile.worker ✅
```

### Step 3: Force Redeploy

1. Click **Deployments** tab (top)
2. Click **Deploy** button (top right)
3. Select **Redeploy**
4. Watch the build logs

---

## Expected Build Logs After Fix

You should see Railway building with `Dockerfile.worker`:

```
=========================
Using Detected Dockerfile
=========================

Dockerfile.worker ✅ (not just "Dockerfile")

RUN apt-get update && apt-get install -y ffmpeg libpq5 curl...
✓ 30s

RUN pip install --no-cache-dir fastapi uvicorn pydantic...
✓ 30s

RUN apt-get update && apt-get install -y build-essential...
RUN pip install --no-cache-dir av>=12.0.0
✓ 60s

RUN pip install --no-cache-dir --only-binary=:all: faster-whisper sentence-transformers
✓ 90s

RUN pip install --no-cache-dir --no-deps -e .
✓ 5s

Build complete! ✅
Starting Container...
```

**Then runtime logs should show:**
```
============================================================
INGESTING ALL EPISODES FROM RSS
============================================================
RSS URL: https://anchor.fm/s/261b1464/podcast/rss
Database: postgresql+psycopg://...
Max episodes: 20
============================================================

Fetching RSS feed... ✅
Found 470 episodes
Processing episode 1/470: ...
```

**NOT this error:**
```
ModuleNotFoundError: No module named 'feedparser' ❌
```

---

## Why This Happens

Railway's `railway.toml` configuration applies to **ALL services** by default:

```toml
[build]
builder = "dockerfile"
# dockerfilePath defaults to "Dockerfile"
```

Since we don't specify a path, Railway uses `Dockerfile` (the lightweight API image).

**You MUST override this in the Dashboard** for the ingestion service to use `Dockerfile.worker`.

---

## Verification Checklist

After configuring and redeploying:

- [ ] Railway Dashboard shows `Dockerfile Path: Dockerfile.worker`
- [ ] Build logs show `Using Detected Dockerfile: Dockerfile.worker`
- [ ] Build includes PyAV and ML dependencies
- [ ] Container starts without `ModuleNotFoundError`
- [ ] Ingestion begins processing episodes

---

## For API Service (Separate Configuration)

**API service should use the default `Dockerfile`:**

1. Go to **mirror-talk-api** service
2. **Settings** → **Build**
3. **Dockerfile Path:** Leave EMPTY (or set to `Dockerfile`)
4. **Settings** → **Deploy**
5. **Start Command:** Leave EMPTY (uses CMD from Dockerfile)
6. **Healthcheck:** Enable, path=`/health`, timeout=`300`

---

## Summary

| Service | Dockerfile | Start Command | Healthcheck |
|---------|-----------|---------------|-------------|
| **mirror-talk-api** | `Dockerfile` (default) | (empty) | ✅ Enable |
| **mirror-talk-ingestion** | `Dockerfile.worker` ⚠️ **MUST SET** | `python scripts/bulk_ingest.py --max-episodes 20 --no-confirm` | ❌ Disable |

---

## Common Mistakes

### ❌ Mistake #1: Not Setting Dockerfile Path
- **Symptom:** `ModuleNotFoundError: No module named 'feedparser'`
- **Fix:** Set `Dockerfile Path: Dockerfile.worker` in Dashboard

### ❌ Mistake #2: Wrong Start Command
- **Symptom:** API service runs ingestion script
- **Fix:** Clear start command for API service

### ❌ Mistake #3: Not Redeploying After Config Change
- **Symptom:** Still uses old configuration
- **Fix:** Click **Deploy** → **Redeploy** after saving settings

---

## Next Steps

1. ✅ **Configure Dockerfile path** in Railway Dashboard for ingestion service
2. ✅ **Redeploy** and watch build logs
3. ✅ **Verify** ingestion starts without errors
4. ✅ **Set `WHISPER_MODEL=tiny`** in Variables to avoid OOM
5. ✅ **Monitor** first ingestion run

**This configuration change is CRITICAL and cannot be skipped!** 🚨
