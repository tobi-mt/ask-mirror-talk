# ✅ EASIEST WAY: Use Railway Dashboard Shell

## Problem with Railway CLI
The Railway CLI runs locally which causes module import issues. 
**Solution: Use Railway's web-based shell instead!**

---

## 🎯 Step-by-Step Instructions

### 1. Open Railway Dashboard
Go to: https://railway.app/dashboard

### 2. Navigate to Your Service
- Click on project: **"positive-clarity"**
- Click on service: **"ask-mirror-talk"** (or "mirror-talk-ingestion")

### 3. Open Web Shell
Look for one of these options:
- Click **"..."** (three dots menu) at top right → Select **"Shell"**
- Or look for a terminal/console icon
- Or go to the **"Deployments"** tab → Latest deployment → **"View Logs"** → **"Shell"** tab

### 4. Run the Ingestion Command

In the web shell that opens, type:

```bash
python scripts/ingest_all_episodes.py
```

Or if that doesn't work:

```bash
python3 scripts/ingest_all_episodes.py
```

### 5. Wait and Monitor

The script will output:
```
🎙️ Starting ingestion from RSS feed...
📡 Found X episodes in feed
⚠️  0 episodes already in database

Processing: Episode 1/X
  ⬇️  Downloading audio...
  🎤 Transcribing...
  🔢 Creating embeddings...
  💾 Saved to database
  ✅ Episode 1 complete
```

---

## ⏱️ Expected Time

- **Per episode:** 2-5 minutes
- **Total (50 episodes):** 2-4 hours
- **Good news:** You can close the browser and check back later!

---

## 📊 Verify Success

After ingestion completes (or while it's running), check:

```bash
curl https://ask-mirror-talk-production.up.railway.app/status
```

Should show increasing episode/chunk counts.

---

## 🚨 Alternative: GitHub Actions (Background Ingestion)

If you don't want to wait and watch:

### 1. Add GitHub Secrets

Go to: https://github.com/YOUR_USERNAME/ask-mirror-talk/settings/secrets/actions

Add these secrets:
- **DATABASE_URL:**
  ```
  postgresql+psycopg://neondb_owner:npg_0l7bPAnmJYOH@ep-snowy-smoke-aj2dycz7-pooler.c-3.us-east-2.aws.neon.tech/neondb?sslmode=require&options=endpoint%3Dep-snowy-smoke-aj2dycz7-pooler
  ```

- **RSS_URL:**
  ```
  https://anchor.fm/s/261b1464/podcast/rss
  ```

### 2. Manually Trigger Workflow

- Go to Actions tab
- Find "Update Episodes" workflow
- Click "Run workflow" → "Run workflow"

GitHub will run the ingestion in the background for you!

---

## ✅ Summary

**Best Method:** Railway Dashboard Web Shell
- No CLI issues
- Runs in production environment
- Can close browser and check later
- Same environment as your deployed service

**Steps:**
1. Railway Dashboard → positive-clarity → ask-mirror-talk
2. Open Shell (three dots menu or terminal icon)
3. Run: `python scripts/ingest_all_episodes.py`
4. Wait or check back in a few hours
5. Verify: `curl https://your-app.railway.app/status`

---

**That's it!** The Railway web shell is the most reliable way. 🚀
