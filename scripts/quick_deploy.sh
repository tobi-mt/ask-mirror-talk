#!/usr/bin/env bash
# Quick deployment script for Railway + Neon
# Run this after setting up Neon database and configuring Railway

set -e

echo "🚀 Ask Mirror Talk - Railway + Neon Quick Setup"
echo "================================================"

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL environment variable is not set"
    echo ""
    echo "Please set your Neon connection string:"
    echo "export DATABASE_URL='postgresql+psycopg://user:pass@host/db?sslmode=require'"
    exit 1
fi

echo "✓ DATABASE_URL is set"

# Verify Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ ERROR: Python 3 is not installed"
    exit 1
fi

echo "✓ Python 3 is available"

# Step 1: Initialize Neon database
echo ""
echo "📊 Step 1: Initializing Neon database..."
python3 scripts/setup_neon.py
if [ $? -ne 0 ]; then
    echo "❌ Database initialization failed"
    exit 1
fi

# Step 2: Load initial data (optional)
echo ""
read -p "📥 Step 2: Load initial podcast data? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Loading data (this may take a few minutes)..."
    python3 -m app.ingestion.pipeline_optimized
    if [ $? -eq 0 ]; then
        echo "✓ Data loaded successfully"
    else
        echo "⚠️  Data loading had issues, but you can continue"
    fi
else
    echo "⏭️  Skipping data load (you can do this later)"
fi

# Step 3: Test the setup
echo ""
echo "🧪 Step 3: Testing database connection..."
python3 -c "
from app.core.db import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) FROM episodes'))
    episodes = result.scalar()
    result = conn.execute(text('SELECT COUNT(*) FROM chunks'))
    chunks = result.scalar()
    print(f'✓ Database connected: {episodes} episodes, {chunks} chunks')
"

if [ $? -ne 0 ]; then
    echo "⚠️  Database test had issues"
fi

# Summary
echo ""
echo "================================================"
echo "✅ Setup Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Push to GitHub (if not already done):"
echo "   git add ."
echo "   git commit -m 'Railway + Neon deployment setup'"
echo "   git push"
echo ""
echo "2. Deploy to Railway:"
echo "   - Go to https://railway.app"
echo "   - Create new project from your GitHub repo"
echo "   - Add environment variables from .env.railway"
echo "   - Generate public domain"
echo ""
echo "3. Test your API:"
echo "   curl https://your-app.up.railway.app/health"
echo "   curl https://your-app.up.railway.app/status"
echo ""
echo "4. Update WordPress with your Railway URL"
echo ""
echo "📚 See RAILWAY_NEON_SETUP.md for detailed instructions"
echo "================================================"
