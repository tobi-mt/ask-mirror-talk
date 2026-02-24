# API Troubleshooting: "Not Found" Error

## Issue
Curl to `/ask` endpoint returns "Not Found" instead of processing the request.

## Possible Causes

### 1. **Service Not Restarted** (Most Likely)
The bug fix was applied via `sed`, but the Python process hasn't reloaded the code yet.

**Solution:**
```bash
# In the Render shell, find and kill the process:
ps aux | grep python

# Kill the main process (usually PID 1)
kill 1

# Or use this one-liner:
kill $(ps aux | grep uvicorn | grep -v grep | head -1 | awk '{print $2}')
```

### 2. **Wrong Base URL**
Check if you're hitting the correct service URL.

**Solution:**
```bash
# First, verify the health endpoint:
curl https://ask-mirror-talk-api.onrender.com/health

# Then check status:
curl https://ask-mirror-talk-api.onrender.com/status

# Then try /ask:
curl -X POST https://ask-mirror-talk-api.onrender.com/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this podcast about?"}'
```

### 3. **Route Not Registered**
The FastAPI route exists but might not be registered properly.

**Verify from shell:**
```bash
# Check if the endpoint exists in the code:
grep -n "def ask" /app/app/api/main.py

# Check if uvicorn is running:
ps aux | grep uvicorn
```

## Step-by-Step Fix (Run in Render Shell)

```bash
# 1. Verify the fix was applied:
grep "episode_id" /app/app/qa/service.py

# 2. Check what's running:
ps aux

# 3. Find the Python/Uvicorn PID (usually 1):
ps aux | grep python

# 4. Kill it to restart:
kill 1

# 5. Wait 10-20 seconds for Render to auto-restart

# 6. Test the health endpoint first:
curl http://localhost:10000/health

# 7. Test the ask endpoint:
curl -X POST http://localhost:10000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "test"}'
```

## Alternative: Restart from Render Dashboard

1. **Exit the shell**: `exit`
2. **In Render Dashboard**:
   - Go to your service
   - Click **"Manual Deploy"** → **"Deploy latest commit"**
   - Or look for a **"Restart"** button
3. **Wait** for service to come back online (check logs)
4. **Test** from your local machine:
   ```bash
   curl https://ask-mirror-talk-api.onrender.com/health
   curl -X POST https://ask-mirror-talk-api.onrender.com/ask \
     -H "Content-Type: application/json" \
     -d '{"question": "What is this podcast about?"}'
   ```

## Quick Diagnostic Commands

```bash
# Are you in the right container?
hostname

# Is the app code there?
ls -la /app/app/api/main.py

# What's the fix status?
grep -A2 -B2 "episode_id" /app/app/qa/service.py

# What processes are running?
ps auxf

# Can you reach the app locally?
curl http://localhost:10000/health
```

## If Still Not Found

The issue might be:
- Service is down completely
- Wrong port in Dockerfile (should be ${PORT} or 10000)
- Render hasn't picked up the changes

**Check Render Logs:**
- Go to Render Dashboard → Your Service → Logs
- Look for startup messages or errors

## Expected Working Response

After restart, you should see:
```json
{
  "question": "What is this podcast about?",
  "answer": "...",
  "citations": [...],
  "latency_ms": 1234
}
```

## Current Status
- ✅ Bug fix applied via sed
- ⏳ Service needs restart
- ❓ Testing shows "Not Found"

## Action Required
**Kill the Python process** in the Render shell to force a restart, then retest.
