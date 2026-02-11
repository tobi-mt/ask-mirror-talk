# 🎯 Railway + Neon Deployment Checklist

Use this checklist to track your deployment progress.

## ✅ Pre-Deployment Checklist

### Neon Database Setup
- [ ] Created Neon account at https://neon.tech
- [ ] Created new project: `ask-mirror-talk-db`
- [ ] Enabled pgvector extension (SQL Editor: `CREATE EXTENSION vector;`)
- [ ] Copied connection string
- [ ] Converted connection string to SQLAlchemy format (+psycopg)
- [ ] Tested connection locally:
  ```bash
  export DATABASE_URL="your-neon-connection-string"
  python scripts/setup_neon.py
  ```
- [ ] Database initialized successfully (tables created)

### Code Preparation
- [ ] Code pushed to GitHub/Bitbucket
- [ ] `railway.toml` exists in repository root
- [ ] `Dockerfile` exists in repository root
- [ ] `.env.railway` reviewed for correct values
- [ ] All sensitive data removed from repository

## 🚀 Railway Deployment Checklist

### Railway Account Setup
- [ ] Created Railway account at https://railway.app
- [ ] Connected GitHub/Bitbucket account
- [ ] Repository access granted to Railway

### Project Creation
- [ ] Created new Railway project
- [ ] Selected "Deploy from GitHub repo"
- [ ] Connected to correct repository
- [ ] Railway detected Dockerfile automatically

### Environment Variables (Critical!)
Copy these to Railway Variables tab:

- [ ] `DATABASE_URL` - Neon connection string (with +psycopg)
- [ ] `APP_NAME` - Ask Mirror Talk
- [ ] `ENVIRONMENT` - production
- [ ] `RSS_URL` - Your podcast RSS feed
- [ ] `RSS_POLL_MINUTES` - 60
- [ ] `MAX_EPISODES_PER_RUN` - 10
- [ ] `EMBEDDING_PROVIDER` - local
- [ ] `WHISPER_MODEL` - base
- [ ] `TRANSCRIPTION_PROVIDER` - faster_whisper
- [ ] `TOP_K` - 6
- [ ] `MIN_SIMILARITY` - 0.15
- [ ] `RATE_LIMIT_PER_MINUTE` - 20
- [ ] `ALLOWED_ORIGINS` - Your WordPress domains (comma-separated)
- [ ] `ADMIN_ENABLED` - true
- [ ] `ADMIN_USER` - Your admin username
- [ ] `ADMIN_PASSWORD` - Secure password

### Networking
- [ ] Generated public domain in Railway Settings
- [ ] Domain noted: `https://______________.up.railway.app`
- [ ] Health check path configured: `/health`

### Deployment
- [ ] Build started automatically
- [ ] Build completed successfully (check logs)
- [ ] Deployment status shows "Active"
- [ ] No errors in deployment logs

## 📊 Data Loading Checklist

### Initial Data Load
Choose one method:

#### Method A: Load from Local Machine
- [ ] Set DATABASE_URL to Neon connection
- [ ] Set RSS_URL to podcast feed
- [ ] Run: `python -m app.ingestion.pipeline_optimized`
- [ ] Verified episodes loaded successfully

#### Method B: Load from Railway Shell
- [ ] Opened Railway shell (... menu → Shell)
- [ ] Run: `python -m app.ingestion.pipeline_optimized`
- [ ] Verified episodes loaded successfully

### Data Verification
- [ ] Episodes count > 0
- [ ] Chunks count > 0
- [ ] No errors in logs

## 🧪 Testing Checklist

### API Endpoint Tests
Replace `YOUR_APP_URL` with your Railway domain:

- [ ] Health check works:
  ```bash
  curl https://YOUR_APP_URL/health
  # Expected: {"status":"ok"}
  ```

- [ ] Status check shows data:
  ```bash
  curl https://YOUR_APP_URL/status
  # Expected: {"status":"ok","episodes":3,"chunks":354,"ready":true}
  ```

- [ ] Ask endpoint returns answers:
  ```bash
  curl -X POST https://YOUR_APP_URL/ask \
    -H "Content-Type: application/json" \
    -d '{"question": "What is Mirror Talk about?"}'
  # Expected: JSON with answer and citations
  ```

- [ ] Admin dashboard accessible:
  - Visit: `https://YOUR_APP_URL/admin`
  - [ ] Login page loads
  - [ ] Can login with credentials
  - [ ] Dashboard shows statistics

### CORS Testing
- [ ] WordPress domain allowed in CORS
- [ ] API accessible from WordPress site
- [ ] No CORS errors in browser console

## 🌐 WordPress Integration Checklist

### Update WordPress Files
- [ ] Located `ask-mirror-talk.js` file
- [ ] Updated API_URL to Railway domain:
  ```javascript
  const API_URL = 'https://YOUR_APP_URL/ask';
  ```
- [ ] Saved changes
- [ ] Cleared WordPress cache
- [ ] Cleared browser cache

### Widget Testing
- [ ] Widget loads on WordPress page
- [ ] Can type question in input field
- [ ] Submit button works
- [ ] Receives response from API
- [ ] Answer displays correctly
- [ ] Citations/sources show up
- [ ] No JavaScript errors in console

## 📈 Monitoring Checklist

### Railway Dashboard
- [ ] Bookmarked Railway project URL
- [ ] Checked resource usage (CPU, Memory)
- [ ] Reviewed deployment logs
- [ ] Set up any alerts (optional)

### Neon Dashboard
- [ ] Bookmarked Neon project URL
- [ ] Checked database size
- [ ] Reviewed query performance
- [ ] Noted connection limits

## 🔄 Maintenance Checklist

### Regular Tasks
- [ ] Set up weekly data updates:
  ```bash
  # Run weekly to update with new episodes
  python -m app.ingestion.pipeline_optimized
  ```
- [ ] Monitor error logs in Railway
- [ ] Check database size in Neon
- [ ] Review API usage metrics

### Optional Enhancements
- [ ] Set up automated backups (Neon has this built-in)
- [ ] Configure custom domain (Railway Settings → Domains)
- [ ] Set up monitoring/alerting (Railway integrations)
- [ ] Enable railway.json for more advanced config

## 🎉 Final Verification

### Everything Working?
- [ ] ✅ Neon database is active and responsive
- [ ] ✅ Railway deployment shows "Active" status
- [ ] ✅ All API endpoints return expected results
- [ ] ✅ Admin dashboard is accessible
- [ ] ✅ WordPress widget displays real answers
- [ ] ✅ No errors in any logs
- [ ] ✅ CORS working correctly
- [ ] ✅ Response times are acceptable (<2 seconds)

### Documentation
- [ ] Team members know how to access Railway
- [ ] Team members know how to access Neon
- [ ] Environment variables documented
- [ ] Deployment process documented
- [ ] Troubleshooting guide available (RAILWAY_NEON_SETUP.md)

## 📞 Support Resources

If you encounter issues:

1. **Check logs**: Railway Dashboard → Logs tab
2. **Database status**: Neon Dashboard → Monitoring
3. **Test connection**: `python scripts/setup_neon.py`
4. **Review docs**: `RAILWAY_NEON_SETUP.md`
5. **Common issues**:
   - Connection errors → Check DATABASE_URL format
   - Build failures → Check Dockerfile and dependencies
   - No data → Run ingestion pipeline
   - CORS errors → Check ALLOWED_ORIGINS variable

---

## 📊 Success Metrics

After completing this checklist:

- **Cost**: $0/month (free tiers)
- **Uptime**: 99.9%+
- **Response time**: <2 seconds
- **Data**: 3+ episodes loaded
- **Endpoints**: All working correctly
- **Integration**: WordPress widget functional

---

**Deployment Date**: _______________

**Railway URL**: _______________________________________________

**Neon Project**: _______________________________________________

**Status**: ⭕ In Progress | ✅ Complete

---

*Save this file and mark items as you complete them!*
