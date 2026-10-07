# Astra Child Theme - Mirror Talk Edition

This is the Mirror Talk experience layer for Astra. It includes the Ask Mirror Talk application, the editorial homepage, native topic hubs, contextual reflection journeys, PWA support and privacy-conscious optional analytics.

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
├── answer-archive-template.php    # Editor-curated Insights Library template
├── assets/art/                    # Responsive AVIF + JPEG atmospheric artwork
├── category.php                   # Search-friendly category/topic hubs
├── inc/journey.php                # Context-aware episode → Ask journeys
├── inc/listen-and-connect.php     # RSS player, platform links and CTA dialogs
├── mirror-talk-site.css           # Global Mirror Talk design system
├── mirror-talk-site.js            # Accessible featured-content slider
├── listen-connect.js              # Persistent player and invitation behavior
├── home.php                       # Dark editorial blog index
├── archive.php                    # Dark tag/date/author archives
├── single.php                     # Immersive long-form post template
├── page.php                       # Cohesive standard page template
├── topic.php                      # Virtual topic collections for existing posts
├── player-window.php              # Persistent browser-level listening window
├── page-templates/
│   └── mirror-talk-home.php       # Opt-in editorial homepage
├── theme.json                     # WordPress editor design tokens
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

### Step 4: Preview the New Homepage Safely

1. Create a new draft page in WordPress.
2. Choose the **Mirror Talk Editorial Home** template.
3. Preview it on desktop and mobile in staging.
4. When approved, set it under **Settings → Reading → A static page**.

The template is opt-in and does not replace the existing homepage automatically.

The artwork is intentionally decorative and contains no text, people or literal health imagery. AVIF is served to supporting browsers with optimized JPEG fallbacks; smaller files are selected for mobile layouts. Original PNG masters and the complete art-direction record live in `artwork/` outside the deployable theme.

### Step 5: Use Mirror Talk Intelligence & SEO

Mirror Talk is the authoritative SEO system. It owns titles, descriptions, canonical URLs, featured-image social cards, schema and the XML sitemap. AIOSEO output is suppressed while the plugin remains installed for migration review; after verifying staging, deactivate AIOSEO and any other general-purpose SEO suite so the site has one clear source of SEO truth.

### Step 6: Clean Up (Optional)

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
- **Editorial Homepage:** Native, responsive homepage built around Listen → Read → Explore → Reflect → Ask → Connect → Return
- **Dark Editorial System:** Cohesive high-contrast styling across the header, homepage, blog, archives, posts, standard pages and footer
- **Fluid Viewports:** Full-bleed Astra overrides, 1680px adaptive wide shells and 12px mobile gutters without horizontal overflow
- **Automated Featured Slider:** Compact, control-free adaptive autoplay with progress, visibility awareness, reduced-motion support and an on-device preference-ranked starting conversation across desktop and mobile
- **Privacy-First Personalisation:** Returning-visitor welcome and topic affinity stay in the visitor's browser; no fingerprinting, precise-location lookup or profile transmission
- **Mirror Talk Intelligence & SEO:** Consent-gated first-party journeys, campaigns, podcast completion, Core Web Vitals, link observations, protected reporting, native metadata, social cards, Article/PodcastEpisode/Breadcrumb schema and complete collision-proof `/mirror-talk-sitemap/`, `/mirror-talk-news-sitemap/` and `/mirror-talk-video-sitemap/` feeds
- **Editorial SEO Guidance:** Search-description editor, content-quality checks and internal-link prompts inside the WordPress editor
- **Weekly Site Audit:** WordPress checks priority routes, records broken links and redirects, and emails the administrator a weekly report
- **Listening Companion:** Site-wide RSS-powered player with the latest episode, expandable queue and Media Session metadata
- **Continuous Listening:** Explicit mini-player window preserves the selected episode and timestamp while the main site navigates
- **Intentional Invitations:** Accessible Ask, newsletter and follow/support dialogs with engagement-based frequency caps
- **Direct Newsletter Signup:** Name, email and explicit consent are collected inside the modal and stored as private WordPress subscriber records without a contact-page redirect
- **Layered Signup Defence:** Signed form-age proof, nonce, honeypot, anonymised burst/daily limits, non-enumerating responses and hashed 48-hour double-opt-in confirmation tokens
- **Private Insights Archive:** The Insights template renders the visitor's device-local Ask Mirror Talk saved library instead of substituting public blog posts
- **Smart Topic Collections:** Purpose, resilience, relationships, faith, healing and leadership routes classify the existing archive without manual recategorisation
- **Topic Hubs:** WordPress categories render as indexable discovery pages
- **Contextual Ask:** Episode and topic pages prefill an editable reflection prompt without auto-submitting it
- **Curated Insights:** Only editor-approved WordPress posts appear; private questions are never published
- **Analytics Consent:** Optional product analytics stays off until a visitor explicitly enables it
- **From the Mirror Talk Studio:** The newest YouTube upload is discovered from the channel feed, cached server-side and presented before the footer with cinematic, archive and article layouts
- **Respectful Video Autoplay:** External media loads only after one explicit device-level choice, then autoplays muted only while at least half visible; reduced-motion, Data Saver, hidden tabs and podcast playback are respected
- **Video Intelligence:** First-party consent-gated events measure discovery, starts, progress, completions, autoplay blocking and sound choices, while native SEO can emit a `VideoObject` for the featured upload
- **SEO Platform 8:** Automatic IndexNow batching, Google News/video sitemaps, first-party `llms.txt` and `llms-full.txt`, RSS attribution, protected robots additions, slug-aware redirects, daily whole-site link health, SEO revision rollback and protected REST fields
- **Search Ownership:** Google, Bing and Pinterest verification plus a complete Google OAuth/Search Console connector and encrypted Bing Webmaster connector; verified properties, query data and sitemap status power the native dashboard without scraping search results
- **AI Visibility:** Privacy-preserving, first-party observations of recognized AI crawler requests and AI-service referrals, a citation-readiness score, and AI landing-page discovery—without storing IP addresses, prompts or private reflections
- **Mirror Talk Intelligence:** A separate native WordPress dashboard for consented page views, unique visitors, top pages, acquisition, campaigns, journeys, devices, privacy-safe geography, conversions, podcast completion, episode performance, Core Web Vitals, resource failures, Google/Bing search data, SEO health, AI discovery, period comparisons, weekly reports, table filtering and complete CSV export
- **Evidence-led SEO Learning:** Automatically derives per-post focus keywords from verified Google query/page data, ranks opportunities, runs no more than two guarded search-title experiments at once, requires meaningful impressions and a statistically credible CTR gain, preserves visible headlines, records every decision and restores the baseline when evidence is weak
- **Editorial Intelligence:** Search-title/description suggestions, structural content checks, internal-link prompts, browser spellcheck and reviewable media-alt repair
- **Authority Profiles:** Author expertise, experience, credentials and profile links flow into Person/Article structured data
- **Specialist SEO:** Truthful opt-in LocalBusiness data, conditional WooCommerce Product/Offer schema and 48-hour Google News publisher discovery

#### What is automatic and what needs one connection

All on-site features work immediately after activation. IndexNow creates and serves its own key, the crawlers and reports schedule themselves, and sitemaps, feeds, schema, redirects and both LLM source files need no setup. If AIOSEO is present, Mirror Talk disables only its overlapping LLM-file generator and removes only those two generated files so that one authoritative source remains. Google Search Console, Bing Webmaster and Pinterest still require the site owner to prove ownership once; their platforms do not allow a theme to consent on the owner's behalf. After that one authorization, synchronization is scheduled automatically. LocalBusiness schema remains off until a real public address is supplied, because publishing invented location data would weaken trust rather than improve SEO.

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
