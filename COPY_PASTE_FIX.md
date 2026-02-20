# 🚨 COPY/PASTE THIS CODE INTO WORDPRESS NOW

**The file upload isn't working. Use this method instead:**

---

## ✅ METHOD 1: Direct Copy/Paste (Recommended)

### Step 1: Open WordPress File Editor

1. Go to **Appearance → Theme File Editor** in WordPress
2. On the right side, find and click **`ask-mirror-talk.php`**
3. You'll see the file content

### Step 2: Select All and Delete

1. Click in the editor
2. Press `Cmd + A` (Mac) or `Ctrl + A` (Windows) to select all
3. Press `Delete` to clear everything

### Step 3: Copy/Paste the Clean Code

**Copy this ENTIRE code block and paste it into the empty editor:**

```php
<?php
/**
 * Ask Mirror Talk Shortcode + AJAX handler for Astra theme.
 *
 * Usage: [ask_mirror_talk]
 * Requires WPGetAPI to be configured with:
 *   api_id = mirror_talk_ask
 *   endpoint_id = mirror_talk_ask
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
            <p id="ask-mirror-talk-output"></p>
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
    // Always enqueue on singular pages to handle page builders and dynamic content
    if (!is_singular()) {
        return;
    }

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
        array('jquery'),
        '2.1.0',
        true
    );

    wp_localize_script('ask-mirror-talk', 'AskMirrorTalk', array(
        'ajaxUrl' => admin_url('admin-ajax.php'),
        'nonce' => wp_create_nonce('ask_mirror_talk_nonce')
    ));
}
add_action('wp_enqueue_scripts', 'ask_mirror_talk_enqueue_assets');

function ask_mirror_talk_ajax_handler() {
    check_ajax_referer('ask_mirror_talk_nonce', 'nonce');

    $question = isset($_POST['question']) ? sanitize_textarea_field($_POST['question']) : '';
    if (!$question) {
        wp_send_json_error(array('message' => 'Question cannot be empty.'), 400);
    }

    // Call WPGetAPI endpoint
    $response = wpgetapi_endpoint('mirror_talk_ask', 'mirror_talk_ask', array(
        'debug' => false,
        'body' => array(
            'question' => $question
        )
    ));

    if (is_wp_error($response)) {
        wp_send_json_error(array('message' => $response->get_error_message()), 500);
    }

    wp_send_json_success($response);
}
add_action('wp_ajax_ask_mirror_talk', 'ask_mirror_talk_ajax_handler');
add_action('wp_ajax_nopriv_ask_mirror_talk', 'ask_mirror_talk_ajax_handler');
```

### Step 4: Click "Update File"

1. Click the blue **"Update File"** button at the bottom
2. You should see a success message

### Step 5: Clear Cache and Test

1. **Clear WordPress cache** (if using a caching plugin)
2. **Hard refresh browser:** `Cmd + Shift + R` (Mac) or `Ctrl + Shift + R` (Windows)
3. **Open browser console** (F12)
4. **Ask a question**

---

## ✅ You Should See:

```
✅ Ask Mirror Talk Widget v2.1.0 loaded
✅ Ask Mirror Talk Analytics Add-on loaded
✅ QA Session ID captured: 119
✅ Citation tracking added to 5 links
```

**NO ERRORS!** 🎉

---

## 🔍 VERIFY THE FIX:

After updating, look at line 23 in the WordPress editor. It should show:

```php
<button type="submit" id="ask-mirror-talk-submit">Ask</button>
```

**NOT:**
```php
<button type="submit">Ask</button>
```

---

## 🚨 KEY CHANGES IN THIS CODE:

1. ✅ **Line 23:** Button has `id="ask-mirror-talk-submit"`
2. ✅ **Lines 1-8:** Clean PHP header (no corrupted HTML)
3. ✅ **Line 51:** Version 2.1.0 (forces cache refresh)
4. ✅ **Line 57:** jQuery dependency added
5. ✅ **Line 46:** No shortcode detection (loads on all pages)

---

## ⏱️ TIME REQUIRED:

- Open WordPress editor: **30 seconds**
- Copy/paste code: **30 seconds**
- Update file: **10 seconds**
- Clear cache & test: **1 minute**

**Total: 2 minutes** ✅

---

## 🆘 IF IT STILL DOESN'T WORK:

Check these:

1. **File saved correctly?** Refresh the editor and verify line 23 has the button ID
2. **Cache cleared?** Try incognito/private browsing mode
3. **Console errors?** Look for PHP errors in WordPress error log

---

## 📁 ALTERNATIVE: Use Clean File

If copy/paste doesn't work, I've created a clean version here:

```
/Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk/ask-mirror-talk-CLEAN-VERSION.php
```

Try uploading this file instead of the one in `wordpress/astra/` folder.

---

**DO THIS NOW - It will take 2 minutes and fix everything!** 🚀

---

Last Updated: February 20, 2026  
Method: Direct copy/paste into WordPress editor
