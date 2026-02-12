# 🚨 WPGetAPI Error Fix Guide

## Problem Identified

WPGetAPI is sending:
```json
{"question":"{{question}}"}
```

Instead of:
```json
{"question":"What is this podcast about?"}
```

The `{{question}}` placeholder is not being replaced with the actual question.

---

## 🔧 Fix #1: Update WPGetAPI Endpoint Configuration

### Step 1: Check Your WPGetAPI Endpoint Setup

1. **Go to:** `WPGetAPI → Setup → Your API → Endpoints`
2. **Find:** Your "Ask Question" endpoint
3. **Check the Body/Query String section**

### Step 2: Configure the Body Correctly

WPGetAPI has different ways to pass parameters. Try these options:

#### Option A: Use Query String Format

**In WPGetAPI Endpoint Settings:**

**Query String:** (instead of Body)
```
question={{question}}
```

**Method:** Keep as `POST`

#### Option B: Use Dynamic Body Variables

**In WPGetAPI Endpoint Settings:**

**Body Format:** `JSON`

**Body Content:**
```json
{
  "question": "{{query_string:question}}"
}
```

This tells WPGetAPI to get the `question` value from the query parameters.

---

## 🔧 Fix #2: Update PHP Code to Pass Variables Correctly

The issue is in how your PHP code calls WPGetAPI. Let me update the file:

### Update ask-mirror-talk.php

The current code needs to pass the question as a query parameter, not in the body.

**Change this:**
```php
$response = wpgetapi_endpoint('mirror_talk_ask', 'mirror_talk_ask', array(
    'debug' => false,
    'body' => array(
        'question' => $question
    )
));
```

**To this:**
```php
$response = wpgetapi_endpoint(
    'mirror_talk_ask',        // API ID
    'mirror_talk_ask',        // Endpoint ID
    array(
        'question' => $question  // This becomes a query parameter
    )
);
```

---

## 🔧 Fix #3: Alternative - Bypass WPGetAPI, Use Direct wp_remote_post()

If WPGetAPI continues to give issues, bypass it completely:

### Updated ask-mirror-talk.php (Direct API Call)

Replace the AJAX handler function:

```php
function ask_mirror_talk_ajax_handler() {
    check_ajax_referer('ask_mirror_talk_nonce', 'nonce');

    $question = isset($_POST['question']) ? sanitize_textarea_field($_POST['question']) : '';
    if (!$question) {
        wp_send_json_error(array('message' => 'Question cannot be empty.'), 400);
    }

    // Direct API call without WPGetAPI
    $api_url = 'https://ask-mirror-talk-production.up.railway.app/ask';
    
    $response = wp_remote_post($api_url, array(
        'timeout' => 30,
        'headers' => array(
            'Content-Type' => 'application/json',
        ),
        'body' => json_encode(array(
            'question' => $question
        ))
    ));

    if (is_wp_error($response)) {
        wp_send_json_error(array('message' => $response->get_error_message()), 500);
    }

    $response_code = wp_remote_retrieve_response_code($response);
    $response_body = wp_remote_retrieve_body($response);

    if ($response_code !== 200) {
        wp_send_json_error(array('message' => 'API returned error: ' . $response_body), $response_code);
    }

    $data = json_decode($response_body, true);
    
    if (json_last_error() !== JSON_ERROR_NONE) {
        wp_send_json_error(array('message' => 'Invalid JSON response'), 500);
    }

    wp_send_json_success($data);
}
add_action('wp_ajax_ask_mirror_talk', 'ask_mirror_talk_ajax_handler');
add_action('wp_ajax_nopriv_ask_mirror_talk', 'ask_mirror_talk_ajax_handler');
```

---

## 🧪 Test the API Directly First

Before testing through WordPress, verify the API works:

```bash
curl -X POST "https://ask-mirror-talk-production.up.railway.app/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this podcast about?"}'
```

**Expected Response:**
```json
{
  "question": "What is this podcast about?",
  "answer": "...",
  "sources": [...]
}
```

If this fails, the issue is with the Railway API, not WordPress.

---

## 🔍 Check Railway Logs

The "Internal Server Error" means the Railway API crashed. Check logs:

1. **Go to:** Railway Dashboard → Your Service → Deployments
2. **Click:** Latest deployment → "View Logs"
3. **Look for:** Error messages around the timestamp: `Thu, 12 Feb 2026 20:59:02 GMT`

Common errors:
- Missing ML models (embeddings not loaded)
- Database connection timeout
- Out of memory
- Missing environment variables

---

## 📝 Quick Fix Steps (In Order)

### 1. Test API Directly (Terminal)
```bash
curl -X POST "https://ask-mirror-talk-production.up.railway.app/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "test"}'
```

### 2. If API Test Works:
Problem is in WPGetAPI configuration.

**Fix:** Use Fix #3 (bypass WPGetAPI, use direct `wp_remote_post()`)

### 3. If API Test Fails:
Problem is in Railway.

**Fix:** Check Railway logs for the actual error.

---

## 🛠️ Recommended Solution

**Use Fix #3 (Direct API Call)** - This is more reliable and doesn't depend on WPGetAPI's template system.

### Files to Update:

**File:** `/wp-content/themes/astra/ask-mirror-talk.php`

**Replace the `ask_mirror_talk_ajax_handler` function** with the code from Fix #3 above.

**Benefits:**
- ✅ No WPGetAPI dependency
- ✅ Full control over request format
- ✅ Better error handling
- ✅ Easier debugging

---

## 🎯 Action Items

1. **Test API directly** (curl command above)
2. **Check Railway logs** for actual error
3. **Update PHP file** with Fix #3 (direct API call)
4. **Clear WordPress cache** (if using caching plugin)
5. **Test from WordPress** widget

---

## 📊 Debugging Checklist

- [ ] API responds to curl test
- [ ] Railway logs show request received
- [ ] Database has episodes loaded (at least 3)
- [ ] CORS allows your domain
- [ ] PHP file updated with direct API call
- [ ] WordPress debug.log shows no PHP errors
- [ ] Browser console shows no JavaScript errors

---

## 🆘 If Still Not Working

**Share with me:**
1. Result of curl test (direct API call)
2. Railway logs from the error timestamp
3. WordPress debug.log errors

This will help identify if it's:
- API issue (Railway/Database)
- WordPress issue (PHP/WPGetAPI)
- Network issue (CORS/Firewall)

---

**Most Likely Fix:** Use direct `wp_remote_post()` instead of WPGetAPI (Fix #3)
