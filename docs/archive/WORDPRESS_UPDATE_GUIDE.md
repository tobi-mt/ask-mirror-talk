# WordPress Frontend Update Guide

## Quick Steps to Update WordPress Widget

### Files to Upload

You need to upload these 4 files to your WordPress installation:

**Location:** `/wp-content/themes/astra-child/`

1. ✅ `ask-mirror-talk.js` (v1.0.2)
2. ✅ `ask-mirror-talk.css` (v1.0.2)

**Source files location:**
```
wordpress/astra/ask-mirror-talk.js
wordpress/astra/ask-mirror-talk.css
```

---

## Method 1: Via SFTP/FTP (Recommended)

1. **Connect to your WordPress site via SFTP**
   - Host: Your hosting provider's SFTP address
   - Username: Your SFTP username
   - Password: Your SFTP password

2. **Navigate to:**
   ```
   /wp-content/themes/astra-child/
   ```

3. **Upload these files** (overwrite existing):
   - `ask-mirror-talk.js`
   - `ask-mirror-talk.css`

4. **Done!** The changes are live immediately.

---

## Method 2: Via WordPress File Manager (cPanel/Plesk)

1. **Log in to cPanel or Plesk**

2. **Open File Manager**

3. **Navigate to:**
   ```
   public_html/wp-content/themes/astra-child/
   ```
   (May be `www/` instead of `public_html/` depending on host)

4. **Upload files:**
   - Click "Upload"
   - Select the 2 files from your local `wordpress/astra/` folder
   - Overwrite when prompted

5. **Done!**

---

## Method 3: Via WordPress Theme File Editor (Not Recommended)

⚠️ **Warning:** Only use this if you don't have SFTP access. Editing files directly in WordPress can be risky.

1. **WordPress Admin → Appearance → Theme File Editor**

2. **Select:** "Astra Child" theme

3. **Find and edit each file:**
   - `ask-mirror-talk.js`
   - `ask-mirror-talk.css`

4. **Copy/paste the new content** from your local files

5. **Click "Update File"** for each

---

## Verify Installation

After uploading, verify the changes:

### 1. Check File Versions (Optional but Recommended)

If using version-based PHP file, update the version numbers:

Edit `ask-mirror-talk-v2.php` or `ask-mirror-talk.php`:

```php
// Change version from 1.0.1 to 1.0.2
wp_enqueue_style(
    'ask-mirror-talk',
    $theme_uri . '/ask-mirror-talk.css',
    array(),
    '1.0.2'  // ← Update this
);
wp_enqueue_script(
    'ask-mirror-talk',
    $theme_uri . '/ask-mirror-talk.js',
    array(),
    '1.0.2',  // ← Update this
    true
);
```

### 2. Clear Caches

**WordPress Cache:**
- If using WP Rocket, W3 Total Cache, or similar → Clear cache
- WordPress Admin → Clear cache (plugin-specific)

**Browser Cache:**
- Chrome/Firefox/Edge: `Ctrl + Shift + R` (Windows) or `Cmd + Shift + R` (Mac)
- Safari: `Cmd + Option + R`

### 3. Test the Widget

1. **Visit your page** with the widget
2. **Ask a test question** like: "What is emotional intelligence?"
3. **Verify:**
   - ✅ No 403 errors in console (F12 → Console tab)
   - ✅ Bold text renders as **bold** (not `**bold**`)
   - ✅ Lists render properly with numbers/bullets
   - ✅ Answer is well-formatted and readable

---

## Troubleshooting

### Issue: Changes Not Showing

**Solution 1: Hard Refresh**
```
Chrome/Firefox/Edge: Ctrl + Shift + R (Windows) or Cmd + Shift + R (Mac)
Safari: Cmd + Option + R
```

**Solution 2: Clear WordPress Cache**
```
WP Rocket: Settings → Clear Cache
W3 Total Cache: Performance → Purge All Caches
Other plugins: Look for "Clear Cache" button
```

**Solution 3: Disable Cache Temporarily**
```
1. Deactivate caching plugin
2. Test the widget
3. Reactivate caching plugin after confirming it works
```

**Solution 4: Check File Permissions**
```
Files should be:
- Readable by web server (644 or 664)
- Located in correct directory
```

**Solution 5: Check for JavaScript Errors**
```
1. Open browser console (F12)
2. Look for errors in Console tab
3. If you see "Uncaught SyntaxError", file may not have uploaded correctly
4. Re-upload the file
```

### Issue: Still Seeing `**bold**` Text

**Check:**
1. Clear browser cache (hard refresh)
2. Verify file was actually uploaded (check file size/date)
3. Check console for JavaScript errors
4. Verify you updated the correct theme (Astra Child, not Astra parent)

### Issue: Widget Not Loading at All

**Check:**
1. Is shortcode `[ask_mirror_talk]` present on the page?
2. Open console (F12) - any JavaScript errors?
3. Are the files in the correct location?
4. Is the PHP file (`ask-mirror-talk-v2.php`) properly registered?

---

## File Checksums (Optional Verification)

To verify files uploaded correctly, check file sizes:

```
ask-mirror-talk.js:         ~7.5 KB
ask-mirror-talk.css:        ~7.8 KB
```

---

## Rollback Plan

If something breaks:

1. **Re-upload previous version** of files
2. Or **restore from backup** if available
3. Or **contact support** if needed

---

## Quick Test Script

After uploading, run this test in browser console (F12):

```javascript
// Test if markdown function exists
console.log(typeof formatMarkdownToHtml);
// Should output: "function"

// Test markdown conversion
console.log(formatMarkdownToHtml("**bold** and *italic*"));
// Should output: "<strong>bold</strong> and <em>italic</em>"
```

---

## Support

If you encounter issues:
1. Check browser console for errors
2. Verify files are in correct location
3. Clear all caches
4. Test in incognito/private browsing mode

---

**Status:** ✅ Ready for WordPress Upload
**Version:** 1.0.2
**Date:** February 16, 2026
