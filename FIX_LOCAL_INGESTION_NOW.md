# 🚀 Quick Fix for Local Ingestion

## The Problem
Your script was trying to connect to localhost database instead of your Neon production database.

## The Fix (2 Options)

### Option 1: Automatic (If you have Railway CLI)

```bash
# Run the helper script
./scripts/create_local_env.sh

# Then run ingestion
python scripts/ingest_all_episodes.py
```

### Option 2: Manual (Recommended)

1. **Create .env file:**
   ```bash
   touch .env
   ```

2. **Get your DATABASE_URL from Railway:**
   ```bash
   railway variables | grep DATABASE_URL
   ```

3. **Edit .env and paste:**
   ```bash
   DATABASE_URL=postgresql+psycopg://[your-actual-database-url]
   RSS_URL=https://mirrortalkpodcast.com/feed.xml
   OPENAI_API_KEY=sk-[your-actual-key]
   TRANSCRIPTION_PROVIDER=openai
   MAX_EPISODES_PER_RUN=1
   EMBEDDING_PROVIDER=sentence_transformers
   EMBEDDING_DIM=384
   ```

4. **Run ingestion:**
   ```bash
   python scripts/ingest_all_episodes.py
   ```

---

## What I Fixed

1. ✅ Script now loads `.env` file automatically
2. ✅ Validates required environment variables
3. ✅ Shows helpful error messages
4. ✅ Added duplicate code cleanup

---

## Files Changed

- `scripts/ingest_all_episodes.py` - Now loads .env and validates
- `scripts/create_local_env.sh` - Helper script to create .env from Railway
- `LOCAL_INGESTION_SETUP.md` - Comprehensive setup guide

---

## Next Steps

1. Create `.env` file (use one of the two options above)
2. Run: `python scripts/ingest_all_episodes.py`
3. Watch as it connects to your Neon database and ingests episodes!

---

## Quick Test

```bash
# Check if .env exists
ls -la .env

# Check if it has DATABASE_URL
grep DATABASE_URL .env

# Run the script
python scripts/ingest_all_episodes.py
```

Should now show:
```
✓ Loaded environment from: .env
============================================================
INGESTING ALL EPISODES FROM RSS
============================================================
RSS URL: https://mirrortalkpodcast.com/feed.xml
Database: postgresql+psycopg://...
```

---

**Bottom Line:** Create a `.env` file with your Neon DATABASE_URL, and the script will work! 🎉
