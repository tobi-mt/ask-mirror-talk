#!/bin/bash
# Mirror Talk Podcast - Quick Setup
# Customized for: https://anchor.fm/s/261b1464/podcast/rss

set -e

echo "=========================================="
echo "🎙️  Mirror Talk: Soulful Conversations"
echo "    Quick Ingestion Setup"
echo "=========================================="
echo ""

# Set the RSS URL
export RSS_URL='https://anchor.fm/s/261b1464/podcast/rss'

# Update .env file
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << 'EOF'
# Mirror Talk Podcast Configuration
RSS_URL=https://anchor.fm/s/261b1464/podcast/rss

# Memory-optimized settings
EMBEDDING_PROVIDER=sentence_transformers
WHISPER_MODEL=base
MAX_EPISODES_PER_RUN=10
RATE_LIMIT_PER_MINUTE=20

# Database
DATABASE_URL=postgresql+psycopg://mirror:mirror@db:5432/mirror_talk

# Admin access
ADMIN_ENABLED=true
ADMIN_USER=admin
ADMIN_PASSWORD=change-me-please

# Retrieval
TOP_K=6
MIN_SIMILARITY=0.15
EOF
    echo "✓ Created .env file"
else
    # Update existing .env
    if ! grep -q "RSS_URL" .env; then
        echo "RSS_URL=https://anchor.fm/s/261b1464/podcast/rss" >> .env
        echo "✓ Added RSS_URL to .env"
    else
        echo "✓ .env already configured"
    fi
fi

echo ""
echo "=========================================="
echo "Choose your ingestion approach:"
echo "=========================================="
echo ""
echo "1) Quick Test (5 episodes, ~15-25 minutes)"
echo "   Perfect for testing if everything works"
echo ""
echo "2) Standard (10 episodes, ~30-50 minutes)"
echo "   Good balance for getting started"
echo ""
echo "3) Bulk (ALL episodes, 1-3 hours)"
echo "   Complete archive ingestion"
echo ""
read -p "Select [1-3]: " choice

case $choice in
    1)
        MAX_EPISODES=5
        echo ""
        echo "Will process 5 episodes (~15-25 minutes)"
        ;;
    2)
        MAX_EPISODES=10
        echo ""
        echo "Will process 10 episodes (~30-50 minutes)"
        ;;
    3)
        MAX_EPISODES=""
        echo ""
        echo "Will process ALL episodes (may take 1-3 hours)"
        echo "⚠️  This is a long process. Consider running in tmux/screen."
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
read -p "Continue? [y/N]: " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "=========================================="
echo "Starting Ingestion..."
echo "=========================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "⚠️  Docker is not running. Please start Docker first."
    exit 1
fi

# Start services if not running
echo "Ensuring services are running..."
docker-compose -f docker-compose.prod.yml up -d db
sleep 5

# Run ingestion
if [ -z "$MAX_EPISODES" ]; then
    docker-compose -f docker-compose.prod.yml run --rm app \
        python scripts/bulk_ingest.py
else
    docker-compose -f docker-compose.prod.yml run --rm app \
        python scripts/bulk_ingest.py --max-episodes "$MAX_EPISODES"
fi

echo ""
echo "=========================================="
echo "✓ Ingestion Complete!"
echo "=========================================="
echo ""

# Start the API service
echo "Starting API service..."
docker-compose -f docker-compose.prod.yml up -d app

echo "Waiting for service to be ready..."
sleep 5

# Check status
echo ""
echo "Checking status..."
if command -v curl &> /dev/null; then
    STATUS=$(curl -s http://localhost:8000/status 2>/dev/null || echo "{}")
    echo "$STATUS" | jq '.' 2>/dev/null || echo "$STATUS"
fi

echo ""
echo "=========================================="
echo "🎉 Your Ask Mirror Talk service is ready!"
echo "=========================================="
echo ""
echo "Test it now:"
echo ""
echo "curl -X POST http://localhost:8000/ask \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"question\": \"What topics do you discuss on Mirror Talk?\"}'"
echo ""
echo "Or visit: http://localhost:8000/admin"
echo "  Username: admin"
echo "  Password: change-me-please (update this in .env!)"
echo ""
echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo ""
echo "1. Test your API with the curl command above"
echo "2. Change your admin password in .env"
echo "3. Set up automatic updates:"
echo "   docker-compose -f docker-compose.prod.yml up -d worker"
echo ""
echo "Monitor logs:"
echo "   docker-compose -f docker-compose.prod.yml logs -f app"
echo ""
