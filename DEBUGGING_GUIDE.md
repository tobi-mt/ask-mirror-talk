# 🔍 DEBUGGING: "The string did not match the expected pattern"

## Issue Analysis

This error suggests the JavaScript is getting an unexpected response format. Let's debug step by step.

---

## ✅ Step 1: Verify Files Are Uploaded Correctly

Check that you uploaded these 3 files to `/wp-content/themes/astra/`:

1. ✅ `ask-mirror-talk-standalone.php` (NOT ask-mirror-talk.php, NOT ask-mirror-talk-v2.php)
2. ✅ `ask-mirror-talk.js` (the updated version with debugging)
3. ✅ `ask-mirror-talk.css`

---

## ✅ Step 2: Update functions.php

**CRITICAL:** Your `functions.php` MUST reference the standalone file:

```php
/**
 * Ask Mirror Talk Widget Integration
 * Version: 2.0.0
 */
require_once ASTRA_THEME_DIR . 'ask-mirror-talk-standalone.php';
```

**NOT:**
```php
// ❌ WRONG - this is the old AJAX version
require_once ASTRA_THEME_DIR . 'ask-mirror-talk-v2.php';

// ❌ WRONG - this is the very old version
require_once ASTRA_THEME_DIR . 'ask-mirror-talk.php';
```

---

## ✅ Step 3: Clear All Caches

### Browser Cache
1. Hard refresh: **Cmd+Shift+R** (Mac) or **Ctrl+Shift+R** (Windows)
2. Or open in **Incognito/Private window**

### WordPress Cache (if using cache plugin)
1. WP Super Cache → Delete Cache
2. W3 Total Cache → Empty All Caches
3. Cloudflare → Purge Everything (if using Cloudflare)

---

## ✅ Step 4: Check Browser Console

1. Visit your page with the widget
2. Press **F12** or **Cmd+Option+I** (Mac)
3. Go to **Console** tab
4. You should see:

```
Ask Mirror Talk Widget v2.0.0 loaded
```

5. Submit a question
6. Look for debug output:

```
=== DEBUG INFO ===
API URL: https://ask-mirror-talk-production.up.railway.app/ask
WordPress Config: {apiUrl: "...", version: "2.0.0"}
Question: your question here
==================
Response status: 200
Raw response: {"question":"...","answer":"...
```

---

## ✅ Step 5: Check Network Tab

1. Stay in DevTools (F12)
2. Go to **Network** tab
3. Submit a question
4. Look for the request

### If calling WordPress AJAX (WRONG):
```
Request URL: https://yoursite.com/wp-admin/admin-ajax.php
```
**This means:** Old PHP file is still active! Check functions.php

### If calling Railway directly (CORRECT):
```
Request URL: https://ask-mirror-talk-production.up.railway.app/ask
Status: 200
```
**This is what you want!**

---

## 🐛 Common Problems & Solutions

### Problem 1: Still calling admin-ajax.php

**Cause:** Wrong PHP file loaded in functions.php

**Solution:**
```php
// Edit functions.php and change to:
require_once ASTRA_THEME_DIR . 'ask-mirror-talk-standalone.php';
```

Then clear caches and hard refresh!

---

### Problem 2: Console shows "WordPress Config: undefined"

**Cause:** Standalone PHP file not loaded

**Solution:**
1. Verify file uploaded: `/wp-content/themes/astra/ask-mirror-talk-standalone.php`
2. Check functions.php has correct require statement
3. Clear WordPress object cache if using Redis/Memcached

---

### Problem 3: CORS Error

**Console shows:**
```
Access to fetch at 'https://ask-mirror-talk-production...' has been blocked by CORS policy
```

**Solution:**
1. Go to Railway → Your Project → Variables
2. Check `ALLOWED_ORIGINS` includes your domain:
   ```
   https://mirrortalkpodcast.com,https://www.mirrortalkpodcast.com
   ```
3. No trailing slashes!
4. Restart Railway service

---

### Problem 4: "The string did not match the expected pattern"

**This error text suggests:**

1. **WordPress is intercepting the response**
   - Old AJAX handler still active
   - Check functions.php is loading standalone version

2. **JavaScript parsing issue**
   - Check Console for "Raw response" 
   - Should see valid JSON starting with `{"question":`
   - If you see HTML instead, wrong endpoint is being called

3. **Validation error from WordPress**
   - `sanitize_textarea_field()` rejecting input
   - But this shouldn't happen with standalone version!

---

## 🔧 Quick Fix: Manual Test

Add this **temporary** test directly in your page (not in widget):

```html
<script>
// TEMPORARY TEST - Remove after debugging
async function testAPI() {
    console.log('Testing direct API call...');
    try {
        const response = await fetch('https://ask-mirror-talk-production.up.railway.app/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({question: 'test'})
        });
        
        console.log('Status:', response.status);
        const data = await response.json();
        console.log('Success!', data);
        alert('API works! Check console for response.');
    } catch (error) {
        console.error('API test failed:', error);
        alert('API failed: ' + error.message);
    }
}

// Run test on page load
testAPI();
</script>
```

**If this works:** The API is fine, issue is in widget setup.
**If this fails:** CORS or API issue on Railway.

---

## 📋 Complete Checklist

Run through this checklist:

- [ ] Uploaded `ask-mirror-talk-standalone.php` to `/wp-content/themes/astra/`
- [ ] Uploaded updated `ask-mirror-talk.js` to `/wp-content/themes/astra/`
- [ ] Uploaded `ask-mirror-talk.css` to `/wp-content/themes/astra/`
- [ ] Updated `functions.php` to use `ask-mirror-talk-standalone.php`
- [ ] No leading slash in require path
- [ ] Cleared WordPress cache (if using cache plugin)
- [ ] Hard refreshed browser (Cmd+Shift+R)
- [ ] Opened browser console (F12)
- [ ] See "Widget v2.0.0 loaded" in console
- [ ] Submitted test question
- [ ] See "DEBUG INFO" in console with Railway URL
- [ ] Network tab shows call to Railway (not admin-ajax.php)
- [ ] Response status is 200
- [ ] Raw response is valid JSON

---

## 🆘 Still Not Working?

### Share This Debug Info:

When asking for help, share:

1. **Console output** when submitting question (copy ALL debug lines)
2. **Network tab** screenshot showing the request
3. **functions.php** last 5 lines (to verify require statement)
4. **WordPress theme** name and version

### Files to Double-Check:

```bash
# In your theme directory, you should see:
/wp-content/themes/astra/ask-mirror-talk-standalone.php ← NEW
/wp-content/themes/astra/ask-mirror-talk.js              ← UPDATED
/wp-content/themes/astra/ask-mirror-talk.css             ← SAME

# These are OLD, can delete:
/wp-content/themes/astra/ask-mirror-talk.php      ← OLD (WPGetAPI version)
/wp-content/themes/astra/ask-mirror-talk-v2.php   ← OLD (AJAX version)
```

---

## 🎯 Expected Working State

When everything is correct:

### Browser Console:
```
Ask Mirror Talk Widget v2.0.0 loaded
=== DEBUG INFO ===
API URL: https://ask-mirror-talk-production.up.railway.app/ask
WordPress Config: {apiUrl: "...", version: "2.0.0"}
==================
Response status: 200
Raw response: {"question":"test","answer":"Hey there!...
```

### Network Tab:
```
Status: 200 OK
Request URL: https://ask-mirror-talk-production.up.railway.app/ask
Request Method: POST
Content-Type: application/json
```

### Page:
- Warm, conversational answer (2-4 paragraphs)
- 6 unique episode citations
- Clickable timestamp links
- No errors!

---

**Try these steps and report back what you see in the console!** 🔍
