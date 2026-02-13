# 🚨 URGENT: Fix Railway Ingestion Database Connection

## The Error You're Seeing

```
Database URL format: postgresql+psycopg://***@mirror-talk-db.railway.internal:5432/railway
ERROR | extension "vector" is not available
```

**Problem:** Your ingestion service is using Railway's internal PostgreSQL (`mirror-talk-db.railway.internal`), which doesn't have pgvector.

**Solution:** Change it to use your Neon database (which has pgvector).

---

## Solution 1: Update via Railway Dashboard (EASIEST)

### Step 1: Open Railway Dashboard
1. Go to: https://railway.app
2. Click your project
3. Click the **"mirror-talk-ingestion"** service (the one that's failing)

### Step 2: Go to Variables
1. Click the **"Variables"** tab
2. Look for `DATABASE_URL` 

### Step 3: Update DATABASE_URL
**Current value (WRONG):**
```
Something with "mirror-talk-db.railway.internal"
```

**Change to (CORRECT):**
```
postgresql://neondb_owner:YOUR_PASSWORD@YOUR_ENDPOINT-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require&options=endpoint%3DYOUR_ENDPOINT-pooler
```

### Step 4: Get Your Neon Connection String

**Option A: From Neon Console**
1. Go to: https://console.neon.tech
2. Select your project
3. Click **"Connection Details"**
4. Toggle to **"Pooled connection"** (important!)
5. Make sure format is: **"Connection string"** (not individual fields)
6. Copy the entire string
7. **IMPORTANT:** Must include `&options=endpoint%3D...` at the end

**Option B: From Your Working API Service**
Your `mirror-talk-web` (API) service is already working correctly. Copy its `DATABASE_URL`:
1. In Railway dashboard
2. Click your **"mirror-talk-web"** or main API service
3. Go to **"Variables"** tab
4. Copy the `DATABASE_URL` value
5. Use the SAME value for the ingestion service

### Step 5: Save and Redeploy
1. Click "Save" or the changes auto-save
2. The service will automatically redeploy
3. Wait 2-3 minutes
4. Check deployment logs for success

---

## Solution 2: Delete Railway's PostgreSQL Service

Since you're using Neon and don't need Railway's built-in database:

### Step 1: Remove the Database Link
1. In Railway dashboard, click your **ingestion service**
2. Click **"Settings"** tab
3. Look for "Service Connections" or "Connected Services"
4. If you see `mirror-talk-db` connected, click "Disconnect" or "Remove"

### Step 2: Delete Railway's PostgreSQL (Optional)
1. In Railway dashboard, find the **"mirror-talk-db"** service
2. Click on it
3. Go to **"Settings"** → scroll down to "Danger Zone"
4. Click **"Remove Service"**
5. Confirm deletion

**Warning:** Only do this AFTER you've set the correct DATABASE_URL in both services!

---

## Solution 3: Use Railway CLI (If You Have It)

If you have Railway CLI installed:

```bash
# Switch to the ingestion service
railway link

# Set the correct DATABASE_URL (replace with your Neon URL)
railway variables set DATABASE_URL="postgresql://neondb_owner:YOUR_PASSWORD@YOUR_ENDPOINT-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require&options=endpoint%3DYOUR_ENDPOINT-pooler"

# Trigger redeploy
railway up
```

---

## Solution 4: Remove DATABASE_URL from Code (Use Railway's Provided Variable)

If Railway is automatically setting `DATABASE_URL` to the internal database:

### Step 1: Create a New Variable
1. In Railway dashboard → ingestion service → Variables
2. Click **"New Variable"**
3. Name: `NEON_DATABASE_URL`
4. Value: Your full Neon pooled connection string
5. Save

### Step 2: Update Your Code
Edit `app/core/config.py` to prefer `NEON_DATABASE_URL`:

```python
database_url: str = Field(
    default_factory=lambda: os.getenv("NEON_DATABASE_URL") or os.getenv("DATABASE_URL", ""),
    alias="DATABASE_URL"
)
```

Then commit and push to trigger redeploy.

---

## Verify It's Fixed

After making changes, check the deployment logs:

### ✅ SUCCESS - You'll See:
```
INFO | app.core.db | Database URL format: postgresql+psycopg://***@ep-something.us-east-2.aws.neon.tech/neondb
INFO | app.core.db | ✓ Database initialization complete
INFO | __main__ | Starting ingestion...
INFO | app.ingestion.pipeline | Fetching RSS feed...
INFO | app.ingestion.pipeline | Found 50 episodes
INFO | app.ingestion.pipeline | Processing episode 1/3: ...
```

### ❌ STILL BROKEN - You'll See:
```
INFO | app.core.db | Database URL format: postgresql+psycopg://***@mirror-talk-db.railway.internal:5432/railway
ERROR | app.core.db | extension "vector" is not available
```

---

## Quick Comparison

### Wrong Database (Railway Internal):
```
Hostname: mirror-talk-db.railway.internal
Port: 5432
Database: railway
Problem: ❌ No pgvector extension
```

### Correct Database (Neon):
```
Hostname: ep-something-pooler.us-east-2.aws.neon.tech
Port: 5432
Database: neondb
Solution: ✅ Has pgvector extension
```

---

## Complete Environment Variables

Your ingestion service should have these variables:

```bash
# PRIMARY - Database (must be Neon)
DATABASE_URL=postgresql://neondb_owner:PASSWORD@ep-ENDPOINT-pooler.REGION.aws.neon.tech/neondb?sslmode=require&options=endpoint%3Dep-ENDPOINT-pooler

# RSS Feed
RSS_URL=https://anchor.fm/s/261b1464/podcast/rss

# Optional - Ingestion Settings
WHISPER_MODEL=base
EMBEDDING_PROVIDER=local
MAX_EPISODES=3
ENVIRONMENT=production
```

**DO NOT have:**
- ❌ `DATABASE_PRIVATE_URL` pointing to Railway
- ❌ Any variable with `mirror-talk-db.railway.internal`

---

## Why This Happened

Railway automatically:
1. Created a PostgreSQL service for you
2. Connected it to your services
3. Set `DATABASE_URL` to point to it

But:
- Railway's PostgreSQL doesn't have pgvector
- You can't install extensions on Railway's managed Postgres
- Your Neon database has pgvector pre-installed

**Solution:** Override Railway's automatic DATABASE_URL with your Neon URL.

---

## If You Can't Find Your Neon Connection String

### Method 1: Check Your API Service
Your API service is working, so it has the correct URL:

1. Railway dashboard → Click your **API/web service** (the one that works)
2. Variables tab
3. Copy the `DATABASE_URL` value
4. Use the same value for ingestion service

### Method 2: From Neon Console
1. https://console.neon.tech
2. Select your project
3. Dashboard → "Connection Details" button
4. Select "Pooled connection" from dropdown
5. Copy the connection string
6. Ensure it ends with `&options=endpoint%3D...`

### Method 3: From Previous Documentation
Check these files in your project:
- `NEON_IPV6_FIX.md`
- `railway.env.example`
- `.env` (if you have it locally)

---

## Common Mistakes to Avoid

### ❌ Mistake #1: Using Direct Connection Instead of Pooled
```
Wrong: @ep-something.us-east-2.aws.neon.tech
Right: @ep-something-pooler.us-east-2.aws.neon.tech
         Notice the "-pooler" ────────────┘
```

### ❌ Mistake #2: Missing the options Parameter
```
Wrong: ...?sslmode=require
Right: ...?sslmode=require&options=endpoint%3Dep-something-pooler
                            ────────────────┘ This is required!
```

### ❌ Mistake #3: Using Railway's Internal DB
```
Wrong: mirror-talk-db.railway.internal
Right: ep-something-pooler.us-east-2.aws.neon.tech
```

---

## Testing After Fix

### Test 1: Check the Logs
```
Railway Dashboard → Ingestion Service → Deployments → Latest → Deploy Logs

Look for:
✅ "Database URL format: postgresql+psycopg://***@ep-...neon.tech/neondb"
✅ "Database initialization complete"
✅ "Starting ingestion..."
```

### Test 2: Trigger Manual Ingestion
From Railway's web shell or your terminal:
```bash
curl -X POST "https://your-ingestion-service.up.railway.app/ingest"
```

### Test 3: Check Database
Your API should still work and see the same data:
```bash
curl "https://ask-mirror-talk-production.up.railway.app/status"
```

---

## Need Help?

If you're still stuck after trying these solutions:

1. **Share your Railway dashboard screenshot** (Variables tab) - Hide passwords!
2. **Share the first 20 lines** of your deployment logs
3. **Confirm:** Is your API service working? (test `/health` endpoint)
4. **Check:** Do both services (API + ingestion) use the same DATABASE_URL?

---

## TL;DR - Fastest Fix

1. **Go to Railway** → Ingestion service → Variables
2. **Find DATABASE_URL** variable
3. **Replace it** with your Neon pooled connection string
4. **Save** (auto-redeploys)
5. **Wait 3 minutes** and check logs

**Neon URL format:**
```
postgresql://neondb_owner:PASSWORD@ep-ENDPOINT-pooler.REGION.aws.neon.tech/neondb?sslmode=require&options=endpoint%3Dep-ENDPOINT-pooler
```

**Don't have the Neon URL?**
→ Copy it from your working API service's Variables tab!

---

*This fix takes 2 minutes once you have the correct Neon connection string.*
