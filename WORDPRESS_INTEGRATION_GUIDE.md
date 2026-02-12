# 🔗 WordPress Integration Guide - WPGetAPI + Astra Theme

## 📋 Overview

This guide shows you how to connect your Railway API to your WordPress site using:
- **WPGetAPI plugin** (handles API calls)
- **Astra theme** (custom shortcode integration)

**Your API URL:** `https://ask-mirror-talk-production.up.railway.app`

---

## 🔌 Part 1: Install & Configure WPGetAPI

### Step 1: Install WPGetAPI Plugin

1. **Go to WordPress Admin:**
   - Navigate to **Plugins → Add New**
   - Search for **"WPGetAPI"**
   - Click **"Install Now"** → **"Activate"**

### Step 2: Create New API Connection

1. **Go to:** `WPGetAPI → Setup`
2. **Click:** "Add New API"
3. **Configure:**

   | Field | Value |
   |-------|-------|
   | **API Name** | `Mirror Talk Ask` |
   | **Unique ID** | `mirror_talk_ask` |
   | **Base URL** | `https://ask-mirror-talk-production.up.railway.app` |
   | **Method** | `POST` |
   | **Timeout** | `30` seconds |

4. **Click:** "Save Changes"

### Step 3: Create API Endpoint

1. **Still in WPGetAPI Setup page**
2. **Under your "Mirror Talk Ask" API, click:** "Add Endpoint"
3. **Configure:**

   | Field | Value |
   |-------|-------|
   | **Endpoint Name** | `Ask Question` |
   | **Unique ID** | `mirror_talk_ask` |
   | **Endpoint** | `/ask` |
   | **Method** | `POST` |
   | **Content-Type** | `application/json` |

4. **Headers Section:**
   - Click "Add Header"
   - **Key:** `Content-Type`
   - **Value:** `application/json`

5. **Body Format:** Select `JSON`

6. **Click:** "Save Endpoint"

### Step 4: Test the Connection

1. **In WPGetAPI:** Click "Test Endpoint"
2. **Add Test Data:**
   ```json
   {
     "question": "What is this podcast about?"
   }
   ```
3. **Click:** "Send Test Request"
4. **You should see a response like:**
   ```json
   {
     "question": "What is this podcast about?",
     "answer": "Mirror Talk is...",
     "sources": [...]
   }
   ```

✅ If you see a response, WPGetAPI is configured correctly!

---

## 🎨 Part 2: Install Astra Theme Integration

### Step 1: Upload Files via FTP/File Manager

**Upload these 3 files to:**
```
wp-content/themes/astra/
```

**Files to upload:**
1. `ask-mirror-talk.php` (shortcode handler)
2. `ask-mirror-talk.js` (frontend JavaScript)
3. `ask-mirror-talk.css` (styling)

**Using FTP:**
```
Local Path: /Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk/wordpress/astra/
Remote Path: /wp-content/themes/astra/
```

### Step 2: Enable the Shortcode in functions.php

1. **Edit:** `wp-content/themes/astra/functions.php`
2. **Add this line at the bottom:**

```php
// Ask Mirror Talk Integration
require_once get_stylesheet_directory() . '/ask-mirror-talk.php';
```

3. **Save the file**

### Step 3: Create or Edit a Page

1. **Go to:** Pages → Add New (or edit existing page)
2. **Add the shortcode anywhere in your content:**

```
[ask_mirror_talk]
```

3. **Publish/Update the page**

### Step 4: Test on Your Website

Visit the page where you added the shortcode. You should see:
- A text area for questions
- An "Ask" button
- Response and citation areas

**Try asking:** "What topics does this podcast cover?"

---

## 🔧 Part 3: Customize the Integration

### Update API URL (if needed)

If your Railway URL changes, update in 2 places:

**1. WPGetAPI Settings:**
- `WPGetAPI → Setup → Mirror Talk Ask`
- Change "Base URL"

**2. JavaScript (if using direct fetch):**
- Edit `ask-mirror-talk.js`
- Update the API URL

### Customize Styling

Edit `wp-content/themes/astra/ask-mirror-talk.css`:

```css
.ask-mirror-talk {
  max-width: 720px;
  margin: 0 auto;
  padding: 24px;
  border: 1px solid #e6e2dc;
  background: #faf8f4;
  font-family: "Source Serif 4", Georgia, serif;
}

/* Customize colors to match your site */
.ask-mirror-talk button {
  background: #2e2a24;  /* Change this */
  color: #fff;
}
```

### Add Loading States

The JavaScript already handles loading with "Thinking..." text, but you can add a spinner.

Edit `ask-mirror-talk.js` - find the line:
```javascript
output.textContent = "Thinking...";
```

Replace with:
```javascript
output.innerHTML = '<span class="spinner">🤔 Thinking...</span>';
```

---

## 📁 File Locations Summary

| File | Location | Purpose |
|------|----------|---------|
| `ask-mirror-talk.php` | `/wp-content/themes/astra/` | Shortcode handler & AJAX |
| `ask-mirror-talk.js` | `/wp-content/themes/astra/` | Frontend JavaScript |
| `ask-mirror-talk.css` | `/wp-content/themes/astra/` | Styling |
| `functions.php` | `/wp-content/themes/astra/` | Loads the shortcode |

---

## 🚀 Quick Setup Checklist

- [ ] Install WPGetAPI plugin
- [ ] Configure WPGetAPI with your Railway URL
- [ ] Test WPGetAPI connection
- [ ] Upload 3 files to Astra theme folder
- [ ] Add `require_once` line to `functions.php`
- [ ] Add `[ask_mirror_talk]` shortcode to a page
- [ ] Test the widget on your website

---

## 🔍 Troubleshooting

### Error: "We couldn't reach the service"

**Check:**
1. WPGetAPI Base URL is correct: `https://ask-mirror-talk-production.up.railway.app`
2. Endpoint is `/ask` (not `/api/ask`)
3. Method is `POST`
4. CORS is enabled in Railway for your domain

**Fix CORS (if needed):**
Add to Railway environment variables:
```
ALLOWED_ORIGINS=https://mirrortalkpodcast.com,https://www.mirrortalkpodcast.com
```

### Shortcode doesn't appear

**Check:**
1. `functions.php` has the `require_once` line
2. Files are uploaded to correct location
3. File permissions are readable (644)

### Styling looks wrong

**Check:**
1. `ask-mirror-talk.css` is uploaded
2. Clear WordPress cache (if using caching plugin)
3. Hard refresh browser (Cmd+Shift+R on Mac)

### Citations not showing

**Check API response format:**
The API should return `sources` array with:
```json
{
  "sources": [
    {
      "episode_title": "Episode Name",
      "episode_number": 1,
      "audio_url": "https://..."
    }
  ]
}
```

If your API returns different field names, update `ask-mirror-talk.js`.

---

## 🎨 Customization Examples

### Change Widget Title

Edit `ask-mirror-talk.php`, find:
```php
<h2>Ask Mirror Talk</h2>
```

Change to:
```php
<h2>Ask Us Anything</h2>
```

### Change Button Text

Edit `ask-mirror-talk.php`, find:
```php
<button type="submit">Ask</button>
```

Change to:
```php
<button type="submit">Submit Question</button>
```

### Add Placeholder Text

Edit `ask-mirror-talk.php`, find:
```php
<textarea id="ask-mirror-talk-input" rows="4" placeholder="Ask a question..."></textarea>
```

Change to:
```php
<textarea id="ask-mirror-talk-input" rows="4" placeholder="What would you like to know about the podcast?"></textarea>
```

---

## 📊 Testing Your Setup

### Test 1: Check WPGetAPI Connection

`WPGetAPI → Setup → Test Endpoint`

Should return JSON response with answer.

### Test 2: Check Page Shortcode

Visit your page with `[ask_mirror_talk]` shortcode.

Should display the widget form.

### Test 3: Submit a Question

Type: "What is this podcast about?"

Should display answer and episode references.

### Test 4: Check Browser Console

Press `F12` → Console tab

Should see no JavaScript errors.

---

## 🔐 Security Notes

1. **AJAX Nonces:** Already implemented in the PHP file
2. **Input Sanitization:** Already implemented with `sanitize_textarea_field()`
3. **CORS:** Make sure Railway ALLOWED_ORIGINS includes your domain
4. **Rate Limiting:** Railway API has rate limiting built-in

---

## 📚 Additional Resources

**WPGetAPI Documentation:**
- https://wpgetapi.com/docs/

**Astra Theme:**
- https://wpastra.com/docs/

**Railway Logs:**
- https://railway.app/dashboard (check if API calls are reaching your service)

---

## ✅ Success Indicators

After setup, you should have:

✅ WPGetAPI shows successful test connection  
✅ Shortcode renders widget on your page  
✅ Asking a question returns an answer  
✅ Episode citations appear below answer  
✅ Styling matches your site theme  

---

## 🆘 Need Help?

**Check Railway Logs:**
- Railway Dashboard → Your Service → Deployments → View Logs
- Look for POST requests to `/ask`

**Check WordPress Debug:**
Add to `wp-config.php`:
```php
define('WP_DEBUG', true);
define('WP_DEBUG_LOG', true);
```

Check `/wp-content/debug.log` for errors.

**Test API directly:**
```bash
curl -X POST "https://ask-mirror-talk-production.up.railway.app/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Test question"}'
```

---

**You're all set!** Your WordPress site can now interact with your Railway API. 🎉
