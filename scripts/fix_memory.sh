#!/bin/bash
# Quick fix script for memory issues

set -e

echo "================================"
echo "Memory Optimization Quick Fix"
echo "================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file with memory-optimized settings..."
    cat > .env << EOF
# Memory-optimized configuration
EMBEDDING_PROVIDER=local
WHISPER_MODEL=tiny
MAX_EPISODES_PER_RUN=1
RATE_LIMIT_PER_MINUTE=10
EOF
    echo "✓ Created .env file"
else
    echo "⚠ .env file exists. Please manually add these lines if not present:"
    echo ""
    echo "EMBEDDING_PROVIDER=local"
    echo "WHISPER_MODEL=tiny"
    echo "MAX_EPISODES_PER_RUN=1"
    echo ""
fi

echo ""
echo "================================"
echo "Changes Applied:"
echo "================================"
echo "✓ Model caching added to embeddings.py"
echo "✓ Model caching added to transcription.py"
echo "✓ Garbage collection added after requests"
echo "✓ Uvicorn configured with --workers 1 --limit-concurrency 10"
echo ""
echo "================================"
echo "Next Steps:"
echo "================================"
echo "1. Review and commit the changes"
echo "2. Rebuild Docker image:"
echo "   docker-compose -f docker-compose.prod.yml build"
echo ""
echo "3. Restart the service:"
echo "   docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo "4. Monitor memory usage:"
echo "   docker stats"
echo ""
echo "================================"
echo "Optional: Further Reduce Memory"
echo "================================"
echo "If issues persist, set these in .env:"
echo "  EMBEDDING_PROVIDER=local  (no ML model, uses hash-based embeddings)"
echo "  WHISPER_MODEL=tiny        (smallest Whisper model, ~75MB)"
echo "  MAX_EPISODES_PER_RUN=1    (process one episode at a time)"
echo ""
