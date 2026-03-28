# Astra Child Theme - Mirror Talk Edition

This is a child theme for the Astra WordPress theme, containing the Ask Mirror Talk widget with PWA, push notifications, gamification, and a full v5.0.0 UX feature set.

## Files Included

```
astra-child/
├── style.css                      # Child theme header (required)
├── functions.php                  # Loads parent theme + Ask Mirror Talk widget
├── ask-mirror-talk.php            # Shortcode, AJAX handlers, PWA setup (v5.0.0)
├── ask-mirror-talk.js             # Widget frontend logic (v5.0.0)
├── ask-mirror-talk.css            # Widget styles (v5.0.0)
├── ask-mirror-talk-enhanced.css   # Additional premium styles
├── ask-mirror-talk-enhanced.js    # Enhanced interaction layer
├── analytics-addon.js             # Citation tracking and feedback
├── answer-archive-template.php    # Custom page template for answer archive
├── manifest.json                  # PWA manifest
├── sw.js                          # Service worker for offline + push notifications
├── pwa-icon-192.png               # PWA icon (192x192)
├── pwa-icon-512.png               # PWA icon (512x512)
├── pwa-icon-180.png               # Apple touch icon (180x180)
├── pwa-icon-167.png               # iPad retina icon (167x167)
├── pwa-icon-152.png               # iPad icon (152x152)
└── pwa-icon.svg                   # Vector icon source
```

## Installation Instructions

### Step 1: Upload to WordPress

1. **Via FTP/SFTP:**
   - Connect to your server
   - Navigate to `/wp-content/themes/`
   - Upload the entire `astra-child` folder

2. **Via WordPress Dashboard:**
   - Zip the `astra-child` folder
   - Go to **Appearance → Themes → Add New → Upload Theme**
   - Upload the zip file
   - Click **Install Now**

### Step 2: Activate the Child Theme

1. Go to **Appearance → Themes**
2. Find **Astra Child - Mirror Talk**
3. Click **Activate**

⚠️ **Important:** Make sure the parent **Astra** theme is installed before activating the child theme.

### Step 3: Verify Installation

1. Edit any page/post
2. Add the shortcode: `[ask_mirror_talk]`
3. View the page — you should see the Ask Mirror Talk widget

### Step 4: Clean Up (Optional)

After confirming the child theme works:

1. **Remove** the custom files from the parent theme (`/wp-content/themes/astra/`):
   - `ask-mirror-talk.php`
   - `ask-mirror-talk.js`
   - `ask-mirror-talk.css`
   - `analytics-addon.js`
   - `manifest.json`
   - `sw.js`
   - PWA icons

2. **Remove** the custom code from the parent theme's `functions.php` if you added it

This ensures you're only using the child theme version.

## Features

### Core
- **Ask Mirror Talk Widget:** Semantic search through 471 podcast episodes with streamed AI answers
- **PWA Support:** Installable as a mobile/desktop app ("Add to Home Screen")
- **Push Notifications:** Daily Question of the Day + streak protection reminders + midday motivation
- **Offline Mode:** Service worker caches widget for offline access
- **Analytics:** Citation click tracking, answer feedback, and engagement reporting
- **Answer Archive:** Custom page template listing all archived answers
- **Theme-Safe:** Updates to Astra won't affect your customizations

### Gamification & Engagement (v4.x)
- **Streak Tracking:** Daily question streak with fire emoji milestones and XP points
- **Badges:** Unlockable achievement badges (First Question, 7-day streak, 30-day streak, etc.)
- **Milestone Toasts:** Animated toast notifications for streak and depth milestones
- **Explore Expander:** Collapsible panel for "Browse by topic" and "Try asking about" suggestions

### UX Enhancements (v5.0.0)
1. **Saved Insights (🔖):** Bookmark any answer — stored locally, re-askable from the insights panel (up to 30)
2. **Streak Protection Banner:** Amber reminder banner after 6 PM when today's streak is at risk
3. **Reflection Prompts:** Post-answer prompt with a private journaling textarea (saved to localStorage)
4. **Come Back Tomorrow Teaser:** After a "Deep session" milestone, shows a preview of tomorrow's theme
5. **Share v2:** Two-mode share toggle — share a specific answer *or* invite a friend with a referral link
6. **About Modal (ⓘ):** Bottom-sheet panel showing app purpose, stats, and a CTA — opens from heading bar
7. **Auto-Open Explore:** Explore panel gently opens on first visit (1.8 s delay) with a gold glow highlight
8. **Mood Reactions:** Five emoji reaction buttons (😮 💡 😢 🙏 ❤️) appear after every answer
9. **Copy Answer Button:** One-tap clipboard copy of the full answer text with ✓ Copied feedback
10. **Text Size Toggle (Aa):** Three-level font size toggle (small / default / large), persisted across sessions
11. **Animated Icon Parade:** Explore toggle cycles through themed icons when the panel is closed
12. **Response Progress Bar:** Sticky gold progress bar fills as the user scrolls through a long answer

## Updating Custom Code

When you need to update the widget code:

1. Edit files in `/wp-content/themes/astra-child/` (NOT the parent theme)
2. Or update your local files and re-upload the entire child theme folder

## Support

For questions or issues:
- Website: https://mirrortalkpodcast.com
- Email: hello@mirrortalkpodcast.com

## License

GNU General Public License v2 or later
