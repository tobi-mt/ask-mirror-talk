# Ask Mirror Talk v5.0 - UX Overhaul
**Release Date:** March 28, 2026  
**Version:** 5.0.0  
**Status:** ✅ Deployed — `wordpress/ask-mirror-talk-v5.0.0.zip`

---

## 🎉 What's New in v5.0

This release is a comprehensive UX overhaul focused on **retention**, **growth**, and **premium feel**. It adds 12 new interactive features across the widget, all implemented in vanilla ES6+ — no new dependencies.

---

## ✨ New Features

### Retention

#### 1. Saved Insights (🔖)
- Bookmark button appears after every answer
- Saved answers stored in localStorage (up to 30)
- Dedicated insights panel in the stats bar — shows all saved Q&As with delete and "ask again" actions
- Badge counter on the 🔖 icon updates in real time

#### 2. Streak Protection Banner
- Checks streak status each page load
- After 6 PM, if the user has a streak but hasn't asked today, an amber banner appears
- One-tap CTA scrolls user to the input field

#### 3. Reflection Prompts
- After each answer, a random reflection question appears (7 rotating prompts)
- Collapsible private textarea for journaling
- Notes auto-saved to `amt_reflect_notes` in localStorage

#### 4. Come Back Tomorrow Teaser
- Fires 5 seconds after the "🌊 Deep session!" milestone toast
- Picks a theme for tomorrow and shows a soft teaser card
- Encourages deliberate return visits

---

### Growth

#### 5. Share v2 (Two-Mode Toggle)
- Replaces the basic share button
- **Mode A — Share Answer:** Formats the answer + question into shareable text with Web Share API fallback (clipboard copy)
- **Mode B — Invite a Friend:** Shows a referral-style invite message with the site URL
- Includes a "Save this insight" button inline

#### 6. About Modal (ⓘ)
- New ⓘ button in the widget heading bar
- Opens a bottom-sheet modal with app purpose, 3 key benefits, and personalised usage stats
- Closes via Escape, backdrop tap, or explicit button

#### 7. Auto-Open Explore on First Visit
- On first ever visit, the Explore panel opens automatically after 1.8 seconds
- Panel toggle button gets a gold glow pulse animation (×3)
- Sets `amt_explore_opened` flag so it never auto-opens again

---

### Premium Feel

#### 8. Mood Reactions
- Five emoji buttons (😮 💡 😢 🙏 ❤️) appear after each answer with staggered fade-in
- Single tap to select; selected state shown with dark fill + scale pop
- Reactions are tracked (no backend required — UX hook ready for future analytics)

#### 9. Copy Answer Button
- Appears in the response header next to the answer title
- Uses `navigator.clipboard.writeText` with graceful fallback
- Button label changes to "✓ Copied" for 2 seconds after copying

#### 10. Text Size Toggle (Aa)
- New Aa button in the widget heading bar
- Cycles through three sizes: Small → Default → Large
- Applies `.amt-text-small` or `.amt-text-large` to the widget root
- Persisted to `amt_text_size` in localStorage

#### 11. Animated Icon Parade
- Explore toggle button cycles through themed icons (🌟 🌀 💭 🔍 ✨ 🎯 💡 🗂️) every 2 seconds
- Animation only plays when the panel is closed
- Smooth fade-out / fade-in transition between icons

#### 12. Response Progress Bar
- Sticky 3px gold gradient bar at the top of the response container
- Fills from 0 → 100% as the user scrolls through a long answer
- Resets automatically when a new answer loads

---

## 🐛 Fixes Included

- **Share button overflow on mobile** — milestone toast now uses `flex-wrap: wrap`; share button becomes full-width below the message on small screens
- **Explore expander** (v4.9.6) — "Browse by topic" and "Try asking about" sections packed into a collapsible panel with an animated toggle and chevron

---

## 📁 Files Changed

| File | Lines | Changes |
|------|-------|---------|
| `ask-mirror-talk.php` | 425 | Restructured response container; added heading controls; new panel containers |
| `ask-mirror-talk.js` | 3807 | 12 feature blocks appended (lines 3150–3807); wiring via MutationObserver |
| `ask-mirror-talk.css` | 3940 | Full styles for all 12 features + mobile overrides appended at EOF |

---

## 🔑 localStorage Keys Added

| Key | Purpose |
|-----|---------|
| `amt_saved_insights` | JSON array of saved Q&A pairs (max 30) |
| `amt_text_size` | Preferred text size (`small` / `large`, absent = default) |
| `amt_explore_opened` | Boolean flag — auto-open has already triggered |
| `amt_reflect_notes` | JSON array of private reflection journal entries |

---

## 🚀 Deployment

ZIP: `wordpress/ask-mirror-talk-v5.0.0.zip` (351 KB, 19 files)

Install via **WordPress → Appearance → Themes → Add New → Upload Theme**, or copy `astra-child/` contents via FTP/SFTP.
