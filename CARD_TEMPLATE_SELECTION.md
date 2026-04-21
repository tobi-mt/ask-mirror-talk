# Card Template Selection System
**How Ask Mirror Talk Dynamically Selects Card Templates**

## 🎯 Executive Summary

Card templates are **automatically and dynamically selected** based on:
- ✅ **Theme** (courage, leadership, grief, etc.)
- ✅ **Text characteristics** (length, word count, power words)
- ✅ **Content hash** (deterministic visual variations)
- ❌ **NOT based on:** Time of day, date, or random selection

**Each card is unique but deterministic** - the same reflection always gets the same template and visual variant.

---

## 🔍 How It Works

### Main Selection Function: `getInsightShareFamily(insight)`

Location: [ask-mirror-talk.js](wordpress/astra-child/ask-mirror-talk.js#L5761-L5797)

```javascript
function getInsightShareFamily(insight) {
  if (TEST_FORCE_FAMILY) return TEST_FORCE_FAMILY;
  
  const headline = extractShareHeadline(insight);
  const words = headline.split(/\s+/).filter(Boolean);
  const theme = String(insight.theme || '').toLowerCase();
  
  // PRIORITY 1: Gradient Immersive (bold emotional themes)
  if ((theme === 'courage' || theme === 'fear' || theme === 'healing' || theme === 'faith') 
      && words.length >= 8 && words.length <= 22 
      && headline.length >= 60 && headline.length <= 180) {
    return 'gradient_immersive';
  }
  
  // PRIORITY 2: Neon Contemplative (modern, forward-looking themes)
  if ((theme === 'leadership' || theme === 'boundaries' || theme === 'purpose') 
      && words.length >= 10 && words.length <= 24
      && headline.length >= 70) {
    return 'neon_contemplative';
  }
  
  // PRIORITY 3: Prismatic Quote (universal, powerful statements)
  if (words.length >= 9 && words.length <= 20 
      && headline.length >= 65 && headline.length <= 160
      && /\b(always|never|most|deepest|truest|only|every)\b/i.test(headline)) {
    return 'prismatic_quote';
  }
  
  // PRIORITY 4: Poster (concise, punchy)
  if (canUsePosterFamily(insight, headline)) {
    return 'poster';
  }
  
  // DEFAULT: Editorial (longer, contextual reflections)
  return 'editorial';
}
```

---

## 📊 Template Selection Matrix

| Template | Themes | Word Count | Character Length | Special Requirements |
|----------|--------|------------|------------------|---------------------|
| **Gradient Immersive** | courage, fear, healing, faith | 8-22 words | 60-180 chars | Emotional depth |
| **Neon Contemplative** | leadership, boundaries, purpose | 10-24 words | 70+ chars | Forward-looking |
| **Prismatic Quote** | Any | 9-20 words | 65-160 chars | Power words (always, never, most, deepest, truest, only, every) |
| **Poster** | Any | 6-18 words | 44-150 chars | Concise, max word length ≤16 |
| **Editorial** (default) | Any | Any | Any | Fallback for everything else |

---

## 🎨 Visual Variant Selection: `getInsightShareVariant(insight)`

Each template also gets a **visual variant** (different orb positions, text alignment, accent placements).

```javascript
function getInsightShareVariant(insight) {
  const seed = hashInsightShareSeed(`${insight.theme}|${insight.question}|${insight.excerpt}`);
  const variants = [/* 4 different visual layouts */];
  return variants[seed % variants.length];  // Deterministic hash-based selection
}
```

**Key Points:**
- Uses **content hash** (theme + question + excerpt) as seed
- **4 visual variants** available per template
- Same content → Same variant (deterministic, not random)
- Variants differ in: alignment (center/left), orb positions, panel insets, accent widths

**Example variants:**
1. **Center-aligned** with top-right & bottom-left orbs
2. **Left-aligned** with offset orbs
3. **Center-aligned** with left & right orbs
4. **Left-aligned** with different panel inset

---

## 🎯 Real-World Examples

### Example 1: Courage Theme
**Text:** "This simple act anchors you when everything else feels unsteady." (11 words, 66 chars)

**Selection process:**
1. ✅ Theme: courage
2. ✅ Words: 11 (within 8-22)
3. ✅ Length: 66 chars (within 60-180)
4. **Result:** `gradient_immersive` ✨

### Example 2: Leadership Theme
**Text:** "The best leaders create space for others to discover their own strength." (13 words, 78 chars)

**Selection process:**
1. ✅ Theme: leadership
2. ✅ Words: 13 (within 10-24)
3. ✅ Length: 78 chars (over 70)
4. **Result:** `neon_contemplative` 💎

### Example 3: Gratitude Theme
**Text:** "This simple act can help anchor you and provide a fresh perspective amidst overwhelming feelings." (16 words, 98 chars)

**Selection process:**
1. ❌ Theme: gratitude (not in courage/fear/healing/faith)
2. ❌ Theme: gratitude (not in leadership/boundaries/purpose)
3. ❌ No power words (always, never, etc.)
4. ❌ Not in poster range
5. **Result:** `editorial` (default) 📰

### Example 4: Self-Worth with Power Words
**Text:** "Come back to the truth that your worth does not need proving." (12 words, 62 chars)

**Selection process:**
1. ❌ Theme: self-worth (not in gradient_immersive themes)
2. ❌ Theme: self-worth (not in neon_contemplative themes)
3. ❌ Length: 62 chars (needs 65+ for prismatic)
4. ✅ Words: 12 (within 6-18), length: 62 (within 44-150)
5. **Result:** `poster` 🎪

---

## ⚙️ Selection Priority Order

```
1. TEST_FORCE_FAMILY (developer override)
   ↓
2. Gradient Immersive (courage/fear/healing/faith + right dimensions)
   ↓
3. Neon Contemplative (leadership/boundaries/purpose + right dimensions)
   ↓
4. Prismatic Quote (any theme + power words + right dimensions)
   ↓
5. Poster (any theme + concise dimensions)
   ↓
6. Editorial (default fallback)
```

---

## 🔧 Developer Override

You can force a specific template for testing:

```javascript
window.__AMT_TEST_FORCE_FAMILY__ = 'neon_contemplative';
```

Then all cards will use that template regardless of theme/content.

---

## 📈 Template Distribution (Based on Selection Logic)

**Estimated distribution across themes:**

| Template | % of Cards | Why |
|----------|-----------|-----|
| **Editorial** | ~45% | Default for most longer reflections |
| **Gradient Immersive** | ~20% | Courage, fear, healing, faith themes |
| **Neon Contemplative** | ~15% | Leadership, boundaries, purpose themes |
| **Poster** | ~15% | Short, concise statements |
| **Prismatic Quote** | ~5% | Rare power words requirement |

---

## 🎨 Theme → Template Mapping

### Themes → Gradient Immersive (Bold, Emotional)
- ✅ Courage
- ✅ Fear  
- ✅ Healing
- ✅ Faith

### Themes → Neon Contemplative (Modern, Forward)
- ✅ Leadership
- ✅ Boundaries
- ✅ Purpose

### Themes → Editorial (Default)
- ✅ Gratitude
- ✅ Self-Worth
- ✅ Grief
- ✅ Relationships
- ✅ Forgiveness
- ✅ Inner Peace
- ✅ Any other theme

---

## 🚀 What This Means

### ✅ Advantages
1. **Consistent** - Same reflection always looks the same
2. **Content-aware** - Template fits the emotional tone
3. **Predictable** - No random surprises for users
4. **Shareable** - Users can reference "my courage card" knowing it looks the same

### ❌ Limitations
1. **No time-based variation** - Morning vs evening doesn't change template
2. **No randomness** - Can't surprise users with different looks
3. **Theme-dependent** - Gratitude stuck with Editorial unless text has power words
4. **Fixed rules** - No ML/AI learning from user preferences

---

## 💡 Recommendations

### To Add Variety:
1. **Expand Gradient Immersive themes:** Add gratitude, self-worth to bold themes list
2. **Lower Prismatic barriers:** Reduce 65 char requirement to 50 to catch more cards
3. **Add time-based variants:** Different color intensities for morning vs evening
4. **Seasonal themes:** Special templates for holidays/seasons
5. **User preference:** Let users pick favorite template style

### To Improve Current System:
1. **Test coverage:** Ensure all theme combinations tested
2. **Edge cases:** Handle very short (< 40 chars) or very long (> 200 chars) text
3. **Power word list:** Expand beyond 7 words to catch more universal statements
4. **Theme fallback:** Better default when theme is unknown/miscategorized

---

## 🧪 Testing Template Selection

**Test a specific reflection:**
```javascript
const insight = {
  question: "How do I find courage?",
  answer: "This simple act anchors you when everything else feels unsteady.",
  theme: "Courage",
  excerpt: "Simple acts of courage..."
};

const family = getInsightShareFamily(insight);
console.log(family); // Expected: 'gradient_immersive'
```

**Force a template:**
```javascript
window.__AMT_TEST_FORCE_FAMILY__ = 'prismatic_quote';
// All cards now use prismatic until page reload
```

---

## 📝 Summary

**Q: Is selection automatic?**  
A: ✅ Yes, fully automatic based on content.

**Q: Is it based on theme?**  
A: ✅ Yes, theme is the primary factor.

**Q: Is it based on time of day?**  
A: ❌ No, purely content-driven.

**Q: Is it random?**  
A: ❌ No, deterministic. Same content = same template.

**Q: Can it change?**  
A: ✅ Yes, if the text or theme changes.

**The system is smart but predictable** - it analyzes your reflection's theme and text characteristics to pick the most visually appropriate template, ensuring both variety across the platform and consistency for individual users.
