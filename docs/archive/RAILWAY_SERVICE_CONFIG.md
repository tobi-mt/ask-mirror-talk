# Railway Service Configuration Guide

## Problem
Your deployment is failing because:
1. **Wrong Dockerfile**: Railway is using the heavy `Dockerfile.worker` (1.5GB with transcription) for the API service
2. **Memory crash**: The heavy image causes OOM errors on Railway's free tier
3. **Healthcheck failure**: The service can't start due to memory issues

## Solution: Configure Each Service Separately

Railway requires you to configure the Dockerfile path **per service** in the Dashboard.

---

## Service 1: `mirror-talk-api` (FastAPI Service)

### Build Settings
1. Go to: **Railway Dashboard** → **mirror-talk-api** → **Settings** → **Build**
2. Set **Dockerfile Path**: `Dockerfile.api`
3. Save changes

### Deploy Settings
1. Go to: **Settings** → **Deploy**
2. **Start Command**: Leave empty (uses default CMD from Dockerfile)
3. **Healthcheck**: 
   - Enable: ✅ Yes
   - Path: `/health`
   - Timeout: `300` seconds
   - Interval: `60` seconds

### Environment Variables
Already configured in Railway (DATABASE_URL, OPENAI_API_KEY, etc.)

### Expected Behavior
- Uses lightweight Dockerfile (~200MB)
- Fast startup, low memory usage
- Healthcheck passes after 30-60 seconds
- API available at your Railway domain

---

## Service 2: `mirror-talk-ingestion` (Worker Service)

### Build Settings
1. Go to: **Railway Dashboard** → **mirror-talk-ingestion** → **Settings** → **Build**
2. Set **Dockerfile Path**: `Dockerfile.worker`
3. Save changes

### Deploy Settings
1. Go to: **Settings** → **Deploy**
2. **Start Command**: `python scripts/bulk_ingest.py --max-episodes 20 --no-confirm`
3. **Healthcheck**: 
   - Enable: ❌ No (this is a one-time job, not a long-running service)

### Environment Variables
1. Go to: **Settings** → **Variables**
2. Add/Update:
   - `WHISPER_MODEL`: `tiny` (prevents OOM)
   - `DATABASE_URL`: (same as API service)
   - `OPENAI_API_KEY`: (same as API service)

### Expected Behavior
- Uses heavy Dockerfile with transcription (~1.5GB)
- Runs once, exits after completion
- Processes 20 episodes per batch
- No healthcheck needed (one-time job)

---

## Step-by-Step Fix Instructions

### 1. Commit and Push Changes
```bash
cd /Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk
git add -A
git commit -m "fix: Rename Dockerfile to Dockerfile.api, update railway.toml"
git push origin main
```

### 2. Configure API Service
1. Open Railway Dashboard: https://railway.app/dashboard
2. Select **mirror-talk-api** service
3. Go to **Settings** → **Build**
4. Scroll to **Dockerfile Path** field
5. Enter: `Dockerfile.api`
6. Click **Save**
7. Go to **Settings** → **Deploy**
8. Enable **Healthcheck**:
   - Path: `/health`
   - Timeout: `300`
9. Click **Save**
10. Click **Deploy** button (top right)

### 3. Configure Ingestion Service
1. Select **mirror-talk-ingestion** service
2. Go to **Settings** → **Build**
3. Set **Dockerfile Path**: `Dockerfile.worker`
4. Click **Save**
5. Go to **Settings** → **Deploy**
6. Set **Start Command**: `python scripts/bulk_ingest.py --max-episodes 20 --no-confirm`
7. **Disable Healthcheck** (uncheck the box)
8. Click **Save**
9. Go to **Settings** → **Variables**
10. Add: `WHISPER_MODEL` = `tiny`
11. Click **Deploy** button

### 4. Monitor Deployment
Watch the build logs in Railway Dashboard:
- **API service**: Should build in ~2-3 minutes, start successfully
- **Ingestion service**: Should build in ~5-7 minutes, run ingestion, then exit

---

## Troubleshooting

### API Service Still Fails
- Check: Is `Dockerfile.api` path correct in Build settings?
- Check: Does healthcheck show `/health` path?
- Check: Are DATABASE_URL and OPENAI_API_KEY set?

### Ingestion Service OOM
- Check: Is `WHISPER_MODEL=tiny` set?
- Reduce batch size: Change start command to `--max-episodes 10`
- Upgrade Railway plan for more memory

### Build Fails
- Check: Did you push the renamed Dockerfile.api to Git?
- Check: Is branch name correct in Railway (usually `main`)?

---

## Expected Results

### After Fix
✅ **API Service**:
- Memory usage: ~150-200MB
- Startup time: 30-60 seconds
- Healthcheck: Passing
- Status: Running

✅ **Ingestion Service**:
- Memory usage: ~500MB-1GB (spikes during transcription)
- Runtime: 10-30 minutes (for 20 episodes)
- Exit code: 0 (success)
- Status: Exited (this is normal for one-time jobs)

---

## Notes

- **Railway.toml limitations**: Railway doesn't support per-service Dockerfile paths in `railway.toml`, so you MUST configure them in the Dashboard
- **Ingestion is a job, not a service**: It runs once and exits. Don't enable healthcheck for it.
- **Memory optimization**: Using `tiny` Whisper model and lightweight API Dockerfile keeps memory under Railway's free tier limits

---

## Next Steps

1. ✅ Rename Dockerfile → Dockerfile.api
2. ✅ Update railway.toml
3. ⏳ Commit and push changes
4. ⏳ Configure Railway Dashboard (see Step-by-Step above)
5. ⏳ Monitor deployment logs
6. ⏳ Test API at Railway domain
7. ⏳ Verify episodes are loaded in database
