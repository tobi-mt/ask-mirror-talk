# 🔥 FINAL TROUBLESHOOTING - If Healthcheck Still Fails

## All Optimizations Applied ✅

1. ✅ **Docker image size**: Reduced from 9GB to 2GB
2. ✅ **Lazy imports**: ML models, ingestion pipeline  
3. ✅ **Lazy DB engine**: No connection at startup
4. ✅ **Background DB init**: Delayed 2 seconds
5. ✅ **Minimal uvicorn flags**: Fastest possible startup
6. ✅ **30s healthcheck start period**: Realistic timing

## If It STILL Fails

There are only a few possible reasons left:

### 1. Missing Environment Variables

**Symptom:** App crashes immediately with import/config errors

**Fix:** Check Railway Variables tab has all required vars:
```bash
DATABASE_URL=postgresql+psycopg://...
RSS_URL=https://anchor.fm/s/261b1464/podcast/rss
ENVIRONMENT=production
EMBEDDING_PROVIDER=local
TRANSCRIPTION_PROVIDER=faster_whisper
WHISPER_MODEL=base
```

**Test in Railway Shell:**
```bash
railway run env | grep DATABASE_URL
```

### 2. Railway Free Tier Limitations

**Symptom:** "Out of memory" or "CPU limit exceeded"

**Current Resources:**
- Image size: ~2GB
- Runtime memory: Should be <512MB
- CPU: Minimal (no ML at startup)

**If hitting limits:**
- Railway free tier has strict resource limits
- May need to upgrade to Hobby plan ($5/month)
- Check Railway dashboard → "Metrics" tab

### 3. Port Binding Issues

**Symptom:** Healthcheck fails but no errors in logs

**Current Setup:**
```bash
# Dockerfile CMD
uvicorn app.api.main:app --host 0.0.0.0 --port ${PORT:-8000}

# Railway sets PORT dynamically
```

**Debug:**
```bash
# Check if PORT is set
railway run echo $PORT

# Test locally
docker build -t test .
docker run -e PORT=8000 -p 8000:8000 test
curl http://localhost:8000/health
```

### 4. FastAPI/Uvicorn Startup Crash

**Symptom:** Container starts but crashes before healthcheck

**Check Railway Logs for:**
```
ModuleNotFoundError: No module named 'xxx'
ImportError: cannot import name 'xxx'
RuntimeError: xxx
SyntaxError: xxx
```

**Common Causes:**
- Missing Python dependency in `pyproject.toml`
- Circular import
- Config validation error

**Debug:**
```bash
# Test in Railway shell
railway run python -c "from app.api.main import app; print('OK')"
```

### 5. Neon Database Unreachable

**Symptom:** App starts but background DB init fails

**This is OK!** The app should still pass healthcheck.

**Check:**
- Neon project is active (not paused/deleted)
- DATABASE_URL is correct
- Neon allows connections from Railway IPs

**Test Connection:**
```bash
# From Railway shell
railway run python -c "import psycopg; conn = psycopg.connect('$DATABASE_URL'); print('✓ Connected')"
```

## Alternative: Skip Railway, Use Render

If Railway continues to fail, **Render** is a great alternative:

### Why Render Might Work Better:
- More forgiving healthcheck timeouts
- Better free tier resources
- PostgreSQL included
- Simpler configuration

### Quick Migration:
1. Go to https://render.com
2. Connect GitHub repo
3. Create "Web Service"
4. Set build command: `pip install -e .`
5. Set start command: `uvicorn app.api.main:app --host 0.0.0.0 --port $PORT`
6. Add environment variables
7. Create PostgreSQL database (free tier)
8. Connect and deploy

**Render Advantages:**
- Healthcheck timeout: 5 minutes (vs Railway's 100s)
- Better logging and debugging
- PostgreSQL with pgvector built-in

## Nuclear Option: Simplify Health Endpoint

If absolutely nothing works, make the healthcheck endpoint even simpler:

```python
@app.get("/health")
def health():
    """Ultra-simple healthcheck - returns immediately."""
    return {"ok": True}  # Even simpler JSON
```

Remove ALL logic from startup:
```python
@app.on_event("startup")
async def on_startup():
    # Do literally nothing
    pass
```

This guarantees the app responds within seconds.

## Debug Checklist

- [ ] Check Railway logs for specific errors
- [ ] Verify all environment variables are set
- [ ] Test Docker image builds locally
- [ ] Check Railway Metrics for resource usage
- [ ] Try deploying to Render as backup
- [ ] Test `/health` endpoint locally
- [ ] Check Neon database is accessible
- [ ] Verify GitHub webhook triggered deployment

## Get Railway Logs

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# View logs
railway logs

# Open shell
railway shell
```

## Contact Information

If all else fails:
- **Railway Support**: https://railway.app/help
- **Railway Discord**: https://discord.gg/railway
- **Neon Support**: https://neon.tech/docs/introduction/support

## Expected Timeline

With all current optimizations:
- **Build**: 70-80 seconds
- **Container start**: 5-10 seconds  
- **Healthcheck**: Should pass at attempt #2-3 (20-30 seconds)

**Total**: Under 2 minutes from push to healthy

---

**Current Status:** Waiting for Railway to rebuild with latest optimizations
**Next**: Monitor Railway dashboard for deployment status
**If this fails**: Consider migrating to Render or upgrading Railway plan
