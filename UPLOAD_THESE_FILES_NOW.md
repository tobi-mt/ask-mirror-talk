# 🔧 WORDPRESS INTEGRATION FIX - READY TO UPLOAD

## ⚠️ Problem Identified

**Error:** "The string did not match the expected pattern"

**Root Cause:** Mismatch between HTML (direct API call) and PHP (expects WordPress AJAX)

---

## ✅ SOLUTION: Use Standalone Version (Simpler)

### Files to Upload (3 files):

1. **`ask-mirror-talk-standalone.php`** → Upload to `/wp-content/themes/astra/`
2. **`ask-mirror-talk.js`** → Upload to `/wp-content/themes/astra/`
3. **`ask-mirror-talk.css`** → Upload to `/wp-content/themes/astra/`

---

## 📝 Update functions.php

Replace or add this at the end:

```php
/**
 * Ask Mirror Talk Widget Integration
 * Version: 2.0.0
 */
require_once ASTRA_THEME_DIR . 'ask-mirror-talk-standalone.php';
```

**Note:** Remove the leading slash before the filename!

---

## 🚀 What Changed

### ✅ Fixed PHP File
- Now uses `ask-mirror-talk-standalone.php`
- Passes API URL via `wp_localize_script()` 
- No AJAX handler needed (simpler!)
- Version 2.0.0 on all assets

### ✅ Updated JavaScript  
- Now reads API URL from WordPress config
- Falls back to window variable if needed
- Adds console logging for debugging
- Compatible with both approaches

### ✅ Same CSS
- No changes needed
- Version 2.0.0

---

## 📋 Installation Steps

### 1. Upload Files via FTP/cPanel

Upload these 3 files to `/wp-content/themes/astra/`:
```
ask-mirror-talk-standalone.php
ask-mirror-talk.js
ask-mirror-talk.css
```

### 2. Edit functions.php

Add at the very end (remove old version if present):
```php
/**
 * Ask Mirror Talk Widget Integration
 * Version: 2.0.0
 */
require_once ASTRA_THEME_DIR . 'ask-mirror-talk-standalone.php';
```

### 3. Add Shortcode

Edit any page and add:
```
[ask_mirror_talk]
```

### 4. Test

1. Visit the page
2. Open browser DevTools (F12)
3. Check Console:
   - Should see: "Ask Mirror Talk Widget v2.0.0 loaded"
   - When submitting: "Calling API: https://ask-mirror-talk..."
4. Submit a test question
5. Should get a warm, conversational response with citations

---

## 🧪 Verification Checklist

- [ ] Files uploaded to `/wp-content/themes/astra/`
- [ ] functions.php updated with correct require statement
- [ ] No leading slash in require path
- [ ] Shortcode added to a page
- [ ] Page loads without PHP errors
- [ ] Console shows "Widget v2.0.0 loaded"
- [ ] Console shows "Calling API: https://ask-mirror-talk-production..."
- [ ] Question submits successfully
- [ ] Response appears (2-4 paragraphs)
- [ ] Citations show with unique episodes
- [ ] Timestamp links work
- [ ] No error messages

---

## 🐛 Troubleshooting

### Widget doesn't appear
```php
// Add to functions.php temporarily to debug
add_action('wp_footer', function() {
    echo '<!-- ASTRA_THEME_DIR: ' . ASTRA_THEME_DIR . ' -->';
    echo '<!-- File exists: ' . (file_exists(ASTRA_THEME_DIR . 'ask-mirror-talk-standalone.php') ? 'YES' : 'NO') . ' -->';
});
```

### "The string did not match..." error
- Old PHP file still active
- Clear WordPress cache
- Make sure using `ask-mirror-talk-standalone.php`, not `-v2.php`

### CORS errors
- Check Railway `ALLOWED_ORIGINS` includes your domain
- Format: `https://mirrortalkpodcast.com,https://www.mirrortalkpodcast.com`
- Restart Railway service after changing

### API not responding
```bash
# Test API directly
curl -X POST https://ask-mirror-talk-production.up.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "test"}'
```

---

## 📊 What You Get

✅ **Simple Setup** - No WordPress AJAX complexity
✅ **Fast** - Direct API call, one less server hop  
✅ **Reliable** - No nonce/session issues  
✅ **Debuggable** - Console logs show what's happening  
✅ **Cache-Friendly** - Versioned assets (2.0.0)  
✅ **Modern** - Warm, intelligent AI responses  
✅ **Smart** - Deduplicated citations  
✅ **Accurate** - Working timestamp links  

---

## 🎯 Summary

**Old Issue:**
- HTML called Railway API directly
- PHP expected WordPress AJAX
- Nonce validation failed
- Error: "The string did not match the expected pattern"

**New Solution:**
- Standalone PHP file (no AJAX)
- JavaScript reads API URL from WordPress config
- Direct API calls (fast & simple)
- Everything works! ✅

---

**Ready to upload and test!** 🚀

If you encounter any issues, check the console logs first - they'll tell you exactly what's happening.
