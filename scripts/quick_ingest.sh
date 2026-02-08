#!/bin/bash
# Quick Start Ingestion Script
# This script helps you get your podcast data ingested quickly

set -e

echo "=========================================="
echo "Ask Mirror Talk - Quick Ingestion Setup"
echo "=========================================="
echo ""

# Check if RSS_URL is set
if [ -z "$RSS_URL" ]; then
    echo "⚠️  RSS_URL not set!"
    echo ""
    echo "Please set your RSS feed URL:"
    echo "  export RSS_URL='https://your-podcast-feed.com/feed.xml'"
    echo ""
    echo "Or add it to your .env file:"
    echo "  echo 'RSS_URL=https://your-podcast-feed.com/feed.xml' >> .env"
    echo ""
    exit 1
fi

echo "RSS Feed: $RSS_URL"
echo ""

# Check current status
echo "Checking current status..."
if command -v curl &> /dev/null; then
    STATUS=$(curl -s http://localhost:8000/status 2>/dev/null || echo "")
    if [ -n "$STATUS" ]; then
        CHUNKS=$(echo "$STATUS" | grep -o '"chunks":[0-9]*' | grep -o '[0-9]*' || echo "0")
        EPISODES=$(echo "$STATUS" | grep -o '"episodes":[0-9]*' | grep -o '[0-9]*' || echo "0")
        echo "  Episodes: $EPISODES"
        echo "  Chunks: $CHUNKS"
        echo ""
        
        if [ "$CHUNKS" -gt "0" ]; then
            echo "✓ Your website is already ready!"
            echo ""
            read -p "Do you want to ingest more episodes? [y/N]: " -n 1 -r
            echo ""
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 0
            fi
        fi
    fi
fi

# Choose ingestion method
echo "Choose ingestion method:"
echo ""
echo "1) Quick (3-5 episodes, ~10-15 minutes)"
echo "2) Bulk (all episodes, may take 1-5 hours)"
echo "3) Custom (specify number)"
echo ""
read -p "Select [1-3]: " choice

case $choice in
    1)
        MAX_EPISODES=5
        echo "Will process up to 5 episodes"
        ;;
    2)
        MAX_EPISODES=""
        echo "Will process ALL episodes from feed"
        ;;
    3)
        read -p "Number of episodes: " MAX_EPISODES
        echo "Will process up to $MAX_EPISODES episodes"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "Starting Ingestion..."
echo "=========================================="
echo ""

# Check if running in Docker
if [ -f "docker-compose.prod.yml" ]; then
    echo "Running in Docker mode..."
    if [ -z "$MAX_EPISODES" ]; then
        docker-compose -f docker-compose.prod.yml run --rm app python scripts/bulk_ingest.py
    else
        docker-compose -f docker-compose.prod.yml run --rm app python scripts/bulk_ingest.py --max-episodes "$MAX_EPISODES"
    fi
else
    echo "Running in local mode..."
    if [ -z "$MAX_EPISODES" ]; then
        python scripts/bulk_ingest.py
    else
        python scripts/bulk_ingest.py --max-episodes "$MAX_EPISODES"
    fi
fi

echo ""
echo "=========================================="
echo "Checking Results..."
echo "=========================================="
echo ""

# Check final status
sleep 2
if command -v curl &> /dev/null; then
    STATUS=$(curl -s http://localhost:8000/status 2>/dev/null || echo "")
    if [ -n "$STATUS" ]; then
        CHUNKS=$(echo "$STATUS" | grep -o '"chunks":[0-9]*' | grep -o '[0-9]*' || echo "0")
        EPISODES=$(echo "$STATUS" | grep -o '"episodes":[0-9]*' | grep -o '[0-9]*' || echo "0")
        echo "Final Status:"
        echo "  Episodes: $EPISODES"
        echo "  Chunks: $CHUNKS"
        echo ""
        
        if [ "$CHUNKS" -gt "0" ]; then
            echo "✓ SUCCESS! Your website can now answer questions!"
            echo ""
            echo "Test it:"
            echo "  curl -X POST http://localhost:8000/ask \\"
            echo "    -H 'Content-Type: application/json' \\"
            echo "    -d '{\"question\": \"What topics do you discuss?\"}'"
        else
            echo "⚠️  No chunks created. Check logs for errors:"
            echo "  docker-compose logs -f app"
        fi
    fi
fi

echo ""
echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo ""
echo "1. Test your website:"
echo "   Open http://localhost:8000/admin"
echo ""
echo "2. Monitor ingestion:"
echo "   docker-compose logs -f app"
echo ""
echo "3. Set up automatic updates:"
echo "   The scheduler will check for new episodes every hour"
echo ""
