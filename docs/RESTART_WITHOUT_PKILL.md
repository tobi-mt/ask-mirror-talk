# Restart Service Without pkill

## Problem
`pkill` command is not available in the Render shell environment.

## Alternative Methods to Restart the Service

### Method 1: Using `ps` and `kill` (Recommended)
```bash
# Find the uvicorn process
ps aux | grep uvicorn

# Look for a line like:
# root  1  ... python -m uvicorn app.api.main:app --host 0.0.0.0 --port 10000

# Kill the process by PID (usually PID 1 in Docker)
kill 1

# Or if there are multiple processes, kill them all:
ps aux | grep uvicorn | grep -v grep | awk '{print $2}' | xargs kill
```

### Method 2: Exit Shell and Use Render Dashboard
Since the bug fix is applied, you can simply:

1. **Exit the shell**: Type `exit` or close the terminal
2. **In Render Dashboard**: Go to your service → **Manual Deploy** → Click "Clear build cache & deploy"
   - This will restart the service with the fixed code
   - OR: Just click "Restart" if available (doesn't use build minutes)

### Method 3: Using `killall` (if available)
```bash
killall python
# or
killall uvicorn
```

### Method 4: Find and Kill by Process Tree
```bash
# Check process tree
ps auxf

# Kill the main process (usually PID 1)
kill -15 1  # SIGTERM (graceful)
# or
kill -9 1   # SIGKILL (force)
```

## Simplest Approach (No Shell Needed)

Since your bug fix is already applied in production via `sed`:

1. **Exit the Render shell** (type `exit`)
2. **In Render Dashboard**:
   - Go to your "ask-mirror-talk-api" service
   - Click the **"Manual Deploy"** dropdown
   - Select **"Deploy latest commit"** or just click **"Restart"**
   
This will restart the service with the fixed code WITHOUT using build minutes.

## Verify the Fix After Restart

```bash
# Test the /ask endpoint
curl -X POST https://ask-mirror-talk-api.onrender.com/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this podcast about?"}'
```

Expected: Should return a JSON response with answer and citations, no 500 error.

## Current Status
- ✅ Bug fix applied to production code via sed
- ⏳ Waiting for service restart
- 🔄 After restart: Test /ask endpoint and WordPress integration

## Next Steps
1. Exit shell
2. Restart service via Render Dashboard
3. Test /ask endpoint
4. Test WordPress integration
5. Monitor for any errors
