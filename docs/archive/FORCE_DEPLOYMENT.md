# Force Railway API Deployment 🚀

## Issue
You've pushed code changes but users are still getting old-style answers. This means the **Railway API service hasn't deployed the new code**.

## Quick Fix: Force Deployment

### Option 1: Trigger via Empty Commit (Easiest)
```bash
cd /Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk

# Create empty commit to trigger deployment
git commit --allow-empty -m "Force Railway API redeploy"
git push origin main
git push github main
```

This forces Railway to rebuild and redeploy the API service.

---

### Option 2: Manual Trigger in Railway Dashboard

1. Go to https://railway.app
2. Select your project: **positive-clarity**
3. Click on **mirror-talk-api** service (NOT ingestion)
4. Click the **"Deploy"** tab
5. Find the latest deployment (commit 7476453)
6. Click **"Redeploy"** button

---

### Option 3: Check if API Service Exists

You might only have the ingestion service configured. Check:

1. Go to Railway dashboard
2. Look for **TWO services**:
   - `mirror-talk-api` (should use Dockerfile)
   - `mirror-talk-ingestion` (should use Dockerfile.worker)

**If you only see ONE service:**

You need to create a second service for the API!

#### Create API Service:
1. In Railway dashboard, click **"+ New Service"**
2. Select **"GitHub Repo"** 
3. Choose your `ask-mirror-talk` repository
4. **Service Name:** `mirror-talk-api`
5. **Settings:**
   - Dockerfile Path: `Dockerfile` (default)
   - Start Command: Leave default (it will use CMD from Dockerfile)
6. **Environment Variables:** Copy from ingestion service:
   - `OPENAI_API_KEY`
   - `DATABASE_URL`
   - `RSS_URL`
7. **Generate Domain:** Enable public networking

---

## How to Verify Deployment

### Check Logs
```bash
# Switch to API service
railway link
# Select: mirror-talk-api

# View logs
railway logs
```

Look for:
```
STARTING ASK MIRROR TALK API
✓ FastAPI app created
CORS enabled for ALL origins (*)
✓ CORS middleware configured
```

### Test API Directly
```bash
curl https://your-api-url.railway.app/health
```
Should return: `{"status": "ok"}`

### Test Intelligent Answers
```bash
curl -X POST https://your-api-url.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I overcome fear?"}'
```

**OLD response (without GPT):**
```json
{
  "answer": "Here are grounded reflections from Mirror Talk that speak to your question:\n\n1. Sometimes we need to face our fears..."
}
```

**NEW response (with GPT):**
```json
{
  "answer": "Overcoming fear and building confidence starts with understanding that fear is natural...\n\nKey insights from Mirror Talk:\n\n1. **Face Fears Gradually**: Take small steps..."
}
```

Look for:
- ✅ Multiple paragraphs
- ✅ Bold text markers `**text**`
- ✅ Structured format
- ✅ Direct answer to the question

---

## Troubleshooting

### Issue: Only see ingestion service in Railway
**Solution:** Create a separate API service (see Option 3 above)

### Issue: Logs show old code
**Solution:** Use Option 1 (empty commit) to force rebuild

### Issue: API service not starting
Check logs for errors:
```bash
railway logs --service mirror-talk-api
```

Common issues:
- Missing environment variables (OPENAI_API_KEY, DATABASE_URL)
- Port configuration (should use $PORT from Railway)
- Dockerfile errors

### Issue: Still getting old answers after deployment
1. **Clear browser cache** (hard refresh: Ctrl+Shift+R)
2. **Check API logs** to confirm GPT is being called
3. **Verify OPENAI_API_KEY** is set in API service

---

## Expected Behavior After Deployment

### In Railway Logs (API Service)
```
Generated intelligent answer using gpt-3.5-turbo (length: 423 chars)
```

### In API Response
You should see:
- Multi-paragraph structured text
- Bold text with `**text**` markers
- Clear sections and bullet points
- Direct, helpful answers

### In OpenAI Dashboard
Visit https://platform.openai.com/usage

You should see API calls increasing (one per question asked).

---

## Quick Test Script

Save as `test_api.sh`:

```bash
#!/bin/bash

API_URL="https://your-api-url.railway.app"

echo "Testing health endpoint..."
curl "$API_URL/health"
echo -e "\n"

echo "Testing intelligent answers..."
curl -X POST "$API_URL/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I build confidence?"}' | jq '.answer'
```

Run:
```bash
chmod +x test_api.sh
./test_api.sh
```

---

## Next Steps

1. ✅ **Force deployment** (use Option 1 - empty commit)
2. ⏳ **Wait 2-3 min** for Railway to rebuild
3. 🧪 **Test API** with curl
4. ✅ **Verify logs** show GPT calls
5. 🎉 **Test WordPress widget**

---

## Summary

The code changes are committed and pushed, but Railway might not have automatically deployed them. Use the **empty commit trick** to force a rebuild:

```bash
git commit --allow-empty -m "Force Railway API redeploy"
git push origin main
git push github main
```

Then wait 2-3 minutes and test!
