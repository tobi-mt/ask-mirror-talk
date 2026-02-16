#!/bin/bash
# Helper script to create .env file from Railway variables

echo "Creating .env file from Railway environment variables..."
echo ""

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "⚠️  Railway CLI not found"
    echo ""
    echo "Please install it first:"
    echo "  npm install -g @railway/cli"
    echo ""
    echo "Or manually create .env file with your Neon database credentials"
    exit 1
fi

# Create .env file
cat > .env << EOF
# Environment Configuration (Generated from Railway)
APP_NAME="Ask Mirror Talk"
ENVIRONMENT=development

# Database - From Railway
DATABASE_URL=$(railway variables | grep "^DATABASE_URL=" | cut -d'=' -f2-)

# RSS Feed
RSS_URL=$(railway variables | grep "^RSS_URL=" | cut -d'=' -f2- || echo "https://mirrortalkpodcast.com/feed.xml")

# OpenAI API Key - From Railway
OPENAI_API_KEY=$(railway variables | grep "^OPENAI_API_KEY=" | cut -d'=' -f2-)

# Transcription
TRANSCRIPTION_PROVIDER=openai

# Ingestion (Process one episode at a time)
MAX_EPISODES_PER_RUN=1

# Embeddings
EMBEDDING_PROVIDER=sentence_transformers
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIM=384

# Answer Generation
ANSWER_GENERATION_PROVIDER=openai
ANSWER_GENERATION_MODEL=gpt-3.5-turbo
ANSWER_MAX_TOKENS=500
ANSWER_TEMPERATURE=0.7

# Retrieval
TOP_K=6
MIN_SIMILARITY=0.15

# Chunking
MAX_CHUNK_CHARS=1400
MIN_CHUNK_CHARS=300

# API Rate Limiting
RATE_LIMIT_PER_MINUTE=10

# Admin Dashboard
ADMIN_ENABLED=false
ADMIN_USER=admin
ADMIN_PASSWORD=change-me

# CORS
ALLOWED_ORIGINS=https://mirrortalkpodcast.com,https://www.mirrortalkpodcast.com
EOF

echo "✓ Created .env file"
echo ""
echo "Verifying..."
echo ""

# Verify critical variables
if grep -q "DATABASE_URL=" .env && [ "$(grep DATABASE_URL .env | cut -d'=' -f2-)" != "" ]; then
    echo "✓ DATABASE_URL is set"
else
    echo "⚠️  DATABASE_URL is missing or empty"
    echo "   Please add it manually to .env"
fi

if grep -q "OPENAI_API_KEY=" .env && [ "$(grep OPENAI_API_KEY .env | cut -d'=' -f2-)" != "" ]; then
    echo "✓ OPENAI_API_KEY is set"
else
    echo "⚠️  OPENAI_API_KEY is missing or empty"
    echo "   Please add it manually to .env"
fi

if grep -q "RSS_URL=" .env && [ "$(grep RSS_URL .env | cut -d'=' -f2-)" != "" ]; then
    echo "✓ RSS_URL is set"
else
    echo "⚠️  RSS_URL is missing or empty"
    echo "   Please add it manually to .env"
fi

echo ""
echo "Done! You can now run:"
echo "  python scripts/ingest_all_episodes.py"
