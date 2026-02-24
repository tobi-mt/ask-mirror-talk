# 🚀 Quick Deploy to Railway - Checklist

## ⚡ 5-Minute Deploy Guide

### Step 1: Go to Railway
```
https://railway.app
→ Login with GitHub
→ New Project
→ Deploy from GitHub repo
→ Select: ask-mirror-talk
```

### Step 2: Add Environment Variables
Click **Variables** tab, add these:

```bash
DATABASE_URL=postgresql+psycopg://neondb_owner:npg_0l7bPAnmJYOH@ep-snowy-smoke-aj2dycz7.c-3.us-east-2.aws.neon.tech/neondb?sslmode=require

EMBEDDING_PROVIDER=local
RSS_URL=https://anchor.fm/s/261b1464/podcast/rss
ALLOWED_ORIGINS=https://mirrortalkpodcast.com,https://www.mirrortalkpodcast.com
WHISPER_MODEL=base
ADMIN_ENABLED=true
ADMIN_USER=tobi
ADMIN_PASSWORD=@GoingPlaces#2026
TOP_K=6
MIN_SIMILARITY=0.15
```

### Step 3: Generate Domain
```
Settings → Domains → Generate Domain
```
Copy your URL (e.g., `https://ask-mirror-talk-production.up.railway.app`)

### Step 4: Test
```bash
curl https://YOUR_URL/health
curl https://YOUR_URL/status
```

### Step 5: Update WordPress
```javascript
const API_URL = 'https://YOUR_RAILWAY_URL/ask';
```

## ✅ Done!

---

## 📊 What You Get

- ✅ **Free hosting** ($0/month)
- ✅ **3 episodes** loaded (354 chunks)
- ✅ **Fast API** (<3s response time)
- ✅ **Unlimited deploys**
- ✅ **Auto-scaling**
- ✅ **Better than Render**

---

## 🔄 Weekly Updates

Run locally every Sunday:
```bash
~/update-mirror-talk.sh
```

Or setup cron:
```bash
crontab -e
# Add: 0 2 * * 0 /Users/tobi/update-mirror-talk.sh >> /Users/tobi/mirror-talk-cron.log 2>&1
```

---

## 🆘 Need Help?

- Full guide: `docs/RAILWAY_DEPLOYMENT.md`
- Migration summary: `docs/MIGRATION_COMPLETE.md`
- Troubleshooting: Check Railway logs

---

**Time to deploy:** ~10 minutes
**Difficulty:** Easy
**Cost:** $0/month

**Let's go! 🚀**
