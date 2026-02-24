# ⚡ QUICK FIX CHECKLIST - Do This Now!

## 🚨 ERROR: "Can't find variable: AskMirrorTalk"

**This is a script loading order issue. Here's the 5-minute fix:**

---

## ✅ DO THESE 3 THINGS NOW:

### 1️⃣ Upload Updated `ask-mirror-talk.php` ⚠️ CRITICAL!

**This is the main fix!**

```
Local file:
/Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk/wordpress/astra/ask-mirror-talk.php

Upload to WordPress:
wp-content/themes/astra/ask-mirror-talk.php

Action: REPLACE the existing file
```

**Why:** This removes the shortcode detection that's preventing the script from loading.

---

### 2️⃣ Update `functions.php` in WordPress

**Edit:** `wp-content/themes/astra/functions.php`

**Find and REPLACE the `mirror_talk_enqueue_analytics` function:**

**REMOVE THIS:**
```php
function mirror_talk_enqueue_analytics() {
    // Only load if the main widget script is going to load
    if (!is_singular()) {
        return;
    }

    global $post;
    if (!$post || !has_shortcode($post->post_content, 'ask_mirror_talk')) {
        return;
    }

    // Now enqueue the analytics addon with the correct dependency
    $theme_uri = get_stylesheet_directory_uri();
    wp_enqueue_script(
        'ask-mirror-talk-analytics',
        $theme_uri . '/analytics-addon.js',
        array('ask-mirror-talk'), // Depends on the main widget script
        '1.0.0',
        true
    );
}
add_action('wp_enqueue_scripts', 'mirror_talk_enqueue_analytics', 20);
```

**ADD THIS:**
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
        array('ask-mirror-talk'), // Load after main widget script
        '2.1.0',
        true
    );
}
add_action('wp_enqueue_scripts', 'mirror_talk_enqueue_analytics', 20);
```

**Save the file.**

---

### 3️⃣ Clear ALL Caches

1. **WordPress cache** (if using WP Super Cache, W3 Total Cache, etc.)
2. **Browser cache:** Hard refresh with `Cmd + Shift + R` (Mac) or `Ctrl + Shift + R` (Windows)
3. **Or test in Incognito/Private mode**

---

## ✅ HOW TO VERIFY IT WORKED

1. **Go to your page** with the widget
2. **Open browser console** (F12 or right-click → Inspect → Console tab)
3. **Refresh the page**
4. **Look for these messages:**

```
✅ Ask Mirror Talk Widget v2.1.0 loaded
✅ Ask Mirror Talk Analytics Add-on loaded
```

**NO MORE ERRORS!** 🎉

---

## 🎯 WHAT THIS FIXES

**Problem:**
- Main script only loaded if WordPress detected the shortcode
- Your shortcode is in a page builder, so WordPress didn't detect it
- Main script didn't load
- Analytics addon tried to load anyway
- ERROR: Can't find variable

**Solution:**
- Main script now loads on ALL singular pages
- Analytics addon loads right after it (with dependency)
- Both scripts load in the correct order
- Everything works!

---

## 📦 COMPLETE FILE LIST (All 3 Files)

If you haven't uploaded the other files yet, here's everything:

```
1. ask-mirror-talk.php  (UPDATED - fixes script loading)
   → wp-content/themes/astra/ask-mirror-talk.php

2. ask-mirror-talk.js   (UPDATED - has tracking attributes)
   → wp-content/themes/astra/ask-mirror-talk.js

3. analytics-addon.js   (NEW - tracks clicks and feedback)
   → wp-content/themes/astra/analytics-addon.js
```

---

## 🆘 STILL NOT WORKING?

Run this in browser console:

```javascript
// Check if AskMirrorTalk is defined
console.log(typeof AskMirrorTalk);
// Should show: "object"

// Check script versions
Array.from(document.scripts)
  .filter(s => s.src.includes('ask-mirror-talk'))
  .forEach(s => console.log(s.src));
// Should show version 2.1.0
```

If still broken:
1. Make sure you uploaded the NEW `ask-mirror-talk.php` file
2. Try clearing cache again
3. Check file permissions (should be 644)
4. Check error logs: WordPress → Tools → Site Health → Info → Server

---

## ⏱️ TIME REQUIRED

- Upload 1 file: **1 minute**
- Edit functions.php: **2 minutes**
- Clear cache: **1 minute**
- Test: **1 minute**

**Total: 5 minutes**

---

**DO IT NOW!** 🚀

The fix is simple: upload the updated PHP file and update functions.php!

---

Last Updated: February 20, 2026  
Fix: Script loading order issue
