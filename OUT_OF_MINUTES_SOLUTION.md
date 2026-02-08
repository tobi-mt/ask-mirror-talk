# 🚨 Out of Pipeline Minutes - Alternative Solution

## Problem Summary

1. ❌ Render out of pipeline minutes - can't deploy config changes
2. ❌ Connection to production database unstable from local machine
3. ✅ Production has 3 episodes (240 chunks) but with wrong embeddings
4. ⚠️ Embeddings mismatch: Data has `sentence_transformers`, API uses `local`

---

## ✅ Best Solution: Wait & Use Render Shell

Since you're out of build minutes, the cleanest approach is:

### Option 1: Wait for Build Minutes to Reset

Render's free tier resets monthly. Once reset:
1. The pending deployment will complete automatically
2. API will use `sentence_transformers` (matching your data)
3. WordPress will work perfectly!

**When**: Check Render dashboard for when build minutes reset

---

### Option 2: Use Render Web Service Shell (Now)

Instead of fixing embeddings, just reload data using the shell:

#### Step 1: Open Shell
1. Go to: https://dashboard.render.com
2. Click **`ask-mirror-talk`** web service
3. Click **"Shell"** tab

#### Step 2: Clear Data
```bash
python -c "from app.core.db import SessionLocal; from sqlalchemy import text; db = SessionLocal(); db.execute(text('DELETE FROM chunks')); db.execute(text('DELETE FROM transcripts')); db.execute(text('DELETE FROM episodes')); db.commit(); print('✓ Cleared'); db.close()"
```

#### Step 3: Load Data with Correct Embeddings
```bash
# Production uses 'local' embeddings, so this will work:
python scripts/bulk_ingest.py --max-episodes 5 --no-confirm
```

This runs inside Render's network, so no IP/connection issues!

---

### Option 3: Upgrade Render Plan (Immediate Fix)

If you need this working NOW:

1. **Upgrade to paid plan** (gets more/unlimited build minutes)
2. **Pending deployment will complete** (uses `sentence_transformers`)
3. **WordPress works immediately!**

**Cost**: ~$7/month for web service builds

**How**: Render Dashboard → Settings → Upgrade Plan

---

## 🧪 Test Current State

Even with embedding mismatch, it might partially work. Let's test:

```bash
curl -X POST https://ask-mirror-talk.onrender.com/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Tell me about financial alignment"}'
```

If you get a real answer (not "I could not find..."), then **it's working well enough!**

The mismatch just means:
- ❌ Search quality is lower
- ❌ May not find the best matches
- ✅ But might still find *some* matches

---

## 📊 Current Status

| Item | Status | Notes |
|------|--------|-------|
| **Episodes in DB** | 3 | ✅ Data loaded |
| **Chunks in DB** | 240 | ✅ Searchable |
| **Data Embeddings** | sentence_transformers | High quality |
| **API Embeddings** | local | Low quality |
| **Match** | ❌ NO | Search may not work well |
| **Build Minutes** | 0 | ❌ Can't deploy fixes |
| **Workaround** | Use Shell | ✅ Available |

---

## 🎯 Recommended Action

**Best**: Use Render Web Service Shell (Option 2 above)
- No cost
- No build minutes needed
- Works immediately
- 15-25 minutes to reload 5 episodes

**Alternative**: Wait for build minutes to reset
- No action needed
- Pending deployment will fix everything
- Check Render dashboard for reset date

**Immediate**: Upgrade Render plan
- Costs money
- But fixes it right now
- Best for production use

---

## 📝 Files Updated

- ✅ `.env` - Changed to `EMBEDDING_PROVIDER=local`
- ✅ `scripts/clear_production.py` - Script to clear production data
- ⏳ `render.yaml` - Config change pending (needs build minutes)

---

**Next**: Choose one of the 3 options above and proceed! 🚀

**Quick Test**: Try the API anyway - it might work despite the mismatch!
