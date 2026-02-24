# Quick Fix Reference - Exit Status 1 Error

## What Was Wrong
- **Database URL**: Render uses `postgres://`, SQLAlchemy 2.0+ needs `postgresql+psycopg://`
- **Missing ffmpeg**: Required for audio transcription, not installed by default
- **No error visibility**: Silent failures during database initialization

## What Was Fixed

### 1. Database URL Auto-Conversion
**File**: `app/core/config.py`
```python
@field_validator("database_url")
@classmethod
def fix_database_url(cls, v: str) -> str:
    if v.startswith("postgres://"):
        return v.replace("postgres://", "postgresql+psycopg://", 1)
    return v
```

### 2. System Dependencies Installation
**File**: `render-build.sh` (NEW)
```bash
apt-get update
apt-get install -y ffmpeg
pip install -e '.[transcription,embeddings]'
```

**File**: `render.yaml`
```yaml
buildCommand: "./render-build.sh"
```

### 3. Enhanced Error Logging
**Files**: `app/api/main.py`, `app/core/db.py`
- Shows startup status, environment, database URL
- Logs each initialization step
- Full error messages with stack traces

## Deploy Now

```bash
# Commit and push
git add .
git commit -m "Fix deployment: DB URL compatibility, ffmpeg install, enhanced logging"
git push origin main

# Render auto-deploys on push
# Watch logs at: https://dashboard.render.com
```

## Verify Success

```bash
# Check health endpoint
curl https://your-app.onrender.com/health
# Expected: {"status": "ok"}

# Check status endpoint  
curl https://your-app.onrender.com/status
# Expected: {"status": "ok", "episodes": 0, "chunks": 0, ...}
```

## Look for in Logs

✓ Build phase:
```
Installing system dependencies...
✓ System dependencies installed
✓ Python dependencies installed
```

✓ Startup phase:
```
Starting Ask Mirror Talk API
Environment: production
Database URL: postgresql+psycopg://...
✓ pgvector extension enabled
✓ Database tables created/verified
✓ Application startup complete
```

## If It Still Fails

1. Check build logs for ffmpeg installation errors
2. Check startup logs for database connection errors
3. Verify DATABASE_URL env var in Render dashboard
4. Confirm database is running and accessible
5. Check that render-build.sh is executable (git ls-files -s render-build.sh should show 100755)

## Cost Breakdown (2026 Pricing)
- Web Service: $7/mo (starter)
- Database: $6/mo (basic-256mb)
- Cron Job: Free
- **Total: ~$13-15/mo**
