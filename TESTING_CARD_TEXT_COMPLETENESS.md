# Testing Card Text Completeness Fixes

## Quick Test in Browser Console

Open the Ask Mirror Talk page and run these tests in the browser console:

### Test 1: Incomplete Text with Unclosed Parenthesis
```javascript
// The problem case from the user's screenshot
const badText = 'So when those thoughts pop up ("Why don\'t I have what they have?';

// Should return empty string or cleaned version
console.log('ensureReflectionSentence:', ensureReflectionSentence(badText));
// Expected: "" or "So when those thoughts pop up."

// Should get very low score
console.log('scoreReflectionSentence:', scoreReflectionSentence(badText, {}));
// Expected: Large negative number (around -50 or lower)

// Should be truncated
console.log('trimDanglingHeadlineTail:', trimDanglingHeadlineTail(badText));
// Expected: "So when those thoughts pop up"

// Should fail completeness check
console.log('isCompleteReflectionSentence:', isCompleteReflectionSentence(badText));
// Expected: false
```

### Test 2: Incomplete Text with Unclosed Quote
```javascript
const badQuote = 'She said "courage means';

console.log('ensureReflectionSentence:', ensureReflectionSentence(badQuote));
// Expected: ""

console.log('trimDanglingHeadlineTail:', trimDanglingHeadlineTail(badQuote));
// Expected: "She said" or ""
```

### Test 3: Complete Valid Text (Should Pass)
```javascript
const goodText = 'Come back to the truth that your worth does not need proving.';

console.log('ensureReflectionSentence:', ensureReflectionSentence(goodText));
// Expected: "Come back to the truth that your worth does not need proving."

console.log('scoreReflectionSentence:', scoreReflectionSentence(goodText, {}));
// Expected: Positive number (likely 5-15+)

console.log('isCompleteReflectionSentence:', isCompleteReflectionSentence(goodText));
// Expected: true
```

### Test 4: Valid Text with Balanced Quotes
```javascript
const goodQuote = 'The teacher said "trust the process" and I finally understood.';

console.log('isCompleteReflectionSentence:', isCompleteReflectionSentence(goodQuote));
// Expected: true

console.log('scoreReflectionSentence:', scoreReflectionSentence(goodQuote, {}));
// Expected: Positive number (no penalty for balanced quotes)
```

---

## End-to-End Test: Generate a Card

1. **Ask a question** about self-worth or another theme
2. **Review the generated card** in the Save & Share section
3. **Verify the text** is complete:
   - ✅ No unclosed quotes
   - ✅ No unclosed parentheses
   - ✅ Ends with proper punctuation
   - ✅ Forms a complete thought
   - ✅ Is inspirational and shareable

---

## Problematic Test Cases to Try

Force the system to use potentially incomplete text and verify it handles it gracefully:

```javascript
// Create a mock insight with problematic text
const problematicInsight = {
  question: 'How do I find my worth?',
  answer: 'So when those thoughts pop up ("Why don\'t I have what they have? This is incomplete.',
  excerpt: 'She said "courage means',
  theme: 'Self-worth'
};

// Extract headline - should avoid incomplete text
const headline = extractShareHeadline(problematicInsight);
console.log('Extracted headline:', headline);
// Expected: Should fall back to theme-appropriate default, NOT the incomplete text
```

---

## Python Validation Script

Run the validation script to check cards:

```bash
cd /Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk
python3 scripts/validate_reflection_cards.py
```

This should validate that reflection card fixtures render correctly and text is complete.

---

## What to Look For

### ✅ Good Signs
- Empty strings returned for incomplete text
- Large negative scores (-50 or worse) for unbalanced text
- Truncated text that removes problematic sections
- Complete sentences making it to cards
- Proper fallbacks when no good text is available

### ❌ Red Flags
- Incomplete text passing `isCompleteReflectionSentence()`
- Positive scores for unbalanced quotes/parens
- Cards displaying text with unclosed quotes
- Missing proper punctuation on card text
- Mid-sentence cutoffs on shareable cards

---

## Browser DevTools Testing

### Test the Full Pipeline

```javascript
// Simulate the full reflection card generation
const testReflection = {
  question: 'What does Mirror Talk teach about returning to my worth?',
  answer: `The podcast explores how comparison can lead to questions like "Why don't I have what they have?" This pattern keeps you focused outward instead of inward. Your worth is not determined by what others possess. Come back to the truth that your worth does not need proving. Rest in what is already true about you.`,
  theme: 'Self-worth',
  timestamp: Date.now()
};

// 1. Test sentence splitting
const sentences = splitReflectionSentences(testReflection.answer);
console.log('Sentences found:', sentences.length);

// 2. Test sentence scoring
sentences.forEach((sentence, i) => {
  const score = scoreReflectionSentence(sentence, { themeKeywords: ['worth', 'value', 'identity'] });
  const isComplete = isCompleteReflectionSentence(sentence);
  console.log(`${i + 1}. Score: ${score}, Complete: ${isComplete}`);
  console.log(`   "${sentence}"`);
});

// 3. Test headline extraction
const headline = extractShareHeadline(testReflection);
console.log('Final headline:', headline);
// Should be something like: "Come back to the truth that your worth does not need proving."
```

---

## Expected Results Summary

| Test Case | isComplete | Score | Result |
|-----------|-----------|-------|--------|
| `"So when thoughts pop up ("Why"` | `false` | `-50` or lower | Rejected ❌ |
| `'She said "courage means'` | `false` | `-50` or lower | Rejected ❌ |
| `"Worth does not need proving."` | `true` | `10+` | Accepted ✅ |
| `"Trust the next brave step."` | `true` | `8+` | Accepted ✅ |

---

## Manual Card Review Checklist

For each generated reflection card, verify:

- [ ] Text is grammatically complete
- [ ] All quotes are balanced
- [ ] All parentheses are balanced
- [ ] Ends with proper punctuation (. ! ?)
- [ ] Forms a complete, meaningful thought
- [ ] Is 8-20 words (ideally)
- [ ] Is inspirational and shareable
- [ ] Uses active, present-tense language
- [ ] Avoids hedging words (maybe, perhaps, can help)
- [ ] Avoids meta-language (this reflection, one thing that stood out)

---

## Deployment Verification

After deploying these changes:

1. **Monitor new cards** generated by users
2. **Check for incomplete text** in production logs
3. **User feedback** - Any complaints about card quality?
4. **Analytics** - Are share rates improving?

---

**Test Date:** May 10, 2026  
**Tested By:** GitHub Copilot AI  
**Status:** Ready for manual verification
