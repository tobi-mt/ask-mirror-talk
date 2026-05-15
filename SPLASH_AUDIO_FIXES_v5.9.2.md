# Splash Screen & Audio Fixes - v5.9.2

## Issues Fixed

### Issue 1: Black Screen Before Splash

**Problem**: Users reported a persistent black screen appearing before the splash screen on startup.

**Root Causes**:
- Inline CSS in PHP head lacked `!important` flag to override WordPress theme defaults
- CSS was only applied to `html, body` but not to `.ask-mirror-talk` container
- On some devices/browsers, the pre-paint background wasn't rendering immediately

**Solution Applied**:
- Updated inline CSS in `wordpress/astra-child/ask-mirror-talk.php` to use `!important` on both `html, body` and `.ask-mirror-talk`
- This ensures the cream background (#f1ece4) renders before any external CSS loads
- Works on both browser (normal site) and PWA standalone contexts

**Code Changes**:
```php
<!-- In ask-mirror-talk.php, in <head> -->
<style>
  html, body { background-color: #f1ece4 !important; }
  .ask-mirror-talk { background-color: #f1ece4 !important; }
</style>
```

---

### Issue 2: Splash Appears for Very Short Time / Instant Dismiss

**Problem**: On cached PWA loads, the splash was appearing and immediately disappearing (300-500ms).

**Root Causes**:
- The 1800ms minimum display time gate wasn't checking multiple document ready states
- `window.load` event can fire instantly from service worker cache
- No check for `document.readyState` before applying minimum timeout

**Solution Applied**:
- Enhanced `initLaunchSplash()` to check `document.readyState` before waiting for `load` event
- If document is already `interactive` or `complete`, apply the minimum timeout immediately
- Ensures 1800ms minimum is always respected, even on instant-cache loads

**Code Changes**:
```javascript
// Check multiple ready states to ensure we never dismiss too early
if (document.readyState === 'complete') {
  _hideSplashAfterMin('Ready to reflect');
} else if (document.readyState === 'interactive') {
  _hideSplashAfterMin('Ready to reflect');
} else {
  window.addEventListener('load', () => {
    _hideSplashAfterMin('Ready to reflect');
  }, { once: true });
}
```

---

### Issue 3: Splash Reappears After App Opens

**Problem**: After the splash disappeared and the app loaded, the splash would reappear after a few seconds on reload/navigation.

**Root Causes**:
- `hasHiddenLaunchSplash` flag was only a `let` variable in memory
- On page reload, the flag resets, allowing splash to re-initialize
- No persistent state to track "splash already shown in this session"

**Solution Applied**:
- Introduced `sessionStorage` persistence with `SPLASH_SHOWN_SESSION_KEY`
- Added `wasSplashShownThisSession()` check at init time
- If splash was already shown in this session, immediately hide it without re-initializing
- Updated `hideLaunchSplash()` to mark the session state when hiding

**Code Changes**:
```javascript
const SPLASH_SHOWN_SESSION_KEY = 'amt_splash_shown_session';

function wasSplashShownThisSession() {
  try {
    return sessionStorage.getItem(SPLASH_SHOWN_SESSION_KEY) === '1';
  } catch (e) {
    return false;
  }
}

function markSplashShownThisSession() {
  try {
    sessionStorage.setItem(SPLASH_SHOWN_SESSION_KEY, '1');
  } catch (e) {}
}

// In initLaunchSplash():
if (wasSplashShownThisSession()) {
  launchSplash.style.display = 'none';
  return; // Skip re-initialization
}

// In hideLaunchSplash():
markSplashShownThisSession();
```

---

### Issue 4: Audio Controls Clutter Splash / Move to In-App Settings

**Problem**: Audio control buttons ("Play calm intro", "Autoplay off") were cluttering the splash screen. Users want these in a dedicated app Settings panel instead.

**Solution Applied**:

#### 4a. Removed Audio Buttons from Splash HTML
- Deleted `<button id="amt-launch-splash-audio-toggle">` and `<button id="amt-launch-splash-audio-autoplay-toggle">` from splash markup
- Removed the entire `<div class="amt-launch-actions">` container
- Splash now shows only status text: "Loading your premium calm mode..."

#### 4b. Added Settings Button to Header Controls
- Added new ⚙️ Settings button in the app heading controls (next to Journal, Note, About)
- Button ID: `amt-settings-btn`, with proper accessibility attributes (`aria-expanded`)

#### 4c. Created Dedicated Settings Modal
- New modal: `#amt-settings-modal` with professional styling
- Contains "Audio & Sound" section with:
  - Checkbox: "Enable intro sound on startup"
  - Status display: "On" or "Off"
  - Description: "When enabled, a calm ambient sound will play when you open the app."
- Modal slides up from bottom with blur backdrop (consistent with About modal)
- Close button and Escape key support

#### 4d. Audio Preference Logic
- Autoplay preference still persists in `localStorage` with key `amt_launch_audio_autoplay`
- Settings checkbox syncs with this preference
- Audio still plays during splash if autoplay is enabled (via `createLaunchSplashAmbientTrack()`)
- Users can control it from Settings panel instead of splash buttons

**Code Changes Summary**:

**HTML** (`ask-mirror-talk.php`):
- Removed both audio buttons from splash
- Added ⚙️ Settings button to heading
- Added settings modal with audio autoplay checkbox

**CSS** (`ask-mirror-talk.css`):
- Styled `.amt-settings-btn` (cream background, brown text, hover effects)
- Styled `.amt-settings-modal` with animated slide-up from bottom
- Styled `.amt-settings-content`, `.amt-settings-header`, `.amt-settings-body`
- Styled checkbox, label, description text with proper accessibility

**JavaScript** (`ask-mirror-talk.js`):
- Removed queries for `launchSplashAudioToggle` and `launchSplashAudioAutoplayToggle` (no longer exist)
- Removed `updateLaunchAutoplayToggleLabel()` function (splash buttons gone)
- Simplified `initLaunchSplash()` - no audio button event listeners
- Added new `initSettingsModal()` IIFE to handle:
  - Settings button click (show modal)
  - Checkbox change (save preference, update label)
  - Close button and backdrop click (hide modal)
  - Escape key support
  - Sync checkbox state when opening modal

---

## Testing Checklist

- [ ] **Black Screen**: Open app on fresh PWA install - no black screen before splash appears
- [ ] **Splash Duration**: Splash visible for at least 1800ms (not instant-dismissed on cached loads)
- [ ] **Splash Once**: Reload page mid-session - splash does NOT reappear
- [ ] **Settings Button**: ⚙️ icon visible in heading controls
- [ ] **Settings Modal**: Clicking ⚙️ shows modal with audio settings
- [ ] **Audio Checkbox**: Checkbox reflects current autoplay preference
- [ ] **Audio Toggle**: Toggling checkbox updates status label ("On"/"Off") and saves to localStorage
- [ ] **Modal Close**: Click close button or backdrop to dismiss modal
- [ ] **Escape Key**: Press Escape to close modal
- [ ] **Audio Playback**: Audio still works if autoplay enabled (plays during splash)
- [ ] **Device Support**: Test on iOS Safari PWA, Android Chrome PWA, and browser

---

## Files Modified

1. `wordpress/astra-child/ask-mirror-talk.php`
   - Strengthened inline CSS with `!important`
   - Removed audio buttons from splash
   - Added Settings button to heading
   - Added settings modal HTML

2. `wordpress/astra-child/ask-mirror-talk.js`
   - Removed audio button element queries
   - Removed `updateLaunchAutoplayToggleLabel()` function
   - Enhanced `initLaunchSplash()` with sessionStorage and readyState checks
   - Removed audio button event listeners
   - Added `wasSplashShownThisSession()`, `markSplashShownThisSession()`
   - Added new `initSettingsModal()` function

3. `wordpress/astra-child/ask-mirror-talk.css`
   - Added `.amt-settings-btn` styling
   - Added `.amt-settings-modal`, `.amt-settings-content`, `.amt-settings-header` styling
   - Added `.amt-setting-item`, `.amt-setting-checkbox`, `.amt-setting-description` styling

---

## Version Update

Ready to bump version from **5.9.1** to **5.9.2** and package.

**Changes Summary for Release Notes**:
- Fixed persistent black screen before splash on PWA startup
- Fixed splash screen disappearing too quickly on cached loads
- Fixed splash screen reappearing after app opens
- Moved audio controls from splash screen to dedicated Settings panel (⚙️)
- Enhanced splash state persistence using sessionStorage
- Improved document readyState checks for more reliable splash timing
