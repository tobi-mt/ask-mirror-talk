# WordPress functions.php - Correct Setup

## ✅ Correct Code

Replace the last line in your `functions.php`:

### Current (has extra slash):
```php
require_once ASTRA_THEME_DIR . '/ask-mirror-talk.php';
```

### Fixed (remove leading slash):
```php
require_once ASTRA_THEME_DIR . 'ask-mirror-talk.php';
```

---

## 📁 Complete Section to Add

Add this at the end of your `functions.php` (after all the Astra theme requires):

```php
/**
 * Ask Mirror Talk Widget Integration
 * Version: 2.0.0
 * 
 * Provides AI-powered Q&A functionality for Mirror Talk Podcast
 * Uses shortcode: [ask_mirror_talk]
 */
require_once ASTRA_THEME_DIR . 'ask-mirror-talk.php';
```

---

## 📋 Why This Matters

`ASTRA_THEME_DIR` is defined as:
```php
define( 'ASTRA_THEME_DIR', trailingslashit( get_template_directory() ) );
```

The `trailingslashit()` function **already adds a trailing slash**, so:
- `ASTRA_THEME_DIR` = `/var/www/html/wp-content/themes/astra/`

Therefore:
- ❌ `ASTRA_THEME_DIR . '/ask-mirror-talk.php'` = `...astra//ask-mirror-talk.php` (double slash)
- ✅ `ASTRA_THEME_DIR . 'ask-mirror-talk.php'` = `...astra/ask-mirror-talk.php` (correct)

---

## 🚀 Complete Setup Steps

### 1. Upload Files via FTP/cPanel

Upload these files to `/wp-content/themes/astra/`:
```
ask-mirror-talk.php  (rename from ask-mirror-talk-v2.php)
ask-mirror-talk.js
ask-mirror-talk.css
```

### 2. Edit functions.php

Add at the very end:
```php
/**
 * Ask Mirror Talk Widget Integration
 * Version: 2.0.0
 */
require_once ASTRA_THEME_DIR . 'ask-mirror-talk.php';
```

### 3. Add Shortcode to Page

Edit any page and add:
```
[ask_mirror_talk]
```

### 4. Verify Installation

1. Visit the page with the shortcode
2. Open browser DevTools (F12)
3. Check Console for: `Ask Mirror Talk Widget v2.0.0 loaded`
4. Check Network tab for files loading with version `2.0.0`

---

## ✅ Final Checklist

- [ ] Renamed `ask-mirror-talk-v2.php` to `ask-mirror-talk.php`
- [ ] Uploaded 3 files to `/wp-content/themes/astra/`:
  - `ask-mirror-talk.php`
  - `ask-mirror-talk.js`
  - `ask-mirror-talk.css`
- [ ] Edited `functions.php` with correct path (no leading slash)
- [ ] Added shortcode `[ask_mirror_talk]` to a page
- [ ] Tested in browser - widget appears
- [ ] Console shows "Widget v2.0.0 loaded"
- [ ] Submitted test question successfully

---

## 🔍 Troubleshooting

### Widget doesn't appear
```php
// Add this temporarily to debug
add_action('wp_footer', function() {
    echo '<!-- ASTRA_THEME_DIR: ' . ASTRA_THEME_DIR . ' -->';
    echo '<!-- File exists: ' . (file_exists(ASTRA_THEME_DIR . 'ask-mirror-talk.php') ? 'YES' : 'NO') . ' -->';
});
```

### Check shortcode is registered
```php
// View page source and look for:
<!-- Shortcode registered: YES or NO -->
```

Add to functions.php temporarily:
```php
add_action('wp_footer', function() {
    if (shortcode_exists('ask_mirror_talk')) {
        echo '<!-- Shortcode registered: YES -->';
    } else {
        echo '<!-- Shortcode registered: NO -->';
    }
});
```

---

**That's it! Your WordPress integration should now be working perfectly with v2.0.0.** 🎉
