# 🍎 Local Setup Guide (No Docker)

## Perfect! Let's run everything locally on your Mac

Since you don't have Docker, we'll set up everything natively on macOS. This is actually **simpler** and **faster** for development!

---

## 🚀 One-Command Setup (Easiest)

```bash
./scripts/setup_local.sh
```

This will automatically:
1. ✅ Check Python is installed
2. ✅ Install PostgreSQL if needed (via Homebrew)
3. ✅ Create virtual environment
4. ✅ Install all dependencies
5. ✅ Setup database
6. ✅ Run ingestion
7. ✅ Start API server

**Time**: 20-30 minutes total (including ingestion)

---

## 📋 Prerequisites

You need these installed (script will help with most):

### Required:
- **Python 3.10+** - [Download](https://www.python.org/downloads/)
- **Homebrew** - [Install](https://brew.sh/)

### The script will install:
- PostgreSQL (via Homebrew)
- Python packages
- FFmpeg (for audio processing)

---

## 🔧 Manual Setup (If You Prefer)

### Step 1: Install Prerequisites

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install PostgreSQL
brew install postgresql@16 pgvector ffmpeg

# Start PostgreSQL
brew services start postgresql@16
```

### Step 2: Setup Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -e ".[transcription,embeddings]"
```

### Step 3: Configure Database

```bash
# Create database and user
psql postgres -c "CREATE USER mirror WITH PASSWORD 'mirror';"
psql postgres -c "CREATE DATABASE mirror_talk OWNER mirror;"
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE mirror_talk TO mirror;"

# Install pgvector extension
psql postgres -d mirror_talk -c "CREATE EXTENSION vector;"
```

### Step 4: Create Configuration

```bash
# Create .env file
cat > .env << 'EOF'
RSS_URL=https://anchor.fm/s/261b1464/podcast/rss
DATABASE_URL=postgresql+psycopg://mirror:mirror@localhost:5432/mirror_talk
EMBEDDING_PROVIDER=sentence_transformers
WHISPER_MODEL=base
MAX_EPISODES_PER_RUN=10
ADMIN_ENABLED=true
ADMIN_USER=admin
ADMIN_PASSWORD=change-me-please
EOF

# Create data directories
mkdir -p data/audio data/transcripts
```

### Step 5: Initialize Database

```bash
source venv/bin/activate
python3 -c "from app.core.db import init_db; init_db()"
```

### Step 6: Run Ingestion

```bash
# Quick test (5 episodes)
python3 scripts/bulk_ingest.py --max-episodes 5

# Or all episodes
python3 scripts/bulk_ingest.py
```

### Step 7: Start API Server

```bash
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --workers 1
```

---

## 🎯 Quick Start Commands

```bash
# ONE COMMAND - Does everything!
./scripts/setup_local.sh

# Then choose option 1 (5 episodes)
# Wait 15-25 minutes
# Done! ✅
```

---

## ✅ Verify It's Working

### Check API Status
```bash
curl http://localhost:8000/health
# Should return: {"status":"ok"}

curl http://localhost:8000/status | jq
# Should show episodes and chunks
```

### Test a Question
```bash
curl -X POST http://localhost:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question": "What is the PACT method?"}' | jq
```

### Check Database
```bash
psql -U mirror -d mirror_talk -c "SELECT COUNT(*) FROM episodes;"
psql -U mirror -d mirror_talk -c "SELECT COUNT(*) FROM chunks;"
```

---

## 🔄 Daily Usage

### Start Everything
```bash
# Activate virtual environment
source venv/bin/activate

# Start PostgreSQL (if not running)
brew services start postgresql@16

# Start API server
uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

### Ingest New Episodes
```bash
source venv/bin/activate
python3 scripts/bulk_ingest.py --max-episodes 5
```

### Stop Everything
```bash
# Stop API: Ctrl+C in terminal

# Stop PostgreSQL (optional)
brew services stop postgresql@16
```

---

## 📊 Performance Expectations

Local setup is **just as fast** as Docker!

| Episodes | Time | Memory |
|----------|------|--------|
| 5 | 15-25 min | ~500MB |
| 10 | 30-50 min | ~500MB |
| 20 | 1-2 hours | ~500MB |

---

## 🐛 Troubleshooting

### "psql: command not found"
```bash
brew install postgresql@16
```

### "Permission denied on PostgreSQL"
```bash
# Run as your user (not 'mirror')
psql postgres -c "CREATE EXTENSION vector;" -d mirror_talk
```

### "ModuleNotFoundError"
```bash
source venv/bin/activate
pip install -e ".[transcription,embeddings]"
```

### "Port 8000 already in use"
```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn app.api.main:app --port 8001
```

### Check PostgreSQL is running
```bash
brew services list | grep postgresql
# Should show "started"

# If not:
brew services start postgresql@16
```

---

## 💡 Advantages of Local Setup

✅ **No Docker overhead** - Uses less memory  
✅ **Faster startup** - No container initialization  
✅ **Easier debugging** - Direct access to logs  
✅ **Native performance** - Full CPU/GPU access  
✅ **Simple deployment** - Just activate venv and run  

---

## 🎬 Let's Get Started!

Run this now:

```bash
./scripts/setup_local.sh
```

Choose option 1 (5 episodes), and in 20-30 minutes you'll have:
- ✅ PostgreSQL database with your podcast episodes
- ✅ API server running on http://localhost:8000
- ✅ Admin dashboard at http://localhost:8000/admin
- ✅ Ready to answer questions about Mirror Talk!

---

## 🌟 Pro Tips

1. **Keep PostgreSQL running** - Set it to start at login:
   ```bash
   brew services start postgresql@16
   ```

2. **Use a terminal multiplexer** - Run API in background:
   ```bash
   brew install tmux
   tmux new -s mirrortalk
   # Run your server here
   # Detach: Ctrl+B, then D
   ```

3. **Auto-activate venv** - Add to your `~/.zshrc`:
   ```bash
   alias mirror='cd ~/PycharmProjects/pythonProject/ask-mirror-talk && source venv/bin/activate'
   ```

4. **Monitor logs** - Use Python's logging:
   ```bash
   uvicorn app.api.main:app --log-level info
   ```

---

## 📞 Ready?

```bash
cd /Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk
./scripts/setup_local.sh
```

You're 20-30 minutes away from having your Ask Mirror Talk service running! 🚀

No Docker needed! 🎉
