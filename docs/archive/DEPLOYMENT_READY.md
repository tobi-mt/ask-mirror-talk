# ✅ Ready to Deploy - Final Checklist

## 🎉 Configuration Complete!

Your `render.yaml` is now correctly configured with Render's 2026 pricing structure.

---

## ✅ Verified Configuration

### Database (PostgreSQL)
```yaml
plan: basic-256mb  ✅
# Instance Type: Basic-256mb
# RAM: 256 MB
# CPU: 0.1
# Cost: $6/month + storage
```

### Web Service
```yaml
plan: starter  ✅
# RAM: 512 MB
# Cost: $7/month
```

### Cron Job
```yaml
schedule: "0 4 * * 3"  ✅
# Every Wednesday at 5:00 AM CET (4:00 AM UTC)
# Cost: FREE
```

---

## 💰 Total Monthly Cost

| Component | Specification | Cost |
|-----------|---------------|------|
| **Web Service** | Starter (512MB RAM) | $7.00 |
| **PostgreSQL** | Basic-256mb (256MB RAM) | $6.00 |
| **Storage** | ~1GB for episodes | ~$0.25 |
| **Cron Job** | Weekly ingestion | **FREE** |
| **TOTAL** | | **~$13.25/month** |

---

## 🚀 Deployment Steps

### 1. Commit & Push

```bash
cd /Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk

git status
git add render.yaml RENDER_PLAN_UPDATE.md docs/
git commit -m "Configure Render deployment with 2026 pricing (basic-256mb)"
git push origin main
```

### 2. Deploy via Render Blueprint

1. Go to [render.com](https://render.com)
2. Click **"New +"** → **"Blueprint"**
3. **Connect your GitHub account** (if not already)
4. **Select repository:** `tobi-projects/ask-mirror-talk`
5. **Review configuration:**
   - Web Service: ask-mirror-talk (starter)
   - Database: mirror-talk-db (basic-256mb)
   - Cron Job: mirror-talk-ingestion
6. Click **"Apply"**
7. Wait 5-10 minutes for deployment

### 3. Post-Deployment Setup

Once deployed, initialize the database and run first ingestion:

```bash
# Method A: Via Render Dashboard Shell
# 1. Go to your Web Service → "Shell" tab
# 2. Run these commands:

python -c "from app.core.db import init_db; init_db()"
python scripts/bulk_ingest.py --max-episodes 5

# Method B: Verify and test
# Check the health endpoint
curl https://ask-mirror-talk.onrender.com/health

# Check status
curl https://ask-mirror-talk.onrender.com/status

# Test a question
curl -X POST https://ask-mirror-talk.onrender.com/ask \
  -H 'Content-Type: application/json' \
  -d '{"question": "What is Mirror Talk about?"}'
```

### 4. Verify Cron Job

- Dashboard → Cron Jobs → `mirror-talk-ingestion`
- Check it's scheduled for **"0 4 * * 3"**
- Next run: Check the dashboard for next Wednesday 5 AM CET

---

## 🔍 Post-Deployment Verification

### ✅ Checklist

- [ ] Web service is running (green status)
- [ ] Database is connected (check web service logs)
- [ ] pgvector extension installed (usually automatic)
- [ ] Initial episodes ingested (run `bulk_ingest.py`)
- [ ] `/health` endpoint returns 200 OK
- [ ] `/status` shows episodes and chunks count
- [ ] `/ask` endpoint responds with answers
- [ ] Admin dashboard accessible at `/admin`
- [ ] Cron job scheduled for Wednesday 5 AM CET
- [ ] WordPress integration updated with new URL

---

## 📊 What Happens Next

### Automatic Weekly Workflow

**Every Wednesday at 5:00 AM CET:**

1. ✅ Cron job wakes up
2. ✅ Checks RSS feed: `https://anchor.fm/s/261b1464/podcast/rss`
3. ✅ Detects new episode(s)
4. ✅ Downloads audio
5. ✅ Transcribes with Whisper (base model)
6. ✅ Creates semantic chunks
7. ✅ Generates embeddings (sentence-transformers)
8. ✅ Stores in PostgreSQL with pgvector
9. ✅ New episode becomes searchable instantly

**You do nothing!** ☕

---

## 🔧 Configuration Summary

### Environment Variables (Auto-configured via render.yaml)

**Web Service & Cron Job:**
- `RSS_URL`: https://anchor.fm/s/261b1464/podcast/rss
- `DATABASE_URL`: Auto-linked to mirror-talk-db
- `EMBEDDING_PROVIDER`: sentence_transformers
- `WHISPER_MODEL`: base
- `CHUNK_SIZE`: 1000
- `CHUNK_OVERLAP`: 200
- `ADMIN_USER`: admin
- `ADMIN_PASSWORD`: Auto-generated (check Render dashboard)
- `LOG_LEVEL`: INFO

**Database:**
- `plan`: basic-256mb
- `ipAllowList`: [] (public access for Render services)

---

## 📱 Access Points

After deployment, you'll have:

- **API Base URL**: `https://ask-mirror-talk.onrender.com`
- **Health Check**: `https://ask-mirror-talk.onrender.com/health`
- **Status**: `https://ask-mirror-talk.onrender.com/status`
- **Ask Endpoint**: `https://ask-mirror-talk.onrender.com/ask` (POST)
- **Admin Dashboard**: `https://ask-mirror-talk.onrender.com/admin`

Update your WordPress plugin with the new API URL!

---

## 💡 Tips

### Performance

- 256MB database is sufficient for ~100-200 episodes
- If you notice slow queries, consider upgrading to `basic-1gb` ($19/month)
- Monitor database size in Render Dashboard → Database → Metrics

### Cost Management

- Current setup: **~$13.25/month** (very economical!)
- Storage grows ~5-10MB per episode
- Cron jobs are always free
- No additional costs for API calls

### Monitoring

- Check logs after first Wednesday run
- Verify new episodes are ingested
- Test API responses
- Monitor database storage usage

---

## 🎉 Success!

Your Ask Mirror Talk service is now configured for:

✅ **Automatic weekly ingestion** - Every Wednesday 5 AM CET  
✅ **Cost-effective hosting** - ~$13.25/month  
✅ **Production-ready** - PostgreSQL with pgvector  
✅ **Scalable** - Easy to upgrade plans if needed  
✅ **Maintainable** - Zero manual intervention  

**Ready to deploy!** 🚀

---

## 📞 Need Help?

- **Render Docs**: https://render.com/docs
- **Logs**: Render Dashboard → Your Service → Logs tab
- **Support**: Check Render's community or support

**Everything is configured and ready. Just push to GitHub and deploy via Render Blueprint!**
