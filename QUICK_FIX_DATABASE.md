# 🔴 QUICK FIX: Database Connection Error

## The Problem
```
Network is unreachable - IPv6 connection failed
```

## The Solution (Copy & Paste)

### 1. Go to Railway Dashboard
- Your Service → Settings → Variables → DATABASE_URL

### 2. Replace with this EXACT string:

```
postgresql+psycopg://neondb_owner:npg_0l7bPAnmJYOH@ep-snowy-smoke-aj2dycz7-pooler.c-3.us-east-2.aws.neon.tech/neondb?sslmode=require&options=endpoint%3Dep-snowy-smoke-aj2dycz7-pooler
```

### 3. Save and Wait
- Railway will auto-restart (30-60 seconds)
- Check logs for: `✓ Database initialization successful`

---

## What Changed?

**Before (Broken):**
```
...?sslmode=require&channel_binding=require
```

**After (Fixed):**
```
...?sslmode=require&options=endpoint%3Dep-snowy-smoke-aj2dycz7-pooler
```

The `options=endpoint%3D...` parameter forces IPv4 routing, which Railway requires.

---

## Alternative (If Above Doesn't Work)

Try the simpler version:

```
postgresql+psycopg://neondb_owner:npg_0l7bPAnmJYOH@ep-snowy-smoke-aj2dycz7-pooler.c-3.us-east-2.aws.neon.tech/neondb?sslmode=require
```

---

## Verify It Worked

```bash
# Check status endpoint
curl https://your-app.railway.app/status

# Should return JSON with "database": "connected"
```

---

**Full documentation:** See `NEON_IPV6_FIX.md`
