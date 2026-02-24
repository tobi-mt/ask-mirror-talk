# 🚀 Quick Start: WPGetAPI Setup

## 📝 WPGetAPI Configuration (Copy & Paste)

### API Setup

**Go to:** `WPGetAPI → Setup → Add New API`

| Field | Value |
|-------|-------|
| **API Name** | Mirror Talk Ask |
| **Unique ID** | `mirror_talk_ask` |
| **Base URL** | `https://ask-mirror-talk-production.up.railway.app` |
| **Method** | POST |
| **Timeout** | 30 |

---

### Endpoint Setup

**Under your API, click:** "Add Endpoint"

| Field | Value |
|-------|-------|
| **Endpoint Name** | Ask Question |
| **Unique ID** | `mirror_talk_ask` |
| **Endpoint** | `/ask` |
| **Method** | POST |

**Headers:**
- Key: `Content-Type`
- Value: `application/json`

**Body Format:** JSON

---

### Test Request

**Test Data:**
```json
{
  "question": "What is this podcast about?"
}
```

**Expected Response:**
```json
{
  "question": "What is this podcast about?",
  "answer": "Mirror Talk is a podcast that...",
  "sources": [
    {
      "episode_title": "Episode Name",
      "episode_number": 1
    }
  ]
}
```

---

## 📂 Astra Theme Setup

### 1. Upload Files (via FTP/cPanel)

Upload to: `/wp-content/themes/astra/`

**Files:**
- `ask-mirror-talk.php`
- `ask-mirror-talk.js`  
- `ask-mirror-talk.css`

**Location on your computer:**
```
/Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk/wordpress/astra/
```

### 2. Edit functions.php

**File:** `/wp-content/themes/astra/functions.php`

**Add at the bottom:**
```php
// Ask Mirror Talk Integration
require_once get_stylesheet_directory() . '/ask-mirror-talk.php';
```

### 3. Use the Shortcode

**In any page or post:**
```
[ask_mirror_talk]
```

---

## ✅ Verification Checklist

- [ ] WPGetAPI plugin installed and activated
- [ ] API configured with Railway URL
- [ ] Endpoint test returns valid JSON
- [ ] 3 files uploaded to Astra theme folder
- [ ] `functions.php` updated with `require_once` line
- [ ] Shortcode added to a page
- [ ] Widget appears on the page
- [ ] Test question returns an answer

---

## 🔧 Quick Fixes

### Widget not appearing?
- Check `functions.php` has the `require_once` line
- Verify files are in `/wp-content/themes/astra/`
- Clear WordPress cache

### API errors?
- Verify WPGetAPI Base URL: `https://ask-mirror-talk-production.up.railway.app`
- Check endpoint is `/ask` (not `/api/ask`)
- Ensure CORS includes your domain in Railway

### No response?
- Test API directly:
  ```bash
  curl -X POST "https://ask-mirror-talk-production.up.railway.app/ask" \
    -H "Content-Type: application/json" \
    -d '{"question": "test"}'
  ```

---

## 🎯 Your Railway API Details

**Base URL:** `https://ask-mirror-talk-production.up.railway.app`  
**Endpoint:** `/ask`  
**Method:** POST  
**Content-Type:** application/json  

**Allowed Origins (already configured):**
- https://mirrortalkpodcast.com
- https://www.mirrortalkpodcast.com

---

**That's it!** Your WordPress site will be connected to your Railway API. 🚀

See **WORDPRESS_INTEGRATION_GUIDE.md** for detailed instructions.
