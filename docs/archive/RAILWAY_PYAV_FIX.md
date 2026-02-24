# Railway Ingestion Fix - PyAV/FFmpeg Dependencies

## Problem
Railway ingestion was failing with:
```
ModuleNotFoundError: No module named 'av'
RuntimeError: faster-whisper is not installed. Install optional dependency 'transcription'.
```

## Root Cause
- `faster-whisper` requires `PyAV` (the `av` Python module)
- `PyAV` requires FFmpeg system libraries (libavcodec, libavformat, etc.)
- Railway's Dockerfile wasn't installing PyAV dependencies or the av module
- The project uses Dockerfile builds (not Nixpacks), so `nixpacks.toml` was ignored

## Solution Applied

### 1. Updated `Dockerfile` and `Dockerfile.worker`
Added FFmpeg development libraries and build tools:
```dockerfile
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        libavcodec-dev \
        libavformat-dev \
        libavutil-dev \
        libswresample-dev \
        gcc \
        python3-dev \
        ...
```

### 2. Added PyAV to pip install
```dockerfile
RUN pip install --no-cache-dir \
    ...
    av>=12.0.0 \
    faster-whisper==1.0.3 \
    ...
```
Removed `--no-deps` flag from faster-whisper to ensure all dependencies are installed.

### 3. Created `requirements.txt` (for reference)
Added all dependencies including:
- `av>=12.0.0` (PyAV for audio processing)
- `faster-whisper>=1.0.0`
- `sentence-transformers>=2.6.0`

### 4. Created `nixpacks.toml` (not used, but for future reference)
Note: This file is ignored because `railway.toml` specifies Dockerfile builds.

### 5. Updated `pyproject.toml`
Made transcription and embeddings core dependencies instead of optional.

## Deployment

The fix has been:
✅ Committed to git
✅ Pushed to Bitbucket (commits `4213c06`, `31526d2`, `9d8042c`)

Railway will automatically:
1. Detect the push
2. Rebuild both services with new Dockerfile
3. Install FFmpeg libraries (libavcodec, libavformat, etc.)
4. Install PyAV module (av>=12.0.0)
5. Install faster-whisper with dependencies
6. Deploy the updated services

## Next Steps

### 1. Wait for Railway Rebuild
- Check Railway dashboard for deployment progress
- Both `mirror-talk-api` and `mirror-talk-ingestion` will rebuild
- Should take 5-10 minutes

### 2. Verify the Fix
Once deployed, check the ingestion logs:
```bash
railway logs --service mirror-talk-ingestion
```

You should see:
- ✅ FFmpeg libraries installed
- ✅ PyAV module loaded
- ✅ Transcription starting without errors

### 3. Run Full Ingestion

After successful deployment, you can run the full ingestion:

**Option A: Via Railway Dashboard**
1. Go to `mirror-talk-ingestion` service
2. Settings → Deploy → Custom Start Command
3. Change to: `python scripts/bulk_ingest.py --max-episodes 100 --no-confirm`
4. Click Deploy

**Option B: Via Railway Shell**
```bash
railway run bash
python scripts/bulk_ingest.py --max-episodes 100 --no-confirm
```

**Option C: Multiple Batches**
Process in smaller batches to avoid timeouts:
```bash
# Batch 1
python scripts/bulk_ingest.py --max-episodes 50 --no-confirm

# Wait for completion, then batch 2
python scripts/bulk_ingest.py --max-episodes 50 --no-confirm

# Repeat until all episodes loaded
```

## Verification Commands

### Check episode count:
```bash
railway run python -c "from app.core.db import SessionLocal; from app.storage.models import Episode; db = SessionLocal()(); print(f'Episodes: {db.query(Episode).count()}')"
```

### Check chunk count:
```bash
railway run python -c "from app.core.db import SessionLocal; from sqlalchemy import text; db = SessionLocal()(); print(f'Chunks: {db.execute(text(\"SELECT COUNT(*) FROM chunks\")).scalar()}')"
```

### Test API:
```bash
curl -X POST "https://your-railway-app.railway.app/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Mirror Talk about?"}'
```

## Troubleshooting

### If build still fails:
1. Check Railway build logs for FFmpeg installation
2. Verify `nixpacks.toml` is in root directory
3. Check `requirements.txt` includes `av>=12.0.0`

### If transcription still fails:
1. Check that `av` module is importable:
   ```bash
   railway run python -c "import av; print('PyAV version:', av.__version__)"
   ```
2. Verify FFmpeg is available:
   ```bash
   railway run ffmpeg -version
   ```

### If memory issues occur:
- Process in smaller batches (--max-episodes 20)
- Upgrade Railway plan for more memory
- Use smaller Whisper model: `WHISPER_MODEL=tiny`

## Files Changed

- ✅ `Dockerfile` - Added FFmpeg dev libraries, gcc, python3-dev, av module
- ✅ `Dockerfile.worker` - Added FFmpeg dev libraries, gcc, python3-dev
- ✅ `requirements.txt` - Created with all dependencies (for reference)
- ✅ `nixpacks.toml` - Created (not used, but for future Nixpacks builds)
- ✅ `pyproject.toml` - Updated to make dependencies non-optional
- ✅ `scripts/bulk_ingest.py` - Already fixed session bug

## Success Indicators

You'll know it's working when you see in logs:
```
2026-02-13 XX:XX:XX | INFO | app.ingestion.pipeline_optimized | Processing episode: ...
2026-02-13 XX:XX:XX | INFO | app.ingestion.pipeline_optimized |   ├─ Downloaded audio: episode_X.mp3
2026-02-13 XX:XX:XX | INFO | app.ingestion.pipeline_optimized |   ├─ Transcribing (model=base)...
2026-02-13 XX:XX:XX | INFO | faster_whisper | Processing audio with duration XX:XX.XXX
2026-02-13 XX:XX:XX | INFO | faster_whisper | Detected language 'en' with probability 0.99
2026-02-13 XX:XX:XX | INFO | app.ingestion.pipeline_optimized |   ├─ Transcription complete (XXX segments)
2026-02-13 XX:XX:XX | INFO | app.ingestion.pipeline_optimized |   └─ ✓ Episode complete
```

## Timeline

- **Now:** Waiting for Railway rebuild (~5-10 min)
- **After rebuild:** Run ingestion in batches
- **Estimated time:** 50 episodes = ~2 hours, 467 episodes = ~20 hours

## Resources

- Railway Dashboard: https://railway.app
- Neon Database: https://console.neon.tech
- API Status: https://your-app.railway.app/status
- Admin Panel: https://your-app.railway.app/admin
