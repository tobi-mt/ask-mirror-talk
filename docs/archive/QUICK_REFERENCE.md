# 🚀 Quick Deployment Reference

## Current Configuration

| Setting | Value | Notes |
|---------|-------|-------|
| **Render Plan** | starter | $7/month, 512MB RAM |
| **Database Plan** | basic-256mb | $6/month, pgvector enabled |
| **Cron Job** | Free | Wednesdays 5 AM CET |
| **Embedding Provider** | local | Low memory, fast |
| **Whisper Model** | base | Good quality/speed balance |
| **CORS Domains** | mirrortalkpodcast.com | www included |

## Service URLs

- **API Base**: `https://ask-mirror-talk.onrender.com`
- **Health Check**: `https://ask-mirror-talk.onrender.com/health`
- **Status**: `https://ask-mirror-talk.onrender.com/status`
- **API Docs**: `https://ask-mirror-talk.onrender.com/docs`
- **Render Dashboard**: `https://dashboard.render.com`

## Key Files Modified

```
✅ render.yaml              - Render Blueprint (plans, env vars, schedule)
✅ Dockerfile               - Docker config with ffmpeg
✅ app/core/config.py       - psycopg3 URL validator, CORS config
✅ app/api/main.py          - CORS middleware
✅ app/core/db.py           - Database init, logging
✅ app/indexing/embeddings.py - Singleton pattern, local fallback
```

## Quick Test Commands

### Test Health (Should return immediately)
```bash
curl https://ask-mirror-talk.onrender.com/health
```

### Test Status (Requires DB connection)
```bash
curl https://ask-mirror-talk.onrender.com/status
```

### Test Question API
```bash
curl -X POST https://ask-mirror-talk.onrender.com/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is discussed in the podcast?"}'
```

## Monitoring Checklist

After deployment (check in Render dashboard):

- [ ] Build completes successfully
- [ ] Service status shows "Live" (not "Suspended")
- [ ] Memory usage < 400MB
- [ ] No "Killed" or "OOM" errors in logs
- [ ] Health endpoint returns 200 OK
- [ ] Status endpoint shows episode count
- [ ] CORS test from WordPress works
- [ ] Question API returns relevant answers

## Common Issues & Quick Fixes

### Service Won't Start
- Check logs for `psycopg` errors → database URL format issue
- Check logs for `ModuleNotFoundError` → dependency issue
- Check logs for `MemoryError` or `Killed` → OOM (see below)

### Out of Memory
- Should be fixed with `EMBEDDING_PROVIDER=local`
- If still occurring, reduce `CHUNK_SIZE` to 500
- Or upgrade to `plan: standard` ($25/month, 2GB RAM)

### CORS Not Working
- Ensure WordPress uses exact domains in `ALLOWED_ORIGINS`
- Check browser console for error messages
- Verify no trailing slashes in URLs

### Database Connection Failed
- Check if pgvector extension installed
- Verify `DATABASE_URL` format: `postgresql+psycopg://...`
- Check Render database is running (basic-256mb plan)

## Upgrade Path (If Needed)

If local embeddings don't provide good enough quality:

1. Edit `render.yaml`:
   ```yaml
   plan: standard  # Change from 'starter'
   
   - key: EMBEDDING_PROVIDER
     value: sentence_transformers  # Change from 'local'
   ```

2. Commit and push:
   ```bash
   git add render.yaml
   git commit -m "Upgrade to Standard plan for better embeddings"
   git push origin main
   ```

3. Cost impact: +$18/month ($25 vs $7)

## Cron Job Details

- **Schedule**: `0 4 * * 3` (Wednesday 4 AM UTC = 5 AM CET)
- **Command**: `python scripts/bulk_ingest.py --max-episodes 3`
- **Purpose**: Auto-ingest new podcast episodes
- **First run**: Next Wednesday after deployment

## Support & Documentation

- `DEPLOYMENT_STATUS.md` - Detailed verification guide
- `MEMORY_FIX.md` - Memory optimization details
- `RENDER_PLAN_UPDATE.md` - 2026 plan compatibility
- `DEPLOYMENT_READY.md` - Original deployment guide
- `README.md` - Project overview

---

**Last Push**: Commit f3162f6 (Memory optimization)  
**Status**: ✅ Ready for production  
**Next Action**: Monitor deployment in Render dashboard
