# Service Worker Update Guide

## How PWA Users Get Updates

The service worker automatically updates for all PWA users through this process:

1. **Version Check**: Every time a user visits the site, `sw-init` compares the current SW version with the deployed version
2. **Automatic Unregister**: If versions don't match, the old SW is automatically unregistered
3. **Fresh Install**: The new SW is registered and activated
4. **Auto-Reload**: Page automatically reloads once the new SW activates

## The Caching Problem

Service workers can cache themselves, creating a chicken-and-egg problem:
- Old SW caches sw.js
- Browser never sees the new sw.js
- Users stuck on old version forever

## Our Solution

### 1. Never Cache sw.js
```javascript
// In sw.js line ~101
if (url.pathname.endsWith('sw.js') || url.pathname === '/sw-init'...) return;
```

### 2. BUILD_TIMESTAMP Force Update
```javascript
// In sw.js - change this timestamp to force browser to detect changes
const BUILD_TIMESTAMP = '2026-05-13T00:00:00.000Z';
```

Even if a CDN or cache serves the old file, changing `BUILD_TIMESTAMP` ensures the browser sees it as a different file.

### 3. Version Parameters
```javascript
// sw-init loads: /sw.js?v=5.8.1
var SW_URL = '/sw.js?v=' + SW_VER;
```

## How to Force an Update for All Users

If you deploy a critical fix and need ALL PWA users to update immediately:

1. **Update BUILD_TIMESTAMP** in sw.js:
   ```javascript
   const BUILD_TIMESTAMP = '2026-05-13T12:30:00.000Z';  // Use current time
   ```

2. **Bump CACHE_VERSION**:
   ```javascript
   const CACHE_VERSION = 'amt-v5.8.2';  // Increment version
   ```

3. **Update theme version** in ask-mirror-talk.php:
   ```php
   function ask_mirror_talk_theme_version() {
     return '5.8.2';
   }
   ```

4. **Deploy** - Users will automatically update within minutes of visiting

## Testing Updates Locally

1. Open DevTools → Application → Service Workers
2. Click "Unregister"  
3. Hard refresh (Cmd+Shift+R)
4. Verify new version loads

## Troubleshooting

**If users report being stuck on old version:**
- Check BUILD_TIMESTAMP was updated
- Check theme version matches across all files
- Check LiteSpeed cache is cleared for sw.js
- Users can manually clear by: Settings → App Info → Clear Data

**To verify SW version:**
```javascript
// In browser console
navigator.serviceWorker.controller.scriptURL
```

Should show: `/sw.js?v=5.8.1`
