# 🚀 Complete Railway + Neon Setup Guide

This guide will walk you through deploying Ask Mirror Talk on Railway with Neon Postgres.

## 📋 Overview

- **Database**: Neon (Serverless Postgres with pgvector)
- **API**: Railway (Container hosting)
- **Cost**: Free tier available for both services
- **Benefits**: Automatic scaling, better performance, easy maintenance

---

## Part 1: Neon Database Setup

### Step 1: Create Neon Account
1. Go to: **https://neon.tech**
2. Click **"Sign Up"** (GitHub login recommended)
3. Verify your email

### Step 2: Create Database Project
1. Click **"Create Project"**
2. Configure:
   - **Project Name**: `ask-mirror-talk-db`
   - **Region**: Choose closest to your users (e.g., US East)
   - **Postgres Version**: 16 (latest)
3. Click **"Create Project"**

### Step 3: Enable pgvector Extension
1. In your project dashboard, click **"SQL Editor"**
2. Run this command:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```
3. Click **"Run"** - you should see "Success"

### Step 4: Get Connection String
1. Click **"Dashboard"** or **"Connection Details"**
2. Find **"Connection string"** section
3. Copy the connection string that looks like:
```
postgresql://neondb_owner:npg_XXX@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
```
4. **IMPORTANT**: Convert it for SQLAlchemy by adding `+psycopg`:
```
postgresql+psycopg://neondb_owner:npg_XXX@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
```

psql 'postgresql+psycopg://neondb_owner:npg_0l7bPAnmJYOH@ep-snowy-smoke-aj2dycz7-pooler.c-3.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require'

5. **Save this** - you'll need it for Railway!

### Step 5: Initialize Database Schema
Run locally to set up tables:
```bash
# Set your Neon connection string
export DATABASE_URL="postgresql+psycopg://neondb_owner:npg_XXX@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require"

# Initialize database
python -c "from app.core.db import init_db; init_db()"
```

You should see:
```
✓ Database connection successful
✓ Tables created
✓ pgvector extension enabled
```

---

## Part 2: Railway Deployment

### Step 1: Sign Up for Railway
1. Go to: **https://railway.app**
2. Click **"Login"**
3. Select **"Login with GitHub"**
4. Authorize Railway to access your repositories

### Step 2: Create New Project
1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. If you don't see your repo:
   - Click **"Configure GitHub App"**
   - Grant access to your repository
   - Go back and select it
4. Railway will detect your `Dockerfile` automatically

### Step 3: Configure Environment Variables

Click on your service → **"Variables"** tab → Add these variables:

#### Required Variables:
```bash
# Database (CRITICAL - Use your actual Neon connection string!)
DATABASE_URL=postgresql+psycopg://neondb_owner:npg_XXX@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require

# App Settings
APP_NAME=Ask Mirror Talk
ENVIRONMENT=production

# RSS Feed
RSS_URL=https://anchor.fm/s/261b1464/podcast/rss
RSS_POLL_MINUTES=60

# Ingestion
MAX_EPISODES_PER_RUN=10

# Embeddings & Transcription
EMBEDDING_PROVIDER=local
WHISPER_MODEL=base
TRANSCRIPTION_PROVIDER=faster_whisper

# Retrieval
TOP_K=6
MIN_SIMILARITY=0.15

# API
RATE_LIMIT_PER_MINUTE=20
ALLOWED_ORIGINS=https://mirrortalkpodcast.com,https://www.mirrortalkpodcast.com

# Admin Dashboard
ADMIN_ENABLED=true
ADMIN_USER=tobi
ADMIN_PASSWORD=@GoingPlaces#2026
```

**Pro Tip**: You can copy all variables at once using "Raw Editor" mode in Railway!

### Step 4: Update Railway Configuration

Your `railway.toml` should look like this (already configured):
```toml
[build]
builder = "dockerfile"
dockerfilePath = "Dockerfile"

[deploy]
startCommand = "uvicorn app.api.main:app --host 0.0.0.0 --port $PORT"
restartPolicyType = "on-failure"
restartPolicyMaxRetries = 10
```

### Step 5: Generate Public Domain
1. Go to **"Settings"** tab
2. Scroll to **"Networking"** → **"Public Networking"**
3. Click **"Generate Domain"**
4. Your URL will be something like:
   ```
   https://ask-mirror-talk-production.up.railway.app
   ```
5. **Copy this URL** - you'll need it!

### Step 6: Deploy
1. Go to **"Deployments"** tab
2. Railway will automatically start building
3. Watch the logs - it should show:
   - Installing system dependencies
   - Installing Python packages
   - Starting uvicorn server
4. Wait for **"Success"** status (2-5 minutes)

---

## Part 3: Load Initial Data

You have two options:

### Option A: Load from Local Machine (Recommended)
```bash
# Set connection to Neon database
export DATABASE_URL="postgresql+psycopg://neondb_owner:npg_XXX@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require"

# Set RSS feed
export RSS_URL="https://anchor.fm/s/261b1464/podcast/rss"

# Run ingestion (processes 3 episodes by default)
python -m app.ingestion.pipeline_optimized
```

### Option B: Use Railway Shell
1. In Railway dashboard, click your service
2. Click **"..."** menu → **"Shell"**
3. Run:
```bash
python -m app.ingestion.pipeline_optimized
```

**Expected output:**
```
✓ Processing episode 1/3...
✓ Processing episode 2/3...
✓ Processing episode 3/3...
✓ Loaded 3 episodes with 354 chunks
```

---

## Part 4: Test Your Deployment

### Test 1: Health Check
```bash
curl https://YOUR-APP.up.railway.app/health
```
Expected: `{"status":"ok"}`

### Test 2: Status Check
```bash
curl https://YOUR-APP.up.railway.app/status
```
Expected: 
```json
{
  "status": "ok",
  "episodes": 3,
  "chunks": 354,
  "ready": true
}
```

### Test 3: Ask Question
```bash
curl -X POST https://YOUR-APP.up.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What topics does Mirror Talk discuss?"}'
```
Expected: JSON response with answer and citations

### Test 4: Admin Dashboard
Visit: `https://YOUR-APP.up.railway.app/admin`
- Username: `tobi`
- Password: `@GoingPlaces#2026`

---

## Part 5: Update WordPress

### Update API Endpoint
1. Go to WordPress Admin
2. Navigate to your theme or plugin files
3. Find `ask-mirror-talk.js` (usually in `wordpress/` directory)
4. Update the API URL:
```javascript
const API_URL = 'https://YOUR-APP.up.railway.app/ask';
```
5. Save and clear cache

### Test Widget
1. Visit: https://mirrortalkpodcast.com
2. Find the Ask Mirror Talk widget
3. Ask: "What is Mirror Talk about?"
4. You should get a real answer! 🎉

---

## 🎯 Success Checklist

- [ ] Neon account created
- [ ] Neon project created with pgvector extension
- [ ] Database connection string obtained and converted
- [ ] Railway account created
- [ ] Repository connected to Railway
- [ ] All environment variables configured
- [ ] Public domain generated
- [ ] Deployment successful
- [ ] Initial data loaded (3+ episodes)
- [ ] Health endpoint returns OK
- [ ] Status endpoint shows correct counts
- [ ] Ask endpoint returns answers
- [ ] Admin dashboard accessible
- [ ] WordPress updated with new URL
- [ ] Widget returns real answers

---

## 📊 What You've Accomplished

✅ **Serverless Database**: Neon Postgres with pgvector (scales to zero)
✅ **Container Hosting**: Railway with automatic deployments
✅ **Zero Downtime**: Both services have 99.9% uptime
✅ **Cost Effective**: Free tier supports moderate traffic
✅ **Auto Scaling**: Both services scale automatically
✅ **Easy Updates**: Push to GitHub → Automatic deployment

---

## 🔧 Ongoing Maintenance

### Monitor Resource Usage
1. **Neon Dashboard**: Check database size and queries
2. **Railway Dashboard**: Monitor CPU, memory, and requests

### Update Data (Weekly)
```bash
# Connect to Railway shell and run:
python -m app.ingestion.pipeline_optimized

# Or run locally with Neon connection:
export DATABASE_URL="your-neon-connection-string"
python -m app.ingestion.pipeline_optimized
```

### View Logs
- **Railway**: Click service → "Logs" tab
- **Neon**: Click project → "Monitoring" tab

### Scale Up (If Needed)
- **Neon**: Automatically scales with usage
- **Railway**: Upgrade plan for more resources

---

## 🆘 Troubleshooting

### Database Connection Issues
```bash
# Test connection locally
python -c "from app.core.db import engine; print(engine.connect())"
```

### Railway Build Fails
- Check environment variables are set correctly
- Verify DATABASE_URL has `+psycopg` in the connection string
- Check Railway logs for specific errors

### No Data in API
```bash
# Check if data exists
psql YOUR_NEON_CONNECTION_STRING -c "SELECT COUNT(*) FROM episodes;"
```

### Railway Deployment Not Starting
- Verify `railway.toml` exists
- Check that `PORT` environment variable is used
- Review startup logs in Railway dashboard

---

## 📚 Additional Resources

- **Railway Docs**: https://docs.railway.app
- **Neon Docs**: https://neon.tech/docs
- **pgvector Guide**: https://github.com/pgvector/pgvector

---

## 🎉 You're All Set!

Your Ask Mirror Talk API is now running on Railway with Neon Postgres!

**Next Steps:**
1. Test the widget on your WordPress site
2. Set up automatic data updates (optional)
3. Monitor usage and adjust resources as needed
4. Share your podcast Q&A with the world! 🚀
