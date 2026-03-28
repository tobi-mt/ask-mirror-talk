# Ask Mirror Talk - Project Status

**Last Updated:** March 28, 2026  
**Widget Version:** 5.0.0  
**Status:** ✅ Production Ready — v5.0.0 ZIP deployed

---

## 🎯 Project Overview

Ask Mirror Talk is a Q&A system with PWA capabilities and push notifications for daily QOTD (Question of the Day) and new episode alerts.

---

## ✅ Completed Features

### 1. **PWA (Progressive Web App)**
- ✅ Installable on mobile and desktop
- ✅ Offline support with service worker
- ✅ App manifest with custom icons (192, 512, 180, 167, 152px)
- ✅ Native app-like experience

**Files:**
- `wordpress/astra-child/manifest.json`
- `wordpress/astra-child/sw.js`
- `wordpress/astra-child/pwa-icon-*.png`

### 2. **Push Notifications**
- ✅ Daily QOTD notifications (Railway cron)
- ✅ Streak protection reminders (6 PM if streak at risk)
- ✅ Midday motivation messages
- ✅ Opt-in/opt-out UI
- ✅ Platform detection (iOS, Safari, PWA)
- ✅ VAPID key management (base64url format)

**Backend:**
- `app/notifications/push.py` - Push notification service
- `scripts/send_daily_qotd.py` - Daily QOTD cron job
- `scripts/send_midday_motivation.py` - Midday motivation cron
- `scripts/send_streak_protection.py` - Streak protection cron
- `app/api/main.py` - Push notification API endpoints

**Frontend:**
- `wordpress/astra-child/ask-mirror-talk.js` - Notification opt-in logic
- `wordpress/astra-child/ask-mirror-talk.css` - Notification UI styles

### 3. **Gamification (v4.x)**
- ✅ Daily question streak tracking with fire emoji milestones
- ✅ XP points system
- ✅ Unlockable badges (First Question, 7-day streak, 30-day streak, etc.)
- ✅ Animated milestone toast notifications
- ✅ Session depth tracking ("Deep session" milestone at 3+ questions)
- ✅ Stats bar showing streak, XP, and badge count

### 4. **Widget UX — v4.9.x**
- ✅ Collapsible Explore expander ("Browse by topic" + "Try asking about" suggestions)
- ✅ Share button in milestone toast — full-width on mobile (flex-wrap fix)
- ✅ Streaming answer display with SSE
- ✅ Reading time badge on answers
- ✅ Answer archive page template

### 5. **Widget UX — v5.0.0 (12 new features)**
- ✅ **Saved Insights (🔖)** — bookmark answers to localStorage panel (up to 30, re-askable)
- ✅ **Streak Protection Banner** — amber reminder after 6 PM when streak is at risk
- ✅ **Reflection Prompts** — post-answer private journaling with random prompts
- ✅ **Come Back Tomorrow Teaser** — fires after "Deep session" milestone with tomorrow's theme
- ✅ **Share v2** — two-mode toggle: share specific answer OR invite a friend (referral)
- ✅ **About Modal (ⓘ)** — bottom-sheet panel with app purpose, personalised stats, CTA
- ✅ **Auto-Open Explore** — explore panel opens on first visit (1.8 s delay + gold glow)
- ✅ **Mood Reactions** — 5 emoji reactions (😮 💡 😢 🙏 ❤️) after every answer
- ✅ **Copy Answer Button** — one-tap clipboard copy with ✓ Copied feedback
- ✅ **Text Size Toggle (Aa)** — 3-level font size toggle persisted to localStorage
- ✅ **Animated Icon Parade** — explore toggle cycles themed icons when panel is closed
- ✅ **Response Progress Bar** — sticky gold bar fills as user scrolls answer

**localStorage keys (v5):** `amt_saved_insights`, `amt_text_size`, `amt_explore_opened`, `amt_reflect_notes`

### 6. **WordPress Child Theme**
- ✅ All customizations in `astra-child` theme — safe from parent theme updates
- ✅ Deployment ZIP: `wordpress/ask-mirror-talk-v5.0.0.zip`

**Location:** `wordpress/astra-child/`

**Key Files:**
- `functions.php` - Theme initialization
- `ask-mirror-talk.php` - Widget PHP + shortcode (v5.0.0)
- `ask-mirror-talk.js` - Widget JavaScript (3807 lines, v5.0.0)
- `ask-mirror-talk.css` - Widget styles (3940 lines, v5.0.0)
- `ask-mirror-talk-enhanced.css` / `.js` - Additional premium layer
- `analytics-addon.js` - Citation tracking and feedback
- `answer-archive-template.php` - Answer archive page template
- `manifest.json` - PWA manifest
- `sw.js` - Service worker
- `README.md` - Installation instructions

### 7. **Analytics**
- ✅ Citation click tracking
- ✅ Answer feedback (thumbs)
- ✅ Episode engagement tracking
- ✅ Weekly engagement reports
- ✅ Dashboard analytics via `scripts/analytics_queries.py`

### 8. **Project Cleanup**
- ✅ Removed archived documentation, old deployment configs, virtual environments
- ✅ Removed macOS metadata and Python cache files
- ✅ Removed custom files from parent Astra theme

---

## 📂 Current Project Structure

```
ask-mirror-talk/
├── app/                          # Core application code
│   ├── api/                      # FastAPI endpoints
│   ├── core/                     # Config, DB, logging
│   ├── indexing/                 # Chunking, embeddings, tagging
│   ├── ingestion/                # Audio, RSS, transcription
│   ├── notifications/            # Push notification service
│   ├── qa/                       # Q&A retrieval & answer generation
│   └── storage/                  # DB models & repository
│
├── scripts/                      # Maintenance & operation scripts
│   ├── analytics_queries.py
│   ├── bulk_ingest.py
│   ├── cleanup_orphaned_data.py
│   ├── generate_vapid_keys.py
│   ├── ingest_*.py              # Episode ingestion scripts
│   ├── send_daily_qotd.py       # Daily QOTD cron job
│   ├── weekly_engagement_report.py
│   └── *.sh                     # Shell scripts for ops
│
├── wordpress/                    # WordPress theme files
│   ├── astra-child/             # Child theme (all customizations)
│   │   ├── functions.php
│   │   ├── ask-mirror-talk.php
│   │   ├── ask-mirror-talk.js
│   │   ├── ask-mirror-talk.css
│   │   ├── analytics-addon.js
│   │   ├── manifest.json
│   │   ├── sw.js
│   │   ├── answer-archive-template.php
│   │   ├── ask-mirror-talk-enhanced.css
│   │   ├── ask-mirror-talk-enhanced.js
│   │   ├── pwa-icon-*.png
│   │   └── README.md
│   ├── astra/                   # Parent theme (clean, no custom files)
│   └── ask-mirror-talk-v5.0.0.zip  # Latest deployment ZIP
│
├── data/                         # Audio, transcripts, logs
│   ├── audio/                   # Episode MP3 files
│   ├── transcripts/             # Episode transcripts
│   └── logs/                    # Application logs
│
├── reports/                      # Weekly engagement reports
├── tests/                        # Test files
│
├── Dockerfile                    # API container
├── Dockerfile.worker             # Worker container
├── pyproject.toml               # Python project config
├── requirements.txt             # Python dependencies
├── railway.toml                 # Railway deployment config
├── railway.env.example          # Railway env template
├── railway-build.sh             # Railway build script
├── .env.example                 # Environment template
├── cleanup-project.sh           # Project cleanup script
└── README.md                    # Project documentation
```

---

## 🚀 Deployment

### **Railway (Production)**

**Services:**
1. **API** - FastAPI application
2. **Worker** - Background job processing
3. **Cron** - Daily QOTD notifications

**Environment Variables:**
See `railway.env.example` for complete list.

**Key Variables:**
- `DATABASE_URL` - Neon Postgres connection
- `OPENAI_API_KEY` - OpenAI API key
- `VAPID_PUBLIC_KEY` - Push notification public key (base64url)
- `VAPID_PRIVATE_KEY` - Push notification private key (base64url)
- `VAPID_MAILTO` - Admin email for VAPID

**Cron Job (QOTD):**
```bash
python scripts/send_daily_qotd.py
```
Scheduled daily via Railway cron service.

### **WordPress (Production)**

**Theme:** Astra Child (astra-child)

**Installation:**
1. Upload `wordpress/ask-mirror-talk-v5.0.0.zip` to WordPress
2. Activate the child theme
3. Widget will auto-load on pages

**Deployment Script:**
```bash
cd wordpress
./deploy-child-theme.sh
```

---

## 🛠️ Development

### **Setup**

1. **Clone Repository**
   ```bash
   git clone <repo-url>
   cd ask-mirror-talk
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

5. **Generate VAPID Keys**
   ```bash
   python scripts/generate_vapid_keys.py
   ```

6. **Run Locally**
   ```bash
   uvicorn app.api.main:app --reload
   ```

### **Useful Scripts**

- `scripts/ingest_single_episode.py` - Ingest one episode
- `scripts/ingest_missing_episodes.py` - Ingest missing episodes
- `scripts/cleanup_orphaned_data.py` - Clean orphaned data
- `scripts/weekly_engagement_report.py` - Generate engagement report
- `cleanup-project.sh` - Clean project files

---

## 📊 Database

**Provider:** Neon Postgres (Serverless)

**Tables:**
- `episodes` - Episode metadata
- `transcripts` - Episode transcripts
- `chunks` - Transcript chunks with embeddings
- `analytics` - User interaction tracking
- `push_subscriptions` - Push notification subscribers

**Migrations:**
- `scripts/init_neon.sql` - Initial schema
- `scripts/migrate_add_analytics_tables.py` - Add analytics
- `scripts/migrate_add_push_subscriptions.py` - Add push subs

---

## 🔐 Security

- ✅ VAPID keys stored as base64url (not PEM)
- ✅ Environment variables for all secrets
- ✅ No hardcoded credentials
- ✅ Gitignored `.env` files
- ✅ Railway secrets for production

---

## 📈 Analytics

**Tracked Events:**
- Widget views
- Questions asked
- Episode engagement
- Follow-up clicks
- Source tracking

**Reports:**
- Weekly engagement reports in `reports/`
- Dashboard analytics via `scripts/analytics_queries.py`

---

## 🐛 Debugging

### **Common Issues**

1. **Push Notifications Not Working**
   - Check VAPID keys are base64url format
   - Verify `pywebpush` and `py-vapid` installed
   - Check Railway environment variables
   - Verify database connection

2. **PWA Not Installable**
   - Verify `manifest.json` is accessible
   - Check service worker registration
   - Ensure HTTPS enabled
   - Clear browser cache

3. **Service Worker Issues**
   - Check console for errors
   - Verify scope is correct (`/`)
   - Ensure SW is registered early
   - Clear SW cache and re-register

---

## 📦 Dependencies

**Python:**
- `fastapi` - API framework
- `sqlalchemy` - ORM
- `openai` - OpenAI API client
- `pywebpush` - Web push notifications
- `py-vapid` - VAPID key generation

**JavaScript:**
- Vanilla JS (no frameworks)
- Service Worker API
- Push API
- Notifications API

---

## 🎨 Theme Updates

**Important:** Always use the child theme (`astra-child`) for customizations.

**To Update Parent Theme:**
1. Update Astra theme in WordPress
2. Child theme will remain unaffected
3. No custom code will be lost

**To Update Child Theme:**
1. Edit files in `wordpress/astra-child/`
2. Run `./deploy-child-theme.sh`
3. Upload ZIP to WordPress
4. Activate theme

---

## ✅ Next Steps

### **Recommended Actions:**

1. **Monitor Production**
   - Check Railway logs for errors
   - Monitor push notification delivery
   - Track user engagement

2. **Test PWA Features**
   - Install on mobile device
   - Test offline functionality
   - Verify push notifications

3. **Optimize Performance**
   - Monitor API response times
   - Check database query performance
   - Optimize embeddings retrieval

4. **Enhance Analytics**
   - Add more tracking events
   - Create custom dashboards
   - Set up automated reports

### **Future Enhancements:**

- [ ] User authentication & profiles
- [ ] Personalised recommendations (track mood reactions over time)
- [ ] Cloud-synced saved insights (currently localStorage only)
- [ ] Advanced search filters (by episode, topic, date)
- [ ] Multi-language support
- [ ] Referral tracking backend (link Share v2 invites to analytics)

---

## 📝 Notes

- **Version:** 5.0.0 (latest)
- **Last Widget Update:** March 28, 2026
- **Last Backend Update:** March 2026
- **Last Cleanup:** March 12, 2025
- **Deployment ZIP:** `wordpress/ask-mirror-talk-v5.0.0.zip` (351 KB)

**Production URLs:**
- API: `https://your-railway-url.railway.app`
- WordPress: `https://your-domain.com`

---

## 🤝 Contributing

When making changes:

1. Always edit the child theme, not parent
2. Test locally before deploying
3. Update version numbers
4. Document changes in git commits
5. Run cleanup script if adding/removing files

---

## 📞 Support

For issues or questions:
- Check Railway logs
- Review browser console
- Verify environment variables
- Check database connectivity

---

**Status:** ✅ All features implemented, tested, and production-ready!
