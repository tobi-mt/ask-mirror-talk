# Railway.app Bitbucket Integration

## Current Status (2026)

Railway **does not natively support Bitbucket** integration. Railway only supports:
- ✅ **GitHub** (native integration)
- ✅ **GitLab** (native integration)
- ❌ **Bitbucket** (not supported)

## 🔧 Solutions for Bitbucket Users

### **Option 1: Mirror to GitHub (Recommended)**

Create a GitHub mirror of your Bitbucket repo and sync automatically.

#### Setup Steps:

```bash
# 1. Create a new GitHub repository (empty, no README)
# Go to: https://github.com/new
# Name: ask-mirror-talk
# Keep it public or private
# Don't initialize with README

# 2. Add GitHub as a second remote
git remote add github https://github.com/YOUR_USERNAME/ask-mirror-talk.git

# 3. Push to both remotes
git push origin main        # Bitbucket (existing)
git push github main        # GitHub (new)

# 4. Create an alias for easy dual-push
git config alias.pushall '!git push origin main && git push github main'

# Now you can use:
git pushall
```

#### Automated Sync (Optional):
```bash
# Create a post-commit hook to auto-push to GitHub
cat > .git/hooks/post-commit << 'EOF'
#!/bin/bash
git push github main &
EOF

chmod +x .git/hooks/post-commit
```

---

### **Option 2: Deploy from Docker Hub**

Build Docker image locally and deploy to Railway via Docker Hub.

#### Setup Steps:

```bash
# 1. Create Docker Hub account: https://hub.docker.com

# 2. Build and push image
docker build -t YOUR_USERNAME/ask-mirror-talk:latest .
docker push YOUR_USERNAME/ask-mirror-talk:latest

# 3. In Railway:
# - New Project
# - Deploy Docker Image
# - Enter: YOUR_USERNAME/ask-mirror-talk:latest
```

**Downside**: Manual push required for each update (no auto-deploy).

---

### **Option 3: Use GitHub Actions for CI/CD**

Keep code in Bitbucket, use GitHub Actions to deploy to Railway.

#### Setup:

1. Mirror to GitHub (see Option 1)
2. Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Railway

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Railway
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
        run: |
          npm install -g @railway/cli
          railway up --service YOUR_SERVICE_ID
```

---

### **Option 4: Alternative Platforms with Bitbucket Support**

If you must use Bitbucket directly, consider these alternatives:

#### **A. Render.com** (your current platform)
- ✅ Supports Bitbucket
- ❌ But you're migrating away due to cost/limits

#### **B. Heroku**
- ✅ Supports Bitbucket (via Heroku Git)
- ❌ No free tier anymore
- 💰 Cost: ~$7/month minimum

#### **C. Fly.io with Bitbucket Pipelines**
- ✅ Free tier available
- ✅ Can deploy via Bitbucket Pipelines
- 📝 Requires pipeline configuration

**Example `bitbucket-pipelines.yml`:**
```yaml
pipelines:
  branches:
    main:
      - step:
          name: Deploy to Fly.io
          script:
            - curl -L https://fly.io/install.sh | sh
            - flyctl deploy --remote-only
```

#### **D. DigitalOcean App Platform**
- ✅ Supports Bitbucket
- 💰 Cost: $5/month (starter tier)
- ✅ Simple setup

---

## 🎯 **Recommended Solution for You**

### **Mirror Bitbucket to GitHub** (Best option)

**Why:**
- ✅ Free (both Bitbucket and GitHub)
- ✅ Keeps your Bitbucket repo as source of truth
- ✅ Automatic sync with git aliases
- ✅ Railway auto-deploys from GitHub
- ✅ No ongoing maintenance
- ✅ 5-minute setup

**How:**
```bash
# One-time setup
git remote add github https://github.com/YOUR_USERNAME/ask-mirror-talk.git
git push github main

# Daily workflow (after committing):
git push origin main   # Push to Bitbucket
git push github main   # Push to GitHub (Railway auto-deploys)

# Or use alias:
git config alias.pushall '!git push origin main && git push github main'
git pushall
```

---

## 🚀 **Quick Start: Mirror Your Repo Now**

### Step 1: Create GitHub Repo
1. Go to: https://github.com/new
2. Repository name: `ask-mirror-talk`
3. Keep it **public** (for Railway free tier) or private (if you have Railway Pro)
4. **Don't** initialize with README
5. Click "Create repository"

### Step 2: Add GitHub Remote
```bash
cd /Users/tobi/PycharmProjects/pythonProject/ask-mirror-talk

# Add GitHub as second remote
git remote add github https://github.com/YOUR_USERNAME/ask-mirror-talk.git

# Push all branches and tags
git push github --all
git push github --tags

# Verify both remotes
git remote -v
# Should show:
# origin   https://bitbucket.org/... (Bitbucket)
# github   https://github.com/...   (GitHub)
```

### Step 3: Create Push Alias
```bash
# Add to your git config
git config alias.pushall '!git push origin main && git push github main'

# Test it
git pushall
```

### Step 4: Deploy to Railway
1. Go to: https://railway.app
2. Login with GitHub
3. New Project → Deploy from GitHub
4. Select: `ask-mirror-talk` (from GitHub)
5. Done! 🎉

---

## 📊 **Comparison**

| Method | Setup Time | Ongoing Work | Auto-Deploy | Cost |
|--------|-----------|--------------|-------------|------|
| **Mirror to GitHub** | 5 min | Push to both | ✅ Yes | Free |
| Docker Hub | 10 min | Manual deploy | ❌ No | Free |
| GitHub Actions | 15 min | Auto sync | ✅ Yes | Free |
| Use Fly.io instead | 20 min | Pipeline config | ✅ Yes | Free |
| Use DO App Platform | 10 min | Auto from BB | ✅ Yes | $5/mo |

---

## ✅ **My Recommendation**

**Use the GitHub mirror approach:**

1. It takes 5 minutes to setup
2. Your Bitbucket repo remains the source
3. Railway auto-deploys from GitHub
4. No ongoing maintenance
5. Completely free
6. Works perfectly

**Ready to set it up?** I can help you create the GitHub repo and configure the dual-push!

---

## 🔄 **Alternative: Stay with Current Git Setup**

If you don't want to mirror, you could also:
- Keep using Bitbucket for development
- Manually export/deploy when ready
- Use Docker Hub for Railway deploys

But the GitHub mirror is much simpler and more automated.

**What would you like to do?**
1. Mirror to GitHub (recommended)
2. Try Docker Hub approach
3. Explore alternative platforms
4. Something else?
