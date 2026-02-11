#!/usr/bin/env bash
# Resume bulk ingestion after timeout or error
# This script runs the ingestion without confirmation prompt

set -e

echo "🔄 Resuming Bulk Ingestion"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  DATABASE_URL not set. Using .env file..."
fi

# Set Python to use virtual environment if available
if [ -d "venv" ]; then
    PYTHON="./venv/bin/python"
    echo "✓ Using virtual environment"
elif [ -d ".venv" ]; then
    PYTHON="./.venv/bin/python"
    echo "✓ Using virtual environment"
else
    PYTHON="python3"
    echo "✓ Using system Python"
fi

echo ""
echo "Starting ingestion (no confirmation prompt)..."
echo "This will skip already-ingested episodes."
echo ""

# Run with no confirmation
$PYTHON scripts/bulk_ingest.py --max-episodes 500 --no-confirm

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Ingestion complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
