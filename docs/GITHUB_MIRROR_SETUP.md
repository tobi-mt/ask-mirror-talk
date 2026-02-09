# GitHub Mirror Setup Guide

## 🎯 Quick Setup (5 minutes)

### Step 1: Create GitHub Repository

1. **Go to**: https://github.com/new
2. **Repository name**: `ask-mirror-talk`
3. **Description**: Mirror Talk Podcast Q&A Service
4. **Visibility**: Choose **Public** (required for Railway free tier)
5. **Important**: ⚠️ **DO NOT** check any of these boxes:
   - ❌ Add a README file
   - ❌ Add .gitignore
   - ❌ Choose a license
6. Click **"Create repository"**

### Step 2: Add GitHub Remote & Push

Once you've created the GitHub repo, run these commands:

```bash
# Replace YOUR_GITHUB_USERNAME with your actual GitHub username
GITHUB_USERNAME="YOUR_GITHUB_USERNAME"

# Add GitHub as a remote
git remote add github "https://github.com/$GITHUB_USERNAME/ask-mirror-talk.git"

# Push all code to GitHub
git push github main

# If you need to authenticate, GitHub will prompt you
# Use a Personal Access Token (not password) when prompted
```

### Step 3: Create Dual-Push Alias

```bash
# Create an alias to push to both remotes at once
git config alias.pushall '!git push origin main && git push github main'

# Test it
git pushall
```

### Step 4: Verify Setup

```bash
# Check your remotes
git remote -v

# Should show:
# origin   https://bitbucket.org/...  (Bitbucket)
# github   https://github.com/...     (GitHub)
```

---

## 🔐 GitHub Authentication

If GitHub asks for authentication:

### Option 1: Personal Access Token (Recommended)

1. Go to: https://github.com/settings/tokens
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Name: `Railway Deploy`
4. Expiration: `No expiration` (or your preference)
5. Scopes: Check ✅ **repo** (full control)
6. Click **"Generate token"**
7. **Copy the token** (you won't see it again!)
8. When git asks for password, paste the token

### Option 2: GitHub CLI

```bash
# Install GitHub CLI (if not installed)
brew install gh

# Authenticate
gh auth login

# Then push
git push github main
```

---

## 🚀 After Setup

### Daily Workflow

```bash
# Make your changes
git add .
git commit -m "Your commit message"

# Push to both Bitbucket and GitHub
git pushall

# Railway will auto-deploy from GitHub! 🎉
```

### Push to Specific Remote

```bash
# Push to Bitbucket only
git push origin main

# Push to GitHub only
git push github main
```

---

## ✅ Verification Checklist

- [ ] GitHub repo created (public, empty)
- [ ] GitHub remote added (`git remote -v` shows it)
- [ ] Code pushed to GitHub (visit your GitHub repo URL)
- [ ] `pushall` alias configured
- [ ] Tested dual-push successfully

---

## 🎯 Next: Deploy to Railway

Once GitHub is set up:

1. Go to: https://railway.app
2. Click **"Login"** → **"Login with GitHub"**
3. Click **"New Project"**
4. Select **"Deploy from GitHub repo"**
5. Choose: `ask-mirror-talk`
6. Add environment variables (see `DEPLOY_NOW.md`)
7. Generate domain
8. Test and enjoy! 🎉

---

## 🐛 Troubleshooting

### "Authentication failed"
- Use a Personal Access Token instead of password
- See "GitHub Authentication" section above

### "Remote already exists"
```bash
# Remove and re-add
git remote remove github
git remote add github "https://github.com/YOUR_USERNAME/ask-mirror-talk.git"
```

### "Repository not found"
- Make sure the repo exists on GitHub
- Check the URL is correct
- Verify you're logged into the right GitHub account

### Can't push to GitHub
```bash
# Check if you have push access
git push github main

# If authentication fails, use GitHub CLI:
gh auth login
git push github main
```

---

## 📋 Quick Reference

```bash
# View remotes
git remote -v

# Push to both
git pushall

# Push to Bitbucket
git push origin main

# Push to GitHub
git push github main

# Update GitHub remote URL
git remote set-url github NEW_URL
```

---

**Ready?** Create your GitHub repo and let's push the code!
