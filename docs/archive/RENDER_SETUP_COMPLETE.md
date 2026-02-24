# ✅ Render Deployment Configuration - Complete

## 🎉 What Was Created

I've created a complete Render.com deployment configuration optimized for your **weekly Wednesday 5 AM CET (Central European Time) podcast releases**.

### 📁 New Files

1. **`render.yaml`** ⭐
   - Complete Render deployment configuration
   - Web service, cron job, and database setup
   - Scheduled for Wednesdays at 5:00 AM CET (4:00 AM UTC)

2. **`docs/RENDER_DEPLOYMENT.md`**
   - Complete deployment guide
   - Step-by-step instructions
   - Troubleshooting section
   - Security best practices

3. **`RENDER_QUICKSTART.md`**
   - Quick reference guide
   - 3-step deployment
   - Common tasks and URLs
   - Monitoring checklist

---

## 🎯 Key Configuration Details

### Automatic Ingestion Schedule

```yaml
schedule: "0 4 * * 3"
# = 4:00 AM UTC every Wednesday
# = 5:00 AM CET (Central European Time)
# = 6:00 AM CEST (summer time)
# (Day 3 = Wednesday, 0 = Sunday)
```

**What happens every Wednesday at 5 AM CET:**
1. ✅ Cron job wakes up
2. ✅ Checks RSS feed for new episodes
3. ✅ Downloads and transcribes new episode
4. ✅ Creates searchable chunks with embeddings
5. ✅ Updates database
6. ✅ New episode becomes searchable instantly

**You do nothing!** ☕

---

## 💰 Cost Breakdown

| Component | Plan | Cost |
|-----------|------|------|
| **Web Service** | Starter | $7/month |
| **PostgreSQL DB** | Starter | $7/month |
| **Cron Job** | Included | **FREE** ✨ |
| **HTTPS/SSL** | Included | FREE |
| **Auto-deploy** | Included | FREE |
| **Backups** | Included | FREE |
| **TOTAL** | | **$14/month** |

---

## 🚀 Deployment Options

### ❌ NO Background Worker Needed!

You asked: "Do I still need a Background Worker on Render?"

**Answer: NO!** ✅

**Why:**
- ✅ Cron jobs are **FREE** on Render (all plans)
- ✅ Perfect for weekly releases (not every hour)
- ✅ Same automation as background worker
- ✅ Saves $10/month vs always-on worker

**Cron Job vs Background Worker:**

| Feature | Cron Job | Background Worker |
|---------|----------|-------------------|
| **Cost** | **FREE** ✨ | $10/month |
| **Schedule** | Your choice | Every hour |
| **Perfect for** | Weekly releases | High-frequency |
| **Resource usage** | Only when running | Always running |

**For weekly Wednesday releases → Cron Job is perfect!** ⭐

---

## 📝 Quick Deploy (3 Steps)

### Step 1: Push to GitHub
```bash
cd /Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk
git add render.yaml docs/RENDER_DEPLOYMENT.md RENDER_QUICKSTART.md
git commit -m "Add Render deployment config for Wednesday 5 AM releases"
git push origin main
```

### Step 2: Deploy on Render
1. Go to [render.com](https://render.com)
2. Click "New +" → "Blueprint"
3. Connect your GitHub repository
4. Select `ask-mirror-talk`
5. Click "Apply"
6. Wait 5-10 minutes ⏰

### Step 3: Initialize & Test
```bash
# Get your URL (shown in Render dashboard)
export RENDER_URL="https://ask-mirror-talk.onrender.com"

# Initialize database (via Render Shell, do once)
python -c "from app.core.db import init_db; init_db()"

# Ingest first episodes
curl -X POST $RENDER_URL/ingest?max_episodes=5

# Verify it's working
curl $RENDER_URL/status

# Test question answering
curl -X POST $RENDER_URL/ask \
  -H 'Content-Type: application/json' \
  -d '{"question": "What is Mirror Talk about?"}'
```

**Done!** 🎉

---

## 🎛️ Configuration Customization

### Change Schedule

Edit `render.yaml`, line 63:

```yaml
# Current: Wednesday 5 AM CET (4 AM UTC)
schedule: "0 4 * * 3"

# Other options (all in UTC - subtract 1 hour for CET):
schedule: "0 5 * * *"     # Every day 6 AM CET
schedule: "0 4 * * 1"     # Monday 5 AM CET
schedule: "0 4 * * 1,4"   # Monday & Thursday 5 AM CET
schedule: "0 */6 * * *"   # Every 6 hours
```

**Note:** Render cron uses UTC. CET = UTC+1, CEST (summer) = UTC+2.

### Change Processing Settings

Edit `render.yaml`, environment variables:

```yaml
# Transcription quality
- key: WHISPER_MODEL
  value: base  # Options: tiny, base, small, medium

# Episodes per run
startCommand: "python scripts/bulk_ingest.py --max-episodes 3"
# Change to --max-episodes 1, 5, 10, etc.

# Embedding provider
- key: EMBEDDING_PROVIDER
  value: sentence_transformers  # Keep this for quality
```

---

## 📊 What to Monitor

### After First Deployment

✅ **Immediate checks:**
```bash
# Service health
curl https://your-app.onrender.com/health
# Should return: {"status": "healthy"}

# Data status
curl https://your-app.onrender.com/status
# Should show: episodes > 0, chunks > 0, ready: true

# Test API
curl -X POST https://your-app.onrender.com/ask \
  -H 'Content-Type: application/json' \
  -d '{"question": "What topics do you cover?"}'
# Should return answer with citations
```

### Weekly Checks (After Wednesday 5 AM)

1. **Check Cron Job Logs:**
   - Render Dashboard → `mirror-talk-ingestion`
   - Click "Logs" tab
   - Verify ingestion succeeded

2. **Verify New Episode:**
   ```bash
   curl https://your-app.onrender.com/status
   # episodes count should increase by 1
   ```

3. **Test New Content:**
   Ask a question about the latest episode

---

## 🔧 Customization Examples

### Example 1: Change to Daily Releases

```yaml
# In render.yaml, line 63
schedule: "0 5 * * *"  # Every day at 5 AM
```

### Example 2: Multiple Episodes Per Week

```yaml
# Release Tuesday + Friday
schedule: "0 5 * * 2,5"  # Tuesday (2) and Friday (5) at 5 AM
```

### Example 3: Faster/Slower Processing

```yaml
# For faster (lower quality)
- key: WHISPER_MODEL
  value: tiny

# For better quality (slower)
- key: WHISPER_MODEL
  value: small
```

---

## 🐛 Troubleshooting Quick Fixes

### Build Fails
```bash
# Check Python version in Render
# Minimum required: 3.10

# Verify pyproject.toml exists in repo
```

### Database Connection Error
```bash
# Render Dashboard → Web Service → Environment
# Verify DATABASE_URL is linked to mirror-talk-db
```

### Cron Not Running
```bash
# Check schedule is correct: "0 5 * * 3"
# Manually trigger: Dashboard → Cron Job → "Trigger Run"
```

### Out of Memory
```yaml
# Use lighter settings
WHISPER_MODEL: tiny
--max-episodes 1
```

---

## 📚 Documentation Structure

```
ask-mirror-talk/
├── render.yaml                    # ⭐ Main config
├── RENDER_QUICKSTART.md           # ⚡ Quick reference
├── docs/
│   ├── RENDER_DEPLOYMENT.md       # 📖 Complete guide
│   └── LOCAL_SETUP.md             # 💻 Local development
├── INGESTION_SUMMARY.md           # 🚀 Speed improvements
└── INGESTION_QUICKSTART.md        # 🎯 Local ingestion
```

**Start with:** `RENDER_QUICKSTART.md`  
**Full details:** `docs/RENDER_DEPLOYMENT.md`

---

## ✅ Success Checklist

After deployment, verify:

- [ ] Web service running (health check passes)
- [ ] Database connected (no errors in logs)
- [ ] Initial episodes ingested (status shows data)
- [ ] Questions work (ask endpoint returns answers)
- [ ] Admin dashboard accessible
- [ ] Cron job scheduled for Wednesdays
- [ ] WordPress integration updated with new URL
- [ ] First Wednesday auto-ingestion successful

---

## 🎉 Final Summary

### What You Get

✅ **Automatic podcast ingestion** - Every Wednesday at 5 AM  
✅ **Public API** - For WordPress integration  
✅ **Admin dashboard** - Monitor and manage  
✅ **No background worker needed** - Saves $10/month  
✅ **HTTPS included** - Secure by default  
✅ **Auto-deploy on git push** - Update anytime  
✅ **Database backups** - Built-in safety  

### Total Cost

**$14/month** - Web + Database + Cron (free!)

### Next Steps

1. ✅ Push `render.yaml` to GitHub
2. ✅ Deploy via Render Blueprint
3. ✅ Initialize database
4. ✅ Ingest initial episodes
5. ✅ Update WordPress with new URL
6. ✅ Wait for first Wednesday!

---

## 🚀 Deploy Command

```bash
# Ready to deploy? Run this:
git add render.yaml docs/ RENDER_QUICKSTART.md
git commit -m "Add Render deployment for Wednesday 5 AM releases"
git push origin main

# Then go to render.com and click "New Blueprint"!
```

---

## 📞 Support

**Questions?**
- See `docs/RENDER_DEPLOYMENT.md` for detailed guide
- Check Render logs for specific errors
- Test locally first (see `docs/LOCAL_SETUP.md`)

**Everything is configured and ready to deploy!** 🎊
