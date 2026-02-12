# 🔄 Git Remotes Guide - Bitbucket + GitHub

Your repository is synced to **two remotes**:
- **Bitbucket** (origin) - Primary repository
- **GitHub** (github) - Connected to Railway for auto-deployment

## Current Configuration

```bash
origin → Bitbucket: https://bitbucket.org/tobi-projects/ask-mirror-talk.git
github → GitHub:    https://github.com/tobi-mt/ask-mirror-talk.git
```

## Why Two Remotes?

Railway deploys from **GitHub**, not Bitbucket. To trigger Railway deployments, you must push to the GitHub remote.

## Push Commands

### Push to Both Remotes (Recommended)
```bash
# Push to Bitbucket (your primary repo)
git push origin main

# Push to GitHub (triggers Railway deployment)
git push github main
```

### Quick Command to Push to Both
```bash
# Add this as a git alias
git config alias.pushall '!git push origin main && git push github main'

# Then use:
git pushall
```

### Or Push to Both at Once
```bash
git push origin main && git push github main
```

## Typical Workflow

1. **Make changes to your code**
2. **Commit changes:**
   ```bash
   git add -A
   git commit -m "Your commit message"
   ```
3. **Push to both remotes:**
   ```bash
   git push origin main   # Bitbucket
   git push github main   # GitHub → Triggers Railway
   ```

## What Just Happened

✅ Pushed 7 commits to GitHub:
- `26178db` - Optimize startup time for Railway healthcheck
- `d227f81` - Add comprehensive Railway startup fix documentation
- `1cf6ea8` - Add quick status check guide for Railway deployment
- `0848d4d` - **Critical: Optimize app startup to pass Railway 100s healthcheck**
- `b1c1d01` - Add critical startup fix documentation

✅ **Railway should now detect the push and start building!**

## Monitor Railway Deployment

1. Go to: https://railway.app/dashboard
2. Click on your `ask-mirror-talk` project
3. You should see "Building..." status
4. Watch the logs for:
   - Docker build progress
   - Healthcheck attempts
   - "Healthy" status ✅

## Expected Timeline

```
Now        → Railway detects GitHub push
+30s       → Build starts (Docker image)
+2-3 min   → Build completes, deployment starts
+3-4 min   → Healthcheck passes ✅
```

## Troubleshooting

### Railway still not building?

1. **Check Railway project settings:**
   - Click your service → "Settings" → "Source"
   - Verify it's connected to `tobi-mt/ask-mirror-talk` (GitHub)
   - Check if auto-deploy is enabled

2. **Manual trigger:**
   - Go to "Deployments" tab
   - Click "Deploy" → "Redeploy"

3. **Check GitHub webhook:**
   - Go to GitHub repo → Settings → Webhooks
   - Look for Railway webhook
   - Check recent deliveries

### Need to verify GitHub sync?

```bash
# Check what's on GitHub
git fetch github
git log github/main

# Verify both remotes are in sync
git log origin/main..github/main  # Should be empty
```

## Future Deployments

**Remember:** Always push to BOTH remotes:
```bash
git push origin main   # ← Bitbucket (backup)
git push github main   # ← GitHub (triggers Railway)
```

Or set up automatic push to both:
```bash
# Edit .git/config and add to [remote "origin"]
[remote "origin"]
    url = https://bitbucket.org/tobi-projects/ask-mirror-talk.git
    pushurl = https://bitbucket.org/tobi-projects/ask-mirror-talk.git
    pushurl = https://github.com/tobi-mt/ask-mirror-talk.git
    fetch = +refs/heads/*:refs/remotes/origin/*

# Then `git push origin main` will push to both!
```

---

**Status:** ✅ All changes pushed to GitHub
**Next:** Railway should be building now - check dashboard!
**ETA:** Deployment in 3-4 minutes
