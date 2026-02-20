# 🎯 WordPress Integration Quick Reference

## 📥 WHAT TO ADD TO YOUR WORDPRESS SITE

### Files to Upload:
```
✅ wordpress-widget-analytics.js  (Main tracking code)
✅ wordpress-widget-analytics.css (Styling for feedback buttons)
```

---

## 🔧 METHOD 1: Add via functions.php (RECOMMENDED)

**Edit:** `wp-content/themes/[your-theme]/functions.php`

**Add this code:**
```php
// Ask Mirror Talk Analytics Integration
function amt_enqueue_analytics() {
    // JavaScript
    wp_enqueue_script(
        'amt-analytics',
        get_template_directory_uri() . '/wordpress-widget-analytics.js',
        array(), 
        '2.0',
        true
    );
    
    // CSS
    wp_enqueue_style(
        'amt-analytics',
        get_template_directory_uri() . '/wordpress-widget-analytics.css',
        array(),
        '2.0'
    );
}
add_action('wp_enqueue_scripts', 'amt_enqueue_analytics');
```

---

## 🔧 METHOD 2: Add to Widget HTML (Alternative)

**Add in your widget/page footer:**
```html
<!-- Ask Mirror Talk Analytics -->
<script src="<?php echo get_template_directory_uri(); ?>/wordpress-widget-analytics.js"></script>
<link rel="stylesheet" href="<?php echo get_template_directory_uri(); ?>/wordpress-widget-analytics.css">
```

---

## 🔧 METHOD 3: Inline in Widget (Quick Test)

**Add directly in your widget HTML:**
```html
<script>
    // Paste entire content of wordpress-widget-analytics.js here
</script>

<style>
    /* Paste entire content of wordpress-widget-analytics.css here */
</style>
```

---

## ✅ REQUIRED HTML STRUCTURE

Your widget must have these elements (probably already exists):

```html
<!-- Question Form -->
<form id="amt-question-form">
    <textarea id="amt-question-input" placeholder="Ask your question..."></textarea>
    <button type="submit">Ask Mirror Talk</button>
</form>

<!-- Answer Container -->
<div id="amt-answer-container"></div>
```

---

## 🧪 TESTING CHECKLIST

### 1. Check JavaScript is Loaded
**Browser Console (F12):**
```
✅ Should see: "Ask Mirror Talk Analytics Tracking initialized"
❌ If errors: Check file path in functions.php
```

### 2. Test Citation Click Tracking
**Steps:**
1. Ask a question (e.g., "What is this podcast about?")
2. Click on any citation link
3. Check console for: `✅ Citation click tracked: {...}`

### 3. Test Feedback
**Steps:**
1. After receiving an answer, look for feedback buttons
2. Click "👍 Yes, helpful" or "👎 Not helpful"
3. Should see "Thank you" message
4. Check console for: `✅ Feedback submitted: positive`

---

## 🎨 WHAT USERS WILL SEE

### After They Ask a Question:
```
╔════════════════════════════════════════╗
║ Answer:                                ║
║ Mirror Talk explores...                ║
║                                        ║
║ 📚 Related Episodes (3):               ║
║ ┌──────────────────────────────────┐  ║
║ │ 1 [Episode Title]                │  ║
║ │   ⏱️ Start at 12:34              │  ║
║ │   "excerpt from episode..."      │  ║
║ └──────────────────────────────────┘  ║
║                                        ║
║ Was this answer helpful?               ║
║ [👍 Yes, helpful] [👎 Not helpful]    ║
╚════════════════════════════════════════╝
```

---

## 📊 WHERE TO SEE ANALYTICS

**Admin Dashboard:**
```
https://ask-mirror-talk-production.up.railway.app/admin
```

**What You'll See:**
- Total questions asked
- Citation clicks (how many times users clicked episode links)
- User feedback (positive/negative ratings)
- Episode performance (which episodes get clicked most)

---

## 🚨 TROUBLESHOOTING

### Problem: "Analytics not working"
**Check:**
1. Open browser console (F12)
2. Look for initialization message
3. Check Network tab for 404 errors on .js or .css files

**Fix:** Verify file paths in functions.php match actual file locations

### Problem: "Feedback buttons not showing"
**Check:**
1. CSS file is loaded (check Network tab)
2. Element exists: `document.getElementById('amt-feedback-section')`

**Fix:** Ensure CSS file is enqueued correctly

### Problem: "Clicks not tracking"
**Check:**
1. Browser console for tracking confirmation
2. Network tab for POST to `/api/citation/click`
3. CORS errors (should be none - already configured)

**Fix:** Ensure API_BASE_URL is correct in JavaScript (already set)

---

## 📞 NEED HELP?

**Quick Tests:**
```bash
# Test API is responding
curl https://ask-mirror-talk-production.up.railway.app/status

# Test analytics endpoint
curl https://ask-mirror-talk-production.up.railway.app/api/analytics/summary

# View admin dashboard
open https://ask-mirror-talk-production.up.railway.app/admin
```

**Documentation:**
- Full guide: `WORDPRESS_INTEGRATION_GUIDE.md`
- Deployment checklist: `WORDPRESS_ANALYTICS_DEPLOYMENT.md`
- Analytics summary: `ANALYTICS_COMPLETE_SUMMARY.md`

---

## ⚡ QUICK START (3 STEPS)

```bash
# 1. Upload files to your theme folder
# 2. Add code to functions.php (see METHOD 1 above)
# 3. Test on your site

# That's it! Analytics will start tracking automatically.
```

---

**API URL:** `https://ask-mirror-talk-production.up.railway.app`  
**Status:** ✅ DEPLOYED & READY  
**Last Updated:** February 20, 2026
