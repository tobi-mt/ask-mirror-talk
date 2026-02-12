# 🚀 Deploy Clickable Citations - Quick Guide

## What You're Deploying

✅ **Fixed:** Duplicate timestamps (4:42-4:42)  
✅ **Added:** Clickable podcast links that play at exact timestamps  
✅ **Enhanced:** Hover effects and visual feedback  

---

## Step 1: Railway API (Auto-Deploys)

Your API changes are already being deployed to Railway automatically!

**Check deployment status:**
1. Go to [Railway Dashboard](https://railway.app)
2. Click your project
3. Watch "Deployments" tab
4. Wait for green checkmark (2-3 minutes)

**Verify deployment:**
```bash
# Test the updated API
curl -X POST "https://ask-mirror-talk-production.up.railway.app/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this podcast about?"}'
```

**Check for new fields in response:**
```json
{
  "citations": [
    {
      "timestamp_start_seconds": 282,
      "timestamp_end_seconds": 315,
      "audio_url": "https://...",
      "episode_url": "https://...#t=282"
    }
  ]
}
```

---

## Step 2: WordPress Widget

Upload these 2 updated files to your WordPress site:

### Files to Upload:
```
wp-content/themes/astra-child/
├── ask-mirror-talk.js   (NEW: Timestamp parsing & clickable links)
└── ask-mirror-talk.css  (NEW: Hover effects)
```

### How to Upload:

#### Option A: WordPress Admin (Easiest)
1. Go to: `Appearance → Theme File Editor`
2. Select: "Astra Child" theme
3. Find: `ask-mirror-talk.js`
4. Copy content from `/Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk/wordpress/astra/ask-mirror-talk.js`
5. Paste and click "Update File"
6. Repeat for `ask-mirror-talk.css`

#### Option B: FTP/SFTP
1. Connect to your WordPress server
2. Navigate to `/wp-content/themes/astra-child/`
3. Upload the files (overwrite existing)

#### Option C: cPanel File Manager
1. Login to cPanel
2. File Manager → `public_html/wp-content/themes/astra-child/`
3. Upload the files

---

## Step 3: Clear Caches

### WordPress Cache
If using a caching plugin:
- **WP Super Cache:** `Settings → WP Super Cache → Delete Cache`
- **W3 Total Cache:** `Performance → Dashboard → Empty All Caches`
- **WP Rocket:** `Settings → Clear Cache`

### Browser Cache
- **Mac:** `Cmd + Shift + R`
- **Windows:** `Ctrl + Shift + R`
- **Or:** Open in Incognito/Private window

### CDN Cache (if using Cloudflare, etc.)
- Login to your CDN dashboard
- Find "Purge Cache" or "Clear Cache"
- Purge everything

---

## Step 4: Test

### 1. Test API First
```bash
curl -X POST "https://ask-mirror-talk-production.up.railway.app/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "test"}'
```

**Expected:** Response includes `audio_url` and `episode_url` in citations

### 2. Test WordPress Widget

Visit your page with the widget and:

1. **Ask a question:** Type and submit
2. **Check citations:**
   - Should show time ranges like "4:42 - 5:15" (not duplicates)
   - Should be clickable (cursor changes to pointer)
   - Should show 🎧 emoji
3. **Hover over citation:**
   - Timestamp badge should turn dark
   - Title should underline
4. **Click citation:**
   - Should open in new tab
   - Should load podcast episode
   - Should start playing at the correct timestamp

### 3. Mobile Test

Open on your phone and verify:
- Citations are tappable
- Links open in podcast app or browser
- Playback works

---

## Troubleshooting

### ❌ Citations Still Show Duplicate Times

**Check:**
```bash
# SSH into Railway or use web shell
railway run python -c "
from app.core.db import get_session_local
db = get_session_local()()
result = db.execute('SELECT start_time, end_time FROM chunks LIMIT 5').fetchall()
print(result)
"
```

**Fix:** If times are the same in database, re-run ingestion:
```bash
curl -X POST "https://ask-mirror-talk-production.up.railway.app/ingest"
```

### ❌ Citations Not Clickable

**Check browser console (F12):**
- Look for JavaScript errors
- Check if `episode_url` exists in API response

**Debug:**
```javascript
// In browser console after asking a question:
console.log('Last API response:', window.lastResponse);
```

**Fix:** Clear browser cache and reload

### ❌ Links Don't Work

**Check Network tab:**
- Open DevTools (F12)
- Go to Network tab
- Submit question
- Look at response for `ask_mirror_talk` request
- Verify `audio_url` exists

**Fix:** 
1. Ensure episodes have `audio_url` in database
2. Check Railway logs for ingestion errors

### ❌ Podcast Doesn't Start at Timestamp

**Cause:** Not all hosting platforms support `#t=` parameter

**Solutions:**
1. Check if your podcast host supports timestamp links
2. Consider embedding custom audio player
3. See `CLICKABLE_CITATIONS_UPDATE.md` for alternatives

---

## Verification Checklist

- [ ] Railway deployment complete (green checkmark)
- [ ] API returns new fields (`audio_url`, `episode_url`, `*_seconds`)
- [ ] WordPress files uploaded successfully
- [ ] All caches cleared
- [ ] Citations show correct time ranges (not duplicates)
- [ ] Citations are clickable with hover effect
- [ ] 🎧 emoji appears on clickable citations
- [ ] Clicking opens podcast in new tab
- [ ] Works on mobile devices

---

## Quick Reference

### Files Changed
```
Backend:  app/qa/answer.py (Railway auto-deploys)
Frontend: wordpress/astra/ask-mirror-talk.js
Frontend: wordpress/astra/ask-mirror-talk.css
```

### What Users See

**Before:**
```
• Episode Title (4:42 - 4:42) [not clickable]
```

**After:**
```
┌─────────────────────────────────┐
│ Episode Title        [🎧 4:42] │ ← Clickable!
└─────────────────────────────────┘
```

### Test URL
```
https://your-site.com/your-page-with-widget
```

---

## Next Steps After Deployment

1. **Monitor Usage**
   - Check Railway logs for API errors
   - Monitor WordPress for JavaScript errors
   - Track user engagement with citations

2. **Load More Episodes**
   - Currently only 3 episodes indexed
   - Run full ingestion to load all episodes
   - See: `RAILWAY_INGESTION_GUIDE.md`

3. **Gather Feedback**
   - Ask users if they clicked citations
   - Check if timestamps are accurate
   - Monitor bounce rate

4. **Future Enhancements**
   - Add embedded audio player
   - Show episode artwork
   - Create playlists from citations
   - See: `CLICKABLE_CITATIONS_UPDATE.md` Phase 2

---

## Support

**API Issues:**
- Check Railway logs: Dashboard → Deployments → View Logs
- Test direct: `curl ...` (see Step 4)

**WordPress Issues:**
- Check browser console (F12)
- Enable WordPress debug: `define('WP_DEBUG', true);`
- Check `/wp-content/debug.log`

**Both:**
- Review: `CLICKABLE_CITATIONS_UPDATE.md`
- Compare response format with expected structure

---

## Rollback (If Needed)

If something breaks:

1. **Revert Git Changes:**
```bash
cd /Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk
git revert HEAD
git push origin main
```

2. **Restore WordPress Files:**
- Use WordPress backup plugin
- Or manually replace with old versions

3. **Wait for Railway:**
- Railway will redeploy previous version
- Takes 2-3 minutes

---

**Estimated Deployment Time:** 5-10 minutes  
**Difficulty:** Easy (just upload 2 files)  
**Impact:** High (major UX improvement!)

---

*Ready to deploy? Start with Step 1! 🚀*
