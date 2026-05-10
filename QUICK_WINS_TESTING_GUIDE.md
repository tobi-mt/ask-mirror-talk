# Quick Wins Testing Guide

## 🧪 Comprehensive Testing Checklist

This guide helps you verify all 8 Quick Win features work correctly before deploying to production.

---

## Prerequisites

- ✅ Files deployed to staging/production
- ✅ Backend endpoint `/api/stats/questions-today` deployed
- ✅ Service worker cleared (Hard refresh: Cmd+Shift+R)

---

## Test 1: Debug Mode (Console Logging)

### Expected Behavior
- **With `?debug=1`:** All logs visible in console
- **Without:** Zero console output in production

### Steps
1. Open site: `https://yoursite.com`
2. Open DevTools Console (F12)
3. Perform actions (ask question, load QOTD)
4. **✓ PASS:** No console output visible

5. Add debug param: `https://yoursite.com?debug=1`
6. Refresh page
7. Perform same actions
8. **✓ PASS:** See `[AMT]` prefixed logs

### Screenshot
```
[AMT] ✓ Nonce refreshed
[AMT] QOTD answer preloaded
[AMT] Voice input enabled
```

---

## Test 2: Enhanced Skeleton Loaders

### Expected Behavior
- 6 animated skeleton lines appear while loading
- Lines have varying widths (92%, 77%, 85%, 63%, 95%, 81%)
- Smooth shimmer animation (left to right)
- Smooth transition to actual answer

### Steps
1. Click "New Question of the Day" or ask a question
2. **✓ PASS:** See 6 gray skeleton lines with shimmer effect
3. Wait for answer to load
4. **✓ PASS:** Skeleton lines smoothly fade out, answer fades in
5. No jarring flash or layout shift

### Visual Check
- Lines should have subtle gradient animation
- Animation should be smooth (60fps)
- Each line has rounded corners
- Lines stack vertically with 10px gap

---

## Test 3: Smart Contextual Error Messages

### Expected Behavior
- Different error messages for different failure types
- Retry button appears for recoverable errors
- Auto-dismiss countdown for rate limits

### Test 3.1: Network Error
1. Open DevTools → Network tab
2. Set throttling to "Offline"
3. Ask a question
4. **✓ PASS:** Error message: "No internet connection. Please check your connection and try again."
5. **✓ PASS:** Retry button appears

### Test 3.2: Rate Limit Error
1. Ask 10+ questions rapidly (trigger rate limit)
2. **✓ PASS:** Error message: "You've reached the question limit. Please wait 30 seconds and try again."
3. **✓ PASS:** Countdown timer appears (30, 29, 28...)
4. Wait for countdown to finish
5. **✓ PASS:** Error auto-dismisses

### Test 3.3: Server Error
1. (Hard to test without backend change)
2. **Expected:** "The server encountered an error. Please try again in a moment."
3. **✓ PASS:** Retry button appears

### Test 3.4: Empty Response
1. (Rare edge case)
2. **Expected:** "No answer was generated. Please try rephrasing your question."

### Visual Check
- Error box has warning icon (⚠️)
- Error text is clear and actionable
- Retry button is prominent
- Rate limit countdown is visible

---

## Test 4: Predictive QOTD Loading

### Expected Behavior
- QOTD answer prefetches in background after 2 seconds
- Answer cached for 1 hour
- Clicking QOTD shows instant answer (no loading)

### Steps
1. Load page with QOTD visible
2. Open DevTools → Network tab
3. Wait 2 seconds
4. **✓ PASS:** See background fetch request to `/ask` endpoint
5. Click "Question of the Day"
6. **✓ PASS:** Answer appears instantly (no skeleton loader)
7. Check localStorage: `amt_qotd_answer_cache`
8. **✓ PASS:** Contains cached answer with timestamp

### Performance Check
- First QOTD click: Instant (< 100ms)
- Cached answer persists for 1 hour
- After 1 hour: Answer refreshes

---

## Test 5: Keyboard Shortcuts

### Expected Behavior
- 7 keyboard shortcuts work correctly
- Help modal shows all shortcuts
- Shortcuts don't interfere with typing in inputs

### Test 5.1: Focus Input (`/`)
1. Click anywhere on page (not in input)
2. Press `/` key
3. **✓ PASS:** Input field focuses
4. Cursor appears in input

### Test 5.2: New QOTD (`n`)
1. Press `n` key
2. **✓ PASS:** New QOTD loads
3. QOTD section updates with new question

### Test 5.3: Share (`s`)
1. After getting an answer, press `s` key
2. **✓ PASS:** Share button clicks (share modal opens)

### Test 5.4: Copy (`c`)
1. After getting an answer, press `c` key
2. **✓ PASS:** Answer copied to clipboard
3. Toast notification: "Copied to clipboard"

### Test 5.5: Browse Topics (`b`)
1. Press `b` key
2. **✓ PASS:** Topics/explore section toggles

### Test 5.6: Quick Ask (`Cmd/Ctrl + K`)
1. Press `Cmd+K` (Mac) or `Ctrl+K` (Windows/Linux)
2. **✓ PASS:** Input focuses AND selects all text

### Test 5.7: Help Modal (`?`)
1. Press `?` key
2. **✓ PASS:** Help modal appears
3. Modal shows all 7 shortcuts
4. Each shortcut has description
5. "Got it" button closes modal

### Edge Cases
- Type in input field → Press `/` → **✓ PASS:** Types "/" (doesn't focus)
- Press shortcuts with modifier keys (Shift, Alt) → **✓ PASS:** No action

---

## Test 6: Voice Input (Mobile Only)

### Expected Behavior
- Microphone button appears on mobile devices
- Tapping mic starts voice recognition
- Spoken words transcribe to input field

### Steps (on iPhone/iPad/Android)
1. Open site on mobile device
2. **✓ PASS:** Microphone button (🎤) appears next to input
3. Tap microphone button
4. **✓ PASS:** Button changes to red dot (🔴)
5. **✓ PASS:** Input placeholder changes to "Listening..."
6. Speak a question: "What is the meaning of life?"
7. **✓ PASS:** Text appears in input field as you speak
8. Stop speaking
9. **✓ PASS:** Button returns to 🎤
10. **✓ PASS:** Placeholder returns to "Ask a question..."

### Visual Check
- Mic button is positioned right of input (60px from right edge)
- Button has hover effect (opacity changes)
- Red dot is visible when listening
- Text transcribes in real-time (interim results)

### Browser Support
- **iOS Safari:** ✅ Supported
- **Chrome Android:** ✅ Supported
- **Desktop:** ❌ Button should NOT appear

---

## Test 7: Pull-to-Refresh (Mobile Only)

### Expected Behavior
- Pull down from top of page refreshes QOTD
- Visual indicator shows during pull
- Haptic feedback on refresh (if supported)

### Steps (on iPhone/iPad/Android)
1. Scroll to top of page (scrollY = 0)
2. Place finger at top of screen
3. Pull down slowly (> 80px)
4. **✓ PASS:** Banner appears: "⬆️ Release to refresh"
5. Continue pulling down
6. **✓ PASS:** Banner stays visible
7. Release finger
8. **✓ PASS:** New QOTD loads
9. **✓ PASS:** Feel brief vibration (if device supports)
10. **✓ PASS:** Banner slides up and disappears

### Edge Cases
- Pull < 80px → Release → **✓ PASS:** No refresh, banner disappears
- Pull while scrolled down → **✓ PASS:** No banner, no refresh
- Pull while loading → **✓ PASS:** No action (button disabled)

### Visual Check
- Banner has rounded bottom corners
- Banner background: orange (rgba(148,62,8,0.95))
- Banner text: white, bold
- Slide animation is smooth (300ms)

---

## Test 8: Social Proof Counter

### Expected Behavior
- Badge shows "X questions asked today" after 3 seconds
- Only shows if count >= 10
- Badge auto-hides after 8 seconds
- Animated slide-in from right

### Test 8.1: Backend Endpoint
1. Open browser or curl:
   ```bash
   curl https://ask-mirror-talk-production.up.railway.app/api/stats/questions-today
   ```
2. **✓ PASS:** Response: `{"count": 47, "date": "2026-01-15T00:00:00+00:00"}`
3. Count should be >= 0
4. Date should be today at midnight UTC

### Test 8.2: Frontend Display
1. Load page
2. Wait 3 seconds
3. **✓ PASS:** Badge slides in from right side
4. **✓ PASS:** Badge shows count: "47 questions asked today"
5. **✓ PASS:** Green pulsing dot next to text
6. Wait 8 seconds
7. **✓ PASS:** Badge slides out to right
8. Badge removes from DOM

### Visual Check
- Badge positioned: bottom-right (20px from edges)
- Background: Orange (rgba(148,62,8,0.95))
- Text: White, bold
- Green dot: 8px circle, pulsing animation
- Shadow: Subtle drop shadow
- Animation: Smooth slide (0.5s)

### Edge Cases
- Count < 10 → **✓ PASS:** Badge doesn't appear
- API error → **✓ PASS:** Badge doesn't appear (silent fail)
- Mobile: Badge positioned above nav bar (bottom: 80px)

---

## 🎯 Integration Tests

### Scenario 1: First-Time User Journey
1. Load page (no cache)
2. **✓ PASS:** QOTD appears
3. Wait 2 seconds
4. **✓ PASS:** Background prefetch starts
5. Wait 3 seconds
6. **✓ PASS:** Social proof badge appears
7. Click QOTD
8. **✓ PASS:** Answer appears instantly
9. Press `s` to share
10. **✓ PASS:** Share modal opens

### Scenario 2: Mobile User Journey
1. Load page on mobile
2. **✓ PASS:** Mic button appears
3. **✓ PASS:** Social proof badge appears (bottom: 80px)
4. Tap mic
5. **✓ PASS:** Voice recognition starts
6. Speak question
7. **✓ PASS:** Text transcribes
8. Submit question
9. **✓ PASS:** Skeleton loaders appear
10. Pull down from top
11. **✓ PASS:** Refresh indicator appears
12. Release
13. **✓ PASS:** New QOTD loads

### Scenario 3: Power User Journey
1. Load page
2. Press `/` to focus
3. Type question
4. Press Enter
5. **✓ PASS:** Skeleton loaders appear
6. Answer loads
7. Press `c` to copy
8. **✓ PASS:** Toast: "Copied to clipboard"
9. Press `n` for new QOTD
10. **✓ PASS:** New question loads
11. Press `?` for help
12. **✓ PASS:** Help modal shows shortcuts

### Scenario 4: Error Recovery Journey
1. Disconnect internet
2. Ask question
3. **✓ PASS:** Network error appears
4. Click "Retry" button
5. **✓ PASS:** Shows loading state
6. Reconnect internet
7. **✓ PASS:** Answer loads successfully

---

## 📊 Performance Tests

### Lighthouse Audit
1. Open Chrome DevTools → Lighthouse
2. Run audit (Mobile, Performance)
3. **✓ PASS:** Performance score >= 90
4. **✓ PASS:** First Contentful Paint < 1.5s
5. **✓ PASS:** Time to Interactive < 3s

### Console Output (Production)
1. Load site WITHOUT `?debug=1`
2. Open Console
3. Perform 10 actions
4. **✓ PASS:** Zero console output
5. Verify no `console.log`, `console.warn`, `console.error`

### Bundle Size
1. Open DevTools → Network tab
2. Filter by JS files
3. Find `ask-mirror-talk.js`
4. **✓ PASS:** File size similar to before (no bloat)
5. All features use native APIs (no dependencies added)

---

## 🐛 Bug Checks

### Known Edge Cases
1. **Voice Input + Keyboard Shortcuts:**
   - Start voice input → Press `/` → **✓ PASS:** No conflict
   
2. **Pull-to-Refresh + Scroll:**
   - Scroll down → Pull → **✓ PASS:** No refresh
   
3. **Social Proof + Small Screens:**
   - Open on 320px width → **✓ PASS:** Badge fits
   
4. **Skeleton Loaders + Dark Mode:**
   - Enable dark mode → **✓ PASS:** Skeleton colors visible
   
5. **Predictive Loading + Cache Expiry:**
   - Wait 1 hour → Click QOTD → **✓ PASS:** Fetches fresh answer

---

## ✅ Final Checklist

- [ ] Debug mode works (logs in dev, silent in prod)
- [ ] Skeleton loaders animate smoothly
- [ ] All 5 error types display correctly
- [ ] QOTD answers load instantly (predictive)
- [ ] All 7 keyboard shortcuts work
- [ ] Voice input works on mobile
- [ ] Pull-to-refresh works on mobile
- [ ] Social proof badge appears and hides
- [ ] No console errors in production
- [ ] Performance score >= 90
- [ ] Mobile responsiveness confirmed
- [ ] All features degrade gracefully

---

## 🚨 Rollback Plan

If issues arise in production:

1. **Quick Rollback:**
   ```bash
   git revert HEAD
   git push origin main
   ```

2. **Partial Rollback (disable single feature):**
   - Comment out feature in [ask-mirror-talk.js](wordpress/astra-child/ask-mirror-talk.js)
   - Example: Comment out `setTimeout(showSocialProof, 3000);`

3. **Emergency Fix:**
   - Add `?debug=1` to see console logs
   - Identify error
   - Apply hotfix
   - Test on staging
   - Deploy to production

---

## 📝 Test Report Template

```markdown
## Test Report: Quick Wins v5.5.29

**Tester:** [Your Name]  
**Date:** [Date]  
**Environment:** [Staging/Production]  
**Device:** [Desktop/iPhone/Android]  
**Browser:** [Chrome/Safari/Firefox]

### Results
- [ ] Test 1: Debug Mode
- [ ] Test 2: Skeleton Loaders
- [ ] Test 3: Smart Error Messages
- [ ] Test 4: Predictive QOTD Loading
- [ ] Test 5: Keyboard Shortcuts
- [ ] Test 6: Voice Input (Mobile)
- [ ] Test 7: Pull-to-Refresh (Mobile)
- [ ] Test 8: Social Proof Counter

### Issues Found
1. [Issue description]
2. [Issue description]

### Performance
- Lighthouse Score: [XX/100]
- Console Errors: [X]
- Load Time: [X.Xs]

### Recommendation
[ ] ✅ APPROVE FOR PRODUCTION
[ ] ⚠️ MINOR FIXES NEEDED
[ ] ❌ MAJOR ISSUES - DO NOT DEPLOY
```

---

**Created:** January 15, 2026  
**Version:** v5.5.29  
**Status:** Ready for Testing
