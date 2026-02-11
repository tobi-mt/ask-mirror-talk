#!/usr/bin/env bash
# Railway.app build script for Ask Mirror Talk
# This script installs system dependencies and Python packages

set -e  # Exit on error

echo "=========================================="
echo "Railway Build: Ask Mirror Talk"
echo "=========================================="

echo "Installing system dependencies..."
# Install ffmpeg for audio processing (required by faster-whisper)
apt-get update
apt-get install -y --no-install-recommends ffmpeg curl
apt-get clean
rm -rf /var/lib/apt/lists/*

echo "✓ System dependencies installed"

echo "=========================================="
echo "Installing Python dependencies..."
echo "=========================================="

# Upgrade pip for better dependency resolution
pip install --upgrade pip

# Install Python packages with transcription and embedding support
pip install --no-cache-dir -e '.[transcription,embeddings]'

echo "✓ Python dependencies installed"

echo "=========================================="
echo "Verifying installation..."
echo "=========================================="

# Verify critical packages
python -c "import fastapi; print(f'✓ FastAPI {fastapi.__version__}')"
python -c "import sqlalchemy; print(f'✓ SQLAlchemy {sqlalchemy.__version__}')"
python -c "import pgvector.sqlalchemy; print('✓ pgvector extension')"

echo "=========================================="
echo "Build complete! 🚀"
echo "=========================================="
