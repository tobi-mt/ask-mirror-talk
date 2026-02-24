# 🚀 Alternative: Deploy to Render Instead of Railway

## Why Consider Render?

Railway has a very strict **100-second healthcheck window**, which your app is struggling to meet even with all optimizations. Render offers:

✅ **5-minute healthcheck timeout** (vs Railway's 100s)
✅ **Built-in PostgreSQL** with pgvector support
✅ **Better free tier** resources
✅ **Simpler configuration**
✅ **More forgiving deployment** process

## Quick Render Setup (10 minutes)

### Step 1: Sign Up

1. Go to https://render.com
2. Click **"Get Started"**
3. Sign up with GitHub (recommended)

### Step 2: Create PostgreSQL Database

1. Click **"New +"** → **"PostgreSQL"**
2. Configure:
   - **Name**: `ask-mirror-talk-db`
   - **Database**: `neondb` (or any name)
   - **User**: Auto-generated
   - **Region**: Oregon (or closest to you)
   - **Plan**: **Free**
3. Click **"Create Database"**
4. Wait 2-3 minutes for provisioning
5. Copy the **"Internal Database URL"** (starts with `postgresql://`)

### Step 3: Enable pgvector Extension

1. In your database dashboard, click **"Connect"** → **"PSQL Command"**
2. Copy the command and run locally:
   ```bash
   psql <your-connection-url>
   ```
3. In psql, run:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   \q
   ```

### Step 4: Create Web Service

1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Select `tobi-mt/ask-mirror-talk`
4. Configure:
   - **Name**: `ask-mirror-talk`
   - **Region**: Same as database
   - **Branch**: `main`
   - **Root Directory**: ` ` (leave empty)
   - **Build Command**: `pip install -e .`
   - **Start Command**: `uvicorn app.api.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: **Free**

### Step 5: Set Environment Variables

Click **"Advanced"** → Add these variables:

```bash
DATABASE_URL=<your-render-postgres-internal-url>
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

**Important:** For `DATABASE_URL`, convert Render's URL format:
- If it's `postgres://...`, change to `postgresql+psycopg://...`
- Example: `postgresql+psycopg://user:pass@host/db`

### Step 6: Deploy

1. Click **"Create Web Service"**
2. Render will automatically:
   - Build Docker image
   - Deploy container
   - Run healthcheck
3. Wait 5-10 minutes for first deployment

**Expected logs:**
```
Building...
==> Installing dependencies
==> Building Docker image
==> Deploying...
==> Health check passed ✓
==> Your service is live at https://ask-mirror-talk.onrender.com
```

### Step 7: Initialize Database

Once deployed, use Render's Shell:

1. Go to your service dashboard
2. Click **"Shell"** tab
3. Run:
   ```bash
   python -m app.ingestion.pipeline_optimized
   ```

Or initialize from your local machine:
```bash
export DATABASE_URL="<render-postgres-url>"
python -m app.ingestion.pipeline_optimized
```

## Render vs Railway Comparison

| Feature | Render | Railway |
|---------|--------|---------|
| **Healthcheck Timeout** | 5 minutes ✅ | 100 seconds ❌ |
| **Free Tier** | 750 hours/month | 500 hours/month |
| **PostgreSQL** | Included, free | Need external (Neon) |
| **Build Time** | ~3-5 min | ~2-3 min |
| **Deployment** | Git push | Git push |
| **Custom Domains** | Free | Free |
| **Auto-deploy** | Yes | Yes |
| **Logs** | Better UI | Basic |

## Render Configuration Files

No special config needed! Render auto-detects:
- `Dockerfile` (will use it)
- Or uses buildpacks if no Dockerfile

**Optional `render.yaml`** (for Infrastructure as Code):
```yaml
services:
  - type: web
    name: ask-mirror-talk
    env: docker
    dockerfilePath: ./Dockerfile
    healthCheckPath: /health
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: ask-mirror-talk-db
          property: connectionString
      - key: RSS_URL
        value: https://anchor.fm/s/261b1464/podcast/rss
      # ... add other vars

databases:
  - name: ask-mirror-talk-db
    databaseName: neondb
    user: mirror_talk
```

## Why Render Might Work Better

1. **Forgiving Healthcheck**: 5 minutes vs 100 seconds gives your app plenty of time
2. **Better Logging**: Easier to debug startup issues
3. **PostgreSQL Included**: No need for external Neon database
4. **Free SSL**: Automatic HTTPS with custom domains
5. **Better Free Tier**: More generous resource limits

## Migration Steps

If you want to switch from Railway to Render:

1. **Stop Railway service** (to avoid double billing)
2. **Create Render account** and follow steps above
3. **Update WordPress** with new Render URL
4. **Test everything** works on Render
5. **Delete Railway project** (optional)

## Testing Your Render Deployment

```bash
# Replace with your actual Render URL
RENDER_URL="https://ask-mirror-talk.onrender.com"

# Health check
curl $RENDER_URL/health

# Status
curl $RENDER_URL/status

# Ask question
curl -X POST $RENDER_URL/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Mirror Talk about?"}'
```

## Render Free Tier Limitations

- **750 hours/month** of runtime
- **Spins down after 15 min** of inactivity (30s cold start)
- **512 MB RAM**
- **0.1 CPU**
- **100 GB bandwidth/month**

**For your use case**: Perfect! Should easily handle 1000s of requests/month.

## Cold Starts on Render

Free tier services spin down after 15 minutes of inactivity. First request after sleep:
- Takes ~30 seconds to wake up
- Subsequent requests are fast

**Solutions:**
1. **Upgrade to paid plan** ($7/month) - no cold starts
2. **Use external ping service** (UptimeRobot) - keeps alive
3. **Accept cold starts** - fine for low-traffic sites

## Next Steps

1. ✅ Try the enhanced Railway deployment with logging
2. ⏰ If it still fails, switch to Render (10 min setup)
3. 🎉 Enjoy a working deployment!

---

**Recommendation**: Give Railway one more try with the enhanced logging. If it still fails, Render is your best bet. The 5-minute healthcheck timeout makes all the difference.
