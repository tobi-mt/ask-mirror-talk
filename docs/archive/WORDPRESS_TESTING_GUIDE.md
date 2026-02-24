# WordPress Widget Testing Guide

**Version 2.0.0** - Updated for UX improvements and deduplication

---

## Quick Start

### 1. Upload Updated Files to WordPress

Upload these files to your WordPress theme directory:

**Files to Upload:**
```
wordpress/astra/ask-mirror-talk-v2.php  → /wp-content/themes/astra/ask-mirror-talk-v2.php
wordpress/astra/ask-mirror-talk.js      → /wp-content/themes/astra/ask-mirror-talk.js
wordpress/astra/ask-mirror-talk.css     → /wp-content/themes/astra/ask-mirror-talk.css
```

**Upload Methods:**
- FTP/SFTP client (FileZilla, Cyberduck)
- WordPress admin → Appearance → Theme File Editor
- cPanel File Manager
- SSH/SCP

---

## 2. Activate the Shortcode

### Option A: In functions.php

Add this to your theme's `functions.php`:

```php
require_once get_stylesheet_directory() . '/ask-mirror-talk-v2.php';
```

### Option B: As a Plugin

1. Create folder: `/wp-content/plugins/ask-mirror-talk/`
2. Create file: `ask-mirror-talk.php` with:

```php
<?php
/**
 * Plugin Name: Ask Mirror Talk
 * Description: AI-powered Q&A widget for Mirror Talk Podcast
 * Version: 2.0.0
 * Author: Your Name
 */

require_once plugin_dir_path(__FILE__) . 'ask-mirror-talk-v2.php';
```

3. Upload `ask-mirror-talk-v2.php`, `.js`, and `.css` to this folder
4. Activate plugin in WordPress admin

---

## 3. Add to a Page

Edit any page/post and add:

```
[ask_mirror_talk]
```

**Best locations:**
- Dedicated "Ask Questions" page
- Bottom of About page
- Sidebar widget
- Footer area

---

## 4. Verify Installation

### Check Files Loaded

1. Visit the page with `[ask_mirror_talk]`
2. Open browser DevTools (F12 or Cmd+Option+I)
3. Go to **Network** tab
4. Refresh page
5. Look for:
   - ✅ `ask-mirror-talk.js?v=2.0.0` (Status: 200)
   - ✅ `ask-mirror-talk.css?v=2.0.0` (Status: 200)

### Check Console

1. Open browser **Console** tab
2. Look for: `Ask Mirror Talk Widget v2.0.0 loaded`
3. No errors in red

### Check HTML

1. Right-click page → View Source
2. Search for: `ask-mirror-talk`
3. Should see:
   ```html
   <div class="ask-mirror-talk">
   ```

---

## 5. Test Functionality

### Test 1: Submit a Question

1. Type a question: "What is alignment?"
2. Click "Ask"
3. **Expected:**
   - Button disables and shows "Loading..."
   - Response appears after 3-5 seconds
   - Citations show below with clickable links
   - Button re-enables

### Test 2: Check Response Quality

**Good Response:**
- ✅ Warm, conversational tone
- ✅ Complete sentences
- ✅ Well-formatted (paragraphs, bold text)
- ✅ 2-4 paragraphs minimum
- ✅ Feels natural, not robotic

**Bad Response (indicates issue):**
- ❌ Short, generic answer
- ❌ Incomplete sentences ("And I...", "So, I don't...")
- ❌ No formatting
- ❌ "I could not find anything" (too few episodes loaded)

### Test 3: Verify Citations

1. Check citations list below answer
2. Each citation should have:
   - ✅ Episode title
   - ✅ Timestamp (e.g., "0:12:34")
   - ✅ Clickable link
   - ✅ Unique episodes (no duplicates)

3. Click a citation link:
   - ✅ Opens episode page/player
   - ✅ Jumps to correct timestamp
   - ✅ URL has `#t=seconds` format

### Test 4: Error Handling

1. Try submitting empty question
   - **Expected:** Error message or disabled button
   
2. Disconnect internet, submit question
   - **Expected:** User-friendly error message
   
3. Submit very long question (500+ chars)
   - **Expected:** Works or shows character limit

---

## 6. Browser Testing

Test in all major browsers:

### Desktop
- [ ] Chrome (latest)
- [ ] Safari (latest)
- [ ] Firefox (latest)
- [ ] Edge (latest)

### Mobile
- [ ] Safari iOS
- [ ] Chrome Android
- [ ] Firefox Mobile

**What to Check:**
- Widget displays correctly
- Text input works
- Button clicks work
- Citations are readable
- Links are clickable
- Responsive layout

---

## 7. Troubleshooting

### Issue: Widget Not Showing

**Check:**
1. Shortcode is correct: `[ask_mirror_talk]` (no spaces)
2. PHP file is loaded in functions.php or as plugin
3. Files are in correct directory
4. Theme is active

**Debug:**
```php
// Add to functions.php temporarily
add_action('wp_footer', function() {
    if (shortcode_exists('ask_mirror_talk')) {
        echo '<!-- Ask Mirror Talk shortcode registered -->';
    } else {
        echo '<!-- Ask Mirror Talk shortcode NOT registered -->';
    }
});
```

### Issue: JS/CSS Not Loading

**Check:**
1. File paths are correct in PHP
2. Files have correct permissions (644)
3. Browser cache is cleared (Cmd+Shift+R)
4. Version number is updated

**Debug:**
```javascript
// Open browser console
console.log(window.ASK_MIRROR_TALK_VERSION); 
// Should show: "2.0.0"
```

### Issue: "Loading Failed" Error

**Check:**
1. API URL is correct in JS
2. Railway service is running
3. CORS is configured for your domain
4. No browser console errors

**Test API directly:**
```bash
curl -X POST https://ask-mirror-talk-production.up.railway.app/ask \
  -H "Content-Type: application/json" \
  -H "Origin: https://mirrortalkpodcast.com" \
  -d '{"question": "test"}'
```

### Issue: AJAX Errors

**Check browser console for:**
- 403 Forbidden → CORS issue (check ALLOWED_ORIGINS)
- 404 Not Found → Wrong API URL
- 500 Server Error → Check Railway logs
- CORS error → Domain not in allowed origins

**Fix CORS:**
1. Go to Railway → Variables
2. Check `ALLOWED_ORIGINS` includes your domain
3. Format: `https://mirrortalkpodcast.com,https://www.mirrortalkpodcast.com`
4. Restart service

### Issue: Old Version Showing

**Clear cache:**
1. Hard refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
2. Clear browser cache
3. Use incognito/private window
4. Bump version to 2.0.1 and re-upload

---

## 8. Performance Optimization

### Caching

Add to WordPress (wp-config.php or via plugin):

```php
// Don't cache the Ask widget
define('DONOTCACHEPAGE', true);
```

Or exclude from cache plugins:
- WP Super Cache: Add `/ask-questions/` to exceptions
- W3 Total Cache: Exclude page with widget
- Cloudflare: Page Rules → Bypass Cache

### Loading

Consider lazy loading if widget is below fold:

```php
// Only load on specific pages
function ask_mirror_talk_enqueue_assets() {
    if (is_page('ask-questions')) {  // Only on "Ask Questions" page
        // ...enqueue scripts
    }
}
```

---

## 9. Styling Customization

### Custom CSS

Add to WordPress Customizer → Additional CSS:

```css
/* Customize widget appearance */
.ask-mirror-talk {
    max-width: 800px;
    margin: 2rem auto;
    padding: 2rem;
    background: #f9f9f9;
    border-radius: 12px;
}

.ask-mirror-talk h2 {
    color: #333;
    font-size: 2rem;
}

#ask-mirror-talk-input {
    width: 100%;
    padding: 1rem;
    border: 2px solid #ddd;
    border-radius: 8px;
    font-size: 1rem;
}

#ask-mirror-talk-submit {
    background: #0066cc;
    color: white;
    padding: 1rem 2rem;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 1rem;
}

#ask-mirror-talk-submit:hover {
    background: #0052a3;
}

#ask-mirror-talk-submit:disabled {
    background: #ccc;
    cursor: not-allowed;
}

/* Citations */
.ask-mirror-talk-citations {
    margin-top: 2rem;
}

.ask-mirror-talk-citations li {
    margin-bottom: 1rem;
    padding: 1rem;
    background: white;
    border-left: 4px solid #0066cc;
    border-radius: 4px;
}

.ask-mirror-talk-citations a {
    color: #0066cc;
    text-decoration: none;
}

.ask-mirror-talk-citations a:hover {
    text-decoration: underline;
}
```

---

## 10. Monitoring & Analytics

### Track Usage

Add to Google Analytics (if installed):

```javascript
// Add to ask-mirror-talk.js
form.addEventListener("submit", async (e) => {
    // Track question submission
    if (typeof gtag !== 'undefined') {
        gtag('event', 'ask_question', {
            'event_category': 'engagement',
            'event_label': 'mirror_talk_widget'
        });
    }
    
    // ...existing code...
});
```

### Log Errors

```javascript
// Add to ask-mirror-talk.js error handling
catch (error) {
    // Log to analytics
    if (typeof gtag !== 'undefined') {
        gtag('event', 'exception', {
            'description': error.message,
            'fatal': false
        });
    }
    
    // ...existing error handling...
}
```

---

## 11. Version History

### Version 2.0.0 (Current)
- ✅ Improved error handling and loading states
- ✅ Episode deduplication in citations
- ✅ Accurate timestamps with #t=seconds format
- ✅ Better AI responses (warm, empathetic, intelligent)
- ✅ Cache-busting with version parameters
- ✅ Console logging for debugging

### Version 1.0.1
- ✅ Basic functionality
- ✅ AJAX integration
- ✅ Citation rendering

---

## 12. Support & Resources

**Documentation:**
- `NEXT_STEPS_GUIDE.md` - Overall project status
- `UX_AI_IMPROVEMENTS_COMPLETE.md` - Recent improvements
- `DEPLOY_NOW.md` - Railway deployment

**Health Check:**
```bash
./scripts/health_check.sh
```

**API Logs:**
```bash
railway logs --tail
```

**Contact:**
- Check Railway dashboard for API status
- Review browser console for client-side errors
- Test API directly with curl before debugging WordPress

---

## ✅ Success Checklist

Before marking as complete:

- [ ] Files uploaded to WordPress
- [ ] Shortcode activated
- [ ] Widget appears on page
- [ ] JS/CSS load with version 2.0.0
- [ ] Console shows "Widget v2.0.0 loaded"
- [ ] Questions submit successfully
- [ ] Responses are warm and conversational
- [ ] Citations show unique episodes
- [ ] Timestamp links work correctly
- [ ] Tested in Chrome, Safari, Firefox
- [ ] Tested on mobile devices
- [ ] Error handling works properly
- [ ] No console errors

---

**You're all set! 🎉** The widget should now provide a great user experience with intelligent, soulful AI responses.
