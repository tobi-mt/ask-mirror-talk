# PWA Refresh Fix - Stop Aggressive Reloads on Resume

## 🐛 Problem

Users were experiencing **unwanted app refreshes** when:
1. Minimizing the PWA  
2. Leaving it in the background for a while
3. Resuming → **App reloads, losing context**

This was frustrating because:
- Lost any text they had typed
- Lost results they were reading  
- Interrupted their workflow
- Made the app feel unreliable

## 🔍 Root Cause

The service worker was **aggressively forcing page reloads** whenever it updated:

### In `sw.js` (Service Worker):
```javascript
// OLD CODE - Too aggressive! ❌
windowClients.forEach((client) => {
  client.navigate(client.url).catch(() => {  // Forces reload
    client.postMessage({ type: 'SW_UPDATED' });
  });
});
```

When a user minimized the app:
1. Browser checked for updates in the background
2. Downloaded new service worker
3. User resumed → New SW activated
4. **Forced immediate reload of all tabs**

### In `ask-mirror-talk.js` (Client Side):
```javascript
// OLD CODE - Always reloads ❌
navigator.serviceWorker.addEventListener('controllerchange', function() {
  window.location.reload(); // Immediate reload!
});
```

---

## ✅ Solution

Implemented a **smart, user-friendly update strategy** with 3 key improvements:

### 1. Service Worker: Only Notify Visible Tabs

**File:** `sw.js` (lines ~47-75)

```javascript
// NEW CODE - Only notify visible tabs ✅
windowClients.forEach((client) => {
  // Check if client is actually visible before notifying
  if (client.visibilityState === 'visible' || client.focused) {
    // Send gentle notification instead of forcing reload
    client.postMessage({ 
      type: 'SW_UPDATED',
      version: CACHE_VERSION,
      timestamp: Date.now()
    });
  } else {
    console.log('[SW] Skipping hidden tab - update will apply on next visit');
  }
});
```

**What changed:**
- ✅ No longer forces `client.navigate()` (which reloads the page)
- ✅ Only sends messages to visible/focused tabs
- ✅ Hidden tabs are left alone - update applies naturally on next visit

---

### 2. Client Side: Smart Reload Logic

**File:** `ask-mirror-talk.js` (lines ~741-782, ~715-735)

```javascript
// NEW CODE - Smart reload decisions ✅
if (event.data && event.data.type === 'SW_UPDATED') {
  // Check if user is actively working
  const hasResults = document.querySelector('.amt-result-card');
  const hasTextInProgress = askInput && askInput.value.trim().length > 0;
  const hasUnsavedWork = hasResults || hasTextInProgress;
  
  // Check if user just opened the app (< 30 seconds ago)
  const timeSinceLoad = Date.now() - (window.amtLoadTime || Date.now());
  const justOpened = timeSinceLoad < 30000;
  
  if (hasUnsavedWork || justOpened) {
    console.log('[AMT] Deferring reload (user active)');
    return; // Skip reload - let user continue working
  }
  
  // Only reload if idle
  if (!sessionStorage.getItem('amt_sw_reloaded')) {
    sessionStorage.setItem('amt_sw_reloaded', '1');
    window.location.reload();
  }
}
```

**What changed:**
- ✅ Checks if user has results displayed
- ✅ Checks if user has typed text (unsaved work)
- ✅ Checks if user just opened the app (< 30 seconds)
- ✅ Only reloads if page is truly idle
- ✅ Skips reload if user is actively working

---

### 3. Load Time Tracking & Visibility Management

**File:** `ask-mirror-talk.js` (lines ~1-6, ~784-795)

```javascript
// Track page load time
window.amtLoadTime = Date.now();

// Clear reload flag when page becomes visible
document.addEventListener('visibilitychange', function() {
  if (!document.hidden) {
    setTimeout(function() {
      sessionStorage.removeItem('amt_sw_reloaded');
    }, 5000); // Allow next reload after 5 seconds
  }
});
```

**What changed:**
- ✅ Tracks when page loaded (prevents reload on fresh opens)
- ✅ Clears reload flag after 5 seconds of visibility
- ✅ Allows future updates to reload after user has seen current version

---

## 📊 Before vs After

### Before ❌
```
User minimizes app
      ↓
Browser downloads SW update in background
      ↓
User resumes app (30 seconds later)
      ↓
New SW activates
      ↓
FORCED RELOAD - Text lost, results gone ❌
```

### After ✅
```
User minimizes app
      ↓
Browser downloads SW update in background
      ↓
User resumes app (30 seconds later)
      ↓
New SW activates
      ↓
Checks: Is user active? Has results? Just opened?
      ↓ YES - User is active
SKIP RELOAD - User continues working ✅
      ↓ Update applies on next natural page load
```

---

## 🧪 Testing

### Test Scenario 1: Resume with Text Typed
1. Open PWA
2. Type a question (don't submit)
3. Minimize app for 1 minute
4. Resume

**Expected:** ✅ Text still there, no reload

### Test Scenario 2: Resume with Results Displayed
1. Open PWA
2. Ask a question and get results
3. Minimize app for 1 minute
4. Resume

**Expected:** ✅ Results still visible, no reload

### Test Scenario 3: Resume Immediately After Opening
1. Open PWA
2. Immediately minimize (within 5 seconds)
3. Resume

**Expected:** ✅ No reload (just opened)

### Test Scenario 4: Resume When Idle
1. Open PWA
2. Don't interact for 2 minutes
3. Minimize
4. Wait 1 minute (SW updates)
5. Resume

**Expected:** ✅ May reload (idle), OR defers to next navigation

---

## 🎯 Key Improvements

| Issue | Old Behavior | New Behavior |
|-------|-------------|--------------|
| **Resume from background** | Always reloads ❌ | Only if idle ✅ |
| **Has typed text** | Reloads, loses text ❌ | Skips reload ✅ |
| **Has results displayed** | Reloads, loses results ❌ | Skips reload ✅ |
| **Just opened app** | Can reload immediately ❌ | Waits 30 seconds ✅ |
| **Hidden tabs** | Forces reload ❌ | Left alone ✅ |
| **Update notification** | Forces navigation ❌ | Gentle message ✅ |

---

## 📝 Technical Details

### Service Worker Lifecycle
The service worker lifecycle hasn't changed, but **update application** is now gentler:

1. **Install** - New SW downloads and pre-caches assets
2. **Wait** - Sits in waiting state (not activated yet)
3. **Activate** - Activates when old SW is no longer in use
4. **Claim** - Takes control of all tabs
5. **Notify** - Sends message to visible tabs only (NEW)
6. **Client Decides** - Each tab decides whether to reload (NEW)

### Why This is Better

**Old strategy:** "Update ASAP, reload everything"
- Pro: Users always get latest code
- Con: Disruptive, loses context, feels buggy

**New strategy:** "Update gracefully, preserve context"
- Pro: Respects user's work, feels stable
- Con: Update might take slightly longer to apply
- **Winner:** User experience is far better ✅

### Edge Cases Handled

1. **Private/Incognito Mode:** Falls back to reload if sessionStorage fails
2. **iOS Safari PWA:** Handles both `controllerchange` and `SW_UPDATED` messages
3. **Multiple Tabs:** Each tab makes its own reload decision
4. **Rapid Updates:** Reload flag prevents loops
5. **Page Visibility:** Clears flag after 5 seconds of being visible

---

## 🚀 Deployment

Changes are in 2 files:
- ✅ `wordpress/astra-child/sw.js` - Service worker
- ✅ `wordpress/astra-child/ask-mirror-talk.js` - Client code

**No cache version bump needed** - Changes will apply on next natural page load.

**Testing Recommendation:** 
1. Deploy to staging first
2. Test all 4 scenarios above
3. Monitor for any reload issues
4. Deploy to production

---

## 📈 Expected Impact

### User Experience
- ✅ **No more surprise reloads** when resuming app
- ✅ **Typed text preserved** during background/resume
- ✅ **Results stay visible** when app is backgrounded
- ✅ **App feels more stable and reliable**

### Metrics to Watch
- 📉 **Bounce rate** should decrease (fewer frustrated exits)
- 📈 **Session duration** should increase (less disruption)
- 📈 **Completion rate** should increase (text not lost)
- 📉 **Error reports** about "app refreshing" should decrease

---

## 🔄 Future Enhancements

Potential improvements for later:

1. **Update Banner:** Show a subtle banner when update is available
   - "New version available. Reload when you're ready."
   
2. **Smart Reload Timing:** Reload during natural breaks
   - After question is answered
   - When user navigates away
   
3. **Update Changelog:** Show what's new after update applies
   - "What's new: Better reflection cards!"

4. **User Preference:** Let users control update behavior
   - Auto-update vs Manual reload

---

**Status:** ✅ **COMPLETE**  
**Date:** May 10, 2026  
**Files Changed:** 2 (sw.js, ask-mirror-talk.js)  
**Impact:** High - Significantly improves PWA stability and user trust
