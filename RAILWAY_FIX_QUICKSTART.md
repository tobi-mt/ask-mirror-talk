# 🚀 RAILWAY FIX - QUICK REFERENCE

## The Problem
Your deployment is **using the wrong Dockerfile**:
- Railway is using `Dockerfile.worker` (1.5GB) for the API service
- This causes **memory crashes** and **healthcheck failures**

## The Fix
Configure each Railway service to use the **correct Dockerfile**:
- `mirror-talk-api` → `Dockerfile.api` (lightweight, 200MB)
- `mirror-talk-ingestion` → `Dockerfile.worker` (heavy, 1.5GB)

---

## ⚡ Quick Steps (Do This Now)

### 1. Open Railway Dashboard
Go to: https://railway.app/dashboard

### 2. Configure API Service
**mirror-talk-api** → **Settings** → **Build**:
- **Dockerfile Path**: `Dockerfile.api` ✅
- Click **Save**

**Settings** → **Deploy**:
- **Healthcheck**: Enable ✅
  - Path: `/health`
  - Timeout: `300`
- Click **Save**
- Click **Deploy** (top right) 🚀

### 3. Configure Ingestion Service
**mirror-talk-ingestion** → **Settings** → **Build**:
- **Dockerfile Path**: `Dockerfile.worker` ✅
- Click **Save**

**Settings** → **Deploy**:
- **Start Command**: `python scripts/bulk_ingest.py --max-episodes 20 --no-confirm`
- **Healthcheck**: Disable ❌
- Click **Save**

**Settings** → **Variables**:
- Add: `WHISPER_MODEL` = `tiny` ✅
- Click **Save**
- Click **Deploy** (top right) 🚀

---

## ✅ Expected Results

### API Service
- Build time: 2-3 minutes
- Memory: ~150-200MB
- Status: **Running** (green)
- Healthcheck: **Passing**

### Ingestion Service
- Build time: 5-7 minutes
- Memory: ~500MB-1GB
- Status: **Exited** (this is normal - it's a one-time job)
- Logs: "Ingestion complete"

---

## 📝 What Changed

| File | Change |
|------|--------|
| `Dockerfile` → `Dockerfile.api` | Renamed for clarity |
| `railway.toml` | Updated with configuration instructions |
| `RAILWAY_SERVICE_CONFIG.md` | Full step-by-step guide |

---

## 🆘 Troubleshooting

### "I don't see Dockerfile Path field"
- Click **Settings** → **Build** → scroll down
- Look for "Docker" section

### "API still fails after deploy"
- Check: Did you set `Dockerfile.api` path?
- Check: Did you click **Deploy** after saving?
- Wait 2-3 minutes for build to complete

### "Ingestion OOM error"
- Check: Is `WHISPER_MODEL=tiny` set?
- Try reducing batch: `--max-episodes 10`

---

## 📚 Full Documentation
See: `RAILWAY_SERVICE_CONFIG.md` for detailed instructions

---

## ✨ Changes Pushed to Git
All changes are committed and pushed to `main` branch.
Railway will auto-deploy after you configure Dockerfile paths.
