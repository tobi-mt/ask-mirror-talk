# Ask Mirror Talk - Project Status

**Last Updated:** March 12, 2025  
**Status:** ✅ Production Ready & Clean

---

## 🎯 Project Overview

Ask Mirror Talk is a Q&A system with PWA capabilities and push notifications for daily QOTD (Question of the Day) and new episode alerts.

---

## ✅ Completed Features

### 1. **PWA (Progressive Web App)**
- ✅ Installable on mobile and desktop
- ✅ Offline support with service worker
- ✅ App manifest with custom icons
- ✅ Native app-like experience

**Files:**
- `wordpress/astra-child/manifest.json`
- `wordpress/astra-child/sw.js`
- `wordpress/astra-child/pwa-icon-*.png`

### 2. **Push Notifications**
- ✅ Daily QOTD notifications (Railway cron)
- ✅ New episode alerts
- ✅ Opt-in/opt-out UI
- ✅ Platform detection (iOS, Safari, PWA)
- ✅ VAPID key management (base64url format)

**Backend:**
- `app/notifications/push.py` - Push notification service
- `scripts/send_daily_qotd.py` - Daily QOTD cron job
- `app/api/main.py` - Push notification API endpoints

**Frontend:**
- `wordpress/astra-child/ask-mirror-talk.js` - Notification opt-in logic
- `wordpress/astra-child/ask-mirror-talk.css` - Notification UI styles

### 3. **WordPress Child Theme**
- ✅ All customizations moved to `astra-child` theme
- ✅ Safe from parent theme updates
- ✅ Deployment script provided
- ✅ Parent theme cleaned (no custom files)

**Location:** `wordpress/astra-child/`

**Key Files:**
- `functions.php` - Theme initialization
- `ask-mirror-talk.php` - Widget PHP code
- `ask-mirror-talk.js` - Widget JavaScript
- `ask-mirror-talk.css` - Widget styles
- `analytics-addon.js` - Analytics tracking
- `manifest.json` - PWA manifest
- `sw.js` - Service worker
- `README.md` - Installation instructions
- `deploy-child-theme.sh` - Deployment helper

### 4. **Project Cleanup**
- ✅ Removed archived documentation
- ✅ Removed `.agents/` skill references
- ✅ Removed old deployment configs (render, nixpacks)
- ✅ Removed virtual environments
- ✅ Removed Python cache files
- ✅ Removed macOS metadata (`.DS_Store`)
- ✅ Removed unnecessary markdown files
- ✅ Removed custom files from parent theme

**What Was Removed:**
- `docs/` - Archived documentation
- `.agents/` - Skill references
- `.env.local`, `.env.railway` - Old env files
- `render.yaml`, `render-build.sh` - Render config
- `nixpacks.toml` - Nixpacks config
- `docker-compose.yml`, `docker-compose.prod.yml` - Old compose files
- `Dockerfile.api` - Unused API Dockerfile
- `setup-github-mirror.sh` - Old setup script
- `.venv/`, `venv/` - Virtual environments
- `ask_mirror_talk.egg-info/` - Python egg info
- `.neon` - Neon config file
- `scripts/README_MONITORING.md` - Monitoring docs
- `wordpress/astra/*` - All custom files from parent theme

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
│   │   ├── pwa-icon-*.png
│   │   ├── README.md
│   │   └── deploy-child-theme.sh
│   ├── astra/                   # Parent theme (clean, no custom files)
│   └── astra-child-mirror-talk.zip
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
1. Upload `wordpress/astra-child-mirror-talk.zip` to WordPress
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

- [ ] User authentication
- [ ] Personalized recommendations
- [ ] Saved questions/favorites
- [ ] Share functionality
- [ ] Advanced search filters
- [ ] Multi-language support

---

## 📝 Notes

- **Version:** 3.9.0 (latest)
- **Last Widget Update:** March 2025
- **Last Backend Update:** March 2025
- **Last Cleanup:** March 12, 2025

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
