# 🔧 FINAL FIX - Script Localization Issue

## ⚠️ PROBLEM IDENTIFIED

Your `ask-mirror-talk.js` relies on WordPress localizing the `AskMirrorTalk` object with:
- `AskMirrorTalk.ajaxUrl`
- `AskMirrorTalk.nonce`

But this is only happening when the shortcode `[ask_mirror_talk]` is detected on the page.

The analytics addon is loading, but the main widget script can't find `AskMirrorTalk`.

---

## ✅ SOLUTION

Update your `functions.php` to ensure the analytics addon loads **AFTER** the main widget script AND only when the widget script is loaded.

---

## 📝 UPDATED FUNCTIONS.PHP

**Replace the analytics section in your functions.php with this:**

```php
// Ask Mirror Talk Analytics Tracking
function amt_add_analytics_tracking() {
    // Only load analytics if the main widget script is enqueued
    if (wp_script_is('ask-mirror-talk', 'enqueued') || wp_script_is('ask-mirror-talk', 'registered')) {
        wp_enqueue_script(
            'amt-analytics-addon',
            get_template_directory_uri() . '/analytics-addon.js',
            array('ask-mirror-talk'), // Load AFTER the main widget script
            '2.0',
            true
        );
    }
}
add_action('wp_enqueue_scripts', 'amt_add_analytics_tracking', 20); // Priority 20 to run after widget enqueue
```

---

## 🎯 WHAT THIS DOES

1. **Checks if main widget is loaded** - Only adds analytics if the widget script exists
2. **Sets dependency** - `array('ask-mirror-talk')` ensures analytics loads AFTER the main script
3. **Higher priority** - Priority `20` ensures it runs after the widget's enqueue (which is default priority 10)

---

## 🧪 TESTING

After updating functions.php:

1. **Clear all caches**
2. **Hard refresh browser** (Ctrl+Shift+R)
3. **Check console** - should see:

```
✅ Ask Mirror Talk Widget v2.1.0 loaded
✅ Ask Mirror Talk Analytics Add-on loaded
```

4. **Ask a question** - should work without errors

---

## 📋 COMPLETE CORRECTED CODE

**Your `functions.php` should have:**

```php
<?php
// ... all your existing Astra theme code ...

require_once ASTRA_THEME_DIR . 'ask-mirror-talk.php';

// Ask Mirror Talk Analytics Tracking
function amt_add_analytics_tracking() {
    // Only load analytics if the main widget script is enqueued
    if (wp_script_is('ask-mirror-talk', 'enqueued') || wp_script_is('ask-mirror-talk', 'registered')) {
        wp_enqueue_script(
            'amt-analytics-addon',
            get_template_directory_uri() . '/analytics-addon.js',
            array('ask-mirror-talk'), // Load AFTER the main widget script
            '2.0',
            true
        );
    }
}
add_action('wp_enqueue_scripts', 'amt_add_analytics_tracking', 20); // Priority 20
```

---

## 🔍 WHY THIS WORKS

**Before:**
- Analytics addon loaded independently
- Main widget script loaded after (or conditionally)
- `AskMirrorTalk` object not available when analytics tried to reference it

**After:**
- Analytics only loads if main widget script is present
- Analytics has dependency on main script (loads second)
- `AskMirrorTalk` object is available when analytics runs

---

## ⚠️ ALTERNATIVE: If This Still Doesn't Work

If the shortcode conditional loading is still causing issues, you can force the widget script to always load:

**In `ask-mirror-talk.php`, change this function:**

```php
function ask_mirror_talk_enqueue_assets() {
    // REMOVE the conditional checks - always load
    
    $theme_uri = get_stylesheet_directory_uri();
    wp_enqueue_style(
        'ask-mirror-talk',
        $theme_uri . '/ask-mirror-talk.css',
        array(),
        '2.1.0'
    );
    wp_enqueue_script(
        'ask-mirror-talk',
        $theme_uri . '/ask-mirror-talk.js',
        array(),
        '2.1.0',
        true
    );

    wp_localize_script('ask-mirror-talk', 'AskMirrorTalk', array(
        'ajaxUrl' => admin_url('admin-ajax.php'),
        'nonce' => wp_create_nonce('ask_mirror_talk_nonce'),
        'apiUrl' => 'https://ask-mirror-talk-production.up.railway.app/ask',
        'version' => '2.1.0'
    ));
}
add_action('wp_enqueue_scripts', 'ask_mirror_talk_enqueue_assets');
```

This removes the shortcode detection and loads the script on every page (slightly less efficient but more reliable).

---

## 🎯 RECOMMENDED ACTION

**Try the updated functions.php code first** (with the dependency check).

If that doesn't work, use the alternative to force-load the widget script.

---

Last Updated: February 20, 2026  
Status: 🔧 Script Loading Order Fixed
