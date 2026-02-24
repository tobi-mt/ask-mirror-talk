# Ask Mirror Talk — WordPress Deployment Guide

> **Version 3.3.0** — Widget + Analytics + Inline Audio Player + Quote Snippets + Browse by Topic + Question of the Day + Cache Pre-warming

---

## 1. Files to Upload

Upload **all 4 files** from this folder into your WordPress theme directory:

```
wp-content/themes/astra/
├── ask-mirror-talk.php      ← Shortcode + AJAX handler
├── ask-mirror-talk.js       ← Widget logic (SSE streaming, fallback, inline player)
├── ask-mirror-talk.css      ← All styles (widget, citations, feedback, player)
└── analytics-addon.js       ← Citation click tracking + feedback buttons
```

**How to upload:**
- **File Manager** (cPanel / hosting panel) → navigate to `wp-content/themes/astra/` → upload all 4 files
- **SFTP** (FileZilla, Cyberduck, etc.) → connect → navigate → upload
- **SSH** → `scp` the files into the theme directory

---

## 2. Enable the Shortcode

Add this line **near the bottom** of `wp-content/themes/astra/functions.php`, **before** the closing `?>` (if present):

```php
require_once get_stylesheet_directory() . '/ask-mirror-talk.php';
```

> ⚠️ **No leading slash** before `'/ask-mirror-talk.php'` — just use `get_stylesheet_directory() . '/ask-mirror-talk.php'`

---

## 3. Add the Widget to a Page

In any WordPress page or post, add this shortcode:

```
[ask_mirror_talk]
```

Works with the Block Editor (Gutenberg), Classic Editor, and page builders (Elementor, etc.).

---

## 4. Clear All Caches

After uploading, clear caches in this order:

1. **WordPress cache plugin** (WP Super Cache, LiteSpeed Cache, W3 Total Cache, etc.)
2. **Cloudflare / CDN** (if applicable) — purge everything
3. **Browser cache** — hard refresh the page with `Cmd + Shift + R` (Mac) or `Ctrl + Shift + R` (Windows)

---

## 5. Verify Everything Works

### Quick checks:
| Check | How to verify |
|-------|--------------|
| Widget loads | Visit the page → you see the "Ask Mirror Talk" form |
| Question of the Day | A highlighted card appears with today's question and an "Ask this →" button |
| Browse by Topic tags | Clickable topic pills (Grief, Faith, Purpose, etc.) render below QOTD |
| Suggested questions appear | Pill-shaped buttons render above the input |
| Ask a question | Type a question → click **Ask** → answer streams in |
| Citations appear | Episode cards with 🎧 timestamps and quote snippets show below the answer |
| Explore this episode | "Explore this episode ↗" link appears under each citation |
| Inline audio player | Click a citation → player opens with skip/close buttons |
| Feedback buttons | "Was this answer helpful?" appears after citations |
| Click tracking | Open browser Console → look for `✅ Citation click tracked` |
| Feedback tracking | Click 👍/👎 → Console shows `✅ Feedback submitted` |

### Browser Console checks:
Open Developer Tools → Console and look for:
```
Ask Mirror Talk Widget v3.3.0 loaded
✅ Ask Mirror Talk Analytics Add-on loaded
✅ QA Session ID captured: <uuid>
✅ Citation tracking added to N links
✅ Feedback buttons added
```

---

## 6. Backend API Endpoints

The widget connects to: `https://ask-mirror-talk-production.up.railway.app`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/status` | GET | System status + episode count |
| `/ask` | POST | Ask a question (non-streaming) |
| `/ask/stream` | POST | Ask a question (SSE streaming) |
| `/api/suggested-questions` | GET | Get suggested questions |
| `/api/question-of-the-day` | GET | Daily rotating question |
| `/api/topics` | GET | Browseable topic tags with episode counts |
| `/api/citation/click` | POST | Track citation clicks |
| `/api/feedback` | POST | Submit user feedback |
| `/api/analytics/summary` | GET | Analytics dashboard summary |
| `/api/analytics/episodes` | GET | Per-episode analytics |

---

## 7. Architecture Overview

```
WordPress (Astra theme)
  ├── ask-mirror-talk.php     → registers [ask_mirror_talk] shortcode
  │                             → AJAX handler proxies to Railway API
  │                             → enqueues JS + CSS
  ├── ask-mirror-talk.js      → tries SSE streaming first (/ask/stream)
  │                             → falls back to WP AJAX → direct /ask
  │                             → renders citations, inline audio, follow-ups
  ├── ask-mirror-talk.css     → styles for everything
  └── analytics-addon.js      → intercepts fetch to capture qa_log_id
                                → tracks citation clicks via /api/citation/click
                                → adds feedback UI, submits via /api/feedback

Railway API (Python / FastAPI)
  ├── /ask, /ask/stream       → answer generation + smart citations
  ├── /api/citation/click     → stores click events
  ├── /api/feedback           → stores user feedback
  └── /api/analytics/*        → admin analytics dashboard
```

---

## 8. Troubleshooting

| Issue | Solution |
|-------|----------|
| Widget not showing | Check `functions.php` has the `require_once` line; check shortcode is on the page |
| "Session expired" errors | Nonce auto-refreshes; if persistent, check `functions.php` isn't loaded twice |
| CORS errors in Console | CORS is configured on Railway; verify the domain is allowed |
| No citations appearing | API may return 0 citations for some questions; try "What is Mirror Talk about?" |
| Analytics not tracking | Ensure `analytics-addon.js` loads **after** `ask-mirror-talk.js` (PHP handles this) |
| 403 from WordPress AJAX | Nonce expired — the widget auto-retries with a fresh nonce |
| Streaming not working | Falls back to `/ask` automatically; check Console for SSE errors |

---

## 9. WPGetAPI (Optional — Not Required)

The current setup calls the Railway API **directly** from PHP (`wp_remote_post`). WPGetAPI is **not required**. If you previously configured WPGetAPI, it won't conflict but is unused.

---

## 10. File Versions

All files are versioned at `3.3.0`. To force a cache bust after updating, increment the version string in `ask-mirror-talk.php`:

```php
wp_enqueue_style('ask-mirror-talk', ..., '3.3.1');
wp_enqueue_script('ask-mirror-talk', ..., '3.3.1');
wp_enqueue_script('ask-mirror-talk-analytics', ..., '3.3.1');
```
