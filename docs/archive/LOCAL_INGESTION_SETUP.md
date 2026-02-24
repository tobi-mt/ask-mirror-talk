# 🔧 Local Ingestion Setup Guide

## Quick Setup (3 Steps)

### Step 1: Create .env File

Create a `.env` file in the project root with your Neon database credentials:

```bash
# Copy from .env.example
cp .env.example .env

# Then edit .env and add your actual credentials
```

### Step 2: Add Your Neon Database URL

Edit `.env` and set:

```bash
# Database - Use your Neon connection string
DATABASE_URL=postgresql+psycopg://[user]:[password]@[host]/neondb?sslmode=require

# Example:
# DATABASE_URL=postgresql+psycopg://user:pass@ep-snowy-smoke-aj2dycz7-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require

# RSS Feed
RSS_URL=https://mirrortalkpodcast.com/feed.xml

# OpenAI (for transcription and answers)
OPENAI_API_KEY=sk-your-key-here

# Transcription
TRANSCRIPTION_PROVIDER=openai

# Ingestion Settings
MAX_EPISODES_PER_RUN=1
EMBEDDING_PROVIDER=sentence_transformers
WHISPER_MODEL=tiny
```

### Step 3: Run Ingestion

```bash
python scripts/ingest_all_episodes.py
```

---

## Where to Find Your Neon Database URL

### Option 1: From Railway Environment Variables

```bash
# If you have Railway CLI installed
railway variables | grep DATABASE_URL

# Copy the value and paste into your local .env
```

### Option 2: From Neon Dashboard

1. Go to https://neon.tech
2. Select your project
3. Go to "Connection Details"
4. Copy the connection string
5. Change the format to: `postgresql+psycopg://...`

---

## Complete .env Template for Local Ingestion

Create `/Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk/.env`:

```bash
# Environment Configuration
APP_NAME="Ask Mirror Talk"
ENVIRONMENT=development

# Database - Get from Railway or Neon Dashboard
DATABASE_URL=postgresql+psycopg://your-user:your-password@your-host.neon.tech/neondb?sslmode=require

# RSS Feed
RSS_URL=https://mirrortalkpodcast.com/feed.xml
RSS_POLL_MINUTES=60

# OpenAI API Key - Get from https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your-actual-key-here

# Transcription
TRANSCRIPTION_PROVIDER=openai  # Use OpenAI for transcription

# Ingestion (Process one episode at a time)
MAX_EPISODES_PER_RUN=1

# Embeddings (for semantic search)
EMBEDDING_PROVIDER=sentence_transformers
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIM=384

# Answer Generation (for intelligent responses)
ANSWER_GENERATION_PROVIDER=openai
ANSWER_GENERATION_MODEL=gpt-3.5-turbo
ANSWER_MAX_TOKENS=500
ANSWER_TEMPERATURE=0.7

# Retrieval
TOP_K=6
MIN_SIMILARITY=0.15

# Chunking
MAX_CHUNK_CHARS=1400
MIN_CHUNK_CHARS=300

# API Rate Limiting
RATE_LIMIT_PER_MINUTE=10

# Admin Dashboard (not needed for local ingestion)
ADMIN_ENABLED=false
ADMIN_USER=admin
ADMIN_PASSWORD=change-me

# CORS (not needed for local ingestion)
ALLOWED_ORIGINS=https://mirrortalkpodcast.com,https://www.mirrortalkpodcast.com
```

---

## Troubleshooting

### Error: "RSS URL: Not set"

**Problem:** Environment variables not loading

**Solution:**
```bash
# Make sure .env file exists
ls -la .env

# Make sure it has the right content
cat .env | grep RSS_URL
```

### Error: "role 'mirror' does not exist"

**Problem:** Using default DATABASE_URL (localhost)

**Solution:** Set DATABASE_URL in .env to your Neon connection string

### Error: "No module named 'openai'"

**Problem:** Missing dependency

**Solution:**
```bash
pip install openai
# Or reinstall all dependencies
pip install -e .
```

### Error: "OPENAI_API_KEY not set"

**Problem:** Missing API key

**Solution:** Get your API key from https://platform.openai.com/api-keys and add to .env

---

## Running Specific Ingestion Scripts

### Ingest All Episodes
```bash
python scripts/ingest_all_episodes.py
```

### Ingest Single Episode
```bash
python scripts/ingest_single_episode.py <episode_number>
```

### Ingest Local Audio File
```bash
python scripts/ingest_local_file.py /path/to/audio.mp3
```

---

## Quick Command to Get Database URL from Railway

```bash
# If you have Railway CLI installed
railway variables | grep DATABASE_URL | cut -d'=' -f2-

# Then add to .env:
# DATABASE_URL=<paste the value here>
```

---

## Verify Setup

Before running ingestion, verify your setup:

```bash
# Check .env file exists
ls -la .env

# Check DATABASE_URL is set
grep DATABASE_URL .env

# Check RSS_URL is set
grep RSS_URL .env

# Check OPENAI_API_KEY is set
grep OPENAI_API_KEY .env
```

All three should show valid values!

---

## Summary

**The issue:** Script wasn't loading `.env` file, so it tried to use default localhost database

**The fix:** Script now:
1. ✅ Loads `.env` file automatically
2. ✅ Validates required variables
3. ✅ Shows helpful error messages
4. ✅ Uses your Neon production database

**Next step:** Create `.env` file with your Neon database URL and run the script!
