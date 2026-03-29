# Ask Mirror Talk — User Experience Guide

Everything a user can experience and do with **Ask Mirror Talk**.

---

## What Is Ask Mirror Talk?

Ask Mirror Talk is an AI-powered companion for the **Mirror Talk podcast** — a faith-based, personal-growth podcast covering emotional intelligence, relationships, healing, and purpose. You ask questions in plain language and receive warm, conversational answers synthesised from real podcast episodes, each linked directly to the moment in the audio where the topic was discussed.

---

## How to Access It

| Platform | How |
|---|---|
| **Website** | Embedded widget on mirrortalkpodcast.com via the `[ask_mirror_talk]` shortcode |
| **Mobile (Android/iOS)** | Install as a PWA: tap "Add to Home Screen" from Android/Chrome or Safari |
| **Desktop** | Install from the browser's install prompt (appears in the address bar) |

---

## Asking a Question

1. Type your question in the text box ("What's on your heart?") — up to 500 characters.
2. Press **Ask** or hit **Ctrl/Cmd + Enter**.
3. The answer streams in word-by-word in real time (shimmer loader shows while it loads).
4. A 3–4 paragraph conversational response appears, synthesised from the most relevant podcast episodes.

The app remembers the last 3 exchanges in a session, so follow-up questions can reference what was said earlier in the conversation.

---

## Reading and Listening to Citations

Every answer comes with **Referenced Episodes** — the specific moments in podcast episodes that informed the answer.

Each citation card shows:
- Episode title and year
- A quote snippet from the relevant segment
- The exact timestamp range (e.g. "14:22 – 17:45")

**Clicking a citation card** opens an inline audio player:
- Jumps directly to the cited moment and auto-plays
- Auto-pauses at the end of the cited segment
- Controls: Back 10s, Forward 10s, open in new tab, close
- "Explore this episode ↗" link opens the full episode externally

Only one player is open at a time; opening a second one automatically closes the first.

---

## Discovering What to Ask

### Question of the Day (QOTD)
A fresh question appears every day at the top of the widget, drawn from a curated pool of 40 questions spanning 20 themes (self-worth, forgiveness, purpose, healing, boundaries, identity, and more). Clicking **"Ask this →"** pre-fills and auto-submits the form.

### Browse by Topic
10 topic categories are available to explore:
- 💔 Grief & Loss
- 🔗 Addiction
- 🧭 Purpose
- ❤️ Relationships
- 🌊 Fear & Doubt
- 🙏 Faith
- 🏆 Leadership
- 🪞 Identity
- 🌱 Healing
- 🕊️ Forgiveness

Each category expands to show 3 ready-made starter questions — one tap and the question is submitted automatically.

### Suggested Questions
Up to 6 clickable question suggestions appear below the topic panel, drawn from popular recent questions and curated defaults.

### Follow-up Questions
After every answer, 3 AI-generated follow-up questions appear as clickable buttons under the response — relevant threads to keep exploring.

### "Others Also Wondered…"
After an answer, up to 3 questions asked by other users who received answers from the same episodes are surfaced. This surfaces perspectives and angles you might not have thought of.

### Journey Continuity
On returning to the app, if there are topic areas you haven't explored yet, a prompt appears with a ready-to-go starter question. If you asked a question in the last 24 hours, it suggests continuing from where you left off.

---

## Sharing and Saving Answers

After every answer, two sharing actions are available:

| Action | What It Does |
|---|---|
| **📤 Share this insight** | Opens the native share sheet (mobile) or copies the answer to the clipboard |
| **📧 Save to email** | Opens your email client with the question and full answer pre-filled in the body |

---

## Giving Feedback

After receiving an answer, thumbs-up and thumbs-down buttons allow rating the response quality. A 1–5 star rating and optional written comment are also available.

---

## Push Notifications (Optional)

After visiting the site (15 seconds for new visitors, 5 seconds for returning ones), an opt-in prompt appears. Notifications are entirely optional and individually configurable.

### What You Can Enable

| Notification | Default Time | What It Sends |
|---|---|---|
| **Question of the Day** | 8 AM in your timezone | A daily thematic question with a direct link to get the AI answer |
| **New Episode Alert** | When published | A notification when a new podcast episode is added to the knowledge base |
| **Midday Motivation** | Midday | A brief midday encouragement prompt |

QOTD notifications stay on screen until tapped. They include:
- A theme-labelled title (e.g. "✨ Today's Wisdom: Self-Worth")
- Two action buttons: **"💬 Get Answer"** (opens the app and submits the question) / **"🔖 Save for Later"**

### Managing Preferences
Tap **Preferences** in the notification banner to toggle each notification type independently. Your timezone is detected automatically.

### Platform Notes
- **iOS (non-PWA)**: Push notifications require the PWA to be installed first (Add to Home Screen).
- **iOS below 16.4**: Push notifications require an iOS update.
- **Private/Incognito mode**: Notifications are unavailable in private browsing.

---

## Gamification & Progress Tracking

A stats bar appears at the top of the widget after you ask your first question.

### Stats Bar
| Stat | Icon | What It Tracks |
|---|---|---|
| Day Streak | 🔥 | Consecutive days you've asked at least one question |
| Questions Asked | 💬 | Total number of questions submitted |
| Topics Explored | 🗺️ | Number of the 20 topic areas visited (out of 20) |
| Badges | 🏆 | Opens the badge shelf |

### Badges
11 badges can be earned and are displayed in a badge shelf:

| Badge | Condition |
|---|---|
| 🌱 First Step | Asked your first question |
| 📚 Curious Mind | Asked 10 questions |
| 🎓 Deep Thinker | Asked 50 questions |
| 🏆 Mirror Master | Asked 100 questions |
| 🔥 On Fire | 3-day streak |
| 💫 Week Warrior | 7-day streak |
| 💎 Devoted | 30-day streak |
| 🗺️ Explorer | Explored 5 topic areas |
| 🌏 World Traveler | Explored 10 topic areas |
| ✨ Enlightened | Explored all 20 topic areas |
| 🦉 Night Owl | Asked a question after 10 PM |

When a streak or question milestone is reached, a milestone toast pops up to celebrate. All progress is stored locally on your device.

---

## Accessibility Features

- Screen reader support with live region announcements as answers stream in
- Keyboard navigation throughout (Ctrl/Cmd + Enter to submit)
- Character counter with a warning as you approach the 500-character limit
- Respects your device's **Reduce Motion** setting (disables animations)
- Accessible labels on all icon-only buttons and expand/collapse controls

---

## Offline Support (PWA)

When installed as a PWA and you lose connectivity:
- Previously loaded pages and assets are served from cache
- A friendly offline message is shown rather than a browser error
- The service worker automatically syncs when your connection returns

---

## Privacy Notes

- Questions are logged (with your IP address) to improve the service and generate analytics
- Feedback and citation clicks are recorded
- Push notification subscriptions are stored server-side; you can unsubscribe at any time from the notification preferences panel
- Gamification data (streaks, badges, question history) is stored only in your browser's `localStorage` — it is never sent to the server
