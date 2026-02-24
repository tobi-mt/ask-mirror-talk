# WordPress Integration - Two Approaches

## Issue Identified

Your setup has a **mismatch**:
- **HTML file** → Calls Railway API directly
- **PHP file** → Expects WordPress AJAX calls

Error: "The string did not match the expected pattern" = WordPress nonce validation failing

---

## Option 1: Direct API Call (RECOMMENDED) ✅

**Use this if:** You want simplest setup, no WordPress backend needed

### Files to Upload:
1. `ask-mirror-talk.js` (already correct - calls Railway directly)
2. `ask-mirror-talk.css`
3. `ask-mirror-talk-standalone.php` (new simplified version)

### Create: `ask-mirror-talk-standalone.php`

```php
<?php
/**
 * Ask Mirror Talk - Standalone Version
 * Version: 2.0.0
 * 
 * This version calls the Railway API directly from JavaScript
 * No WordPress AJAX needed - simpler and faster!
 * 
 * Usage: [ask_mirror_talk]
 */

if (!defined('ABSPATH')) {
    exit;
}

function ask_mirror_talk_shortcode() {
    ob_start();
    ?>
    <div class="ask-mirror-talk">
        <h2>Ask Mirror Talk</h2>
        <form id="ask-mirror-talk-form">
            <label for="ask-mirror-talk-input">What's on your heart?</label>
            <textarea id="ask-mirror-talk-input" rows="4" placeholder="Ask a question..."></textarea>
            <button type="submit" id="ask-mirror-talk-submit">Ask</button>
        </form>
        <div class="ask-mirror-talk-response">
            <h3>Response</h3>
            <div id="ask-mirror-talk-output"></div>
        </div>
        <div class="ask-mirror-talk-citations">
            <h3>Referenced Episodes</h3>
            <ul id="ask-mirror-talk-citations"></ul>
        </div>
    </div>
    <?php
    return ob_get_clean();
}
add_shortcode('ask_mirror_talk', 'ask_mirror_talk_shortcode');

function ask_mirror_talk_enqueue_assets() {
    if (!is_singular()) {
        return;
    }

    global $post;
    if (!$post || !has_shortcode($post->post_content, 'ask_mirror_talk')) {
        return;
    }

    $theme_uri = get_stylesheet_directory_uri();
    
    wp_enqueue_style(
        'ask-mirror-talk',
        $theme_uri . '/ask-mirror-talk.css',
        array(),
        '2.0.0'
    );
    
    wp_enqueue_script(
        'ask-mirror-talk',
        $theme_uri . '/ask-mirror-talk.js',
        array(),
        '2.0.0',
        true
    );
    
    // Pass API URL to JavaScript
    wp_localize_script('ask-mirror-talk', 'AskMirrorTalkConfig', array(
        'apiUrl' => 'https://ask-mirror-talk-production.up.railway.app/ask'
    ));
}
add_action('wp_enqueue_scripts', 'ask_mirror_talk_enqueue_assets');
```

### Update JavaScript to use config:

Change this line in `ask-mirror-talk.js`:
```javascript
// OLD (hardcoded):
const response = await fetch(window.ASK_MIRROR_TALK_API, {

// NEW (from PHP config):
const apiUrl = window.AskMirrorTalkConfig?.apiUrl || 'https://ask-mirror-talk-production.up.railway.app/ask';
const response = await fetch(apiUrl, {
```

**Pros:**
- ✅ Simpler - no WordPress backend logic
- ✅ Faster - one less server hop
- ✅ Easier to debug
- ✅ No nonce/session issues

**Cons:**
- ⚠️ API URL visible in page source (not a security issue for public API)
- ⚠️ CORS must be configured on Railway

---

## Option 2: WordPress AJAX Proxy (More Complex)

**Use this if:** You want to hide API URL, add server-side caching, or extra validation

### Keep: `ask-mirror-talk-v2.php` as-is

### Update JavaScript to use WordPress AJAX:

Replace the fetch call in `ask-mirror-talk.js`:

```javascript
// Instead of direct API call
const response = await fetch(window.AskMirrorTalkConfig.ajaxUrl, {
    method: "POST",
    headers: { 
        "Content-Type": "application/x-www-form-urlencoded",
    },
    body: new URLSearchParams({
        action: 'ask_mirror_talk',
        nonce: window.AskMirrorTalkConfig.nonce,
        question: question
    })
});

// Parse WordPress JSON response format
const result = await response.json();

if (!result.success) {
    throw new Error(result.data?.message || 'Request failed');
}

const data = result.data; // WordPress wraps response in { success: true, data: {...} }
```

**Pros:**
- ✅ API URL hidden from frontend
- ✅ Can add server-side caching
- ✅ Can add extra validation/rate limiting

**Cons:**
- ⚠️ More complex
- ⚠️ Slower (extra server hop)
- ⚠️ Nonce/session management required

---

## Recommendation: Go with Option 1

**Why?**
1. Your current `ask-mirror-talk.js` is already set up for direct API calls
2. Railway API is public anyway (no security benefit from hiding it)
3. Simpler = fewer things to break
4. CORS is already configured on Railway

**Steps:**
1. Use the `ask-mirror-talk-standalone.php` code above
2. Make ONE small change to `ask-mirror-talk.js`
3. Upload 3 files to WordPress
4. Done!

---

## Quick Fix for Current Setup

If you want to test right now with minimal changes:

### In `ask-mirror-talk.js`, update the fetch:

Find this section:
```javascript
const response = await fetch(window.ASK_MIRROR_TALK_API, {
```

Replace with:
```javascript
// Try config from PHP first, fallback to window variable
const apiUrl = (window.AskMirrorTalkConfig && window.AskMirrorTalkConfig.apiUrl) 
    || window.ASK_MIRROR_TALK_API 
    || 'https://ask-mirror-talk-production.up.railway.app/ask';
    
console.log('Using API URL:', apiUrl);

const response = await fetch(apiUrl, {
```

This makes it compatible with both approaches!
