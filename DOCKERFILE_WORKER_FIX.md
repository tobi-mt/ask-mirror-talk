# Dockerfile.worker Fix - Module Not Found Error

## Problem
Ingestion service was failing with:
```
ModuleNotFoundError: No module named 'feedparser'
```

Even though `feedparser` was listed in the pip install command.

## Root Cause
**`Dockerfile.worker` was missing the final package installation step** (`pip install -e .`).

Without this step:
- The `app` package wasn't properly installed
- Python couldn't find the installed dependencies
- Imports failed even though packages were installed

## Fix Applied

### 1. Added Missing Package Installation
```dockerfile
# Install the package to make imports work properly
RUN pip install --no-cache-dir --no-deps -e . \
    && rm -rf /root/.cache/pip /tmp/* /var/tmp/*
```

### 2. Added PostgreSQL Runtime Support
```dockerfile
libpq5 \
```

### 3. Updated Cache-Busting Timestamp
```dockerfile
ENV REBUILD_DATE=2026-02-13-17-30
```

## Changes Made

| File | Change |
|------|--------|
| `Dockerfile.worker` | Added `pip install -e .` step |
| `Dockerfile.worker` | Added `libpq5` dependency |
| `Dockerfile.worker` | Updated rebuild timestamp |
| `Dockerfile` | Updated rebuild timestamp |

## Expected Result

After Railway rebuilds with the updated `Dockerfile.worker`:
- ✅ All Python packages will be properly installed
- ✅ `feedparser` and other imports will work
- ✅ Ingestion script will start without module errors
- ✅ Database connections will work (via libpq5)

## Railway Redeploy Instructions

Since the Dockerfile has changed, Railway will automatically rebuild when you redeploy:

1. Go to Railway Dashboard → **mirror-talk-ingestion** service
2. Click **Deploy** (top right)
3. Watch the build logs - should take 5-7 minutes
4. Verify the build completes without errors
5. Check runtime logs for ingestion progress

## Verification

After successful deployment, you should see:
```
============================================================
INGESTING ALL EPISODES FROM RSS
============================================================
RSS URL: https://anchor.fm/s/261b1464/podcast/rss
Database: postgresql+psycopg://...
Max episodes: UNLIMITED
============================================================
Fetching RSS feed...
Found X episodes
Processing episode 1/X: [Episode Title]
...
```

**NOT** the previous error:
```
ModuleNotFoundError: No module named 'feedparser'
```

## Status

✅ **Fixed and pushed** to both GitHub and Bitbucket  
⏳ **Railway will auto-rebuild** on next deploy  
⏳ **Verify** in Railway logs after rebuild completes

---

## Why This Happened

The `Dockerfile.worker` was incomplete because:
1. It was copied from an earlier version
2. The final `pip install -e .` step was accidentally omitted
3. This step is crucial for editable package installation

The fix ensures the package is properly installed so Python can find all modules.
