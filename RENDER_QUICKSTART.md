# 🚀 Render Deployment - Quick Reference

**For weekly podcast releases on Wednesdays at 5 AM CET (Central European Time)**

---

## 📦 Files Created

- ✅ `render.yaml` - Main deployment configuration
- ✅ `docs/RENDER_DEPLOYMENT.md` - Complete deployment guide

---

## ⚡ Quick Deploy (3 Steps)

### 1. Push to GitHub
```bash
git add render.yaml docs/RENDER_DEPLOYMENT.md
git commit -m "Add Render deployment config"
git push origin main
```

### 2. Deploy on Render
1. Go to [render.com](https://render.com) → "New" → "Blueprint"
2. Connect GitHub repo `ask-mirror-talk`
3. Click "Apply" ✨

### 3. Initialize & Test
```bash
# Initialize database (run once via Render Shell)
python -c "from app.core.db import init_db; init_db()"

# Initial ingestion
curl -X POST https://your-app.onrender.com/ingest?max_episodes=5

# Verify
curl https://your-app.onrender.com/status
```

**Done!** 🎉

---

## 📅 What Happens Now?

### Automatic Schedule

**Every Wednesday at 5:00 AM Central European Time (CET):**
1. ✅ Cron job wakes up
2. ✅ Checks RSS feed for new episode
3. ✅ Downloads audio
4. ✅ Transcribes with Whisper
5. ✅ Creates searchable chunks
6. ✅ Generates embeddings
7. ✅ Saves to database
8. ✅ New episode is searchable!

**You do nothing.** It's completely automatic. ☕

**Note:** Render uses UTC time. The cron runs at 4 AM UTC, which is 5 AM CET (or 6 AM CEST in summer).

---

## 💰 Cost Breakdown

| Service | Plan | Monthly Cost |
|---------|------|--------------|
| **Web Service** | Starter | $7 |
| **PostgreSQL** | Starter | $7 |
| **Cron Job** | Included | $0 |
| **TOTAL** | | **$14/month** |

**Note:** Cron jobs are FREE on all Render plans! 🎁

---

## 🔍 Important URLs

After deployment:

```bash
# Your API
https://ask-mirror-talk.onrender.com

# Health check
https://ask-mirror-talk.onrender.com/health

# Status endpoint
https://ask-mirror-talk.onrender.com/status

# Admin dashboard
https://ask-mirror-talk.onrender.com/admin
# Username: admin
# Password: (check Render env vars)

# Ask questions
https://ask-mirror-talk.onrender.com/ask
```

---

## 🎛️ Key Settings in render.yaml

### Schedule (Change if needed)

```yaml
# Current: Wednesdays at 5 AM CET (4 AM UTC)
schedule: "0 4 * * 3"

# Other examples (all in UTC - subtract 1 hour for CET):
# Every day at 6 AM CET:     "0 5 * * *"
# Mondays at 8 AM CET:       "0 7 * * 1"
# Twice/week (Mon/Thu) 5 AM: "0 4 * * 1,4"
```

### Whisper Model

```yaml
# Current: balanced speed/quality
WHISPER_MODEL: base

# Options:
# tiny   - Fastest, good for testing
# base   - Recommended (current)
# small  - Better quality, slower
# medium - Best quality, needs more RAM
```

### Episodes per Run

```yaml
# Current: process up to 3 new episodes
--max-episodes 3

# Adjust if you release multiple episodes:
--max-episodes 5  # For 5 episodes at once
--max-episodes 1  # For exactly 1 per week
```

---

## ✅ Verify It's Working

### Right After Deployment

```bash
# 1. Check service is running
curl https://your-app.onrender.com/health
# Expected: {"status": "healthy"}

# 2. Initialize database
# (Do this once via Render Shell)
python -c "from app.core.db import init_db; init_db()"

# 3. Ingest first episode manually
curl -X POST https://your-app.onrender.com/ingest?max_episodes=1

# 4. Check status
curl https://your-app.onrender.com/status
# Expected: {"ready": true, "episodes": 1, "chunks": 40+}

# 5. Test question
curl -X POST https://your-app.onrender.com/ask \
  -H 'Content-Type: application/json' \
  -d '{"question": "What is this podcast about?"}'
# Expected: JSON with answer and citations
```

### First Wednesday After Deployment

Check logs to see automatic ingestion:
1. Render Dashboard → `mirror-talk-ingestion` cron job
2. Click "Logs"
3. Should see ingestion running at 5 AM

---

## 🐛 Quick Troubleshooting

### "Build failed"
```bash
# Check Python version (needs 3.10+)
# Check pyproject.toml is in repo
# Verify build command includes: '.[transcription,embeddings]'
```

### "Database connection error"
```bash
# Go to Render Dashboard
# Web Service → Environment → DATABASE_URL
# Should be linked to mirror-talk-db
# Re-link if needed
```

### "Cron job not running"
```bash
# Check Render Dashboard → Cron Jobs
# Verify schedule: "0 4 * * 3" (4 AM UTC = 5 AM CET)
# Check logs for errors
# Manually trigger via "Trigger Run" button
```

### "Out of memory"
```bash
# Option 1: Use smaller model
WHISPER_MODEL=tiny

# Option 2: Process fewer episodes
--max-episodes 1

# Option 3: Upgrade to Standard plan ($25/mo)
```

---

## 🔄 Manual Ingestion (Optional)

If you need to ingest episodes outside the Wednesday schedule:

### Via API
```bash
# Ingest latest episode
curl -X POST https://your-app.onrender.com/ingest

# Ingest multiple episodes
curl -X POST https://your-app.onrender.com/ingest?max_episodes=3
```

### Via Render Shell
```bash
# Dashboard → Web Service → Shell tab
python scripts/bulk_ingest.py --max-episodes 1
```

### Via Cron Job
```bash
# Dashboard → Cron Job → "Trigger Run" button
```

---

## 🎯 WordPress Integration

After deployment, update your WordPress plugin:

```javascript
// In ask-mirror-talk.js
const API_URL = 'https://ask-mirror-talk.onrender.com/ask';
```

**That's it!** Your WordPress site now connects to Render.

---

## 📊 Monitoring

### What to Check Weekly

1. **Cron Job Logs** (after Wednesday 5 AM)
   - Verify ingestion succeeded
   - Check for any errors

2. **Database Usage**
   - Dashboard → Database → Metrics
   - Starter plan: 1GB storage
   - ~100 episodes = ~200MB

3. **API Health**
   ```bash
   curl https://your-app.onrender.com/status
   ```

### When to Upgrade

**Upgrade Web Service to Standard ($25/mo) if:**
- ❌ Getting timeout errors
- ❌ Slow response times (>3 seconds)
- ❌ Out of memory errors

**Upgrade Database to Standard ($20/mo) if:**
- ❌ Storage >80% full (>800MB)
- ❌ Many connection errors
- ❌ Slow queries

---

## 🎉 You're All Set!

**What's automated:**
- ✅ New episode detection (every Wednesday)
- ✅ Audio download
- ✅ Transcription
- ✅ Embedding generation
- ✅ Database updates
- ✅ Automatic deployments (on git push)

**What you do:**
- ☕ Release podcast on Wednesday
- ☕ Check logs occasionally
- ☕ That's it!

---

## 📚 Full Documentation

For complete details, see:
- **`docs/RENDER_DEPLOYMENT.md`** - Complete deployment guide
- **`render.yaml`** - Configuration file with comments
- **`docs/LOCAL_SETUP.md`** - For local testing

---

## 🚀 Deploy Now!

```bash
# 1. Commit config
git add render.yaml docs/
git commit -m "Add Render config for automatic Wednesday ingestion"
git push

# 2. Go to render.com → New → Blueprint → Connect repo → Apply

# 3. Initialize & enjoy!
```

**Happy deploying!** 🎊
