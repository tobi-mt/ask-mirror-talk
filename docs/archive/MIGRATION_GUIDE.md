# Migration to Neon + Railway - Step by Step Guide

## ✅ Step 1: Create Neon Database (Free)

### 1.1 Sign Up for Neon
1. Go to: https://neon.tech
2. Click **"Sign Up"** (use GitHub for easy signup)
3. Verify your email

### 1.2 Create Project
1. Click **"Create a project"**
2. **Project name**: `ask-mirror-talk`
3. **Region**: Choose closest to you (e.g., `US East (Ohio)`)
4. **Postgres version**: 16 (latest)
5. Click **"Create project"**

### 1.3 Enable pgvector Extension
1. In your new project, go to **"SQL Editor"**
2. Run this SQL:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
3. Click **"Run"**

### 1.4 Get Connection String
1. Go to **"Dashboard"** → **"Connection Details"**
2. Copy the **connection string** (looks like):
   ```
   postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
3. **Save this** - we'll use it in the next step

---

## ✅ Step 2: Test Connection from Local Machine

We'll test the connection and load data locally first.

### 2.1 Update .env File
```bash
# Edit .env file
DATABASE_URL=postgresql+psycopg://YOUR_NEON_CONNECTION_STRING_HERE
EMBEDDING_PROVIDER=local
```

**Important:** Replace `postgresql://` with `postgresql+psycopg://` in your connection string!

Example:
```env
# Before (Neon gives you this):
DATABASE_URL=postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require

# After (what you put in .env):
DATABASE_URL=postgresql+psycopg://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
```

### 2.2 Test Connection
```bash
python -c "
from app.core.db import SessionLocal, init_db
init_db()
db = SessionLocal()
print('✅ Connected to Neon!')
db.close()
"
```

---

## ✅ Step 3: Load Initial Data Locally

```bash
# This will take 5-10 minutes
python scripts/bulk_ingest.py --max-episodes 3

# Verify data loaded
python -c "
from app.core.db import SessionLocal
from app.storage.models import Episode, Chunk
db = SessionLocal()
print(f'Episodes: {db.query(Episode).count()}')
print(f'Chunks: {db.query(Chunk).count()}')
db.close()
"
```

---

## ✅ Step 4: Deploy API to Railway

### 4.1 Sign Up for Railway
1. Go to: https://railway.app
2. Click **"Login"** → **"Login with GitHub"**
3. Authorize Railway

### 4.2 Create New Project
1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose your `ask-mirror-talk` repository
4. Railway will detect your Dockerfile automatically

### 4.3 Configure Environment Variables
1. Click on your service → **"Variables"** tab
2. Add these environment variables:
   ```
   DATABASE_URL=postgresql+psycopg://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
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

### 4.4 Deploy
1. Railway will automatically deploy
2. Wait for build to complete (~3-5 minutes)
3. Once deployed, click **"Settings"** → **"Generate Domain"**
4. Copy your Railway URL (e.g., `https://ask-mirror-talk-production.up.railway.app`)

### 4.5 Test Railway API
```bash
# Test health
curl https://your-app.up.railway.app/health

# Test status
curl https://your-app.up.railway.app/status

# Test ask
curl -X POST https://your-app.up.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this podcast about?"}'
```

---

## ✅ Step 5: Setup Local Ingestion Cron

### 5.1 Create Ingestion Script
```bash
# Create a simple shell script
cat > ~/run-mirror-talk-ingestion.sh << 'EOF'
#!/bin/bash
cd /Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk
source venv/bin/activate
python scripts/bulk_ingest.py --max-episodes 10
EOF

chmod +x ~/run-mirror-talk-ingestion.sh
```

### 5.2 Test the Script
```bash
~/run-mirror-talk-ingestion.sh
```

### 5.3 Setup Weekly Cron (Runs Every Sunday at 2 AM)
```bash
# Edit crontab
crontab -e

# Add this line (press 'i' to insert, then paste):
0 2 * * 0 /Users/tobi/run-mirror-talk-ingestion.sh >> /Users/tobi/mirror-talk-cron.log 2>&1

# Save and exit (press ESC, then type :wq and press ENTER)
```

### 5.4 Verify Cron Job
```bash
# List your cron jobs
crontab -l
```

---

## ✅ Step 6: Update WordPress

### 6.1 Update JavaScript
Edit the WordPress plugin to use your new Railway URL:

```javascript
// Change this:
const API_URL = 'https://ask-mirror-talk-api.onrender.com/ask';

// To this:
const API_URL = 'https://your-app.up.railway.app/ask';
```

### 6.2 Test on WordPress
1. Go to your WordPress site
2. Ask a question in the widget
3. Should get a response!

---

## ✅ Step 7: Remove Render (Optional)

Once everything is working on Railway:

1. Go to Render Dashboard
2. Delete the `ask-mirror-talk-api` service
3. Delete the `mirror_talk` database
4. Save $25/month! 🎉

---

## Summary

✅ **Database**: Neon.tech (free serverless Postgres)
✅ **API**: Railway.app (free tier)
✅ **Ingestion**: Local cron job (runs on your Mac weekly)
✅ **Cost**: $0/month
✅ **Memory**: No issues (ingestion runs locally)
✅ **Builds**: Unlimited (no build minutes)
✅ **Storage**: 3GB free (vs 256MB on Render)

---

## What You Get

- 🚀 **Faster deployments** (no build minute limits)
- 💰 **$0/month cost** (vs $25+ on Render)
- 🎯 **Better performance** (serverless scaling)
- 🔧 **Easier maintenance** (separate ingestion from API)
- 📊 **Better monitoring** (Railway has better dashboard)
- 🔒 **More reliable** (no OOM errors)

---

## Next Steps

1. Create Neon account and database
2. Share your Neon connection string with me
3. I'll help update the .env and test
4. Deploy to Railway
5. Setup cron job
6. Done! 🎉

**Ready? Let's start with Step 1 - go to https://neon.tech and create your account!**
