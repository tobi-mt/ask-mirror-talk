# 🔧 ANALYTICS INTEGRATION FIX - Two Conflicting Scripts

## 🔍 PROBLEM IDENTIFIED

From your browser console, I can see you have **TWO JavaScript files** running:

1. ✅ `ask-mirror-talk.js` (v2.1.0) - Your original widget
2. ✅ `wordpress-widget-analytics.js` - The new analytics code

**Issue:** They're both trying to handle the same form, causing conflicts.

---

## ✅ SOLUTION: Choose ONE of These Options

### **OPTION 1: Simple Add-on (RECOMMENDED - Easiest)**

Keep your current working widget and just add analytics tracking.

#### Steps:

1. **Upload the new file** `analytics-addon.js` to your WordPress theme folder

2. **Add this to your `functions.php`:**

```php
// Add analytics tracking to existing widget
function amt_add_analytics_tracking() {
    wp_enqueue_script(
        'amt-analytics-addon',
        get_template_directory_uri() . '/analytics-addon.js',
        array('amt-widget'), // Load after your main widget script
        '2.0',
        true
    );
}
add_action('wp_enqueue_scripts', 'amt_add_analytics_tracking');
```

3. **Add `data-episode-id` attributes to your citation HTML:**

In your citation rendering code, make sure each citation link has the episode ID:

```html
<a href="..." data-episode-id="77" data-timestamp="683" class="citation-link">
    Episode Title
</a>
```

4. **Test:**
   - Ask a question
   - Console should show: `✅ QA Session ID captured: 117`
   - Click a citation
   - Console should show: `✅ Citation click tracked: {episodeId: 77, ...}`
   - Feedback buttons should appear
   - Click feedback
   - Console should show: `✅ Feedback submitted: positive`

---

### **OPTION 2: Replace Existing Widget (More Work)**

Replace your current `ask-mirror-talk.js` with the analytics-enabled version.

#### Steps:

1. **In `functions.php`, REMOVE the old script enqueue:**

```php
// REMOVE or COMMENT OUT:
// wp_enqueue_script('amt-widget', get_template_directory_uri() . '/ask-mirror-talk.js', ...);
```

2. **Add the analytics script instead:**

```php
// NEW: Analytics-enabled widget
function amt_enqueue_analytics() {
    wp_enqueue_script(
        'amt-analytics',
        get_template_directory_uri() . '/wordpress-widget-analytics.js',
        array(),
        '2.0',
        true
    );
    
    wp_enqueue_style(
        'amt-analytics',
        get_template_directory_uri() . '/wordpress-widget-analytics.css',
        array(),
        '2.0'
    );
}
add_action('wp_enqueue_scripts', 'amt_enqueue_analytics');
```

3. **Update your HTML to match the required structure:**

```html
<form id="amt-question-form">
    <textarea id="amt-question-input" placeholder="Ask a question..."></textarea>
    <button type="submit">Ask</button>
</form>

<div id="amt-answer-container"></div>
```

4. **Test thoroughly** - your widget will use the new code entirely

---

## 🎯 MY RECOMMENDATION: Use Option 1

**Why:**
- ✅ Your current widget is working perfectly
- ✅ Minimal changes needed
- ✅ Lower risk of breaking things
- ✅ Just adds tracking on top

**All you need to do:**

1. Upload `analytics-addon.js` (I created this file for you)
2. Add 10 lines to `functions.php`
3. Make sure your citation links have `data-episode-id` attribute
4. Test and verify tracking works

---

## 📊 ABOUT THE "IMPROVED REFERENCED EPISODES"

**Your question:** "The improved referenced episodes does not seem to be working"

**Answer:** The improved citations ARE working! Look at your console logs:

```
[Log] Citations rendered successfully
Citation 1: Breaking the Stigma of Autism with Sam Mitchell
Citation 2: From Barefoot Backpacker to Conscious Leader
Citation 3: JayMikee's 2 Most POWERFUL Pieces of Advice
Citation 4: The Ripple Effect
Citation 5: Rewiring Your Life
```

**You got 5 DIVERSE episodes** (not the same episode repeated). This is the MMR diversity algorithm working! ✅

**What makes them "improved":**
- ✅ Different episodes (diversity = 30%)
- ✅ Relevant to "addiction" topic
- ✅ No duplicates
- ✅ Timestamps included

**How it will get EVEN BETTER:**
Once users start clicking citations and giving feedback, the system will learn which episodes are most helpful and prioritize them for similar questions.

**This happens automatically** - no action needed from you!

---

## 🔍 TESTING CHECKLIST

After implementing Option 1:

### Test 1: QA Log ID Capture
- [ ] Ask a question
- [ ] Check console for: `✅ QA Session ID captured: [number]`

### Test 2: Citation Click Tracking
- [ ] Click on a citation link
- [ ] Check console for: `✅ Citation click tracked: {...}`
- [ ] Link should still work normally (open episode)

### Test 3: Feedback Buttons
- [ ] After answer appears, look for feedback section
- [ ] Should see "Was this answer helpful?"
- [ ] Should see 👍 and 👎 buttons

### Test 4: Feedback Submission
- [ ] Click one of the feedback buttons
- [ ] Check console for: `✅ Feedback submitted: positive/negative`
- [ ] Should see "Thank you" message

### Test 5: Admin Dashboard
- [ ] Visit: `https://ask-mirror-talk-production.up.railway.app/admin`
- [ ] Check "Citation Clicks" count increased
- [ ] Check "User Feedback" count increased

---

## 🚨 IMPORTANT: Add data-episode-id to Citations

For tracking to work, your citation HTML needs the `data-episode-id` attribute.

**Check your current citation rendering code** (probably in `ask-mirror-talk.js` around line 197):

**Current code might look like:**
```javascript
citationHTML += `
    <a href="${citation.episode_url}">
        ${citation.episode_title}
    </a>
`;
```

**Change to:**
```javascript
citationHTML += `
    <a href="${citation.episode_url}" 
       data-episode-id="${citation.episode_id}"
       data-timestamp="${citation.timestamp_start_seconds}"
       class="citation-link">
        ${citation.episode_title}
    </a>
`;
```

**Why:** This tells the tracking code which episode was clicked.

---

## 📝 FILES YOU NEED

### For Option 1 (Recommended):
- ✅ `analytics-addon.js` (created - ready to upload)
- ✅ Add 10 lines to `functions.php`
- ✅ Update citation HTML to include `data-episode-id`

### For Option 2 (Alternative):
- ✅ `wordpress-widget-analytics.js` (already exists)
- ✅ `wordpress-widget-analytics.css` (already exists)
- ✅ Replace old script in `functions.php`
- ✅ Update HTML structure

---

## 🎉 WHAT YOU'LL SEE WHEN IT WORKS

### Console Logs:
```
✅ Ask Mirror Talk Analytics Add-on loaded
✅ QA Session ID captured: 117
✅ Citation tracking added to 5 links
✅ Feedback buttons added
✅ Citation click tracked: {episodeId: 77, timestamp: 683}
✅ Feedback submitted: positive
```

### On the Page:
- Questions/answers work normally ✅
- After answer, feedback buttons appear ✅
- When clicking citation, link works + tracking happens silently ✅
- After feedback click, "Thank you" message appears ✅

### In Admin Dashboard:
- Citation clicks increase ✅
- Feedback count increases ✅
- Episode analytics show which episodes get clicked ✅

---

## 🆘 NEED HELP?

**Share with me:**
1. Which option you choose (1 or 2)
2. Screenshot of your citation HTML (from browser inspector)
3. Console errors (if any)
4. What happens when you click a citation

---

**Files Location:**
```
/Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk/
├── analytics-addon.js                  ← Upload this (Option 1)
├── wordpress-widget-analytics.js       ← OR this (Option 2)
└── wordpress-widget-analytics.css      ← AND this (Option 2)
```

**Recommendation:** Start with Option 1 - it's the easiest!

---

Last Updated: February 20, 2026  
Status: ⚠️ Two Scripts Conflicting → Choose One Approach
