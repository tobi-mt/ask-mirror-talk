# Railway Quick Start

The fastest way to get Ask Mirror Talk running on Railway.

## Prerequisites

- GitHub account with repository access
- Railway account (free tier is fine)
- Neon Postgres database (or use Railway's Postgres plugin)

## Method 1: Automated Setup (Recommended)

```bash
# Clone the repository
cd /Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk

# Run the setup script
./scripts/setup_railway.sh
```

The script will:
1. Install Railway CLI (if needed)
2. Login to Railway
3. Initialize your project
4. Prompt you for environment variables
5. Deploy the application

## Method 2: Manual Setup

### 1. Deploy to Railway

Go to [Railway](https://railway.app/):
1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose `ask-mirror-talk`
4. Railway deploys automatically

### 2. Add Database

**Option A: Railway Postgres Plugin**
1. New Service → Database → PostgreSQL
2. `DATABASE_URL` is auto-created

**Option B: External Neon**
1. Create database at [Neon](https://neon.tech/)
2. Add `DATABASE_URL` in Railway Settings → Variables

### 3. Add Environment Variables

In Railway → Settings → Variables, add from `railway.env.example`:

**Required:**
- `DATABASE_URL` (from Neon or Railway Postgres)
- `RSS_URL`
- `ADMIN_USER`
- `ADMIN_PASSWORD`

Railway redeploys automatically.

### 4. Ingest Episodes

```bash
railway run bash
python scripts/ingest_all_episodes.py
```

### 5. Set Up Automatic Updates

Add GitHub secrets (Settings → Secrets → Actions):
- `DATABASE_URL`
- `RSS_URL`

GitHub Actions will run every 6 hours.

## Verify Everything Works

```bash
# Get your Railway URL from the dashboard, then:
RAILWAY_URL="https://your-app.railway.app"

# Health check
curl "$RAILWAY_URL/health"

# Status check
curl "$RAILWAY_URL/status"

# Test question
curl -X POST "$RAILWAY_URL/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Mirror Talk about?"}'
```

## Complete Documentation

For detailed guides, see:
- **[RAILWAY_SETUP_GUIDE.md](RAILWAY_SETUP_GUIDE.md)** - Complete walkthrough
- **[INGESTION_COMPLETE_GUIDE.md](INGESTION_COMPLETE_GUIDE.md)** - Ingestion methods
- **[railway.env.example](railway.env.example)** - All environment variables

## Need Help?

Check **RAILWAY_SETUP_GUIDE.md** for:
- Troubleshooting common issues
- Monitoring and logs
- Cost optimization
- Best practices
