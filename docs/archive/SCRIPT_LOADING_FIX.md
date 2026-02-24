# 🔧 SCRIPT LOADING FIX - "Can't find variable: AskMirrorTalk"

## 🚨 THE PROBLEM

**Error in console:**
```
[Error] Ask Mirror Talk Error: – ReferenceError: Can't find variable: AskMirrorTalk
```

**Root cause:** The main widget script (`ask-mirror-talk.js`) was only loading when WordPress detected the `[ask_mirror_talk]` shortcode in the post content. If the shortcode is in a page builder (Elementor, etc.) or dynamic content, WordPress doesn't detect it, so the script doesn't load—but the analytics addon tries to load anyway.

---

## ✅ THE FIX

### Fix 1: Update `ask-mirror-talk.php`

**Location:** `wp-content/themes/astra/ask-mirror-talk.php`

**Change:** Remove shortcode detection so the script loads on all singular pages.

**Before:**
```php
function ask_mirror_talk_enqueue_assets() {
    if (!is_singular()) {
        return;
    }

    global $post;
    if (!$post || !has_shortcode($post->post_content, 'ask_mirror_talk')) {
        return;  // ❌ This prevents script from loading!
    }

    // ... rest of function
}
```

**After:**
```php
function ask_mirror_talk_enqueue_assets() {
    // Always enqueue on singular pages to handle page builders and dynamic content
    if (!is_singular()) {
        return;
    }

    $theme_uri = get_stylesheet_directory_uri();
    wp_enqueue_style(
        'ask-mirror-talk',
        $theme_uri . '/ask-mirror-talk.css',
        array(),
        '2.1.0'  // ✅ New version forces cache refresh
    );
    wp_enqueue_script(
        'ask-mirror-talk',
        $theme_uri . '/ask-mirror-talk.js',
        array('jquery'),  // ✅ Added jQuery dependency
        '2.1.0',
        true
    );

    wp_localize_script('ask-mirror-talk', 'AskMirrorTalk', array(
        'ajaxUrl' => admin_url('admin-ajax.php'),
        'nonce' => wp_create_nonce('ask_mirror_talk_nonce')
    ));
}
```

---

### Fix 2: Update `functions.php`

**Location:** `wp-content/themes/astra/functions.php`

**Change:** Match the behavior of the main script (no shortcode detection).

**Before:**
```php
function mirror_talk_enqueue_analytics() {
    if (!is_singular()) {
        return;
    }

    global $post;
    if (!$post || !has_shortcode($post->post_content, 'ask_mirror_talk')) {
        return;  // ❌ This causes mismatch with main script
    }

    // ... rest of function
}
```

**After:**
```php
function mirror_talk_enqueue_analytics() {
    // Always enqueue on singular pages (matches main script behavior)
    if (!is_singular()) {
        return;
    }

    // Enqueue analytics addon with dependency on main script
    $theme_uri = get_stylesheet_directory_uri();
    wp_enqueue_script(
        'ask-mirror-talk-analytics',
        $theme_uri . '/analytics-addon.js',
        array('ask-mirror-talk'), // ✅ Load after main widget script
        '2.1.0',
        true
    );
}
add_action('wp_enqueue_scripts', 'mirror_talk_enqueue_analytics', 20);
```

---

## 📋 DEPLOYMENT STEPS

1. **Upload the updated `ask-mirror-talk.php`** from this project to WordPress:
   ```
   Local: /Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk/wordpress/astra/ask-mirror-talk.php
   WordPress: wp-content/themes/astra/ask-mirror-talk.php
   ```

2. **Update `functions.php`** in WordPress with the new code above

3. **Clear ALL caches:**
   - WordPress cache (if using a caching plugin)
   - Browser cache (Cmd+Shift+R on Mac)
   - CDN cache (if using Cloudflare, etc.)

4. **Test on your page:**
   - Open browser console (F12)
   - Refresh the page
   - Look for these messages:

   ```
   ✅ Ask Mirror Talk Widget v2.1.0 loaded
   ✅ Ask Mirror Talk Analytics Add-on loaded
   ```

---

## 🎯 WHY THIS WORKS

### Before (Broken):
```
Page loads
↓
WordPress checks: Does post content have [ask_mirror_talk]?
↓
NO (because it's in a page builder)
↓
Main script doesn't load ❌
↓
Analytics addon loads anyway
↓
Analytics tries to access AskMirrorTalk variable
↓
ERROR: Can't find variable: AskMirrorTalk ❌
```

### After (Fixed):
```
Page loads (singular page)
↓
Main script loads ✅
↓
wp_localize_script creates AskMirrorTalk variable ✅
↓
Analytics addon loads (with dependency) ✅
↓
Analytics accesses AskMirrorTalk variable ✅
↓
Everything works! 🎉
```

---

## 🔍 HOW TO VERIFY IT'S FIXED

### In Browser Console:
```javascript
// Check if main script loaded
console.log(AskMirrorTalk);
// Should show: {ajaxUrl: "...", nonce: "..."}

// Check if scripts are loaded
document.querySelector('script[src*="ask-mirror-talk.js"]');
// Should show: <script> element

document.querySelector('script[src*="analytics-addon.js"]');
// Should show: <script> element
```

### Expected Console Output:
```
[Log] Ask Mirror Talk Widget v2.1.0 loaded
[Log] Ask Mirror Talk Analytics Add-on loaded
```

**No errors!** ✅

---

## 🚨 TROUBLESHOOTING

### Still seeing the error?

**1. Clear cache properly:**
```bash
# Hard refresh in browser
Cmd + Shift + R (Mac)
Ctrl + Shift + R (Windows)

# Or open in incognito/private mode
```

**2. Check script versions:**
Open browser DevTools → Network tab → Refresh page → Look for:
- `ask-mirror-talk.js?ver=2.1.0` ✅
- `analytics-addon.js?ver=2.1.0` ✅

If you see `ver=1.0.0`, the cache isn't cleared yet.

**3. Check script load order:**
In Console, run:
```javascript
Array.from(document.scripts)
  .filter(s => s.src.includes('ask-mirror-talk') || s.src.includes('analytics'))
  .map(s => s.src);
```

Should show:
```javascript
[
  "https://yoursite.com/wp-content/themes/astra/ask-mirror-talk.js?ver=2.1.0",
  "https://yoursite.com/wp-content/themes/astra/analytics-addon.js?ver=2.1.0"
]
```

Main script should come BEFORE analytics addon.

**4. Check if AskMirrorTalk is defined:**
In Console, run:
```javascript
typeof AskMirrorTalk
```

Should return: `"object"` ✅  
If it returns: `"undefined"` ❌ then `wp_localize_script` isn't working.

---

## 📦 FILES TO UPLOAD

1. **`ask-mirror-talk.php`** (UPDATED)
   - Local: `/Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk/wordpress/astra/ask-mirror-talk.php`
   - Upload to: `wp-content/themes/astra/ask-mirror-talk.php`
   - Action: REPLACE existing file

2. **`ask-mirror-talk.js`** (from previous update)
   - Already should be uploaded with tracking attributes

3. **`analytics-addon.js`** (from previous update)
   - Already should be uploaded

---

## ✅ CHECKLIST

- [ ] Upload updated `ask-mirror-talk.php` to WordPress
- [ ] Update `functions.php` with new code
- [ ] Clear WordPress cache
- [ ] Clear browser cache (hard refresh)
- [ ] Open page with widget in browser
- [ ] Check console for "Widget v2.1.0 loaded" message
- [ ] Check console for "Analytics Add-on loaded" message
- [ ] Verify no "Can't find variable" errors
- [ ] Ask a test question
- [ ] Click a citation link
- [ ] Check feedback buttons appear

---

**Status:** 🔧 **FIX READY TO DEPLOY**

---

Last Updated: February 20, 2026  
Issue: Script loading order / shortcode detection  
Solution: Remove shortcode detection, add dependencies, update versions
