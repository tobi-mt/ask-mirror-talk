#!/bin/bash
# Mirror Talk - Local Setup (No Docker Required)
# This script sets up and runs everything locally on your Mac

set -e

echo "=========================================="
echo "🎙️  Mirror Talk: Local Setup"
echo "    (No Docker Required)"
echo "=========================================="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed."
    echo "Please install Python 3.10+ from https://www.python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Found Python $PYTHON_VERSION"

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo ""
    echo "⚠️  PostgreSQL is not installed."
    echo ""
    echo "Installing PostgreSQL with Homebrew..."
    
    if ! command -v brew &> /dev/null; then
        echo "❌ Homebrew is not installed."
        echo ""
        echo "Install Homebrew first:"
        echo '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        echo ""
        echo "Then run this script again."
        exit 1
    fi
    
    brew install postgresql@16 pgvector
    brew services start postgresql@16
    sleep 5
else
    echo "✓ PostgreSQL is installed"
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -e ".[transcription,embeddings]"

# Configure environment
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file..."
    cat > .env << 'EOF'
# Mirror Talk Podcast Configuration (Local Setup)
RSS_URL=https://anchor.fm/s/261b1464/podcast/rss

# Database (Local PostgreSQL)
DATABASE_URL=postgresql+psycopg://mirror:mirror@localhost:5432/mirror_talk

# Memory-optimized settings
EMBEDDING_PROVIDER=sentence_transformers
WHISPER_MODEL=base
MAX_EPISODES_PER_RUN=10
RATE_LIMIT_PER_MINUTE=20

# Admin access
ADMIN_ENABLED=true
ADMIN_USER=admin
ADMIN_PASSWORD=change-me-please

# Retrieval
TOP_K=6
MIN_SIMILARITY=0.15

# Storage paths
DATA_DIR=data
AUDIO_DIR=data/audio
TRANSCRIPT_DIR=data/transcripts
EOF
    echo "✓ Created .env file"
fi

# Create data directories
mkdir -p data/audio data/transcripts

# Setup database
echo ""
echo "Setting up database..."

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432 &> /dev/null; then
    echo "Starting PostgreSQL..."
    brew services start postgresql@16
    sleep 3
fi

# Create database and user
echo ""
echo "Creating database and user..."
psql postgres -c "CREATE USER mirror WITH PASSWORD 'mirror';" 2>/dev/null || echo "User already exists"
psql postgres -c "CREATE DATABASE mirror_talk OWNER mirror;" 2>/dev/null || echo "Database already exists"
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE mirror_talk TO mirror;" 2>/dev/null

# Install pgvector extension
psql -U mirror -d mirror_talk -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null || \
    psql postgres -d mirror_talk -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null || \
    echo "Note: Run as superuser if needed: psql postgres -c 'CREATE EXTENSION vector;' -d mirror_talk"

echo "✓ Database setup complete"

# Initialize database schema
echo ""
echo "Initializing database schema..."
python3 -c "from app.core.db import init_db; init_db()"
echo "✓ Database schema initialized"

echo ""
echo "=========================================="
echo "✓ Local setup complete!"
echo "=========================================="
echo ""
echo "Choose your ingestion approach:"
echo ""
echo "1) Quick Test (5 episodes, ~15-25 minutes)"
echo "2) Standard (10 episodes, ~30-50 minutes)"
echo "3) Bulk (ALL episodes, 1-3 hours)"
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
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
read -p "Continue with ingestion? [y/N]: " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Setup complete! You can run ingestion later with:"
    echo "  source venv/bin/activate"
    echo "  python scripts/bulk_ingest.py --max-episodes 5"
    echo ""
    echo "Start the API server with:"
    echo "  source venv/bin/activate"
    echo "  uvicorn app.api.main:app --host 0.0.0.0 --port 8000"
    exit 0
fi

echo ""
echo "=========================================="
echo "Starting Ingestion..."
echo "=========================================="
echo ""

# Run ingestion
if [ -z "$MAX_EPISODES" ]; then
    python3 scripts/bulk_ingest.py
else
    python3 scripts/bulk_ingest.py --max-episodes "$MAX_EPISODES"
fi

echo ""
echo "=========================================="
echo "✓ Ingestion Complete!"
echo "=========================================="
echo ""
echo "Starting API server..."
echo ""

# Start the API server in background
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --workers 1 --limit-concurrency 10 &
API_PID=$!

sleep 5

echo ""
echo "=========================================="
echo "🎉 Your Ask Mirror Talk service is ready!"
echo "=========================================="
echo ""
echo "API running at: http://localhost:8000"
echo "Admin dashboard: http://localhost:8000/admin"
echo "  Username: admin"
echo "  Password: change-me-please"
echo ""
echo "Test it:"
echo "  curl -X POST http://localhost:8000/ask \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"question\": \"What topics does Mirror Talk discuss?\"}'"
echo ""
echo "Check status:"
echo "  curl http://localhost:8000/status | jq"
echo ""
echo "To stop the server:"
echo "  kill $API_PID"
echo ""
echo "To restart later:"
echo "  source venv/bin/activate"
echo "  uvicorn app.api.main:app --host 0.0.0.0 --port 8000"
echo ""
