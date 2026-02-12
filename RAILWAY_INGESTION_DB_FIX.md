# 🚨 Railway Ingestion Service - Database Fix

## Problem

Your Railway ingestion service crashed with this error:
```
extension "vector" is not available
Could not open extension control file "/usr/share/postgresql/17/extension/vector.control"
```

**Root Cause:** The ingestion service is connecting to Railway's internal PostgreSQL database (`mirror-talk-db.railway.internal`), which **doesn't have pgvector installed**.

**Solution:** Configure the ingestion service to use your **Neon database** instead (which has pgvector support).

---

## Quick Fix (Railway Dashboard)

### Step 1: Open Railway Dashboard

1. Go to [Railway Dashboard](https://railway.app)
2. Click your project
3. Find the **"mirror-talk-ingestion"** service
4. Click on it

### Step 2: Add/Update Environment Variables

Click **"Variables"** tab and add/update:

```bash
DATABASE_URL=postgresql://neondb_owner:your-password@ep-cool-name-123456.us-east-2.aws.neon.tech/neondb?sslmode=require&options=endpoint%3Dep-cool-name-123456-pooler
```

**Where to get this?**
1. Go to your [Neon Dashboard](https://console.neon.tech)
2. Select your project
3. Click "Connection Details"
4. Copy the **"Pooled connection"** string (IPv4)
5. Make sure it includes `&options=endpoint%3D...` at the end

**Important:** Use the **pooled connection** (with `-pooler` in the hostname), NOT the direct connection.

### Step 3: Remove Old Database Variable

If you see a variable called `DATABASE_PRIVATE_URL` or similar pointing to `mirror-talk-db.railway.internal`:
- Click the "..." menu
- Select "Remove"

### Step 4: Redeploy

After updating the variable:
1. Click "Deployments" tab
2. Click the "⋯" menu on the latest deployment
3. Select "Redeploy"
4. Or just push a new commit to trigger deployment

---

## Alternative: Update via Railway CLI

If you have Railway CLI installed:

```bash
# Set the Neon database URL
railway variables set DATABASE_URL="postgresql://neondb_owner:your-password@ep-cool-name-123456.us-east-2.aws.neon.tech/neondb?sslmode=require&options=endpoint%3Dep-cool-name-123456-pooler" --service mirror-talk-ingestion

# Redeploy
railway up --service mirror-talk-ingestion
```

---

## Verify the Fix

### Step 1: Check Deployment Logs

After redeploying:
1. Go to Railway Dashboard → Your Service → Deployments
2. Click latest deployment → "Deploy Logs"
3. Look for:

**✅ Success indicators:**
```
INFO | app.core.db | ✓ Database initialization complete
INFO | __main__ | Starting ingestion...
INFO | app.ingestion.pipeline | Processing episode: ...
```

**❌ Still broken if you see:**
```
ERROR | app.core.db | extension "vector" is not available
ERROR | Could not open extension control file
```

### Step 2: Test Ingestion

Once deployed successfully, trigger an ingestion:

```bash
# From your local terminal
curl -X POST "https://your-ingestion-service.up.railway.app/ingest"
```

Or use Railway's web shell:
1. Click your ingestion service
2. Click "Shell" tab
3. Run:
```bash
python scripts/bulk_ingest.py --max-episodes 3
```

---

## Why This Happened

Railway created a PostgreSQL service for you (`mirror-talk-db`), but:
- ❌ It's PostgreSQL 17 without pgvector extension
- ❌ You can't install extensions on Railway's managed Postgres
- ✅ Your Neon database has pgvector pre-installed

**The solution:** Use Neon for everything (it's designed for this).

---

## Complete Environment Variables

Your ingestion service should have these variables:

```bash
# Database (Neon - with pgvector)
DATABASE_URL=postgresql://neondb_owner:...@ep-...-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require&options=endpoint%3D...

# RSS Feed
RSS_URL=https://anchor.fm/s/261b1464/podcast/rss

# Ingestion Settings (optional)
WHISPER_MODEL=base
EMBEDDING_PROVIDER=local
MAX_EPISODES=3

# Environment
ENVIRONMENT=production
```

---

## If You Have Both Services

If you have both `mirror-talk-web` (API) and `mirror-talk-ingestion`:

### For Web Service (API):
```bash
DATABASE_URL=postgresql://neondb_owner:...@ep-...-pooler...  # Neon pooled
PORT=8000
```

### For Ingestion Service:
```bash
DATABASE_URL=postgresql://neondb_owner:...@ep-...-pooler...  # Same Neon database
RSS_URL=https://anchor.fm/s/261b1464/podcast/rss
WHISPER_MODEL=base
```

**Both should use the SAME Neon database URL!**

---

## Remove Railway's Built-in PostgreSQL (Optional)

Since you're not using it, you can remove it to avoid confusion:

1. Go to Railway Dashboard
2. Find the `mirror-talk-db` service (PostgreSQL icon)
3. Click on it
4. Settings → Danger Zone → "Remove Service"

**Warning:** Only do this after confirming both services use Neon!

---

## Testing Checklist

After fixing:

- [ ] Ingestion service shows "Database initialization complete" in logs
- [ ] No "vector extension" errors
- [ ] Can run `curl -X POST .../ingest` successfully
- [ ] Episodes are being processed
- [ ] Chunks are created in database
- [ ] API service still works (uses same Neon DB)

---

## Troubleshooting

### Still Getting "vector" Error

**Check:**
```bash
# In Railway service settings → Variables
# Make sure DATABASE_URL points to Neon, not Railway internal DB
```

**Look for:**
- ❌ `mirror-talk-db.railway.internal` (wrong - Railway's DB)
- ✅ `ep-something.us-east-2.aws.neon.tech` (correct - Neon)

### Can't Find Neon Connection String

1. Go to [Neon Console](https://console.neon.tech)
2. Select your project
3. Click "Connection Details"
4. Toggle to "Pooled connection"
5. Copy the full connection string
6. Make sure it has `&options=endpoint%3D...` at the end

### Connection Refused / Timeout

**Problem:** Connection string missing `options` parameter  
**Fix:** Use the pooled connection with full parameters:
```
postgresql://user:pass@host-pooler.region.aws.neon.tech/db?sslmode=require&options=endpoint%3Dhost-pooler
```

---

## Quick Reference

### What You Need:
1. ✅ Neon database URL (pooled connection)
2. ✅ Railway service environment variables updated
3. ✅ Redeploy the service

### Expected Result:
```
✓ Database initialization complete
✓ Starting ingestion...
✓ Processed 3 episodes
✓ Created 150 chunks
```

---

## Next Steps After Fix

1. **Verify API works:** Test `/health` and `/status` endpoints
2. **Run ingestion:** Load all your episodes
3. **Test widget:** Ask questions and verify citations work
4. **Monitor logs:** Check for any other errors

---

**Estimated Fix Time:** 2 minutes  
**Difficulty:** Easy (just update one environment variable)

---

*Need help finding your Neon connection string? Check `NEON_IPV6_FIX.md` for details.*
