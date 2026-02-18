# 🔥 URGENT: Browser Cache Issue - Force Reload

## The Problem

Your browser console shows:
```
Ask Mirror Talk Widget v2.0.0 loaded
```

But **NO debug output** when you submit! This means:

**Your browser is using an OLD CACHED version of the JavaScript!**

---

## ✅ Solution: Force Clear Cache

### Method 1: Hard Refresh (Try This First)

1. **Close ALL browser tabs** with your website
2. **Clear browser cache:**
   - **Chrome/Edge:** Cmd+Shift+Delete (Mac) or Ctrl+Shift+H (Windows)
   - **Safari:** Cmd+Option+E (Mac)
3. Select "All Time" or "Everything"
4. Check "Cached Images and Files"
5. Click "Clear Data"
6. **Restart browser completely**
7. Open site in **Private/Incognito window**

### Method 2: Disable Cache in DevTools

1. Open DevTools (F12)
2. Go to **Network** tab
3. Check "**Disable cache**" checkbox
4. Keep DevTools OPEN
5. Hard refresh (Cmd+Shift+R)

### Method 3: Change Version Number

Update the standalone PHP file to force new version:

```php
wp_enqueue_script(
    'ask-mirror-talk',
    $theme_uri . '/ask-mirror-talk.js',
    array(),
    '2.0.1',  // ← Change from 2.0.0 to 2.0.1
    true
);
```

This forces WordPress to load the new file.

---

## ✅ Verify It's Fixed

After clearing cache, you should see:

```javascript
Ask Mirror Talk Widget v2.0.0 loaded
=== DEBUG INFO ===           ← THIS SHOULD APPEAR!
API URL: https://...
WordPress Config: {...}
Question: your question
==================
Response status: 200
Raw response: {"question":...
```

If you DON'T see "=== DEBUG INFO ===" then cache is still the problem!

---

## 🔧 Alternative: Bypass Cache Completely

### Option A: Add Timestamp to JS URL

Update `ask-mirror-talk-standalone.php`:

```php
$timestamp = time(); // Get current timestamp

wp_enqueue_script(
    'ask-mirror-talk',
    $theme_uri . '/ask-mirror-talk.js?nocache=' . $timestamp,
    array(),
    '2.0.0',
    true
);
```

This makes the URL unique every time!

### Option B: Test with Direct HTML

Create a test page `test-widget.html` on your server:

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Test Widget</title>
    <!-- Force no cache -->
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
</head>
<body>
    <div class="ask-mirror-talk">
        <h2>Ask Mirror Talk (Test)</h2>
        <form id="ask-mirror-talk-form">
            <label for="ask-mirror-talk-input">What's on your heart?</label>
            <textarea id="ask-mirror-talk-input" rows="4"></textarea>
            <button type="submit">Ask</button>
        </form>
        <div class="ask-mirror-talk-response">
            <h3>Response</h3>
            <div id="ask-mirror-talk-output"></div>
        </div>
        <div class="ask-mirror-talk-citations">
            <h3>Referenced Episodes</h3>
            <ul id="ask-mirror-talk-citations"></ul>
        </div>
    </div>

    <script>
        // Set API URL
        window.AskMirrorTalkConfig = {
            apiUrl: 'https://ask-mirror-talk-production.up.railway.app/ask'
        };
    </script>
    <!-- Load with timestamp to bypass cache -->
    <script src="/wp-content/themes/astra/ask-mirror-talk.js?v=<?php echo time(); ?>"></script>
</body>
</html>
```

Visit this test page - it will ALWAYS load fresh JavaScript!

---

## 🎯 Quick Check

Run this in browser console:

```javascript
// Check which version is loaded
console.log('Version check:');
console.log('File URL:', document.querySelector('script[src*="ask-mirror-talk"]')?.src);
console.log('Has debug?', document.querySelector('script[src*="ask-mirror-talk"]')?.textContent?.includes('DEBUG INFO'));

// Check if updated function exists
fetch('/wp-content/themes/astra/ask-mirror-talk.js?nocache=' + Date.now())
  .then(r => r.text())
  .then(code => {
    if (code.includes('=== DEBUG INFO ===')) {
      console.log('✅ File on server HAS debug code');
    } else {
      console.log('❌ File on server MISSING debug code');
    }
    if (code.includes('SyntaxError')) {
      console.log('⚠️ Check for syntax errors in file');
    }
  });
```

---

## 📋 If Still Not Working

The file might not be uploaded correctly. Double-check:

1. **FTP/cPanel:** Verify file size
   - `ask-mirror-talk.js` should be around **8-9 KB**
   - Old version was around **6-7 KB**

2. **View source directly:**
   - Go to: `https://yoursite.com/wp-content/themes/astra/ask-mirror-talk.js`
   - Search for "DEBUG INFO"
   - Should find it around line 135

3. **File permissions:**
   - Should be `644` or `-rw-r--r--`

---

## 🚀 Next Steps

1. ✅ Clear ALL browser cache
2. ✅ Open in Private/Incognito window
3. ✅ Check for "=== DEBUG INFO ===" in console
4. ✅ If still not appearing, change version to 2.0.1 in PHP
5. ✅ Or add timestamp to force refresh

**The debug code WILL reveal exactly what's happening!** 

Once you see it, we can fix the actual issue.
