# ⚠️  Database Password Authentication Failed

## The Issue

The DATABASE_URL password in your `.env` file is incorrect or expired.

## Quick Fix (2 Steps)

### Step 1: Get the correct DATABASE_URL from Railway Dashboard

1. Go to https://railway.app/dashboard
2. Select your project: **positive-clarity**
3. Click on **mirror-talk-api** service (not ingestion)
4. Go to **Variables** tab
5. Find `DATABASE_URL`
6. Click the eye icon to reveal the full value
7. Copy the entire connection string

### Step 2: Update your .env file

Replace the DATABASE_URL line in your `.env` file with the correct one:

```bash
DATABASE_URL=postgresql+psycopg://neondb_owner:npg_0l7bPAnmJYOH@ep-snowy-smoke-aj2dycz7-pooler.c-3.us-east-2.aws.neon.tech/neondb?sslmode=require&options=endpoint%3Dep-snowy-smoke-aj2dycz7-pooler
```

Then run again:
```bash
source .venv/bin/activate
python scripts/ingest_all_episodes.py
```

---

## What I Fixed

1. ✅ Removed invalid `EMBEDDING_MODEL` from .env (not supported by config)
2. ⚠️  DATABASE_URL password needs to be updated from Railway dashboard

---

## Alternative: Use Railway CLI

If Railway CLI can access the correct service:

```bash
# List all services
railway service

# Switch to API service  
railway service mirror-talk-api

# Get DATABASE_URL
railway variables | grep DATABASE_URL

# Copy and update .env
```

---

## Current Status

- ✅ Script loads .env correctly
- ✅ All required variables present
- ✅ Environment configured properly
- ❌ DATABASE_URL password is incorrect/expired

**Next step:** Update DATABASE_URL with the correct password from Railway dashboard!
