#!/bin/bash
# GitHub Mirror Setup for Railway Deployment

echo "=========================================="
echo "GitHub Mirror Setup"
echo "=========================================="

# Step 1: Instructions to create GitHub repo
echo ""
echo "📋 STEP 1: Create GitHub Repository"
echo ""
echo "1. Go to: https://github.com/new"
echo "2. Repository name: ask-mirror-talk"
echo "3. Description: Mirror Talk Podcast Q&A Service"
echo "4. Choose: Public (for Railway free tier)"
echo "5. ⚠️  DO NOT initialize with README, .gitignore, or license"
echo "6. Click 'Create repository'"
echo ""
echo "Press Enter when you've created the GitHub repo..."
read

# Step 2: Get GitHub username
echo ""
echo "📝 STEP 2: Enter your GitHub username"
echo ""
read -p "GitHub username: " GITHUB_USERNAME

if [ -z "$GITHUB_USERNAME" ]; then
    echo "❌ Error: GitHub username cannot be empty"
    exit 1
fi

# Step 3: Add GitHub remote
echo ""
echo "🔗 STEP 3: Adding GitHub as remote..."
echo ""

GITHUB_URL="https://github.com/$GITHUB_USERNAME/ask-mirror-talk.git"
echo "GitHub URL: $GITHUB_URL"

# Check if github remote already exists
if git remote get-url github &> /dev/null; then
    echo "⚠️  'github' remote already exists. Updating URL..."
    git remote set-url github "$GITHUB_URL"
else
    git remote add github "$GITHUB_URL"
fi

echo "✅ GitHub remote added"

# Step 4: Push to GitHub
echo ""
echo "📤 STEP 4: Pushing code to GitHub..."
echo ""

git push github main --force

if [ $? -eq 0 ]; then
    echo "✅ Successfully pushed to GitHub!"
else
    echo "❌ Failed to push to GitHub. You may need to authenticate."
    echo ""
    echo "Try running:"
    echo "  git push github main"
    exit 1
fi

# Step 5: Create push alias
echo ""
echo "⚙️  STEP 5: Creating dual-push alias..."
echo ""

git config alias.pushall '!git push origin main && git push github main'
echo "✅ Alias 'pushall' created"

# Step 6: Verify setup
echo ""
echo "🔍 STEP 6: Verifying setup..."
echo ""
git remote -v

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. ✅ GitHub repo created and synced"
echo "2. ✅ Dual-push configured"
echo ""
echo "💡 Usage:"
echo "  - Push to both repos: git pushall"
echo "  - Push to Bitbucket only: git push origin main"
echo "  - Push to GitHub only: git push github main"
echo ""
echo "🚀 Deploy to Railway:"
echo "  1. Go to: https://railway.app"
echo "  2. Login with GitHub"
echo "  3. New Project → Deploy from GitHub repo"
echo "  4. Select: ask-mirror-talk"
echo "  5. Add environment variables (see DEPLOY_NOW.md)"
echo ""
echo "GitHub repo: https://github.com/$GITHUB_USERNAME/ask-mirror-talk"
echo ""
