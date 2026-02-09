# 🚀 Deploy to Railway - Quick Start

## ✅ Prerequisites (Already Done)
- ✅ Neon database created: `fancy-band-22959768`
- ✅ pgvector extension enabled
- ✅ 3 episodes loaded (354 chunks)
- ✅ Code pushed to GitHub/Bitbucket
- ✅ railway.toml configuration created

## 📋 Step-by-Step Railway Deployment

### Step 1: Sign Up for Railway
1. Go to: **https://railway.app**
2. Click **"Login"**
3. Select **"Login with GitHub"** (or Bitbucket if that's where your repo is)
4. Authorize Railway to access your repositories

### Step 2: Create New Project
1. Click **"New Project"** button (top right)
2. Select **"Deploy from GitHub repo"**
3. Search for `ask-mirror-talk` (or your repository name)
4. Click on your repository to select it
5. Railway will automatically:
   - Detect your `Dockerfile`
   - Read `railway.toml` configuration
   - Start building

### Step 3: Configure Environment Variables
1. While it's building, click on your service card
2. Click **"Variables"** tab at the top
3. Click **"+ New Variable"** and add these one by one:

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

MAX_EPISODES_PER_RUN=10

RATE_LIMIT_PER_MINUTE=20
```

**IMPORTANT:** Copy the DATABASE_URL exactly as shown above with your Neon credentials!

### Step 4: Get Your Railway URL
1. Go to **"Settings"** tab
2. Scroll to **"Domains"** section
3. Click **"Generate Domain"**
4. Your URL will be something like:
   ```
   https://ask-mirror-talk-production.up.railway.app
   ```
5. **Copy this URL** - you'll need it for WordPress

### Step 5: Wait for Deployment
1. Go to **"Deployments"** tab
2. Watch the build logs
3. Wait for it to show **"Success"** (usually 2-3 minutes)
4. Status should show **"Active"**

### Step 6: Test Your API
Open a terminal and test these endpoints:

```bash
# Replace YOUR_URL with your Railway URL

# Test health
curl https://YOUR_URL.up.railway.app/health

# Expected: {"status":"ok"}

# Test status
curl https://YOUR_URL.up.railway.app/status

# Expected: {"status":"ok","episodes":3,"chunks":354,"ready":true}

# Test ask
curl -X POST https://YOUR_URL.up.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this podcast about?"}'

# Expected: JSON with answer and citations
```

### Step 7: Update WordPress
1. Go to your WordPress admin
2. Edit the Ask Mirror Talk plugin JavaScript file
3. Find this line:
   ```javascript
   const API_URL = 'https://ask-mirror-talk-api.onrender.com/ask';
   ```
4. Replace with:
   ```javascript
   const API_URL = 'https://YOUR_URL.up.railway.app/ask';
   ```
5. Save and clear cache

### Step 8: Test on WordPress
1. Visit: https://mirrortalkpodcast.com
2. Find the Ask Mirror Talk widget
3. Ask a question: "What topics does Mirror Talk discuss?"
4. You should get a real answer with citations! 🎉

---

## 🎯 Success Checklist

- [ ] Railway account created
- [ ] Project deployed from GitHub
- [ ] All environment variables set
- [ ] Domain generated
- [ ] Health endpoint returns OK
- [ ] Status endpoint shows 3 episodes, 354 chunks
- [ ] Ask endpoint returns answers with citations
- [ ] WordPress updated with new URL
- [ ] WordPress widget returns real answers

---

## 📊 What You Just Accomplished

✅ **Database**: Migrated from Render to Neon (free serverless Postgres)
✅ **API**: Deployed to Railway (free tier, unlimited builds)
✅ **Data**: 3 episodes loaded with 354 searchable chunks
✅ **Cost**: $0/month (was $25+ on Render)
✅ **Performance**: Better resource allocation and scaling
✅ **Maintenance**: Easier with separated concerns

---

## 🔄 Ongoing Maintenance

### Weekly Data Updates (Local Ingestion)
```bash
# Create a script: ~/update-mirror-talk.sh
#!/bin/bash
cd /Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk
source venv/bin/activate
python scripts/bulk_ingest.py --max-episodes 10
```

### Setup Cron Job (Optional)
```bash
# Run every Sunday at 2 AM
crontab -e

# Add this line:
0 2 * * 0 /Users/tobi/update-mirror-talk.sh >> /Users/tobi/mirror-talk-cron.log 2>&1
```

### Manual Updates
```bash
cd /Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk
python scripts/bulk_ingest.py --max-episodes 10
```

---

## 🐛 Troubleshooting

### Build Failed on Railway
- Check **Deployments** → **Logs** for errors
- Verify Dockerfile is correct
- Ensure all environment variables are set

### API Returns 500 Error
- Check **Logs** in Railway dashboard
- Verify DATABASE_URL is correct (with `postgresql+psycopg://`)
- Check that pgvector extension is enabled in Neon

### No Search Results
- Verify data is loaded: `curl YOUR_URL/status`
- Should show `episodes: 3, chunks: 354`
- If 0, run local ingestion again

### WordPress Widget Not Working
- Check browser console for errors
- Verify CORS settings (ALLOWED_ORIGINS)
- Test API endpoint directly with curl first

---

## 💰 Cost Comparison

| Item | Render (Old) | Neon + Railway (New) |
|------|--------------|----------------------|
| **Web Service** | $7-25/month | **$0/month** (free tier) |
| **Database** | $7/month (256MB) | **$0/month** (3GB free) |
| **Build Minutes** | Limited (OUT) | **Unlimited** |
| **Deploys** | Limited | **Unlimited** |
| **Total** | **$14-32/month** | **$0/month** 🎉 |

---

## 🎉 Next Steps

1. **Deploy to Railway** (follow steps above)
2. **Test everything**
3. **Update WordPress**
4. **Setup local cron** for weekly updates
5. **Delete Render service** (save $25/month!)

---

**Need help?** Check the logs in Railway dashboard or ask for assistance!

**Ready to deploy?** Let's go! 🚀
