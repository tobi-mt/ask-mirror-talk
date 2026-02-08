# 🔧 Manual Data Load via Web Service Shell

## Problem: Out of Pipeline Minutes

Render has limited your pipeline minutes, so we can't use the cron job approach.

**Solution**: Use the **web service shell** to run the ingestion script manually.

---

## Step-by-Step Guide

### 1. Wait for Web Service to Deploy

First, wait for the web service to finish deploying (commit 2a58e4e):

1. Go to https://dashboard.render.com
2. Find **`ask-mirror-talk`** web service
3. Wait for status to show **"Live"** (usually 2-3 minutes)

### 2. Open the Shell

1. In the `ask-mirror-talk` web service page
2. Click the **"Shell"** tab at the top
3. Wait for the terminal to load (shows a command prompt)

### 3. Run the Ingestion Command

Copy and paste this command into the shell:

```bash
python scripts/bulk_ingest.py --max-episodes 3 --no-confirm
```

Press Enter and wait.

⏱️ **Expected time**: 9-15 minutes (3-5 min per episode)

### 4. Watch the Progress

You should see output like:

```
==========================================
BULK INGESTION SCRIPT
==========================================
RSS Feed: https://anchor.fm/s/261b1464/podcast/rss
Max Episodes: 3
Whisper Model: base
Embedding Provider: local
==========================================
Fetching RSS feed...
Found 156 episodes in feed
Already ingested: 0 episodes
New episodes to process: 3

Starting ingestion...

Processing episode 1/3: [Episode Title]
Downloading audio...
✓ Audio downloaded
Transcribing with Whisper...
✓ Transcription complete
Chunking transcript...
✓ Created 50 chunks
Generating embeddings...
✓ Embeddings generated

Processing episode 2/3: ...
[continues...]

==========================================
✓ INGESTION COMPLETE
==========================================
Processed: 3 episodes
Skipped: 0 episodes
==========================================
Total chunks in database: 150

✓ Your website is ready to answer questions!
```

### 5. Verify Success

Test the status endpoint:

```bash
curl https://ask-mirror-talk.onrender.com/status
```

Should show:
```json
{
  "status": "ok",
  "episodes": 3,
  "chunks": 150,
  "ready": true
}
```

---

## If Memory Issues Occur

The web service might run out of memory during ingestion.

### Solution: Process One Episode at a Time

Instead of `--max-episodes 3`, run this command **3 times**:

```bash
python scripts/bulk_ingest.py --max-episodes 1 --no-confirm
```

Wait for each to complete before running the next.

---

## Alternative: Local Ingestion + Database Upload

If the web service shell doesn't work or keeps running out of memory, you can:

### 1. Run Locally with Remote Database

Get the database URL from Render:
1. Go to `mirror-talk-db` database in Render dashboard
2. Copy the **External Connection String**

Create a `.env` file locally:
```bash
DATABASE_URL="<paste-connection-string>"
RSS_URL="https://anchor.fm/s/261b1464/podcast/rss"
EMBEDDING_PROVIDER="local"
WHISPER_MODEL="base"
```

Run locally:
```bash
cd /Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk
python scripts/bulk_ingest.py --max-episodes 3
```

This will:
- Run on your Mac (plenty of RAM)
- Connect to Render's database remotely
- Upload data directly to production

---

## After Data is Loaded

### Test from WordPress

Go to https://mirrortalkpodcast.com and ask:
- "What topics are discussed in the podcast?"
- "Who are the guests?"
- "Tell me about episode 1"

Should get real answers with sources! 🎉

### Monitor Future Updates

The cron job is now set to run **Wednesdays at 5 AM CET**.

It will automatically:
- Check for new episodes
- Process up to 3 new episodes
- Update your WordPress site

No manual intervention needed after initial load!

---

## Troubleshooting

### "Module not found" errors in shell

The shell might not have all dependencies. Try:

```bash
pip install -e '.[transcription,embeddings]'
python scripts/bulk_ingest.py --max-episodes 3 --no-confirm
```

### Shell disconnects or times out

The shell might have a timeout. Use local ingestion method instead (see above).

### "Connection to database failed"

Check that the web service has the `DATABASE_URL` environment variable set correctly.

### Still getting OOM errors

Options:
1. Use `--max-episodes 1` (one at a time)
2. Use `WHISPER_MODEL=tiny` (edit env vars in Render)
3. Upgrade to Standard plan temporarily

---

## Cost Note: Pipeline Minutes

Render free tier has limited build minutes. To avoid hitting the limit:

- ✅ Cron schedule is back to weekly (minimal builds)
- ✅ Use shell or local ingestion for initial load (no new builds)
- ✅ Future updates only rebuild once per week

If you need more builds, consider:
- Upgrading to paid plan (more build minutes)
- Using Docker image caching
- Running ingestion locally when needed

---

**Next Step**: Open the web service shell and run the ingestion command! ⚡

**Deployment**: Commit 2a58e4e (web service should be deploying now)
