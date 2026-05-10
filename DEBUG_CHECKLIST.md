# Debug Checklist for v5.5.30 Issues

## Reported Issues
1. ❌ Nudge buttons below the app not working properly and incomplete
2. ❌ Share, invite buttons not working at all  
3. ❌ Rhythm tab is empty

## Debugging Steps

### 1. Check Browser Console
Open DevTools Console (F12) and look for:
```
- Any JavaScript errors (red text)
- "✨ Ask Mirror Talk Premium Features v5.5.30 loaded" message
- Any warnings about missing elements
```

### 2. Test Nudge Buttons
1. Get an answer to a question
2. Scroll to bottom - do you see nudge buttons?
3. Open Console and run:
```javascript
document.querySelector('#amt-workflow-nudge')
document.querySelector('#amt-workflow-nudge-actions')
```
Expected: Both should return elements, not null

### 3. Test Share/Invite Buttons
1. Get an answer to a question
2. Look for share section
3. Open Console and run:
```javascript
document.querySelector('#amt-share-section')
document.querySelectorAll('.amt-share-btn')
```
Expected: Should find share section and 2 buttons

### 4. Test Rhythm Tab
1. Click "Rhythm" tab in workflow bar
2. Check if content appears
3. Open Console and run:
```javascript
document.querySelector('#amt-workflow-panel-progress')
document.querySelector('#amt-momentum-card')
```
Expected: Both should exist

### 5. Check if Functions Exist
Open Console and run:
```javascript
typeof renderMomentumCard
typeof renderBadgeShelf
typeof renderWeeklyRecap
typeof addShareButtonV2
typeof renderWorkflowNudgeActions
```
Expected: All should be "function"

### 6. Manually Trigger Functions
Try manually calling:
```javascript
// Test stats loading
const stats = localStorage.getItem('amt_stats');
console.log('Stats:', stats);

// Test rhythm tab
const progressPanel = document.querySelector('#amt-workflow-panel-progress');
if (progressPanel) {
  progressPanel.style.display = 'block';
  console.log('Progress panel visible');
}

// Test momentum card
const momentumCard = document.querySelector('#amt-momentum-card');
if (momentumCard) {
  momentumCard.style.display = 'block';
  momentumCard.innerHTML = '<div style="padding:20px;background:yellow;">TEST CONTENT</div>';
}
```

## Common Fixes

### If Premium Features Not Loading
- Check that `ask-mirror-talk-premium.js` is loaded
- Verify version: `console.log` should show v5.5.30
- Check file size: should be ~1055 lines

### If Elements Not Found
- Verify WordPress shortcode is rendering properly
- Check that `ask-mirror-talk.php` is loaded
- Inspect HTML to see if elements exist with correct IDs

### If Buttons Not Clickable
- Check if event listeners are attached
- Look for JavaScript errors preventing execution
- Verify buttons are not disabled or hidden

### If Rhythm Tab Empty
- Check localStorage for stats: `localStorage.getItem('amt_stats')`
- Verify `renderMomentumCard()` function exists
- Try manual test (see step 6 above)

## Quick Fixes to Try

### Fix 1: Clear Cache and Reload
```
1. Open DevTools (F12)
2. Right-click Reload button
3. Select "Empty Cache and Hard Reload"
4. Test again
```

### Fix 2: Reset Stats  
```javascript
// In Console:
localStorage.setItem('amt_stats', JSON.stringify({
  totalQuestions: 5,
  currentStreak: 3,
  earnedBadges: new Set(['first_question']),
  themesExplored: new Set(['faith', 'wisdom']),
  savedInsights: 2,
  sharedReflections: 1
}));
location.reload();
```

### Fix 3: Force Render Rhythm Content
```javascript
// In Console, after clicking Rhythm tab:
if (typeof renderMomentumCard === 'function') {
  const stats = {
    totalQuestions: 10,
    currentStreak: 5,
    themesExplored: new Set(['faith', 'wisdom', 'gratitude']),
    earnedBadges: new Set(['first_question', 'week_1']),
    savedInsights: 3,
    sharedReflections: 2,
    lastSessionDate: new Date().toISOString().split('T')[0],
    dailyQuestions: 2
  };
  renderMomentumCard(stats);
}
```

## Report Back

After testing, provide:
1. Browser name and version
2. Any console errors (screenshot)
3. Which specific buttons/features are broken
4. Whether elements exist in HTML (use Inspector)
5. Whether functions exist (use Console tests above)
