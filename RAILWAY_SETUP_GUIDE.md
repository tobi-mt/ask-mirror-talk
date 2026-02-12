# Railway Setup Guide

This guide walks you through deploying Ask Mirror Talk to Railway with all environment variables configured.

## Prerequisites

- GitHub account with the mirrored repository
- Railway account
- Neon Postgres account (or use Railway's Postgres plugin)

## Step 1: Deploy to Railway

### Option A: Deploy from GitHub (Recommended)

1. Go to [Railway](https://railway.app/)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your `ask-mirror-talk` repository
5. Railway will automatically detect the Dockerfile and deploy

### Option B: Use Railway CLI

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize in your project directory
cd /Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk
railway init

# Deploy
railway up
```

## Step 2: Add Neon Postgres Database

### Option A: Use Railway's Postgres Plugin

1. In your Railway project, click "New Service"
2. Select "Database" → "PostgreSQL"
3. Railway will automatically create a `DATABASE_URL` variable

### Option B: Use External Neon Postgres

1. Create a database at [Neon](https://neon.tech/)
2. Copy the connection string
3. In Railway project → Settings → Variables
4. Add variable: `DATABASE_URL=postgresql://user:password@host/dbname`

## Step 3: Add Environment Variables

In Railway dashboard → Your Service → Settings → Variables, add all variables from `railway.env.example`:

### Required Variables

| Variable | Value | Notes |
|----------|-------|-------|
| `DATABASE_URL` | `postgresql://...` | From Neon or Railway Postgres |
| `RSS_URL` | `https://anchor.fm/s/261b1464/podcast/rss` | Your podcast RSS feed |
| `ADMIN_USER` | `tobi` | Admin dashboard username |
| `ADMIN_PASSWORD` | `@GoingPlaces#2026` | Admin dashboard password |

### Optional Variables (with defaults)

| Variable | Default | Notes |
|----------|---------|-------|
| `APP_NAME` | `Ask Mirror Talk` | Application name |
| `ENVIRONMENT` | `production` | Environment name |
| `RSS_POLL_MINUTES` | `60` | How often to check RSS |
| `MAX_EPISODES_PER_RUN` | `10` | Episodes per ingestion |
| `EMBEDDING_PROVIDER` | `local` | Use local embeddings |
| `WHISPER_MODEL` | `base` | Whisper model size |
| `TRANSCRIPTION_PROVIDER` | `faster_whisper` | Transcription engine |
| `TOP_K` | `6` | Search results count |
| `MIN_SIMILARITY` | `0.15` | Minimum similarity score |
| `RATE_LIMIT_PER_MINUTE` | `20` | API rate limit |
| `ALLOWED_ORIGINS` | (your domains) | CORS allowed origins |
| `ADMIN_ENABLED` | `true` | Enable admin dashboard |

### Railway Auto-Provided Variables

These are automatically set by Railway (don't add them):
- `PORT` - The port your service listens on
- `RAILWAY_ENVIRONMENT`
- `RAILWAY_PROJECT_ID`
- `RAILWAY_SERVICE_ID`

## Step 4: Deploy and Verify

1. After adding all variables, Railway will automatically redeploy
2. Check the deployment logs for successful startup
3. Look for: `✓ Database initialized successfully`
4. Get your public URL from Railway dashboard

## Step 5: Test the Deployment

```bash
# Replace with your Railway URL
RAILWAY_URL="https://your-app.railway.app"

# Test health endpoint
curl "$RAILWAY_URL/health"

# Test status endpoint
curl "$RAILWAY_URL/status"

# Test ask endpoint
curl -X POST "$RAILWAY_URL/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Mirror Talk about?"}'
```

## Step 6: Ingest Podcast Episodes

### Option A: Use Railway Shell (Recommended)

```bash
# Open Railway shell
railway run bash

# Run the ingestion script (ingests ALL episodes)
python scripts/ingest_all_episodes.py

# Or update with latest episodes only
python scripts/update_latest_episodes.py
```

### Option B: Create a One-Off Service

1. In Railway dashboard → New Service → Empty Service
2. Settings → Variables → Share all variables from main service
3. Deploy → Select same GitHub repo
4. Override Start Command: `python scripts/ingest_all_episodes.py`
5. This service will run once and exit

## Step 7: Set Up Automatic Updates

### Option A: GitHub Actions (Recommended)

Create `.github/workflows/update-episodes.yml`:

```yaml
name: Update Latest Episodes

on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
  workflow_dispatch:  # Manual trigger

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Update episodes
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          RSS_URL: ${{ secrets.RSS_URL }}
        run: python scripts/update_latest_episodes.py
```

Then add secrets in GitHub → Settings → Secrets and variables → Actions:
- `DATABASE_URL`
- `RSS_URL`

### Option B: Railway Cron Job

1. Create a new service in Railway
2. Set it as a "Cron Job" type
3. Schedule: `0 */6 * * *` (every 6 hours)
4. Start command: `python scripts/update_latest_episodes.py`
5. Share environment variables from main service

### Option C: External Cron Service

Use services like:
- [cron-job.org](https://cron-job.org/)
- [EasyCron](https://www.easycron.com/)
- [GitHub Actions](https://github.com/features/actions)

Set them to call your Railway endpoint:
```bash
curl -X POST "https://your-app.railway.app/admin/ingest" \
  -H "Authorization: Basic $(echo -n 'tobi:@GoingPlaces#2026' | base64)"
```

## Step 8: Update WordPress Widget

Update the WordPress widget to use your Railway URL:

```javascript
// In wordpress/ask-mirror-talk.js
const API_URL = 'https://your-app.railway.app';
```

## Monitoring

### View Logs
```bash
railway logs
```

### Check Status
```bash
curl https://your-app.railway.app/status
```

### Access Admin Dashboard
Visit: `https://your-app.railway.app/admin`
- Username: `tobi`
- Password: `@GoingPlaces#2026`

## Troubleshooting

### Database Connection Issues

If you see "DATABASE_URL is empty":
1. Check Railway → Settings → Variables
2. Verify `DATABASE_URL` is set correctly
3. Redeploy the service

### Ingestion Fails

If ingestion doesn't complete:
1. Check logs: `railway logs`
2. Verify RSS_URL is accessible
3. Check memory limits in Railway settings (upgrade if needed)
4. Try ingesting in smaller batches:
   ```python
   # In Railway shell
   python scripts/update_latest_episodes.py
   ```

### Health Check Fails

If `/health` returns 503:
1. Database connection failed
2. Check `DATABASE_URL` format
3. Ensure Neon database allows Railway IP addresses

## Cost Optimization

### Railway Free Tier
- 500 hours/month execution time
- $5 credit/month
- Shared CPU and memory

### Neon Free Tier
- 512 MB storage
- 1 project
- Autosuspend after inactivity

### Tips
1. Use `faster_whisper` instead of OpenAI Whisper (free)
2. Use local embeddings instead of OpenAI (free)
3. Set `RSS_POLL_MINUTES=360` to check every 6 hours
4. Use GitHub Actions for scheduled updates (free for public repos)

## Next Steps

- [ ] Add all environment variables
- [ ] Verify deployment with `/health` check
- [ ] Run initial ingestion with `scripts/ingest_all_episodes.py`
- [ ] Set up automatic updates (GitHub Actions or Railway Cron)
- [ ] Update WordPress widget with Railway URL
- [ ] Test the `/ask` endpoint thoroughly
- [ ] Monitor logs for any errors
- [ ] Set up domain (optional)

## Support

- Railway Docs: https://docs.railway.app/
- Neon Docs: https://neon.tech/docs/
- FastAPI Docs: https://fastapi.tiangolo.com/
