# 🔓 Enable External Database Access & Load Production Data

## Problem: External Database Blocked

Render blocks external database connections by default. You need to whitelist your IP address first.

---

## Step 1: Whitelist Your IP Address

### Your Current IP Addresses:
- **IPv4**: `93.209.254.38`
- **IPv6**: `2003:e2:2742:4b00:e072:2d62:106d:78d`

### Add to Render Whitelist:

1. Go to https://dashboard.render.com
2. Navigate to **`mirror-talk-db`** (your PostgreSQL database)
3. Click on **"Networking"** tab (or "Access Control")
4. Find the **"IP Allow List"** section
5. Click **"Add IP Address"**
6. Add both IPs:
   - `93.209.254.38/32` (IPv4)
   - `2003:e2:2742:4b00:e072:2d62:106d:78d/128` (IPv6)
7. Click **"Save"**

⏱️ **Wait 1-2 minutes** for the changes to apply.

---

## Step 2: Get External Database URL

After whitelisting, the **External Database URL** will be available:

1. In the same **`mirror-talk-db`** page
2. Scroll to **"Connection Info"**
3. Look for **"External Database URL"**
4. Click to reveal and copy

It should look like:
```
postgresql://mirror:fiSMfEyMNTDyMqQ0NVDBBq8g6eENdyEh@dpg-d649qai4d50c73e911i0-a.oregon-postgres.render.com/mirror_talk
```

---

## Step 3: Update Local .env File

Edit your `.env` file:

```bash
# Change this line:
DATABASE_URL=postgresql+psycopg://tobi@localhost:5432/mirror_talk

# To this (add +psycopg and use external URL):
DATABASE_URL=postgresql+psycopg://mirror:fiSMfEyMNTDyMqQ0NVDBBq8g6eENdyEh@dpg-d649qai4d50c73e911i0-a.oregon-postgres.render.com/mirror_talk
```

**Important**: Add `+psycopg` after `postgresql` for SQLAlchemy compatibility.

---

## Step 4: Test Connection

```bash
cd /Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk
python -c "from app.core.db import SessionLocal; db = SessionLocal(); print('✓ Connection successful!'); db.close()"
```

Should print: `✓ Connection successful!`

---

## Step 5: Run Production Ingestion

Now load episodes to the production database:

```bash
python scripts/bulk_ingest.py --max-episodes 5 --no-confirm
```

This will:
- Connect to Render's production database
- Process 5 new episodes
- Take ~15-25 minutes

⏱️ **Time**: ~3-5 minutes per episode

---

## Step 6: Verify Production API

```bash
curl https://ask-mirror-talk.onrender.com/status
```

Should show:
```json
{
  "status": "ok",
  "episodes": 5,
  "chunks": ~500,
  "ready": true
}
```

---

## Step 7: Test WordPress

Go to https://mirrortalkpodcast.com and ask:
- "What topics are discussed in the podcast?"
- "Who are the guests?"

Should get real answers! 🎉

---

## Security Notes

### Your IP Address May Change

If your internet connection resets or you use a different network:
1. Get new IP: `curl -s https://ifconfig.me`
2. Add new IP to Render whitelist
3. Remove old IP (optional)

### Alternative: Allow All IPs (Less Secure)

If your IP changes frequently, you can allow all IPs:

In Render → `mirror-talk-db` → Networking:
- Add `0.0.0.0/0` (allows all IPv4)
- **⚠️ Less secure** - only for development/testing

For production, always use IP whitelist.

---

## After Initial Load

### Revert .env to Local Database (Optional)

For future local development:

```bash
# Change back to:
DATABASE_URL=postgresql+psycopg://tobi@localhost:5432/mirror_talk
```

This keeps local and production data separate.

### Let Cron Job Handle Updates

The Render cron job runs **Wednesdays at 5 AM CET** and will:
- Check for new episodes
- Process up to 3 new episodes
- Update production automatically

No manual intervention needed! ✅

---

## Troubleshooting

### "Connection refused" or "Timeout"

1. **Check IP whitelist** - Make sure your IP is added correctly
2. **Wait 2 minutes** - Changes take time to propagate
3. **Check IP hasn't changed** - Run `curl -s https://ifconfig.me` again
4. **Try IPv4 only** - Remove IPv6 from whitelist and try again

### "Authentication failed"

1. **Check password** - Copy the exact password from Render
2. **Check username** - Should be `mirror` (not `tobi`)
3. **Add +psycopg** - Make sure URL has `postgresql+psycopg://`

### "Database does not exist"

1. **Check database name** - Should be `mirror_talk` (no underscore issues)
2. **Use External URL** - Not internal URL
3. **Copy full URL** - From Render dashboard (after whitelisting)

---

## Load More Episodes (Optional)

After initial 5 episodes work, you can load more:

```bash
# Load 20 episodes
python scripts/bulk_ingest.py --max-episodes 20 --no-confirm

# Or load ALL episodes (may take hours)
python scripts/bulk_ingest.py --no-confirm
```

Your Mac has plenty of resources for this! 💪

---

**Next Steps:**
1. ✅ Whitelist your IP: `93.209.254.38`
2. ✅ Get External Database URL from Render
3. ✅ Update .env with production URL
4. ✅ Run ingestion script
5. ✅ Test WordPress site

---

**Your IP**: `93.209.254.38` (IPv4) or `2003:e2:2742:4b00:e072:2d62:106d:78d` (IPv6)  
**Database**: `dpg-d649qai4d50c73e911i0-a.oregon-postgres.render.com`  
**Username**: `mirror`  
**Database Name**: `mirror_talk`
