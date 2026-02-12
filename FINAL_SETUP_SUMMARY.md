# Railway Deployment - Complete Setup Summary

## ✅ What's Been Done

### 1. Code & Configuration
- ✅ Fixed Railway healthcheck by removing `startCommand` from `railway.toml`
- ✅ Dockerfile properly expands `$PORT` environment variable
- ✅ Added comprehensive startup and healthcheck logging
- ✅ Made database initialization fully lazy (only when accessed)
- ✅ Created ingestion scripts for all episodes and incremental updates

### 2. Documentation
- ✅ **RAILWAY_SETUP_GUIDE.md** - Complete deployment walkthrough
- ✅ **INGESTION_COMPLETE_GUIDE.md** - All ingestion methods and troubleshooting
- ✅ **railway.env.example** - All required environment variables
- ✅ **DEPLOYMENT_SUCCESS.md** - Latest deployment status

### 3. Automation
- ✅ **GitHub Actions workflow** - Automatic episode updates every 6 hours
- ✅ **setup_railway.sh** - Automated Railway CLI setup script
- ✅ **Ingestion scripts** - For initial load and incremental updates

### 4. Git & Deployment
- ✅ All changes committed and pushed to both Bitbucket and GitHub
- ✅ Railway automatically deploys from GitHub repository
- ✅ App is live and responding to healthchecks

## 📋 What You Need to Do

### Step 1: Add Environment Variables to Railway

Go to your Railway dashboard → Your Service → Settings → Variables and add these:

**Required:**
```env
DATABASE_URL=postgresql+psycopg://neondb_owner:YOUR_PASSWORD@ep-snowy-smoke-aj2dycz7-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require&options=endpoint%3Dep-snowy-smoke-aj2dycz7-pooler
RSS_URL=https://anchor.fm/s/261b1464/podcast/rss
ADMIN_USER=tobi
ADMIN_PASSWORD=@GoingPlaces#2026
```

⚠️ **CRITICAL for Neon Database:** The `DATABASE_URL` must include:
- `postgresql+psycopg://` (not just `postgresql://`)
- `-pooler` hostname
- `&options=endpoint%3D<your-endpoint>-pooler` parameter (forces IPv4, prevents "Network unreachable" errors)

See **NEON_IPV6_FIX.md** for detailed connection troubleshooting.

**Optional (with sensible defaults already in code):**
```env
APP_NAME=Ask Mirror Talk
ENVIRONMENT=production
RSS_POLL_MINUTES=60
MAX_EPISODES_PER_RUN=10
EMBEDDING_PROVIDER=local
WHISPER_MODEL=base
TRANSCRIPTION_PROVIDER=faster_whisper
TOP_K=6
MIN_SIMILARITY=0.15
RATE_LIMIT_PER_MINUTE=20
ALLOWED_ORIGINS=https://mirrortalkpodcast.com,https://www.mirrortalkpodcast.com
ADMIN_ENABLED=true
```

### Step 2: Run Initial Ingestion

```bash
railway run bash
python scripts/ingest_all_episodes.py
```

### Step 3: Set Up Automatic Updates

Add GitHub secrets:
- `DATABASE_URL`
- `RSS_URL`

The workflow will run every 6 hours automatically.

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **RAILWAY_SETUP_GUIDE.md** | Complete deployment walkthrough |
| **INGESTION_COMPLETE_GUIDE.md** | All ingestion methods & troubleshooting |
| **NEON_IPV6_FIX.md** | 🔴 Fix for "Network unreachable" database errors |
| **railway.env.example** | All required environment variables |

## ✅ Checklist

- [ ] Add environment variables in Railway dashboard
- [ ] Run `scripts/ingest_all_episodes.py` in Railway shell
- [ ] Verify `/status` shows episode counts
- [ ] Test `/ask` endpoint
- [ ] Set up GitHub Actions secrets
- [ ] Update WordPress widget with Railway URL

---

**Status:** ✅ Code complete, ready for environment setup and ingestion
