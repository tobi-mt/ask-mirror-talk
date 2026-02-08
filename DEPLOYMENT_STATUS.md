# Deployment Status & Verification Guide

## ✅ Changes Deployed (Latest Push)

### Memory Optimization (Commit: f3162f6)
- **Changed**: `EMBEDDING_PROVIDER` from `sentence_transformers` to `local`
- **Impact**: Reduced memory usage from ~300MB to ~0MB for embeddings
- **Reason**: Avoid OOM (Out of Memory) errors on Render starter plan (512MB RAM)

### Previous Fixes (Already Committed)
- ✅ psycopg3 dialect fix for SQLAlchemy compatibility
- ✅ CORS middleware for mirrortalkpodcast.com domains
- ✅ Docker runtime configuration with ffmpeg support
- ✅ Render 2026 plan compatibility (starter + basic-256mb)

---

## 🔍 Verification Steps

### 1. Monitor Render Dashboard
Go to: https://dashboard.render.com

**Check these metrics:**
- ✓ Build status (should succeed)
- ✓ Service status (should show "Live" after ~2-5 minutes)
- ✓ Memory usage (should stay under 400MB)
- ✓ No restart loops or OOM errors in logs

### 2. Test Health Endpoint
Once the service is live, test:

```bash
curl https://ask-mirror-talk.onrender.com/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "service": "ask-mirror-talk",
  "database": "connected"
}
```

### 3. Test Status Endpoint
```bash
curl https://ask-mirror-talk.onrender.com/status
```

**Expected response:**
```json
{
  "status": "ok",
  "episode_count": <number>,
  "total_chunks": <number>
}
```

### 4. Test CORS from WordPress
Open browser console on https://mirrortalkpodcast.com and run:

```javascript
fetch('https://ask-mirror-talk.onrender.com/health')
  .then(r => r.json())
  .then(data => console.log('✓ CORS works:', data))
  .catch(err => console.error('✗ CORS error:', err));
```

Should see: `✓ CORS works: {status: "healthy", ...}`

### 5. Test Question API
```bash
curl -X POST https://ask-mirror-talk.onrender.com/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What topics are discussed in the podcast?"}'
```

**Expected response:**
```json
{
  "answer": "<relevant answer>",
  "sources": [...]
}
```

---

## 🚨 Troubleshooting

### If Service Shows "Suspended" or "Failed"
1. Check logs in Render dashboard
2. Look for errors containing:
   - `MemoryError`
   - `Killed`
   - `OOM` (Out of Memory)
   - `psycopg`
   - Database connection errors

### If OOM Errors Persist
The local embeddings should fix this, but if issues continue:

**Option A: Optimize further**
- Reduce `CHUNK_SIZE` in render.yaml (1000 → 500)
- Use `WHISPER_MODEL=tiny` instead of `base`

**Option B: Upgrade plan**
- Change `plan: starter` to `plan: standard` in render.yaml
- Cost: $25/month (2GB RAM)
- Re-enable `sentence_transformers` for better quality

### If CORS Errors Occur
Check that WordPress site uses exactly:
- `https://mirrortalkpodcast.com` (no trailing slash)
- `https://www.mirrortalkpodcast.com` (no trailing slash)

### If Database Errors Occur
Check logs for:
- `CREATE EXTENSION IF NOT EXISTS vector` - should succeed
- Connection string format - should use `postgresql+psycopg://`

---

## 📊 Expected Memory Usage (Starter Plan: 512MB)

| Component | Memory |
|-----------|--------|
| FastAPI app | ~80MB |
| uvicorn worker | ~50MB |
| SQLAlchemy + psycopg3 | ~40MB |
| Local embeddings | ~0MB |
| OS overhead | ~50MB |
| **Total baseline** | **~220MB** |
| **Available for requests** | **~290MB** |

With local embeddings, you should have plenty of headroom for concurrent requests.

---

## 🎯 Next Steps

1. **Monitor first 30 minutes**
   - Watch memory metrics in Render dashboard
   - Check for any restart loops
   - Verify no OOM errors in logs

2. **Test API functionality**
   - Run all verification tests above
   - Test from WordPress site
   - Verify answers are reasonable quality

3. **Wait for Wednesday cron job**
   - Scheduled: 4 AM UTC (5 AM CET) every Wednesday
   - Check cron job logs after it runs
   - Verify new episodes are ingested

4. **Monitor quality vs. performance**
   - Local embeddings are fast but lower quality
   - Test answer relevance with real questions
   - Consider upgrading to Standard plan if needed

---

## 📞 Support Resources

- **Render Docs**: https://render.com/docs
- **Memory Issues**: https://render.com/docs/free#free-web-services
- **Postgres**: https://render.com/docs/databases
- **Docker**: https://render.com/docs/docker

---

**Last Updated**: January 2025  
**Deployment Method**: Git push to main branch  
**Auto-deploy**: Enabled (Render watches main branch)
