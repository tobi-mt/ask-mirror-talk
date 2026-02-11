# 🎯 Railway + Neon Setup - Quick Reference

**Last Updated**: February 10, 2026  
**Status**: ✅ Ready for Deployment

---

## 📁 Files Created for Railway + Neon

### Configuration Files
- ✅ `railway.toml` - Railway deployment configuration
- ✅ `.env.railway` - Environment variables template for Railway
- ✅ `Dockerfile` - Container configuration (already exists)
- ✅ `pyproject.toml` - Python dependencies (already exists)

### Scripts
- ✅ `railway-build.sh` - Custom build script for Railway (optional)
- ✅ `scripts/setup_neon.py` - Neon database initialization
- ✅ `scripts/init_neon.sql` - SQL commands for Neon setup
- ✅ `scripts/quick_deploy.sh` - Automated deployment helper

### Documentation
- ✅ `RAILWAY_NEON_SETUP.md` - Complete step-by-step guide (5 parts)
- ✅ `DEPLOYMENT_CHECKLIST.md` - Interactive deployment checklist
- ✅ `README_QUICK_START.md` - This file

---

## ⚡ Quick Start (5 Minutes)

### 1️⃣ Set Up Neon Database (2 minutes)
```bash
# Go to https://neon.tech and create account
# Create project: ask-mirror-talk-db
# In SQL Editor, run:
CREATE EXTENSION IF NOT EXISTS vector;

# Copy your connection string and convert it:
# FROM: postgres://user:pass@host/db?sslmode=require
# TO:   postgresql+psycopg://user:pass@host/db?sslmode=require
```

### 2️⃣ Initialize Database Locally (1 minute)
```bash
# Set your Neon connection string
export DATABASE_URL="postgresql+psycopg://your-neon-connection-string"

# Initialize database
python scripts/setup_neon.py

# Load initial data (optional, takes 5-10 minutes)
python -m app.ingestion.pipeline_optimized
```

### 3️⃣ Deploy to Railway (2 minutes)
```bash
# 1. Go to https://railway.app
# 2. Login with GitHub
# 3. New Project → Deploy from GitHub repo
# 4. Select your repository
# 5. Add environment variables (see below)
# 6. Generate domain
# 7. Done! ✅
```

---

## 🔐 Environment Variables for Railway

Copy these to Railway Dashboard → Variables tab:

```bash
DATABASE_URL=postgresql+psycopg://YOUR_NEON_CONNECTION_STRING
APP_NAME=Ask Mirror Talk
ENVIRONMENT=production
RSS_URL=https://anchor.fm/s/261b1464/podcast/rss
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
ADMIN_USER=tobi
ADMIN_PASSWORD=@GoingPlaces#2026
```

**⚠️ CRITICAL**: Replace `YOUR_NEON_CONNECTION_STRING` with your actual Neon connection string!

---

## 🧪 Test Your Deployment

Replace `YOUR_APP` with your Railway domain:

```bash
# Health check
curl https://YOUR_APP.up.railway.app/health

# Status (should show episode/chunk counts)
curl https://YOUR_APP.up.railway.app/status

# Ask a question
curl -X POST https://YOUR_APP.up.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Mirror Talk about?"}'

# Admin dashboard
open https://YOUR_APP.up.railway.app/admin
```

---

## 📊 What You Get

| Feature | Railway | Neon | Combined |
|---------|---------|------|----------|
| **Cost** | Free tier | Free tier | **$0/month** |
| **Database** | - | ✅ Postgres + pgvector | Serverless |
| **API Hosting** | ✅ Container | - | Auto-scaling |
| **Build Minutes** | Unlimited | - | No limits |
| **Uptime** | 99.9% | 99.9% | **99.9%+** |
| **Auto Deploy** | ✅ Git push | - | Automatic |
| **Storage** | Persistent | 10GB free | Enough for podcast |

---

## 📂 Project Structure

```
ask-mirror-talk/
├── railway.toml                    # Railway config
├── .env.railway                    # Environment template
├── Dockerfile                      # Container setup
├── railway-build.sh               # Custom build script
│
├── scripts/
│   ├── setup_neon.py              # Database initialization
│   ├── init_neon.sql              # SQL setup commands
│   └── quick_deploy.sh            # Automated deployment
│
├── docs/
│   ├── RAILWAY_NEON_SETUP.md      # Detailed guide (5 parts)
│   └── DEPLOYMENT_CHECKLIST.md    # Step-by-step checklist
│
└── app/
    ├── api/                        # FastAPI endpoints
    ├── core/                       # Config & database
    ├── ingestion/                  # Data pipeline
    ├── qa/                         # Q&A logic
    └── storage/                    # Vector storage
```

---

## 🎯 Deployment Workflow

```mermaid
graph LR
    A[GitHub Repo] --> B[Railway Build]
    B --> C[Docker Container]
    C --> D[API Running]
    D --> E[Neon Database]
    E --> F[Your WordPress Site]
```

1. **Push code** to GitHub
2. **Railway detects** change and builds
3. **Container runs** with your environment variables
4. **API connects** to Neon database
5. **WordPress widget** queries API
6. **Users get answers** from podcast content

---

## 🔄 Update Workflow

### Add New Podcast Episodes
```bash
# Option 1: Local (recommended)
export DATABASE_URL="your-neon-connection"
python -m app.ingestion.pipeline_optimized

# Option 2: Railway Shell
# In Railway Dashboard → ... → Shell:
python -m app.ingestion.pipeline_optimized
```

### Update Code
```bash
# Just push to GitHub
git add .
git commit -m "Update feature"
git push

# Railway automatically rebuilds and redeploys!
```

---

## 🆘 Troubleshooting

### Connection Error
```bash
# Test database connection
python scripts/setup_neon.py

# Check DATABASE_URL format:
# ✅ postgresql+psycopg://...
# ❌ postgres://... (wrong!)
# ❌ postgresql://... (missing +psycopg)
```

### Build Fails on Railway
1. Check environment variables are set
2. Verify DATABASE_URL format
3. Check build logs for specific error
4. Ensure Dockerfile is present

### No Data in API
```bash
# Check if episodes loaded
python -c "
from app.core.db import engine
from sqlalchemy import text
with engine.connect() as conn:
    r = conn.execute(text('SELECT COUNT(*) FROM episodes'))
    print(f'Episodes: {r.scalar()}')
"
```

### CORS Errors
1. Check ALLOWED_ORIGINS in Railway variables
2. Include both with and without www
3. Use comma-separated list (no spaces)

---

## 📞 Support & Resources

### Documentation
- 📖 **Full Guide**: `RAILWAY_NEON_SETUP.md`
- ✅ **Checklist**: `DEPLOYMENT_CHECKLIST.md`
- 🔧 **Local Setup**: `LOCAL_SETUP.md`

### Dashboards
- 🚂 **Railway**: https://railway.app
- 🗄️ **Neon**: https://console.neon.tech
- 🌐 **WordPress**: https://mirrortalkpodcast.com

### Useful Commands
```bash
# Check logs
railway logs

# Connect to database
psql $DATABASE_URL

# Test API locally
uvicorn app.api.main:app --reload

# Load data
python -m app.ingestion.pipeline_optimized
```

---

## ✅ Success Criteria

You're done when:
- [ ] Railway deployment shows "Active"
- [ ] Neon database has data (episodes + chunks)
- [ ] `/health` endpoint returns `{"status":"ok"}`
- [ ] `/status` shows episode/chunk counts
- [ ] `/ask` returns answers with citations
- [ ] Admin dashboard is accessible
- [ ] WordPress widget displays real answers
- [ ] No errors in logs

---

## 🎉 Next Steps After Deployment

1. **Test thoroughly** using the checklist
2. **Update WordPress** with Railway URL
3. **Monitor usage** in Railway dashboard
4. **Set up weekly updates** for new episodes
5. **Share with users** - your Q&A widget is live!

---

## 💡 Pro Tips

1. **Use Railway CLI** for faster deployments:
   ```bash
   npm i -g @railway/cli
   railway login
   railway up
   ```

2. **Monitor costs** (though free tier is generous):
   - Railway: Free tier → $5/month for more resources
   - Neon: Free tier → $19/month for more storage

3. **Custom domain** (optional):
   - Railway Settings → Domains → Add custom domain
   - Point your DNS to Railway

4. **Automated updates** (advanced):
   - Set up GitHub Actions to run ingestion pipeline
   - Use Railway cron jobs for scheduled tasks

---

**Ready to deploy?** Start with `RAILWAY_NEON_SETUP.md` for detailed steps! 🚀

---

*Questions? Check the troubleshooting section or review the full deployment guide.*
