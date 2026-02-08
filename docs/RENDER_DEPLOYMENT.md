# 🚀 Render.com Deployment Guide

Complete guide for deploying Ask Mirror Talk to Render.com with automatic weekly ingestion.

---

## 📋 Overview

**Deployment Setup:**
- ✅ **1 Web Service** - FastAPI application
- ✅ **1 Cron Job** - Automatic ingestion (Wednesdays at 5 AM CET)
- ✅ **1 PostgreSQL Database** - With pgvector extension

**Total Cost:** ~$14/month ($7 web + $7 database)

**Features:**
- 🔄 Automatic episode ingestion every Wednesday at 5 AM CET
- 🌐 Public API endpoint for your WordPress site
- 📊 Admin dashboard for monitoring
- 💾 Automatic backups (PostgreSQL)
- 🔒 HTTPS included

---

## 🎯 Quick Deploy (5 Minutes)

### Option 1: One-Click Deploy via Dashboard

1. **Push code to GitHub**
   ```bash
   git add .
   git commit -m "Add Render configuration"
   git push origin main
   ```

2. **Create New Project on Render**
   - Go to [render.com](https://render.com)
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Select `ask-mirror-talk`
   - Render will automatically detect `render.yaml`

3. **Set Environment Variables** (if not using render.yaml defaults)
   - `ADMIN_PASSWORD` - Set a secure password
   - `ALLOWED_ORIGINS` - Your WordPress site URL

4. **Deploy!**
   - Click "Apply"
   - Wait 5-10 minutes for first deploy
   - Get your URL: `https://ask-mirror-talk.onrender.com`

---

### Option 2: Manual Setup

#### Step 1: Create PostgreSQL Database

1. Dashboard → "New +" → "PostgreSQL"
2. **Settings:**
   - Name: `mirror-talk-db`
   - Database: `mirror_talk`
   - User: `mirror`
   - Region: `Oregon` (or nearest to you)
   - Plan: `Starter` ($7/month)
   - PostgreSQL Version: `16`
3. Click "Create Database"
4. **Enable pgvector:**
   ```bash
   # Connect to database (Render provides connection string)
   psql <connection-string>
   
   # Enable extension
   CREATE EXTENSION vector;
   \q
   ```

#### Step 2: Create Web Service

1. Dashboard → "New +" → "Web Service"
2. Connect GitHub repo: `ask-mirror-talk`
3. **Settings:**
   - Name: `ask-mirror-talk`
   - Region: `Oregon`
   - Branch: `main`
   - Runtime: `Python`
   - Build Command: `pip install -e '.[transcription,embeddings]'`
   - Start Command: `uvicorn app.api.main:app --host 0.0.0.0 --port $PORT`
   - Plan: `Starter` ($7/month)

4. **Environment Variables:**
   ```
   RSS_URL=https://anchor.fm/s/261b1464/podcast/rss
   DATABASE_URL=<link-to-database>
   EMBEDDING_PROVIDER=sentence_transformers
   WHISPER_MODEL=base
   ADMIN_USER=admin
   ADMIN_PASSWORD=<your-secure-password>
   ALLOWED_ORIGINS=https://yourdomain.com
   ```

5. Click "Create Web Service"

#### Step 3: Create Cron Job for Auto-Ingestion

1. Dashboard → "New +" → "Cron Job"
2. Connect same GitHub repo
3. **Settings:**
   - Name: `mirror-talk-ingestion`
   - Region: `Oregon`
   - Branch: `main`
   - Runtime: `Python`
   - Build Command: `pip install -e '.[transcription,embeddings]'`
   - Start Command: `python scripts/bulk_ingest.py --max-episodes 3`
   - Schedule: `0 4 * * 3` (Wednesdays at 4 AM UTC = 5 AM CET)

4. **Environment Variables:** (same as web service)
   ```
   RSS_URL=https://anchor.fm/s/261b1464/podcast/rss
   DATABASE_URL=<link-to-database>
   EMBEDDING_PROVIDER=sentence_transformers
   WHISPER_MODEL=base
   ```

5. Click "Create Cron Job"

---

## 🔧 Configuration

### Cron Schedule Format

The schedule uses standard cron syntax: `minute hour day-of-month month day-of-week`

**Examples:**
```bash
# Every Wednesday at 5 AM CET (4 AM UTC)
0 4 * * 3

# Every day at 6 AM CET (5 AM UTC)
0 5 * * *

# Twice a week (Monday and Thursday at 7 AM CET)
0 6 * * 1,4

# First day of month at midnight UTC
0 0 1 * *

# Every 6 hours
0 */6 * * *
```

**Day of Week:** 0 = Sunday, 1 = Monday, ..., 6 = Saturday
**Note:** Render cron jobs use UTC time. CET is UTC+1, CEST is UTC+2.

### Whisper Model Options

| Model | Speed | Quality | Memory | Best For |
|-------|-------|---------|--------|----------|
| `tiny` | Fastest | Basic | 1GB | Testing |
| `base` | Fast | Good | 1.5GB | **Recommended** |
| `small` | Slower | Better | 2GB | Production |
| `medium` | Slowest | Best | 5GB | High Quality |

**Recommendation:** Use `base` for Render Starter plan (512MB RAM)

---

## 📊 Post-Deployment Setup

### 1. Initialize Database Schema

After first deployment, run once:

```bash
# Using Render Shell
# Go to your web service → "Shell" tab
python -c "from app.core.db import init_db; init_db()"
```

### 2. Manual First Ingestion

Ingest initial episodes before first Wednesday:

```bash
# Option A: Via API
curl -X POST https://ask-mirror-talk.onrender.com/ingest?max_episodes=5

# Option B: Via Render Shell
python scripts/bulk_ingest.py --max-episodes 5
```

### 3. Verify It's Working

```bash
# Check API status
curl https://ask-mirror-talk.onrender.com/health

# Check ingestion status
curl https://ask-mirror-talk.onrender.com/status

# Test question answering
curl -X POST https://ask-mirror-talk.onrender.com/ask \
  -H 'Content-Type: application/json' \
  -d '{"question": "What topics does Mirror Talk cover?"}'
```

### 4. Access Admin Dashboard

Navigate to: `https://ask-mirror-talk.onrender.com/admin`

**Login:**
- Username: `admin`
- Password: (check Render environment variables)

---

## 🔐 Security Best Practices

### 1. Set Strong Admin Password

```bash
# Generate secure password
openssl rand -base64 32

# Add to Render environment variables
ADMIN_PASSWORD=<generated-password>
```

### 2. Configure CORS

Add your WordPress domain:

```bash
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### 3. Enable API Authentication (Optional)

For production, add API key authentication:

```bash
API_KEY=<your-secret-key>
```

---

## 📈 Monitoring & Logs

### View Logs

**Web Service Logs:**
- Dashboard → Your Web Service → "Logs" tab
- See real-time API requests and errors

**Cron Job Logs:**
- Dashboard → Your Cron Job → "Logs" tab
- See ingestion progress every Wednesday

### Monitor Database

**Database Metrics:**
- Dashboard → Your Database → "Metrics" tab
- Storage usage, connections, queries

**Check Data Manually:**
```bash
# Render Shell in Database
psql $DATABASE_URL

# Check episode count
SELECT COUNT(*) FROM episodes;

# Check chunk count
SELECT COUNT(*) FROM chunks;

# Recent ingestions
SELECT title, published_at FROM episodes ORDER BY published_at DESC LIMIT 5;
```

---

## 🐛 Troubleshooting

### Issue: "No episodes found"

**Solution:**
1. Check RSS_URL is correct
2. Verify RSS feed is accessible:
   ```bash
   curl https://anchor.fm/s/261b1464/podcast/rss
   ```
3. Check logs for errors

### Issue: "Database connection failed"

**Solution:**
1. Verify DATABASE_URL is linked correctly
2. Check pgvector extension is installed:
   ```sql
   SELECT * FROM pg_extension WHERE extname = 'vector';
   ```
3. Re-link database in Render dashboard

### Issue: "Out of memory during ingestion"

**Solutions:**
1. **Reduce Whisper model:** Change to `tiny` or `base`
2. **Reduce batch size:** Set `MAX_EPISODES_PER_RUN=1`
3. **Upgrade plan:** Use Standard plan (512MB → 2GB RAM)

### Issue: "Cron job not running"

**Solutions:**
1. Check schedule syntax is correct
2. Verify cron job is not suspended (free plan limitation)
3. Check environment variables are set
4. Manually trigger via Render dashboard

### Issue: "Build fails"

**Solution:**
1. Check `pyproject.toml` is correct
2. Verify Python version (3.10+)
3. Check build command includes extras: `'.[transcription,embeddings]'`

---

## 💰 Cost Optimization

### Current Setup: ~$14/month

| Service | Plan | Cost |
|---------|------|------|
| Web Service | Starter | $7/month |
| PostgreSQL | Starter | $7/month |
| Cron Job | - | **FREE** |
| **TOTAL** | | **$14/month** |

### Upgrade Options

**For Better Performance:**
- Web Service Standard: $25/month (2GB RAM, better CPU)
- PostgreSQL Standard: $20/month (4GB RAM, 50GB storage)

**Free Tier Option (Testing Only):**
- Use Render's free web service (spins down after 15 min inactivity)
- External free PostgreSQL (Supabase, Neon)
- Cron jobs don't work on free tier ❌

---

## 🔄 Maintenance

### Weekly Tasks
- ✅ **Automatic** - Cron job runs every Wednesday
- ✅ Check logs to verify ingestion succeeded
- ✅ Test API with sample question

### Monthly Tasks
- Review database size (upgrade if needed)
- Check error logs
- Update dependencies if security updates available

### Updates & Deployments

**Automatic:**
- Every git push triggers new deployment
- Zero-downtime deployments

**Manual Rollback:**
- Dashboard → Service → "Rollback" button
- Choose previous deployment

---

## 🎉 Success Checklist

After deployment, verify:

- [ ] ✅ Web service is running (`/health` returns 200)
- [ ] ✅ Database is connected (check logs)
- [ ] ✅ Initial episodes ingested (`/status` shows data)
- [ ] ✅ Questions work (`/ask` endpoint returns answers)
- [ ] ✅ Admin dashboard accessible
- [ ] ✅ Cron job scheduled (check Render dashboard)
- [ ] ✅ WordPress integration works
- [ ] ✅ Logs show no errors

---

## 📞 Support & Resources

**Render Documentation:**
- [Cron Jobs](https://render.com/docs/cronjobs)
- [PostgreSQL](https://render.com/docs/databases)
- [Python Apps](https://render.com/docs/deploy-python)

**Ask Mirror Talk:**
- Check logs: Render Dashboard → Logs
- Test locally first: See `docs/LOCAL_SETUP.md`
- Monitor status: `/status` endpoint

**Questions?**
- Check Render docs
- Review logs for specific errors
- Test ingestion manually via Render Shell

---

## 🚀 Next Steps

1. ✅ **Deploy** - Follow quick deploy steps
2. ✅ **Test** - Verify all endpoints work
3. ✅ **Integrate** - Connect WordPress plugin
4. ✅ **Monitor** - Check first Wednesday ingestion
5. ✅ **Optimize** - Adjust settings based on usage

**You're ready to go live!** 🎊
