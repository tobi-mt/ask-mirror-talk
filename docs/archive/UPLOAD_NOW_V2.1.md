# 🎨 Quick Upload Guide - v2.1.0

## ✅ What Changed

### 1. Loading Animation is Back! 🔄
- **Before:** Plain text "Searching..."
- **After:** Animated spinner + styled box

### 2. Citations are Beautiful! 🎨
- **Before:** Simple list with links
- **After:** Card-based design with:
  - Episode titles (bold, larger)
  - Excerpts in italic quotes
  - Button-style timestamps
  - Hover effects (lift up, darken)

---

## 📦 Upload These 3 Files

To `/wp-content/themes/astra/`:

1. ✅ `ask-mirror-talk-standalone.php` (v2.1.0)
2. ✅ `ask-mirror-talk.js` (v2.1.0)
3. ✅ `ask-mirror-talk.css` (v2.1.0)

---

## 🧪 Test It

1. **Clear cache**: Cmd+Shift+R
2. **Check console**: Should see "Widget v2.1.0 loaded"
3. **Submit question**:
   - See spinner animation ✅
   - Get warm answer ✅
   - See styled citation cards ✅
4. **Hover over citations**: Cards lift up ✅
5. **Click timestamp**: Opens at exact moment ✅

---

## 🎨 What You'll See

### Loading:
```
┌─────────────────────────────────┐
│ [🔄] Searching through Mirror   │
│      Talk episodes...            │
└─────────────────────────────────┘
```
(Spinner rotates smoothly)

### Citations:
```
┌─────────────────────────────────┐
│ Episode Title                    │
│                                  │
│ "Relevant excerpt from the       │
│  episode showing context..."     │
│                                  │
│ [🎧 Listen at 0:12:34]          │
└─────────────────────────────────┘

(Hover = lifts up + shadow)
```

---

## 🎯 Features

✨ **Loading Animation**
- Spinning indicator
- Smooth rotation (0.8s)
- Styled background box
- Left border accent

🎨 **Citation Cards**
- White cards with shadows
- Brown left border (→ black on hover)
- Italic excerpts (first 150 chars)
- Button-style timestamps
- Hover: lift + darken
- Click: opens episode

---

**Upload now and see the magic!** ✨

Files are ready in:
- `wordpress/astra/ask-mirror-talk-standalone.php`
- `wordpress/astra/ask-mirror-talk.js`
- `wordpress/astra/ask-mirror-talk.css`
