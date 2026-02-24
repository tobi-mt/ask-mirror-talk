# 🐛 Bug Fix - Ready to Deploy via Shell

## Problem Identified

The `/ask` endpoint is returning **500 Internal Server Error** due to a KeyError bug:

```python
# WRONG (line 41 in service.py):
episode_ids=[e["id"] for e in response["citations"]]

# CORRECT:
episode_ids=[c["episode_id"] for c in response["citations"]]
```

The citations use `episode_id`, not `id`.

---

## ✅ Solution: Fix via Render Shell

Since you're out of build minutes, fix this directly in production:

### Step 1: Open Render Shell
1. Go to: https://dashboard.render.com
2. Click **`ask-mirror-talk`** web service
3. Click **"Shell"** tab

### Step 2: Apply the Fix

```bash
# Edit the file directly
sed -i 's/episode_ids=\[e\["id"\] for e in response\["citations"\]\]/episode_ids=[c["episode_id"] for c in response["citations"]]/' /app/app/qa/service.py

# Restart the service
pkill -f uvicorn
```

The service will automatically restart and pick up the fix!

---

## Alternative: Git Fix (When Build Minutes Available)

The fix is already committed locally (commit c72da1f). When you have build minutes:

```bash
git push origin main
```

This will deploy the fix automatically.

---

## ⏱️ Immediate Fix (Shell Method)

**Time**: ~2 minutes
**Steps**:
1. Open shell
2. Run sed command
3. Restart service
4. Test immediately

---

## 🧪 Test After Fix

```bash
curl -X POST https://ask-mirror-talk.onrender.com/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What topics are discussed?"}'
```

Should return real answers (not 500 error)!

---

## 📊 Current Status

| Item | Status | Notes |
|------|--------|-------|
| **Bug Identified** | ✅ YES | KeyError: 'id' in citations |
| **Fix Created** | ✅ YES | Changed to 'episode_id' |
| **Fix Committed** | ✅ YES | Commit c72da1f |
| **Fix Deployed** | ❌ NO | Need build minutes OR shell fix |
| **Workaround** | ✅ YES | Use Render shell |

---

## Why This Happened

The `compose_answer` function in `answer.py` returns citations with this structure:

```python
{
    "episode_id": episode["id"],  # ← Uses 'episode_id'
    "episode_title": episode["title"],
    ...
}
```

But `service.py` was trying to access `e["id"]` instead of `e["episode_id"]`.

---

## 🎯 Next Action

**Use Render Shell to fix immediately:**
1. Open shell
2. Run the sed command
3. Kill uvicorn process
4. Service restarts automatically
5. Test /ask endpoint
6. ✅ WordPress works!

This is the **fastest path** to getting your WordPress site working!

---

**Fix Ready**: Commit c72da1f (local)  
**Deploy Method**: Render Shell (immediate) or Git push (when build minutes available)  
**Expected Result**: /ask endpoint works, WordPress gets real answers! 🎉
