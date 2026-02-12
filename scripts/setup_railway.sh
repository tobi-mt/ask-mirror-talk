#!/bin/bash

# Railway Setup Script
# This script helps configure your Railway project from the CLI

set -e

echo "=== Railway Setup for Ask Mirror Talk ==="
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
    echo "✅ Railway CLI installed"
fi

# Login to Railway
echo ""
echo "📝 Logging into Railway..."
railway login

# Initialize project
echo ""
echo "📝 Initializing Railway project..."
railway init

# Link to existing project or create new
echo ""
read -p "Do you have an existing Railway project? (y/n): " has_project

if [ "$has_project" = "y" ]; then
    echo "Run: railway link"
    echo "Then run this script again"
    exit 0
fi

# Set environment variables
echo ""
echo "📝 Setting up environment variables..."
echo ""

read -p "Enter your Neon DATABASE_URL: " database_url
railway variables set DATABASE_URL="$database_url"

read -p "Enter your RSS_URL [https://anchor.fm/s/261b1464/podcast/rss]: " rss_url
rss_url=${rss_url:-https://anchor.fm/s/261b1464/podcast/rss}
railway variables set RSS_URL="$rss_url"

read -p "Enter ADMIN_USER [tobi]: " admin_user
admin_user=${admin_user:-tobi}
railway variables set ADMIN_USER="$admin_user"

read -p "Enter ADMIN_PASSWORD: " admin_password
railway variables set ADMIN_PASSWORD="$admin_password"

# Set optional variables with defaults
railway variables set APP_NAME="Ask Mirror Talk"
railway variables set ENVIRONMENT="production"
railway variables set RSS_POLL_MINUTES="60"
railway variables set MAX_EPISODES_PER_RUN="10"
railway variables set EMBEDDING_PROVIDER="local"
railway variables set WHISPER_MODEL="base"
railway variables set TRANSCRIPTION_PROVIDER="faster_whisper"
railway variables set TOP_K="6"
railway variables set MIN_SIMILARITY="0.15"
railway variables set RATE_LIMIT_PER_MINUTE="20"
railway variables set ADMIN_ENABLED="true"

echo ""
echo "✅ Environment variables set!"

# Deploy
echo ""
read -p "Deploy now? (y/n): " deploy_now

if [ "$deploy_now" = "y" ]; then
    echo "🚀 Deploying to Railway..."
    railway up
    echo ""
    echo "✅ Deployment initiated!"
    echo ""
    echo "View logs: railway logs"
    echo "Open dashboard: railway open"
fi

echo ""
echo "=== Next Steps ==="
echo "1. Wait for deployment to complete"
echo "2. Check logs: railway logs"
echo "3. Get your public URL: railway open"
echo "4. Run ingestion: railway run python scripts/ingest_all_episodes.py"
echo "5. Test endpoints: curl https://your-url.railway.app/health"
echo ""
echo "✅ Setup complete!"
