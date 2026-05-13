# Deployment Package v5.8.1 - Service Worker Update Fix

**Release Date**: May 13, 2026  
**Package**: `astra-child-v5.8.1.zip`  
**Priority**: CRITICAL - Fixes PWA update mechanism

---

## 🚨 Critical Fix: Service Worker Auto-Update

### The Problem
After deploying v5.8.0, PWA users were stuck on old service worker version (v5.7.3) because:
- CDN/LiteSpeed cache was caching `sw.js` file
- Even with version parameters (`?v=5.8.0`), cached file was served
- Browser never detected that sw.js had changed
- Users couldn't receive any updates

**Impact**: PWA users would be permanently stuck on old versions unless they manually cleared data.

### The Solution
**BUILD_TIMESTAMP** mechanism to force browser to detect changes:

```javascript
// sw.js - new forced update mechanism
const BUILD_TIMESTAMP = '2026-05-13T00:00:00.000Z';  // Change this to force update
const CACHE_VERSION = 'amt-v5.8.1';
```

**How it works:**
1. Any change to `BUILD_TIMESTAMP` creates a byte-difference in sw.js
2. Even if CDN serves from cache, the timestamp makes it a "new" file  
3. Browser detects the change and installs new service worker
4. Existing update logic (sw-init) triggers automatic reload

### Future Updates
To force ALL PWA users to update immediately:

1. Update `BUILD_TIMESTAMP` in sw.js with current time
2. Bump `CACHE_VERSION` 
3. Update theme version in all files
4. Deploy

Users will automatically update within minutes of visiting the site.

See [SERVICE_WORKER_UPDATE_GUIDE.md](../SERVICE_WORKER_UPDATE_GUIDE.md) for complete documentation.

---

## What's Included in v5.8.1

### Core Files Changed
- ✅ `sw.js` - BUILD_TIMESTAMP mechanism added
- ✅ `style.css` - Version: 5.8.1
- ✅ `ask-mirror-talk.php` - theme_version() returns '5.8.1'
- ✅ `ask-mirror-talk.js` - v5.8.1 log message
- ✅ `ask-mirror-talk-premium.js` - v5.8.1 log message  
- ✅ `analytics-addon.js` - v5.8.1 log message
- ✅ `pyproject.toml` - version = "5.8.1"

### Features from v5.8.0 (Now Accessible to PWA Users)
- Clean card design without blue highlight box
- Unified typography with consistent font sizing
- QR code alignment fixed (80px margin)
- Smart headline layout selection based on length
- Progressive fitting for long headlines (up to 7 lines)

---

## Deployment Instructions

### 1. Upload Theme
```bash
# WordPress admin:
# Appearance → Themes → Astra Child → Delete Old Version
# Upload astra-child-v5.8.1.zip
# Activate
```

### 2. Clear All Caches
- **LiteSpeed Cache**: Dashboard → Purge All
- **CDN**: Cloudflare → Purge Everything
- **Browser**: Hard refresh (Cmd+Shift+R)

### 3. Verify Deployment
```javascript
// Browser console - should show v5.8.1
navigator.serviceWorker.controller.scriptURL
```

### 4. Monitor PWA Users
- Check analytics for active service worker versions
- Users should automatically update within 24 hours
- No manual intervention required

---

## Testing Checklist

### Local Testing
- [ ] Unregister old SW in DevTools
- [ ] Hard refresh page
- [ ] Verify v5.8.1 loads in console
- [ ] Check card rendering with long headline
- [ ] Verify QR code alignment
- [ ] Test offline functionality

### Production Verification  
- [ ] Clear LiteSpeed cache
- [ ] Clear CDN cache
- [ ] Test on multiple devices (iOS, Android, Desktop)
- [ ] Verify automatic SW update after 24h
- [ ] Monitor error logs for update failures

---

## Rollback Plan

If critical issues occur:

1. **Immediate**: Restore from v5.7.9 backup
2. **Service Worker**: Update BUILD_TIMESTAMP in v5.7.9 to force refresh
3. **Notify**: Post in app about temporary rollback

---

## Known Issues & Limitations

### None Expected
The BUILD_TIMESTAMP mechanism is a standard pattern for forcing SW updates. No breaking changes.

### Future Improvements
- Consider service worker versioning in filename (e.g., `sw-v5.8.1.js`)
- Add automated cache purge on deployment
- Implement SW update telemetry to track update success rates

---

## Version History

- **v5.8.1** (2026-05-13): Service worker BUILD_TIMESTAMP force-update mechanism
- **v5.8.0** (2026-05-12): Clean card design without blue box  
- **v5.7.9** (2026-05-12): Font consistency fix
- **v5.7.7** (2026-05-12): QR code alignment fix
- **v5.7.6** (2026-05-12): Spacing rebalance

---

## Support

**Documentation**: See [SERVICE_WORKER_UPDATE_GUIDE.md](../SERVICE_WORKER_UPDATE_GUIDE.md)  
**Logs**: Check browser console for `[PWA]` prefixed messages  
**Status**: Monitor DevTools → Application → Service Workers

