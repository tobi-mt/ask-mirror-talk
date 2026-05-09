# 🧪 Testing Checklist for v5.5.20 Premium Features

## ⚠️ IMPORTANT: This code is UNTESTED in a live browser

**What was done:**
- ✅ Code written with correct syntax
- ✅ Integration points added
- ✅ Safety checks added (DOMContentLoaded, null checks)
- ✅ No linter errors
- ⚠️ **NOT tested in actual browser**

---

## 🔍 Phase 1: Smoke Test (5 min)

### 1. **Deploy & Load Page**
```bash
# Upload astra-child-v5.5.20-premium.zip to WordPress
# Activate theme
# Clear browser cache (Cmd+Shift+R)
```

### 2. **Check Console for Errors**
Open DevTools → Console, look for:
- ✅ `Ask Mirror Talk Widget v5.5.20 loaded`
- ✅ `✨ Ask Mirror Talk Premium Features v5.5.20 loaded`
- ✅ `✅ Local database initialized`
- ✅ `✨ Premium features ready`

**If you see errors here, STOP and share the console output.**

### 3. **Check IndexedDB**
DevTools → Application → IndexedDB → `AskMirrorTalkDB`
- ✅ Database exists
- ✅ 5 object stores: reflections, insights, patterns, engagement, offlineQueue

**If database doesn't exist, check browser support (Chrome 80+, Firefox 75+, Safari 13.1+)**

---

## 🧪 Phase 2: Feature Testing (15 min)

### A. **Question Coaching**
1. Type: "Why am I so stupid?"
2. Wait 1.5 seconds
3. **Expected:** Coaching panel appears with reframe suggestion
4. Click "Use suggested"
5. **Expected:** Input updates to new phrasing

**If coaching doesn't appear:**
- Check console for errors
- Verify `#amt-question-coach` element exists in HTML
- Try typing different patterns: "What's wrong with me", "Should I quit"

### B. **Onboarding (First-Time Users Only)**
1. Clear localStorage: DevTools → Application → Local Storage → Delete `amt_onboarded`
2. Reload page
3. **Expected:** Dark overlay with onboarding card appears
4. Click "Begin Your First Reflection"
5. **Expected:** Overlay dismisses, input pre-filled with starter question

**If onboarding doesn't show:**
- Check `localStorage.getItem('amt_onboarded')` in console
- Check if `.amt-onboarding-overlay` element was created

### C. **Save Reflection to Database**
1. Type any question and submit
2. Wait for answer
3. Check DevTools → Application → IndexedDB → reflections
4. **Expected:** New row with your Q&A, theme, emotion, timestamp

**If not saving:**
- Check console for IndexedDB errors
- Try: `await window.AskMirrorTalkPremium.saveReflection({question: 'test', answer: 'test'})`
- Check if `saveReflection` function exists

### D. **Pattern Recognition (5th Question)**
1. Ask 5 questions (can be quick test questions)
2. After 5th answer
3. **Expected:** Pattern card appears: "You've asked 5 questions. [theme] keeps calling you back..."

**If pattern card doesn't show:**
- Check console for `showPatternInsight` errors
- Verify pattern was calculated: `await window.AskMirrorTalkPremium.getCachedPatterns()`
- Check if `.amt-pattern-card` element was created

### E. **Contextual Greeting (Returning Users)**
1. Submit question, wait for answer
2. Reload page
3. **Expected:** Greeting appears above form: "Welcome back. Still exploring [theme]?"

**If greeting doesn't show:**
- Check console for `showContextualGreeting` errors
- Verify history exists: `await window.AskMirrorTalkPremium.getReflectionHistory(1)`

### F. **Progress Visualization**
1. Click "Rhythm" in workflow bar
2. **Expected:** Progress summary card appears with:
   - Narrative text
   - 4 stats: Total reflections, Weekly average, Top theme, Best time

**If progress doesn't show:**
- Check console for `showProgressSummary` errors
- Verify patterns exist: `await window.AskMirrorTalkPremium.generateProgressSummary()`
- Check if `#amt-workflow-panel-progress` exists

### G. **Export Reflections**
1. Click "Save & Share" in workflow bar
2. Scroll down to data controls
3. Click "📤 Export Reflections"
4. **Expected:** JSON file downloads

**If export doesn't work:**
- Check console for errors
- Try manually: `await window.AskMirrorTalkPremium.exportReflections()`
- Verify reflections exist in database

### H. **Offline Mode**
1. Turn off Wi-Fi or use DevTools → Network → Offline
2. Type question and submit
3. **Expected:** 
   - Offline banner appears at bottom: "You're offline..."
   - Question queued (check offlineQueue in IndexedDB)
4. Turn Wi-Fi back on
5. **Expected:** 
   - Banner disappears
   - Queued question auto-submits

**If offline mode doesn't work:**
- Check if offline event listeners attached
- Manually check queue: `db.transaction(['offlineQueue'], 'readonly').objectStore('offlineQueue').getAll()`

---

## 🐛 Phase 3: Edge Cases (10 min)

### I. **Multiple Quick Questions**
1. Ask 3 questions rapidly (don't wait for answers)
2. **Expected:** No crashes, all save to database

### J. **Long Questions (> 200 chars)**
1. Type very long question
2. **Expected:** Question coaching still works, no UI breaks

### K. **Special Characters**
1. Type question with emojis: "Why do I feel 😢 when 💔 happens?"
2. **Expected:** Saves correctly, theme detection works

### L. **Browser Refresh During Answer**
1. Submit question
2. Refresh page while answer is streaming
3. **Expected:** No errors on reload, previous reflection saved

---

## 📊 Phase 4: Data Verification (5 min)

### M. **Check All Database Stores**
In DevTools → Application → IndexedDB → AskMirrorTalkDB:

**reflections:**
- ✅ Has entries
- ✅ Each has: id, question, answer, theme, emotion, timestamp
- ✅ Themes are correct (relationships, anxiety, growth, etc.)

**patterns:**
- ✅ Has 'current' entry
- ✅ Data includes: topTheme, topEmotion, bestTime, themeCount

**engagement:**
- ✅ Has today's date entry
- ✅ Hours object populated with counts

**insights:**
- Empty initially (user hasn't saved any yet)

**offlineQueue:**
- Empty (unless you tested offline mode)

---

## ❌ Common Errors & Fixes

### Error: "Failed to initialize database"
**Fix:** Browser doesn't support IndexedDB or storage quota exceeded
- Clear IndexedDB in DevTools
- Check browser version
- Try incognito mode

### Error: "Input field not found"
**Fix:** DOM loaded before premium features initialized
- Already added DOMContentLoaded check
- If still failing, add longer delay: `setTimeout(init, 1000)`

### Error: "Cannot read property 'appendChild' of null"
**Fix:** DOM element doesn't exist
- Check if followupsList exists before appending
- Already added null checks, but may need more

### Error: "Quota exceeded"
**Fix:** Too much data in IndexedDB
- Export data, clear database
- Add storage quota check

### Error: "showPatternInsight is not a function"
**Fix:** Function not defined in scope
- Already wrapped in `typeof` check
- Verify function exists in main widget

---

## 🎯 Success Criteria

**Minimum Viable:**
- ✅ Page loads without errors
- ✅ Database initializes
- ✅ Question coaching appears
- ✅ Reflections save to database

**Full Success:**
- ✅ All 12 features working
- ✅ No console errors
- ✅ Export/import works
- ✅ Offline mode functional
- ✅ UI looks good on mobile

---

## 📝 Bug Report Template

If you find issues, please share:

```
**Browser:** Chrome 120 / Safari 17 / Firefox 115
**Device:** Desktop / Mobile / Tablet
**Error Message:** [paste console error]
**Steps to Reproduce:**
1. 
2. 
3. 
**Expected:** 
**Actual:** 
**Screenshot/Video:** [if applicable]
```

---

## 🚀 Next Steps After Testing

1. **If everything works:** Deploy to production, celebrate! 🎉
2. **If minor issues:** Share console errors, I'll fix quickly
3. **If major issues:** Rollback to v5.5.19, debug systematically

---

## 💡 Debug Console Commands

Quick commands to test features manually:

```javascript
// Check premium API exists
window.AskMirrorTalkPremium

// Get reflection history
await window.AskMirrorTalkPremium.getReflectionHistory(10)

// Analyze patterns
await window.AskMirrorTalkPremium.analyzePatterns()

// Test question coaching
window.AskMirrorTalkPremium.coachQuestion("Why am I broken?")

// Generate greeting
await window.AskMirrorTalkPremium.generateContextualGreeting()

// Export data
await window.AskMirrorTalkPremium.exportReflections()

// Check database
indexedDB.databases()

// Clear everything (reset)
localStorage.clear()
indexedDB.deleteDatabase('AskMirrorTalkDB')
```

---

**⚠️ REMEMBER: This is the first deployment. Expect to find issues. That's normal and expected. Test systematically, report findings, and we'll iterate quickly.**
