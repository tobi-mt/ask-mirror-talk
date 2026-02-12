# Neon IPv6 Connection Fix for Railway

## 🔴 Problem

Railway deployment fails with:
```
connection to server at "2600:1f16:12b2:b40a:533d:22ad:38c2:f393", port 5432 failed: 
Network is unreachable
```

**Root Cause:** Neon returns IPv6 addresses, but Railway's network doesn't support IPv6 connections.

---

## ✅ Solution 1: Use Connection Pooler with Forced IPv4 (RECOMMENDED)

### Step 1: Get Your Neon Connection Details

From your Neon dashboard:
- Project: `snowy-smoke-aj2dycz7`
- Region: `us-east-2`
- Pooler hostname: `ep-snowy-smoke-aj2dycz7-pooler.us-east-2.aws.neon.tech`

### Step 2: Update DATABASE_URL in Railway

Go to Railway → Your Service → Settings → Variables

**Replace your current DATABASE_URL with this format:**

```
postgresql+psycopg://neondb_owner:YOUR_PASSWORD@ep-snowy-smoke-aj2dycz7-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require&options=endpoint%3Dep-snowy-smoke-aj2dycz7-pooler
```

**Key parts:**
1. `postgresql+psycopg://` - Use psycopg3 driver
2. `neondb_owner:YOUR_PASSWORD` - Your Neon credentials
3. `@ep-snowy-smoke-aj2dycz7-pooler.us-east-2.aws.neon.tech` - Pooler endpoint
4. `/neondb` - Database name
5. `?sslmode=require` - SSL required
6. `&options=endpoint%3Dep-snowy-smoke-aj2dycz7-pooler` - **Force pooler routing** (critical!)

**Where to find YOUR_PASSWORD:**
- Neon Dashboard → Your Project → Connection Details → Password

---

## ✅ Solution 2: Use Direct Connection with IPv4 Hint

If Solution 1 doesn't work, try adding `hostaddr` to force IPv4 resolution:

```
postgresql+psycopg://neondb_owner:YOUR_PASSWORD@ep-snowy-smoke-aj2dycz7-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require&resolve=ipv4
```

---

## ✅ Solution 3: Enable External Connections in Neon

1. Go to Neon Dashboard → Your Project → Settings
2. Under "IP Allow" or "IP Restrictions", add Railway's IP ranges:
   - Click "Add IP Address"
   - Add: `0.0.0.0/0` (allows all IPs - for testing)

3. Ensure "Enable Pooler" is turned ON

---

## 🧪 Testing the Connection

### Test 1: From Railway Shell

```bash
railway run bash
python -c "import os; from app.core.db import init_db; init_db(); print('✅ Connected!')"
```

### Test 2: Check Logs

After updating DATABASE_URL:
- Railway will automatically restart your service
- Check Deploy Logs for: `✓ Database initialization successful`
- Should NOT see: `Network is unreachable`

### Test 3: Hit the Status Endpoint

```bash
curl https://your-railway-app.railway.app/status
```

Should return:
```json
{
  "status": "healthy",
  "episodes": 0,
  "chunks": 0,
  "database": "connected"
}
```

---

## 🔍 Verify Your Current Setup

### Check Current DATABASE_URL Format

In Railway dashboard, verify your DATABASE_URL has:
- ✅ `postgresql+psycopg://` (not `postgresql://`)
- ✅ `-pooler` in hostname
- ✅ `?sslmode=require` parameter
- ✅ `&options=endpoint%3D...` parameter (add if missing)

### Common Mistakes

❌ **Wrong:** `postgresql://...` (uses psycopg2)
✅ **Correct:** `postgresql+psycopg://...` (uses psycopg3)

❌ **Wrong:** `ep-snowy-smoke-aj2dycz7.us-east-2.aws.neon.tech` (direct connection)
✅ **Correct:** `ep-snowy-smoke-aj2dycz7-pooler.us-east-2.aws.neon.tech` (pooler)

❌ **Wrong:** Only `?sslmode=require`
✅ **Correct:** `?sslmode=require&options=endpoint%3Dep-snowy-smoke-aj2dycz7-pooler`

---

## 📝 Step-by-Step Instructions

1. **Open Neon Dashboard**
   - Go to https://console.neon.tech
   - Select your project: `snowy-smoke-aj2dycz7`
   - Click "Connection Details"

2. **Copy Connection String**
   - Select "Pooled connection"
   - Connection string format: SQL Alchemy
   - Change driver from `psycopg2` to `psycopg`
   - Copy the string

3. **Modify Connection String**
   - Add `&options=endpoint%3D<your-endpoint>-pooler` at the end
   - Example:
   ```
   postgresql+psycopg://neondb_owner:npg_abc123@ep-snowy-smoke-aj2dycz7-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require&options=endpoint%3Dep-snowy-smoke-aj2dycz7-pooler
   ```

4. **Update Railway**
   - Go to Railway dashboard
   - Your Service → Settings → Variables
   - Find `DATABASE_URL`
   - Paste the modified connection string
   - Click "Update" (Railway will auto-restart)

5. **Verify Deployment**
   - Check Deploy Logs
   - Look for: `✓ Database initialization successful`
   - No more IPv6 errors!

---

## 🚨 Still Not Working?

### Option A: Use Railway's Built-in PostgreSQL

Instead of Neon, use Railway's native PostgreSQL:

1. Railway Dashboard → Your Project → "New" → "Database" → "PostgreSQL"
2. Railway automatically sets `DATABASE_URL` for you
3. Much simpler, no IPv6 issues!

**Pros:** Seamless integration, same network
**Cons:** Not free tier like Neon

### Option B: Use a Different External Database

Consider these alternatives:
- **Supabase** (PostgreSQL, free tier, better Railway compatibility)
- **ElephantSQL** (PostgreSQL as a service)
- **Railway PostgreSQL** (native, recommended)

---

## 📚 References

- [Neon Connection Pooling](https://neon.tech/docs/connect/connection-pooling)
- [Railway IPv4/IPv6 Support](https://docs.railway.app/reference/networking)
- [SQLAlchemy Connection Args](https://docs.sqlalchemy.org/en/20/core/engines.html)

---

## ✅ Success Criteria

After applying the fix, you should see:

```
✓ Database initialization successful
✓ Tables created
✓ Basic integrity check passed
```

And your API endpoints should work:
- `/health` → 200 OK
- `/status` → Shows database connected
- `/ask?q=test` → Returns results (after ingestion)

---

**Next Step:** Once connected, run initial data ingestion:
```bash
railway run bash
python scripts/ingest_all_episodes.py
```
