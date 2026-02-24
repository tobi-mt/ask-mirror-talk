# 🚀 Load Data to Production Database

## Quick Guide

### Step 1: Get Production Database URL

1. Go to https://dashboard.render.com
2. Click on **`mirror-talk-db`** (your PostgreSQL database)
3. Scroll down to **Connection Info**
4. Copy the **External Connection String**
   - Should look like: `postgresql://mirror:***@dpg-***-a.oregon-postgres.render.com/mirror_talk_***`

### Step 2: Update .env File

Edit `/Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk/.env`:

```bash
# Replace this line:
DATABASE_URL=postgresql+psycopg://tobi@localhost:5432/mirror_talk

# With the production URL (add +psycopg to dialect):
DATABASE_URL=postgresql+psycopg://mirror:PASSWORD@dpg-***-a.oregon-postgres.render.com/mirror_talk_***
```

**Important**: 
- Add `+psycopg` after `postgresql` (for SQLAlchemy compatibility)
- Use the exact connection string from Render

### Step 3: Run Ingestion to Production

```bash
cd /Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk
python scripts/bulk_ingest.py --max-episodes 5 --no-confirm
```

This will:
- Connect to Render's production database
- Process 5 episodes
- Take ~15-25 minutes

⏱️ **Time**: ~3-5 minutes per episode

### Step 4: Verify Production

```bash
curl https://ask-mirror-talk.onrender.com/status
```

Should show:
```json
{"status":"ok","episodes":5,"chunks":~500,"ready":true}
```

### Step 5: Test WordPress

Go to https://mirrortalkpodcast.com and ask questions - should get real answers!

---

## Alternative: Load All Episodes at Once

If you want to load many episodes quickly:

```bash
# Load 20 episodes (will take ~60-100 minutes)
python scripts/bulk_ingest.py --max-episodes 20 --no-confirm

# Or load ALL episodes (will take several hours)
python scripts/bulk_ingest.py --no-confirm
```

Your Mac has plenty of RAM, so no memory issues! 💪

---

## Why This Works Better

✅ **Your Mac**: Plenty of RAM, fast CPU, no memory limits  
✅ **Direct connection**: No Render shell timeouts  
✅ **Better embeddings**: Uses sentence-transformers (higher quality)  
✅ **One-time setup**: After this, cron job handles weekly updates  

---

## Security Note

**Don't commit the production DATABASE_URL to git!**

The `.env` file is already in `.gitignore`, so it won't be committed. Good! 🔒

---

## After Data Loads

1. **Revert .env** (optional): Change back to local database for future local testing
2. **Commit any code changes**: But NOT the .env file
3. **Let cron job handle updates**: Runs Wednesdays at 5 AM CET automatically

---

**Next**: Get the production database URL and update your `.env` file! ⚡
