# Testing Guide for Both Fixes

## Test Cases for Verification

### Test 1: CORS Fix - Multiple Browsers

**Objective:** Verify 403 errors are resolved across all browsers

**Test Questions:**
1. "What is emotional intelligence?"
2. "How do I handle difficult conversations?"
3. "What does Mirror Talk say about self-reflection?"

**Browser Matrix:**

| Browser | Device | Test | Expected | Status |
|---------|--------|------|----------|--------|
| Chrome (Desktop) | Windows/Mac | Ask question | ✅ Success, no 403 | ☐ |
| Safari (Desktop) | Mac | Ask question | ✅ Success, no 403 | ☐ |
| Firefox (Desktop) | Windows/Mac/Linux | Ask question | ✅ Success, no 403 | ☐ |
| Edge (Desktop) | Windows | Ask question | ✅ Success, no 403 | ☐ |
| Safari (Mobile) | iOS | Ask question | ✅ Success, no 403 | ☐ |
| Chrome (Mobile) | Android | Ask question | ✅ Success, no 403 | ☐ |

**How to Test:**
1. Open browser/device
2. Navigate to your page with widget
3. Open DevTools (F12 or browser console)
4. Ask a test question
5. Check Network tab for response status
6. **Expected:** Status 200, no CORS errors in console

**What to Look For:**
- ✅ **Success:** Answer displays, no red errors in console
- ❌ **Failure:** 403 status, CORS policy error, "Failed to fetch"

**Console Commands to Verify:**
```javascript
// Should see this in Network tab:
// POST https://ask-mirror-talk-production.up.railway.app/ask
// Status: 200
// Response Headers should include:
// Access-Control-Allow-Origin: https://mirrortalkpodcast.com
// Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
```

---

### Test 2: Markdown Rendering - Bold Text

**Objective:** Verify `**bold**` renders as **bold**, not literal asterisks

**Test Question:**
"What are the key principles of personal growth?"

**Expected Response Format:**
```
Based on the Mirror Talk episodes:

**Key Principle 1**: Self-awareness is the foundation
Mirror Talk emphasizes that understanding yourself is crucial...

**Key Principle 2**: Consistent practice matters
Personal growth requires daily commitment...
```

**Visual Verification:**

| Element | Before Fix | After Fix | Status |
|---------|-----------|-----------|--------|
| Bold text | `**Key Principle 1**` | **Key Principle 1** | ☐ |
| Regular text | Understanding yourself... | Understanding yourself... | ☐ |
| HTML structure | Plain text | `<strong>` tags | ☐ |

**How to Test:**
1. Ask the question above
2. Wait for response
3. **Visual Check:** Does text look bold?
4. **HTML Check:** Right-click answer → Inspect Element
5. **Expected:** See `<strong>Key Principle 1</strong>` in HTML

**Console Verification:**
```javascript
// After answer is displayed, run in console:
document.querySelector('#ask-mirror-talk-output strong');
// Should return: <strong>Key Principle 1</strong> (or similar)

// If this returns null, markdown isn't being converted:
document.querySelector('#ask-mirror-talk-output').innerHTML;
// Should see <strong> tags, NOT **text**
```

---

### Test 3: Markdown Rendering - Lists

**Objective:** Verify numbered and bullet lists render properly

**Test Questions:**

**For Numbered Lists:**
"What are the steps to better self-awareness?"

**Expected Response:**
```
Mirror Talk discusses these steps:

1. **Daily reflection**: Set aside time each day
2. **Honest self-assessment**: Ask difficult questions
3. **Seek feedback**: Listen to others' perspectives
```

**For Bullet Lists:**
"What emotions come up in difficult conversations?"

**Expected Response:**
```
According to Mirror Talk:

- **Fear**: Often the primary emotion
- **Anger**: A secondary response
- **Sadness**: Underlying hurt feelings
```

**Visual Verification:**

| Element | Before Fix | After Fix | Status |
|---------|-----------|-----------|--------|
| Numbered list | `1. Daily reflection` | 1. Daily reflection | ☐ |
| Bullet list | `- Fear` | • Fear | ☐ |
| List indentation | No indent | Proper indent | ☐ |
| Bold in list | `**Fear**:` | **Fear**: | ☐ |

**HTML Structure Check:**
```javascript
// Should see proper HTML list structure:
document.querySelector('#ask-mirror-talk-output ol');
// Returns: <ol><li>Daily reflection: Set aside time...</li>...</ol>

document.querySelector('#ask-mirror-talk-output ul');
// Returns: <ul><li><strong>Fear</strong>: Often the primary emotion</li>...</ul>
```

---

### Test 4: Markdown Rendering - Mixed Formatting

**Objective:** Verify complex markdown with multiple formatting types

**Test Question:**
"Tell me about emotional intelligence and self-awareness"

**Expected Response Format:**
```
**Emotional Intelligence** is a core theme in Mirror Talk:

1. **Self-Awareness**: The foundation
   - Understanding your emotions
   - Recognizing patterns

2. **Self-Regulation**: Managing responses
   - *Pause before reacting*
   - Choose thoughtful responses

The podcast emphasizes that **consistency** is key.
```

**What to Verify:**

| Element | Check | Status |
|---------|-------|--------|
| Bold headings | **Emotional Intelligence** renders bold | ☐ |
| Numbered lists | 1, 2 with proper formatting | ☐ |
| Nested bullets | Sub-items with bullets | ☐ |
| Italic text | *Pause before reacting* renders italic | ☐ |
| Inline bold | **consistency** in paragraph renders bold | ☐ |

---

### Test 5: Cross-Origin Verification (CORS)

**Objective:** Verify CORS works from different subdomains

**Test Scenarios:**

| Origin | Expected | Status |
|--------|----------|--------|
| `https://mirrortalkpodcast.com` | ✅ Works | ☐ |
| `https://www.mirrortalkpodcast.com` | ✅ Works | ☐ |
| `http://localhost` (dev) | ✅ Works (if `ALLOWED_ORIGINS` not set) | ☐ |

**How to Test:**
1. Visit each domain variant
2. Test widget on each
3. Check for CORS errors
4. **Expected:** All variants work without 403

**Network Tab Verification:**
```
Request URL: https://ask-mirror-talk-production.up.railway.app/ask
Request Method: POST
Status Code: 200

Response Headers:
  Access-Control-Allow-Origin: https://mirrortalkpodcast.com
  Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
  Access-Control-Allow-Credentials: false
```

---

### Test 6: Edge Cases

**Test Case 6.1: Very Long Bold Text**
Question: "What is the longest advice from Mirror Talk about relationships?"

Expected: Long **bold text** should wrap properly, maintain bold formatting

**Test Case 6.2: Multiple Bold in Same Sentence**
Expected: Multiple **bold** **words** render correctly

**Test Case 6.3: Mixed Bold and Italic**
Expected: `**bold** and *italic*` renders as **bold** and *italic*

**Test Case 6.4: List with Bold Items**
Expected:
```
1. **First bold item**: Description
2. **Second bold item**: Description
```
Renders with bold items and proper numbering

---

## Automated Test Script (Browser Console)

Run this in your browser console after the widget loads:

```javascript
// Test 1: Verify markdown function exists
console.log('✓ Markdown function exists:', typeof formatMarkdownToHtml === 'function');

// Test 2: Test bold conversion
const boldTest = formatMarkdownToHtml('**bold text**');
console.log('✓ Bold conversion:', boldTest === '<strong>bold text</strong>');

// Test 3: Test italic conversion
const italicTest = formatMarkdownToHtml('*italic text*');
console.log('✓ Italic conversion:', italicTest === '<em>italic text</em>');

// Test 4: Test mixed formatting
const mixedTest = formatMarkdownToHtml('**bold** and *italic*');
console.log('✓ Mixed formatting:', mixedTest.includes('<strong>') && mixedTest.includes('<em>'));

// Test 5: Verify CORS headers (after making a request)
fetch('https://ask-mirror-talk-production.up.railway.app/health')
  .then(response => {
    console.log('✓ CORS Status:', response.ok ? 'Working' : 'Failed');
    console.log('✓ Status Code:', response.status);
  })
  .catch(err => console.error('✗ CORS Error:', err));

// Test 6: Check if output element can render HTML
const outputEl = document.querySelector('#ask-mirror-talk-output');
if (outputEl) {
  outputEl.innerHTML = '<strong>Test Bold</strong>';
  const hasBold = outputEl.querySelector('strong') !== null;
  console.log('✓ HTML rendering:', hasBold ? 'Working' : 'Failed');
  outputEl.innerHTML = ''; // Clear test
}

console.log('\n✅ All client-side tests complete!');
```

---

## Expected Console Output

**After running automated test:**
```
✓ Markdown function exists: true
✓ Bold conversion: true
✓ Italic conversion: true
✓ Mixed formatting: true
✓ CORS Status: Working
✓ Status Code: 200
✓ HTML rendering: Working

✅ All client-side tests complete!
```

---

## Manual Verification Checklist

### Backend (CORS) ✅
- [ ] No 403 errors in any browser
- [ ] Safari (desktop) works
- [ ] Safari (iOS) works
- [ ] Chrome (desktop) works
- [ ] Chrome (mobile) works
- [ ] Firefox works
- [ ] Edge works
- [ ] Both www and non-www domains work

### Frontend (Markdown) ✅
- [ ] `**bold**` renders as **bold**
- [ ] `*italic*` renders as *italic*
- [ ] Numbered lists render as `<ol>`
- [ ] Bullet lists render as `<ul>`
- [ ] Mixed formatting works (bold + italic + lists)
- [ ] Text is readable and well-formatted
- [ ] No `**` visible in output
- [ ] CSS styling applied correctly (strong tags are bold)

### Integration ✅
- [ ] Full question-answer cycle works
- [ ] Citations display correctly
- [ ] Loading states work
- [ ] Error states work
- [ ] Multiple questions work in succession
- [ ] No console errors

---

## Failure Scenarios & Solutions

### Scenario 1: Still Seeing 403 Errors

**Diagnosis:**
- Check Railway deployment status
- Check if changes were pushed
- Check ALLOWED_ORIGINS environment variable

**Solution:**
```bash
# Verify deployment
railway logs

# Check environment
railway vars

# Force redeploy if needed
railway up
```

### Scenario 2: Still Seeing `**bold**`

**Diagnosis:**
- WordPress cache not cleared
- Browser cache not cleared
- Wrong files uploaded
- JavaScript errors in console

**Solution:**
1. Hard refresh (Ctrl+Shift+R)
2. Clear WordPress cache
3. Re-upload JavaScript files
4. Check console for errors

### Scenario 3: Lists Not Rendering

**Diagnosis:**
- CSS not loaded
- JavaScript error before list processing
- Wrong CSS file uploaded

**Solution:**
1. Verify CSS file uploaded
2. Check Network tab for CSS load
3. Inspect element to see if CSS rules applied
4. Re-upload CSS file

---

## Success Metrics

**Definition of Done:**

✅ **CORS Fix Complete When:**
- Zero 403 errors across all browsers
- All devices (desktop, mobile) work
- Both www and non-www work
- No CORS errors in console

✅ **Markdown Fix Complete When:**
- No visible `**` in answers
- Bold text is visually bold
- Lists render with proper HTML structure
- CSS styling applied correctly
- Text is readable and well-formatted

---

**Testing Status:** ⏳ Ready for Testing
**Last Updated:** February 16, 2026
