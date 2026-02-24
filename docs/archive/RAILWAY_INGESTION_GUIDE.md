# 🚀 Railway Data Ingestion Guide

## ✅ Database Connected - Now Load Data!

Your database is connected successfully. Here are **3 easy ways** to ingest your podcast data.

---

## 🎯 **METHOD 1: Railway Dashboard (EASIEST - No CLI needed!)**

### Step 1: Open Railway Shell from Dashboard

1. Go to https://railway.app/dashboard
2. Click on your project
3. Click on your service (ask-mirror-talk)
4. Click the **"..."** menu (three dots) at top right
5. Select **"Shell"** or look for terminal icon
6. A web-based terminal will open

### Step 2: Run Ingestion in the Web Terminal

```bash
python scripts/ingest_all_episodes.py
```

**That's it!** The ingestion will run in Railway's environment with full resources.

---

## 🖥️ **METHOD 2: Railway CLI (If you want local control)**

### Step 1: Login to Railway CLI

```bash
railway login --browserless
```

This will give you a URL - open it in your browser to authenticate, then paste the token back.

### Step 2: Link to Your Project

```bash
railway link
```

Select your project from the list.

### Step 3: Run Ingestion via CLI

```bash
railway run python scripts/ingest_all_episodes.py
```

Or open a shell:
```bash
railway run bash
# Then inside the shell:
python scripts/ingest_all_episodes.py
```

---

## 💻 **METHOD 3: Run Locally (Uses your machine)**

### Step 1: Set Environment Variables

```bash
export DATABASE_URL="postgresql+psycopg://neondb_owner:npg_0l7bPAnmJYOH@ep-snowy-smoke-aj2dycz7-pooler.c-3.us-east-2.aws.neon.tech/neondb?sslmode=require&options=endpoint%3Dep-snowy-smoke-aj2dycz7-pooler"
export RSS_URL="https://anchor.fm/s/261b1464/podcast/rss"
```

### Step 2: Install Dependencies (if not already done)

```bash
cd /Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk
pip install -r requirements.txt
```

### Step 3: Run Ingestion

```bash
python scripts/ingest_all_episodes.py
```

---

## ⏱️ **What to Expect During Ingestion**

### Console Output

```
🎙️ Starting ingestion from RSS feed...
📡 RSS Feed: https://anchor.fm/s/261b1464/podcast/rss
📡 Found 50 episodes in feed
⚠️  0 episodes already in database

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Processing: Episode 1/50
Title: "Your Episode Title"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ⬇️  Downloading audio... (15.2 MB)
  🎤 Transcribing with faster-whisper (model: base)...
  📝 Transcript: 15,234 characters
  🔢 Creating embeddings... (125 chunks)
  💾 Saving to database...
  ✅ Episode 1 complete (2m 15s)

Processing: Episode 2/50...
...
```

### Timing Per Episode
- Download: 10-30 seconds
- Transcription: 1-5 minutes (depends on length)
- Embeddings: 10-30 seconds
- **Total per episode:** ~2-5 minutes

### For 50 Episodes
- **Estimated total time:** 2-4 hours
- **Good news:** You can close your terminal and check back later!

---

## 📊 **Verify Ingestion Success**

### Test 1: Check Status Endpoint

```bash
curl https://ask-mirror-talk-production.up.railway.app/status
```

**Should return:**
```json
{
  "status": "healthy",
  "episodes": 50,
  "chunks": 5000,
  "database": "connected"
}
```

### Test 2: Ask a Question

```bash
curl "https://ask-mirror-talk-production.up.railway.app/ask?q=What+is+this+podcast+about"
```

**Should return:**
```json
{
  "question": "What is this podcast about",
  "answer": "Mirror Talk is a podcast about...",
  "sources": [
    {
      "episode_title": "...",
      "audio_url": "..."
    }
  ],
  "processing_time": 1.23
}
```

---

## 🚨 **Troubleshooting**

### "ModuleNotFoundError: No module named 'app'"

**Solution:** Make sure you're in the right directory:
```bash
cd /Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk
python scripts/ingest_all_episodes.py
```

### "command not found: python"

**Solution:** Use `python3` instead:
```bash
python3 scripts/ingest_all_episodes.py
```

### "Connection refused" or Database Errors

**Solution:** Verify DATABASE_URL is correct:
```bash
echo $DATABASE_URL
# Should show: postgresql+psycopg://neondb_owner:npg_...
```

### Process Takes Too Long / Timeout

**Solution:** Use Railway Dashboard shell (METHOD 1) - it has better resources and won't timeout.

### "Out of Memory" Errors

**Solution:** Adjust WHISPER_MODEL to use a smaller model:
```bash
export WHISPER_MODEL=tiny  # Faster, uses less RAM
python scripts/ingest_all_episodes.py
```

---

## ✅ **Recommended Approach**

**Best Method:** Use Railway Dashboard Shell (METHOD 1)

**Why?**
- ✅ No CLI setup needed
- ✅ Runs in Railway's environment (better resources)
- ✅ Won't timeout like local machines
- ✅ Can close browser and check back later
- ✅ Same environment as production

**Steps:**
1. Railway Dashboard → Your Service → "..." → "Shell"
2. `python scripts/ingest_all_episodes.py`
3. Wait (or check back in a few hours)
4. Verify with `/status` endpoint

---

## 🔄 **Setting Up Automatic Updates (After Initial Load)**

Once you've done the initial ingestion, set up GitHub Actions for automatic updates:

### Add GitHub Secrets

Repository → Settings → Secrets and Variables → Actions

Add:
- `DATABASE_URL` = Your full connection string
- `RSS_URL` = `https://anchor.fm/s/261b1464/podcast/rss`

The workflow will:
- Run every 6 hours
- Check for new episodes
- Ingest only new ones (incremental)
- No manual work needed!

---

## 📝 **Quick Command Reference**

```bash
# METHOD 1: Railway Dashboard
# Just open Railway Dashboard → Service → Shell → Run command

# METHOD 2: Railway CLI
railway login --browserless
railway link
railway run python scripts/ingest_all_episodes.py

# METHOD 3: Local
export DATABASE_URL="postgresql+psycopg://neondb_owner:npg_0l7bPAnmJYOH@ep-snowy-smoke-aj2dycz7-pooler.c-3.us-east-2.aws.neon.tech/neondb?sslmode=require&options=endpoint%3Dep-snowy-smoke-aj2dycz7-pooler"
export RSS_URL="https://anchor.fm/s/261b1464/podcast/rss"
python scripts/ingest_all_episodes.py

# Verify success
curl https://ask-mirror-talk-production.up.railway.app/status
```

---

**Start with METHOD 1 (Railway Dashboard Shell) - it's the easiest!** 🎯
