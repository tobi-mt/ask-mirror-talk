# WordPress Critical Error - Diagnostic Steps

## Immediate Actions

### 1. Enable WordPress Debug Mode
Add to `wp-config.php` (above the "That's all" line):
```php
define('WP_DEBUG', true);
define('WP_DEBUG_LOG', true);
define('WP_DEBUG_DISPLAY', false);
```

Then check `/wp-content/debug.log` for the actual error.

### 2. Most Likely Issues

**Issue A: Old versioned file still referenced**
- Check if WordPress cached the old `ask-mirror-talk-v5.8.4.js` reference
- Solution: Clear WordPress cache + browser cache

**Issue B: File upload incomplete**
- The ZIP might not have fully extracted
- Solution: Re-upload via FTP/SFTP instead of WordPress admin

**Issue C: PHP Fatal Error**
- Check the error log at: `/wp-content/debug.log`

### 3. Quick Fix (Rollback)

If you need the site working immediately:
1. Download: `astra-child-v5.7.9.zip` (last known working version)
2. Upload via WordPress → Appearance → Themes → Add New
3. Activate

### 4. Safe Deployment Process

1. **Backup first**: Export current theme via FTP
2. **Use FTP**: Upload files directly instead of ZIP
3. **Test locally**: If possible, test on staging site first
4. **Check PHP version**: Ensure server runs PHP 7.4+

## Files Changed in v5.8.4

1. `ask-mirror-talk.php` - Line 219: Changed filename from `ask-mirror-talk-v5.8.4.js` to `ask-mirror-talk.js`
2. `ask-mirror-talk.js` - Renamed from `ask-mirror-talk-v5.8.4.js`
3. No other code changes

## Emergency Contact

If site is down and urgent:
1. Delete `astra-child` folder via FTP
2. Upload previous working version
3. Clear all caches
