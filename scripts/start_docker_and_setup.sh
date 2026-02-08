#!/bin/bash
# Mirror Talk - Start Docker and Run Setup

echo "=========================================="
echo "🐋 Starting Docker..."
echo "=========================================="
echo ""

# Check if Docker Desktop is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed."
    echo ""
    echo "Please install Docker Desktop for Mac:"
    echo "https://www.docker.com/products/docker-desktop"
    echo ""
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Docker is not running. Starting Docker Desktop..."
    echo ""
    echo "Please wait while Docker starts..."
    echo "(This may take 30-60 seconds)"
    echo ""
    
    # Try to start Docker Desktop
    open -a Docker
    
    # Wait for Docker to be ready
    echo "Waiting for Docker to be ready..."
    for i in {1..60}; do
        if docker info > /dev/null 2>&1; then
            echo ""
            echo "✓ Docker is now running!"
            break
        fi
        echo -n "."
        sleep 2
    done
    
    if ! docker info > /dev/null 2>&1; then
        echo ""
        echo "❌ Docker failed to start automatically."
        echo ""
        echo "Please:"
        echo "1. Manually open Docker Desktop from Applications"
        echo "2. Wait for Docker to fully start (whale icon in menu bar)"
        echo "3. Run this script again"
        echo ""
        exit 1
    fi
else
    echo "✓ Docker is already running!"
fi

echo ""
echo "=========================================="
echo "🚀 Running Mirror Talk Setup..."
echo "=========================================="
echo ""

# Now run the main setup script
exec ./scripts/setup_mirror_talk.sh
