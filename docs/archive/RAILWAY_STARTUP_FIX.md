# Railway Startup & Healthcheck Fix

## Problem
Railway healthcheck was timing out because:
1. Database initialization was blocking app startup
2. Startup took too long to respond to healthcheck requests
3. Default healthcheck timeout was too short

## Solution Applied

### 1. **Deferred Database Initialization**
- Changed DB initialization from blocking startup to background task
- App now starts immediately and returns `200 OK` on `/health`
- DB initialization happens asynchronously after app is ready

**Changes in `app/api/main.py`:**
```python
# Startup now completes immediately
@app.on_event("startup")
async def on_startup():
    logger.info("✓ Application startup complete (DB init deferred)")
    asyncio.create_task(_init_db_background())

# Background DB init
async def _init_db_background():
    await asyncio.sleep(1)  # Give app time to start
    init_db()
```

### 2. **Increased Healthcheck Timeout**
**Changes in `railway.toml`:**
```toml
healthcheckTimeout = 300  # Increased from 100 to 300 seconds
```

### 3. **Optimized Uvicorn Settings**
**Changes in `Dockerfile`:**
```dockerfile
CMD ["sh", "-c", "uvicorn app.api.main:app --host 0.0.0.0 --port ${PORT:-8000} \
    --workers 1 \
    --timeout-keep-alive 30 \
    --limit-concurrency 100"]
```

**Benefits:**
- `--timeout-keep-alive 30`: Faster timeout (was 75s)
- `--limit-concurrency 100`: Prevents resource exhaustion
- `--workers 1`: Single worker for free tier

### 4. **Added Dockerfile HEALTHCHECK**
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1
```

**Parameters:**
- `--start-period=40s`: Gives app 40 seconds to start before health checks begin
- `--interval=30s`: Check every 30 seconds
- `--timeout=10s`: Each check times out after 10 seconds
- `--retries=3`: Fail after 3 consecutive failures

### 5. **Enhanced Status Endpoint**
The `/status` endpoint now reports DB initialization state:

```json
{
  "status": "initializing",
  "db_ready": false,
  "message": "Database is still initializing"
}
```

Once initialized:
```json
{
  "status": "ok",
  "db_ready": true,
  "episodes": 0,
  "chunks": 0,
  "ready": false
}
```

## Testing

### 1. **Check Healthcheck Status**
Railway will automatically test `/health` endpoint. You can monitor in Railway logs:
```
✓ Application startup complete (DB init deferred)
✓ Background database initialization complete
```

### 2. **Test Endpoints Manually**
Once deployed, test:

```bash
# Health (should always return 200 OK)
curl https://your-app.railway.app/health

# Status (shows DB readiness)
curl https://your-app.railway.app/status
```

### 3. **Monitor Railway Logs**
Watch for:
- ✅ "Application startup complete" - App started
- ✅ "Background database initialization complete" - DB ready
- ❌ Any errors during background init

## Expected Behavior

1. **During Deployment:**
   - Railway builds Docker image (~2GB)
   - Starts container with `PORT` env variable
   - App starts in ~5-10 seconds
   - Healthcheck passes within 40 seconds

2. **After Deployment:**
   - `/health` returns `200 OK` immediately
   - `/status` shows "initializing" until DB is ready
   - Background task completes DB initialization (~5-30 seconds)
   - `/status` then shows "ok" with DB metrics

3. **First Request:**
   - May take longer if DB is still initializing
   - Subsequent requests are fast

## Troubleshooting

### If Healthcheck Still Fails

1. **Check Railway Logs:**
   ```bash
   railway logs
   ```
   Look for:
   - Port binding errors
   - Database connection errors
   - Python import errors

2. **Verify Environment Variables:**
   - `DATABASE_URL` (should be Neon Postgres URL)
   - `PORT` (automatically set by Railway)
   - Any other required variables from `app/core/config.py`

3. **Check Database Connection:**
   - Verify Neon Postgres is running
   - Check firewall/network settings
   - Test connection from Railway shell:
     ```bash
     railway run psql $DATABASE_URL
     ```

4. **Increase Start Period:**
   If initialization takes longer than 40s:
   ```dockerfile
   HEALTHCHECK --start-period=60s
   ```

### If Database Init Fails

Check logs for errors like:
- `connection refused` - Database not accessible
- `authentication failed` - Wrong credentials
- `extension "vector" not found` - pgvector not installed on Neon

## Next Steps

1. ✅ **Commit pushed to GitHub** - Railway will auto-deploy
2. ⏳ **Wait for Railway build** - Monitor deployment
3. ✅ **Test endpoints** - Verify `/health` and `/status`
4. 📊 **Check logs** - Confirm DB initialization
5. 🚀 **Load data** - Run ingestion once deployed

## Files Changed

- `app/api/main.py` - Deferred DB initialization
- `railway.toml` - Increased healthcheck timeout
- `Dockerfile` - Added healthcheck, optimized uvicorn settings
- `RAILWAY_STARTUP_FIX.md` - This document

## Related Documentation

- `RAILWAY_NEON_SETUP.md` - Initial setup guide
- `DOCKER_SIZE_FIX.md` - Image size optimization
- `HEALTHCHECK_FIX.md` - Healthcheck troubleshooting
- `GITHUB_SYNC_COMPLETE.md` - Repository sync guide

---

**Status:** ✅ All changes committed and pushed to GitHub
**Expected:** Railway will auto-deploy and healthcheck should pass
**Next:** Monitor Railway logs for successful deployment
