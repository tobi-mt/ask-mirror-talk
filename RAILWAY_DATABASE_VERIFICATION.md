# ✅ Railway Ingestion - Verification Checklist

## Your Correct DATABASE_URL

```
postgresql+psycopg://neondb_owner:npg_0l7bPAnmJYOH@ep-snowy-smoke-aj2dycz7-pooler.c-3.us-east-2.aws.neon.tech/neondb?sslmode=require&options=endpoint%3Dep-snowy-smoke-aj2dycz7-pooler
```

✅ This is the correct format!
✅ Has `-pooler` in hostname
✅ Has `options=endpoint%3D...` parameter
✅ Same as your working API service

---

## Why It's Still Failing

Even though you have the correct DATABASE_URL, the logs show:

```
Database URL format: postgresql+psycopg://***@mirror-talk-db.railway.internal:5432/railway
```

This means Railway is **still connecting to the internal database** instead of Neon.

### Possible Causes:

1. **Variable not saved** - Did you click "Save" or did changes auto-save?
2. **Variable name wrong** - Must be exactly `DATABASE_URL` (uppercase, no spaces)
3. **Railway auto-connecting** - Railway linked the internal database automatically
4. **Old deployment cached** - Need to force redeploy
5. **Service has DATABASE_PRIVATE_URL** - This overrides DATABASE_URL

---

## Solution Steps

### Step 1: Double-Check Variable Name

In Railway Dashboard → Your Ingestion Service → Variables:

**Look for exactly:**
```
DATABASE_URL
```

**NOT:**
- `database_url` (wrong - lowercase)
- `DATABASE_URL ` (wrong - has space)
- `NEON_DATABASE_URL` (wrong - different name)
- `DATABASE_PRIVATE_URL` (this will override it!)

### Step 2: Remove Railway's Auto-Connected Database

Railway might have automatically linked the internal database:

1. In Railway Dashboard → Click **"mirror-talk-ingestion"** service
2. Click **"Settings"** tab
3. Scroll to **"Service Connections"** or **"Connected Services"**
4. If you see `mirror-talk-db` listed:
   - Click the "..." or "X" button
   - Select **"Disconnect"** or **"Remove"**
5. This removes the auto-generated `DATABASE_PRIVATE_URL` variable

### Step 3: Verify Variables

After disconnecting, check Variables tab again:

**Should have:**
```bash
DATABASE_URL=postgresql+psycopg://neondb_owner:npg_0l7bPAnmJYOH@ep-snowy-smoke-aj2dycz7-pooler.c-3.us-east-2.aws.neon.tech/neondb?sslmode=require&options=endpoint%3Dep-snowy-smoke-aj2dycz7-pooler

RSS_URL=https://anchor.fm/s/261b1464/podcast/rss
WHISPER_MODEL=base
EMBEDDING_PROVIDER=local
```

**Should NOT have:**
```bash
DATABASE_PRIVATE_URL=...  ❌ Remove this if present
DATABASE_URL=...mirror-talk-db.railway.internal...  ❌ Wrong!
```

### Step 4: Force Redeploy

After making changes:

**Option A: Via Dashboard**
1. Go to **"Deployments"** tab
2. Click the "..." menu on latest deployment
3. Select **"Redeploy"**

**Option B: Push Empty Commit**
```bash
git commit --allow-empty -m "Force Railway redeploy"
git push origin main
```

**Option C: Restart Service**
1. In service settings
2. Look for "Restart" button
3. Click it

---

## Verify the Fix

### Check 1: Deployment Logs

After redeploying, check logs:

**Go to:** Railway → Ingestion Service → Deployments → Latest → Deploy Logs

**Look for this line:**
```
INFO | app.core.db | Database URL format: postgresql+psycopg://***@ep-snowy-smoke-aj2dycz7-pooler.c-3.us-east-2.aws.neon.tech/neondb
```

**Should NOT see:**
```
postgresql+psycopg://***@mirror-talk-db.railway.internal:5432/railway  ❌
```

### Check 2: Database Initialization

Continue reading logs, should see:
```
✅ INFO | app.core.db | ✓ Database initialization complete
✅ INFO | __main__ | Starting ingestion...
✅ INFO | app.ingestion.pipeline | Fetching RSS feed...
```

**Should NOT see:**
```
❌ ERROR | app.core.db | extension "vector" is not available
```

---

## If Still Failing After All This

### Nuclear Option: Delete and Recreate Service

If Railway keeps auto-connecting the wrong database:

1. **Save your environment variables** (copy them somewhere)
2. **Delete the ingestion service**
3. **Delete the `mirror-talk-db` PostgreSQL service** (you don't need it)
4. **Create new ingestion service** from scratch
5. **Add only these variables:**
   ```
   DATABASE_URL=postgresql+psycopg://neondb_owner:npg_0l7bPAnmJYOH@ep-snowy-smoke-aj2dycz7-pooler.c-3.us-east-2.aws.neon.tech/neondb?sslmode=require&options=endpoint%3Dep-snowy-smoke-aj2dycz7-pooler
   RSS_URL=https://anchor.fm/s/261b1464/podcast/rss
   WHISPER_MODEL=base
   EMBEDDING_PROVIDER=local
   ```
6. **Deploy**

---

## Alternative: Use Railway CLI

If you have Railway CLI:

```bash
# Link to the ingestion service
railway link

# Check current variables
railway variables

# Remove the wrong database variable if it exists
railway variables delete DATABASE_PRIVATE_URL

# Set the correct one
railway variables set DATABASE_URL="postgresql+psycopg://neondb_owner:npg_0l7bPAnmJYOH@ep-snowy-smoke-aj2dycz7-pooler.c-3.us-east-2.aws.neon.tech/neondb?sslmode=require&options=endpoint%3Dep-snowy-smoke-aj2dycz7-pooler"

# Redeploy
railway up
```

---

## Alternative: Override in Code

If Railway keeps forcing the wrong database, update your code:

**Edit:** `app/core/config.py`

```python
import os
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ... existing fields ...
    
    database_url: str = Field(
        default_factory=lambda: (
            # First try explicit NEON_DATABASE_URL
            os.getenv("NEON_DATABASE_URL") or 
            # Then try DATABASE_URL, but reject Railway's internal DB
            (lambda url: url if url and "railway.internal" not in url else "")(os.getenv("DATABASE_URL")) or
            # Fallback to hardcoded Neon (as last resort)
            "postgresql+psycopg://neondb_owner:npg_0l7bPAnmJYOH@ep-snowy-smoke-aj2dycz7-pooler.c-3.us-east-2.aws.neon.tech/neondb?sslmode=require&options=endpoint%3Dep-snowy-smoke-aj2dycz7-pooler"
        ),
        alias="DATABASE_URL"
    )
```

This will:
1. Prefer `NEON_DATABASE_URL` if set
2. Use `DATABASE_URL` only if it's NOT Railway's internal DB
3. Fall back to hardcoded Neon URL

Then commit and push:
```bash
git add app/core/config.py
git commit -m "Force use of Neon database, reject Railway internal DB"
git push origin main
```

---

## Quick Diagnostic Commands

### Check What Railway Sees

In Railway's web shell (click service → Shell tab):

```bash
# Check which database URL is being used
echo $DATABASE_URL

# Should output:
# postgresql+psycopg://...@ep-snowy-smoke-aj2dycz7-pooler...

# Should NOT output:
# ...@mirror-talk-db.railway.internal...
```

### Check Database Connection

```bash
# Test connection to Neon
psql "$DATABASE_URL" -c "SELECT version();"

# Should connect and show PostgreSQL version
# If it fails, the URL is wrong
```

---

## Summary

**Your DATABASE_URL is correct!** ✅

The problem is Railway is still using the internal database. Here's what to do:

1. ✅ Go to Railway → Ingestion Service → **Settings** → Disconnect `mirror-talk-db`
2. ✅ Go to **Variables** → Verify `DATABASE_URL` is exactly as shown above
3. ✅ **Redeploy** the service
4. ✅ Check logs to verify it connects to `ep-snowy-smoke-aj2dycz7-pooler.c-3.us-east-2.aws.neon.tech`

**If that doesn't work:**
- Delete `mirror-talk-db` service entirely (you don't need it)
- Or use the code override solution above

---

## Expected Success

After fixing, you'll see:

```
2026-02-13 XX:XX:XX | INFO | app.core.db | Database URL format: postgresql+psycopg://***@ep-snowy-smoke-aj2dycz7-pooler.c-3.us-east-2.aws.neon.tech/neondb
2026-02-13 XX:XX:XX | INFO | app.core.db | ✓ Database initialization complete
2026-02-13 XX:XX:XX | INFO | __main__ | Starting ingestion...
2026-02-13 XX:XX:XX | INFO | app.ingestion.pipeline | Fetching RSS feed...
2026-02-13 XX:XX:XX | INFO | app.ingestion.pipeline | Found 50 episodes in feed
2026-02-13 XX:XX:XX | INFO | app.ingestion.pipeline | Processing episode 1/3: ...
```

Then your ingestion will work and you can load all your episodes! 🎉

---

*The key issue: Railway auto-connects its internal database. You need to disconnect it and force use of Neon.*
