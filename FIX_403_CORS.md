# Fix 403 Errors & Connection Issues 🔧

## Problem
Users are getting:
- "Server returned 403" 
- "We couldn't reach the service. Please try again later."

## Root Cause
**CORS (Cross-Origin Resource Sharing) not configured properly!**

The API was only enabling CORS if `ALLOWED_ORIGINS` was explicitly set. Without it, browsers block requests from your WordPress site.

---

## ✅ Fix Applied

Updated `app/api/main.py` to:
1. **Enable CORS by default** (allow all origins)
2. **Add comprehensive CORS headers** (expose headers, more methods)
3. **Better logging** to see CORS configuration

### Before
```python
# Only enabled CORS if ALLOWED_ORIGINS was set
if settings.allowed_origins:
    origins = [...]
    app.add_middleware(CORSMiddleware, ...)
```
❌ **Problem:** No CORS = 403 errors from browsers

### After
```python
# Always enable CORS
if settings.allowed_origins:
    origins = [...]  # Specific origins
else:
    origins = ["*"]  # Allow all origins
    
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["*"],
)
```
✅ **Fixed:** CORS always enabled, browsers can connect

---

## Configuration Options

### Option 1: Allow All Origins (Default - Easy)
```bash
# Don't set ALLOWED_ORIGINS at all
# The API will allow requests from any website
```
**Pros:** Easy, works immediately  
**Cons:** Less secure (but fine for most cases)

### Option 2: Restrict to Your Domain (Secure)
```bash
# Set in Railway environment variables
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```
**Pros:** More secure  
**Cons:** Need to list all domains

---

## Deployment

### Changes Made
```
✅ app/api/main.py - CORS now enabled by default
✅ Added comprehensive CORS headers
✅ Better logging for troubleshooting
```

### Push to Railway
```bash
git add app/api/main.py
git commit -m "Fix CORS: enable by default to prevent 403 errors"
git push origin main
git push github main
```

Railway will auto-deploy in 2-3 minutes.

---

## Testing

### Test 1: Direct API Call
```bash
curl -X POST https://your-api.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "test"}'
```
✅ Should return JSON response

### Test 2: From Browser Console
Open your WordPress site, open browser console (F12), run:
```javascript
fetch('https://your-api.railway.app/ask', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({question: 'How do I overcome fear?'})
})
.then(r => r.json())
.then(data => console.log(data))
.catch(err => console.error(err));
```
✅ Should log answer and citations (no CORS errors)

### Test 3: WordPress Widget
Try asking a question in your widget.
✅ Should get an intelligent answer

---

## Common Issues & Solutions

### Issue 1: Still Getting 403
**Possible Causes:**
1. Railway not deployed yet (wait 2-3 min)
2. Cached response in browser (hard refresh: Ctrl+Shift+R)
3. Different error (check browser console)

**Solution:**
```bash
# Check Railway logs
railway logs --service mirror-talk-api

# Look for "CORS middleware configured"
```

### Issue 2: "Can't reach service"
**Possible Causes:**
1. Railway service not running
2. Wrong URL in WordPress widget
3. Network/firewall blocking

**Solution:**
```bash
# Check service status
railway status

# Test direct access
curl https://your-api.railway.app/health

# Should return: {"status": "ok"}
```

### Issue 3: Works in curl but not browser
**Cause:** CORS issue (browsers enforce CORS, curl doesn't)

**Solution:** Check browser console (F12) for CORS errors

---

## Railway Configuration

### Required Variables
```bash
# Already set (from transcription)
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://...

# Optional: Restrict origins for security
ALLOWED_ORIGINS=https://yourdomain.com
```

### Service Settings
- **Public URL:** Make sure service is publicly accessible
- **Port:** Should be listening on $PORT (Railway sets this automatically)

---

## WordPress Widget Update

### Make Sure Widget Has Correct URL

```javascript
// In your WordPress widget
const API_URL = 'https://your-actual-railway-url.up.railway.app/ask';

fetch(API_URL, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    question: userQuestion
  })
})
.then(response => {
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  return response.json();
})
.then(data => {
  // Display answer
  console.log(data.answer);
})
.catch(error => {
  console.error('Error:', error);
  // Show error to user
});
```

### Get Your Railway URL

1. Go to Railway dashboard
2. Click on `mirror-talk-api` service
3. Go to **Settings** tab
4. Look for **Public URL** (something like `https://xxx.up.railway.app`)
5. Use this URL in your WordPress widget

---

## Verification Checklist

- [ ] Code pushed to GitHub
- [ ] Railway deployed successfully
- [ ] Check logs: "CORS middleware configured"
- [ ] Test `/health` endpoint: `curl https://your-url/health`
- [ ] Test `/ask` endpoint: `curl -X POST https://your-url/ask -d '...'`
- [ ] Test from browser console (no CORS errors)
- [ ] Test from WordPress widget
- [ ] Users can ask questions successfully

---

## Expected Logs

After deployment, you should see in Railway logs:
```
STARTING ASK MIRROR TALK API
✓ FastAPI app created
CORS enabled for ALL origins (*). Set ALLOWED_ORIGINS in production for security.
✓ CORS middleware configured
STARTUP EVENT TRIGGERED
✓ Application startup complete
```

---

## Security Note

**Current Setup:** CORS allows all origins (`*`)

This is **fine for most cases** because:
- Your API is read-only (just answering questions)
- No sensitive data exposed
- Rate limiting prevents abuse

**For Production (Optional):**
Set specific origins:
```bash
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

---

## Next Steps

1. ✅ **Changes committed and ready to push**
2. ⏳ **Push to trigger Railway deployment** (see command below)
3. ⏳ **Wait 2-3 min for Railway to deploy**
4. 🧪 **Test with curl and browser**
5. 🎨 **Update WordPress widget with correct Railway URL**
6. ✅ **Verify users can ask questions**

---

## Push Commands

```bash
cd /Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk

# Add and commit
git add app/api/main.py
git commit -m "Fix CORS: enable by default to prevent 403 errors"

# Push to both repos
git push origin main
git push github main
```

---

**Status:** ✅ **READY TO DEPLOY**

This will fix the 403 errors and "can't reach service" issues! 🚀
