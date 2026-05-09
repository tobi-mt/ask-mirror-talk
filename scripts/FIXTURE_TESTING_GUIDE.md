# 🧪 Live Testing with workflow_bar_fixture.html

## 🎯 Purpose
Test Ask Mirror Talk v5.5.20 premium features in a browser **without deploying to WordPress**.

## 🚀 Quick Start

### 1. Open the Fixture
```bash
# From project root
open scripts/workflow_bar_fixture.html
```

Or drag `workflow_bar_fixture.html` into your browser.

### 2. Open DevTools
- **Chrome/Edge:** `Cmd+Option+I`
- **Firefox:** `Cmd+Option+K`
- **Safari:** `Cmd+Option+C`

### 3. Watch the Console
You should see:
```
🧪 Workflow Bar Fixture + Premium Features Testing
📝 Open DevTools → Console for premium API tests
💾 Check DevTools → Application → IndexedDB for database
✨ Ask Mirror Talk Premium Features v5.5.20 loaded
✅ Local database initialized
✨ Premium features ready
🔄 Running auto-test in 2 seconds...
```

After 2 seconds, an **auto-test suite** runs automatically:
```
🧪 Premium Features Test Suite
✓ window.AskMirrorTalkPremium: true
✓ Question coaching: Detected harsh language
✓ Database write: Success
✓ Database read: 1 reflections
✓ Pattern analysis: 1 reflections analyzed
✓ Export: 1 reflections exported
✅ Test suite complete
```

## ✅ What to Check

### A. **Console Messages**
If you see errors instead of checkmarks, **premium features failed to load**.

**Common errors:**
- `Failed to initialize database` → IndexedDB not supported or quota exceeded
- `Input field not found` → DOM timing issue (should be fixed now)
- `undefined is not a function` → JavaScript error in premium code

### B. **IndexedDB**
DevTools → **Application** → **IndexedDB** → `AskMirrorTalkDB`

Should show:
- **reflections** (1 test entry)
- **insights** (empty)
- **patterns** (1 cached entry)
- **engagement** (empty)
- **offlineQueue** (empty)

### C. **Question Coaching**
1. Clear the input field
2. Type: "Why am I so broken?"
3. Wait 1.5 seconds
4. **Expected:** Coaching panel appears below with reframe suggestion

**Test different patterns:**
- "What's wrong with me?" → Reframe to "What am I struggling with?"
- "Should I quit my job?" → Depth prompt about fears/values
- "I'm stupid" → Compassionate reframe

### D. **Contextual Greeting**
1. Reload the page (`Cmd+R`)
2. **Expected:** Greeting appears: "Welcome back. Still exploring [theme]?"

**If no greeting:**
- Database might be empty (run test suite first)
- Check console for errors

## 🎮 Manual Testing

### Run Test Suite Manually
```javascript
await testPremiumFeatures()
```

### Test Individual Features
```javascript
// 1. Question Coaching
window.AskMirrorTalkPremium.coachQuestion("Why am I broken?")

// 2. Save Reflection
await window.AskMirrorTalkPremium.saveReflection({
  question: "How do I handle change?",
  answer: "Change is difficult...",
  citations: [],
  metadata: {}
})

// 3. Get History
await window.AskMirrorTalkPremium.getReflectionHistory(5)

// 4. Analyze Patterns
await window.AskMirrorTalkPremium.analyzePatterns()

// 5. Generate Greeting
await window.AskMirrorTalkPremium.generateContextualGreeting()

// 6. Export Data
await window.AskMirrorTalkPremium.exportReflections()

// 7. Check Cache
await window.AskMirrorTalkPremium.getCachedPatterns()
```

### Clear Database (Reset)
```javascript
localStorage.clear()
indexedDB.deleteDatabase('AskMirrorTalkDB')
// Then reload page
```

## 📱 Mobile Testing

Add `#mobile` to URL:
```
file:///path/to/workflow_bar_fixture.html#mobile
```

Or click the mobile frame in the fixture.

## 🐛 Known Limitations

### What Works:
- ✅ All premium JavaScript APIs
- ✅ Question coaching
- ✅ Database save/load
- ✅ Pattern analysis
- ✅ Export/import
- ✅ Onboarding detection
- ✅ Contextual greetings

### What Doesn't Work (Fixture Only):
- ❌ Actual question submission (no backend API)
- ❌ Real answers (fixture is static HTML)
- ❌ Follow-up suggestions (requires history)
- ❌ Pattern insights after 5th question (no real Q&A flow)
- ❌ Offline queue auto-sync (no network layer)

**For full testing**, deploy to WordPress and use [TESTING_CHECKLIST_v5.5.20.md](../TESTING_CHECKLIST_v5.5.20.md).

## 🎯 Success Criteria

**Fixture testing passes if:**
1. ✅ Console shows no errors
2. ✅ Auto-test suite passes (6 checkmarks)
3. ✅ IndexedDB database created
4. ✅ Question coaching appears when typing harsh questions
5. ✅ Manual API calls work in console

**If all pass → Premium features are likely ready for WordPress deployment.**

## 🔄 Next Steps

1. **If fixture tests pass:** Deploy to WordPress and run full [TESTING_CHECKLIST_v5.5.20.md](../TESTING_CHECKLIST_v5.5.20.md)
2. **If fixture tests fail:** Share console errors, I'll fix immediately
3. **If unsure:** Run manual API tests above and report results

---

## 💡 Pro Tips

### Quick Reload Workflow
```bash
# Edit premium.js
# Then in browser:
Cmd+R  # Reload
```

### Watch for Changes
```javascript
// Run in console to monitor database changes
setInterval(async () => {
  const history = await window.AskMirrorTalkPremium.getReflectionHistory(10);
  console.log('Database:', history.length, 'reflections');
}, 5000);
```

### Debug Specific Features
```javascript
// Enable verbose logging
localStorage.setItem('amt_debug', 'true');
// Then reload
```

---

**⚡ TIP: Use this fixture for rapid iteration. Edit code → Reload → Test → Repeat.**
