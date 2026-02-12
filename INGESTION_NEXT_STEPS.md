# 🚀 Data Ingestion - Now That Database Works!

## ✅ Database Connected Successfully!

Your Railway logs show:
```
✓ pgvector extension enabled
✓ Database tables created/verified
✓ Background database initialization complete
```

**Next:** Load your podcast episodes into the database.

---

## 📥 Method 1: Ingest via Railway Shell (Recommended)

### Step 1: Open Railway Shell

```bash
# If you have Railway CLI installed
railway run bash

# Or use the Railway Dashboard:
# Your Service → Settings → "Open Shell" button
```

### Step 2: Run Ingestion Script

```bash
# Inside Railway shell
python scripts/ingest_all_episodes.py
```

**What this does:**
- Fetches all episodes from your RSS feed
- Downloads and transcribes audio (using faster-whisper)
- Creates embeddings for semantic search
- Stores everything in your Neon database

**Expected time:** 5-15 minutes depending on number of episodes

---

## 📥 Method 2: GitHub Actions Automation (Ongoing Updates)

For automatic updates every 6 hours:

### Step 1: Add GitHub Secrets

Go to your GitHub repository → Settings → Secrets and Variables → Actions

Add these secrets:
- `DATABASE_URL` = Your full Neon connection string (the one that now works!)
- `RSS_URL` = `https://anchor.fm/s/261b1464/podcast/rss`

### Step 2: Workflow is Already Set Up

The workflow file `.github/workflows/update-episodes.yml` is already in your repo and will:
- Run every 6 hours automatically
- Check for new episodes
- Ingest only new ones (incremental updates)

---

## 📥 Method 3: Manual Script (From Your Local Machine)

If you prefer to run from your local machine:

### Step 1: Set Environment Variables

```bash
export DATABASE_URL="postgresql+psycopg://neondb_owner:npg_0l7bPAnmJYOH@ep-snowy-smoke-aj2dycz7-pooler.c-3.us-east-2.aws.neon.tech/neondb?sslmode=require&options=endpoint%3Dep-snowy-smoke-aj2dycz7-pooler"
export RSS_URL="https://anchor.fm/s/261b1464/podcast/rss"
```

### Step 2: Run Script Locally

```bash
cd /Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk
python scripts/ingest_all_episodes.py
```

---

## 🧪 Verify Ingestion Success

After ingestion completes, check your API:

### Test 1: Check Status

```bash
curl https://your-railway-app.railway.app/status
```

**Should return:**
```json
{
  "status": "healthy",
  "episodes": 50,  // or however many you have
  "chunks": 500,   // text chunks for search
  "database": "connected"
}
```

### Test 2: Try a Question

```bash
curl "https://your-railway-app.railway.app/ask?q=What+is+the+podcast+about?"
```

**Should return:**
```json
{
  "question": "What is the podcast about?",
  "answer": "...",
  "sources": [...]
}
```

---

## 📊 Expected Output During Ingestion

You'll see output like:
```
🎙️ Starting ingestion from RSS feed...
📡 Found 50 episodes in feed
⚠️  0 episodes already in database

Processing: Episode 1/50 - "Episode Title"
  ⬇️  Downloading audio...
  🎤 Transcribing with faster-whisper...
  🔢 Creating embeddings...
  💾 Saved to database
  ✅ Episode 1 complete (2m 30s)

Processing: Episode 2/50...
...
```

---

## ⏱️ How Long Will It Take?

**Estimate per episode:**
- Download: 10-30 seconds
- Transcription: 1-3 minutes (depending on episode length)
- Embedding: 10-20 seconds
- Total per episode: ~2-5 minutes

**For 50 episodes:** 2-4 hours total

**Tips:**
- Run in Railway shell (they have good resources)
- Or let GitHub Actions do it in the background
- The progress is logged, so you can close and check back later

---

## 🚨 Troubleshooting

### "ModuleNotFoundError" or Import Errors
```bash
# Make sure dependencies are installed
pip install -r requirements.txt
```

### "Out of Memory" Errors
- Use Railway shell (has more memory than local)
- Or adjust `WHISPER_MODEL=tiny` for faster/lighter processing
- Or process in smaller batches

### "RSS Feed Not Found"
- Verify RSS_URL is correct: `https://anchor.fm/s/261b1464/podcast/rss`
- Check the feed is publicly accessible

---

## ✅ Success Checklist

- [ ] Database connected (✅ Already done!)
- [ ] Run `ingest_all_episodes.py` via Railway shell
- [ ] Verify `/status` shows episode counts > 0
- [ ] Test `/ask` endpoint with a question
- [ ] Set up GitHub Actions secrets for auto-updates
- [ ] Update WordPress widget with Railway URL

---

## 🎯 Recommended: Start with Railway Shell

**Why:** 
- ✅ Direct access to your production environment
- ✅ Uses Railway's compute resources (not your local machine)
- ✅ Same environment as your running service
- ✅ No need to expose your DATABASE_URL locally

**Command:**
```bash
railway run bash
python scripts/ingest_all_episodes.py
```

---

**Ready?** Let's load that data! 🚀

See **INGESTION_COMPLETE_GUIDE.md** for more detailed troubleshooting.
