# Docker Runtime Fix - Exit Status 1 Resolution

## Issue Encountered

**Error during deployment:**
```
==> Running build command './render-build.sh'...
Installing system dependencies...
Reading package lists...
E: List directory /var/lib/apt/lists/partial is missing. 
   - Acquire (30: Read-only file system)
==> Build failed 😞
```

## Root Cause

Render's **Python runtime** has a **read-only filesystem** and doesn't allow running `apt-get` commands. This means we cannot install system dependencies like ffmpeg, which is required by the `faster-whisper` library for podcast transcription.

## Solution

**Switch from Python runtime to Docker runtime** in `render.yaml`. Your project already has a Dockerfile with ffmpeg pre-installed, so this is the perfect solution!

## Changes Made

### 1. `render.yaml` - Web Service

**Before:**
```yaml
- type: web
  name: ask-mirror-talk
  runtime: python
  buildCommand: "./render-build.sh"
  startCommand: "uvicorn app.api.main:app --host 0.0.0.0 --port $PORT --workers 1"
```

**After:**
```yaml
- type: web
  name: ask-mirror-talk
  runtime: docker  # Changed from 'python'
  dockerfilePath: ./Dockerfile
  dockerContext: .
  # No buildCommand or startCommand needed - Docker handles it
```

### 2. `render.yaml` - Cron Job

**Before:**
```yaml
- type: cron
  name: mirror-talk-ingestion
  runtime: python
  buildCommand: "./render-build.sh"
  startCommand: "python scripts/bulk_ingest.py --max-episodes 3"
```

**After:**
```yaml
- type: cron
  name: mirror-talk-ingestion
  runtime: docker  # Changed from 'python'
  dockerfilePath: ./Dockerfile
  dockerContext: .
  dockerCommand: python scripts/bulk_ingest.py --max-episodes 3
```

### 3. `Dockerfile` - Use Render's PORT Variable

**Before:**
```dockerfile
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--limit-concurrency", "10"]
```

**After:**
```dockerfile
ENV PORT=8000
CMD uvicorn app.api.main:app --host 0.0.0.0 --port ${PORT} --workers 1 --limit-concurrency 10
```

### 4. Removed `render-build.sh`

This build script is no longer needed because Docker handles all the build steps.

## Why This Works

### Python Runtime Limitations
- ❌ Read-only filesystem after initial setup
- ❌ Cannot run `apt-get` commands
- ❌ Cannot install system packages (ffmpeg)
- ✅ Fast deployment
- ✅ Simple for pure Python apps

### Docker Runtime Benefits
- ✅ Full control over build environment
- ✅ Can install system packages during image build
- ✅ Your Dockerfile already has everything configured
- ✅ Same cost as Python runtime
- ⚠️ Slightly slower build time (minimal difference)

## Deployment

```bash
# Commit changes
git add Dockerfile render.yaml
git rm render-build.sh
git commit -m "Fix: Switch to Docker runtime for ffmpeg support"
git push origin main
```

Render will automatically:
1. Detect the push
2. Build the Docker image (includes ffmpeg installation)
3. Start the web service
4. Schedule the cron job
5. Run health checks
6. Go live! 🚀

## Expected Build Output

```
==> Building Docker image from Dockerfile
Step 1/8 : FROM python:3.11-slim
Step 2/8 : RUN apt-get update && apt-get install -y ffmpeg
 ---> Running in xxx
✓ ffmpeg installed successfully
Step 3/8 : RUN pip install -e ".[transcription,embeddings]"
✓ Python packages installed
Step 4/8 : COPY app /app/app
✓ Application code copied
==> Successfully built Docker image
==> Deploying...
==> Starting service...
Starting Ask Mirror Talk API
✓ pgvector extension enabled
✓ Database tables created/verified
✓ Application startup complete
==> Health check passed
==> Service is live!
```

## Cost Impact

**No cost change!** Docker runtime costs the same as Python runtime on Render.

- Web Service (Docker): $7/month (starter)
- Database: $6/month (basic-256mb)
- Cron Job (Docker): FREE
- **Total: ~$13-15/month**

## Advantages of Docker Runtime

1. **System Dependencies**: Full control - can install ffmpeg, imagemagick, etc.
2. **Reproducibility**: Same environment locally and on Render
3. **Flexibility**: Can use any base image (Python, Node, custom)
4. **Debugging**: Easier to test locally with `docker build` and `docker run`
5. **Version Control**: Dockerfile is committed to git

## Dockerfile Features (Already Configured)

Your Dockerfile already includes:

✅ **System Dependencies**
```dockerfile
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl ffmpeg
```

✅ **Python Environment**
```dockerfile
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
```

✅ **Application Setup**
```dockerfile
COPY pyproject.toml README.md /app/
RUN pip install -e ".[transcription,embeddings]"
COPY app /app/app
COPY scripts /app/scripts
```

✅ **Runtime Configuration**
```dockerfile
ENV PORT=8000
CMD uvicorn app.api.main:app --host 0.0.0.0 --port ${PORT} --workers 1
```

## Troubleshooting

### If Docker build fails:
1. Check Dockerfile syntax
2. Verify base image is available (python:3.11-slim)
3. Check build logs for specific errors

### If service exits after successful build:
1. Check logs for database connection errors
2. Verify DATABASE_URL environment variable
3. Confirm pgvector extension can be created
4. Check application startup logs

### If health check fails:
1. Verify `/health` endpoint works
2. Check that service is listening on ${PORT}
3. Review application logs

## Summary

The "Read-only file system" error was blocking ffmpeg installation. By switching to Docker runtime, we leverage your existing Dockerfile that already has ffmpeg configured. This is the correct solution for applications that need system dependencies beyond what Python's runtime provides.

**Status:** ✅ Ready to deploy
**Cost:** ✅ Unchanged ($13-15/month)
**Performance:** ✅ Same as Python runtime
**Complexity:** ✅ Minimal (you already have a Dockerfile)

Deploy now and your service should start successfully! 🚀
