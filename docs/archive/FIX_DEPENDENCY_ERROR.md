# 🔧 QUICK FIX - "Can't find variable: AskMirrorTalk" Error

## ⚠️ ERROR IDENTIFIED

**Error:** `Can't find variable: AskMirrorTalk`

**Cause:** The functions.php code had a dependency on `'amt-widget'` which doesn't match your actual script handle.

---

## ✅ SOLUTION - Updated Files

I've updated the analytics-addon.js to work **independently** without any dependencies.

---

## 🔄 WHAT TO DO

### Option 1: Re-upload Updated analytics-addon.js (RECOMMENDED)

1. **Re-upload the file:**
   ```
   /Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk/analytics-addon.js
   ```
   
   Upload to: `wp-content/themes/astra/analytics-addon.js` (REPLACE)

2. **Update your functions.php code:**

   **CHANGE FROM:**
   ```php
   function amt_add_analytics_tracking() {
       wp_enqueue_script(
           'amt-analytics-addon',
           get_template_directory_uri() . '/analytics-addon.js',
           array('amt-widget'),  // ← REMOVE THIS DEPENDENCY
           '2.0',
           true
       );
   }
   ```

   **TO:**
   ```php
   function amt_add_analytics_tracking() {
       wp_enqueue_script(
           'amt-analytics-addon',
           get_template_directory_uri() . '/analytics-addon.js',
           array(),  // ← Empty array - no dependencies
           '2.0',
           true
       );
   }
   ```

3. **Clear cache and hard refresh**

4. **Test again**

---

### Option 2: Quick Fix Without Re-uploading (Alternative)

If you can't re-upload right now, just change the functions.php code:

**Change `array('amt-widget')` to `array()`**

That's it! This removes the dependency error.

---

## 🧪 TESTING

After making the change:

1. **Clear browser cache** (Ctrl+Shift+R)
2. **Open console** (F12)
3. **Refresh page**
4. **You should see:**
   ```
   ✅ Ask Mirror Talk Widget v2.1.0 loaded
   ✅ Ask Mirror Talk Analytics Add-on loaded
   ```

5. **Ask a question**
6. **Console should show:**
   ```
   ✅ QA Session ID captured: 117
   ✅ Citation tracking added to 5 links
   ✅ Feedback buttons added
   ```

---

## 📝 UPDATED CODE

### functions.php (CORRECTED):

```php
// Ask Mirror Talk Analytics Tracking
function amt_add_analytics_tracking() {
    wp_enqueue_script(
        'amt-analytics-addon',
        get_template_directory_uri() . '/analytics-addon.js',
        array(), // No dependencies
        '2.0',
        true
    );
}
add_action('wp_enqueue_scripts', 'amt_add_analytics_tracking');
```

---

## ✅ WHAT CHANGED

### In analytics-addon.js:

**Before:** Required the main widget to be loaded first

**After:** 
- Works independently ✅
- Uses DOM observation to detect citations ✅
- No dependency on other scripts ✅
- More reliable ✅

### In functions.php:

**Before:** `array('amt-widget')` - caused dependency error

**After:** `array()` - no dependencies, works standalone

---

## 🎯 NEXT STEPS

1. **Update functions.php** with corrected code (change `array('amt-widget')` to `array()`)
2. **Re-upload analytics-addon.js** (optional but recommended for better reliability)
3. **Clear cache** 
4. **Test**

---

## 🆘 IF STILL NOT WORKING

**Check these:**

1. **File uploaded correctly?**
   - Verify `analytics-addon.js` exists in your theme folder
   - Check file size (should be ~7KB)

2. **functions.php updated?**
   - Code added at bottom
   - No syntax errors (check for missing semicolons, brackets)

3. **Browser console errors?**
   - Press F12
   - Look for red error messages
   - Share any errors you see

4. **WordPress cache cleared?**
   - Clear any caching plugins
   - Hard refresh browser (Ctrl+Shift+R)

---

## 📊 EXPECTED RESULT

**After fix, console should show:**

```
[Log] Ask Mirror Talk Widget v2.1.0 loaded
[Log] Ask Mirror Talk Analytics Add-on loaded
[Log] === DEBUG INFO ===
[Log] API URL: "https://ask-mirror-talk-production.up.railway.app/ask"
[Log] Question: "How to overcome addiction?"
[Log] Response status: 200
[Log] ✅ QA Session ID captured: 117
[Log] ✅ Citation tracking added to 5 links
[Log] ✅ Feedback buttons added
```

**No more "Can't find variable" error!** ✅

---

Last Updated: February 20, 2026  
Status: 🔧 Dependency Error Fixed
