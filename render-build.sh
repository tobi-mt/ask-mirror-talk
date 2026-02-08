#!/usr/bin/env bash
# Render.com build script for Ask Mirror Talk
# This script installs system dependencies and Python packages

set -e  # Exit on error

echo "=========================================="
echo "Installing system dependencies..."
echo "=========================================="

# Install ffmpeg for audio processing (required by faster-whisper)
apt-get update
apt-get install -y ffmpeg

echo "✓ System dependencies installed"

echo "=========================================="
echo "Installing Python dependencies..."
echo "=========================================="

# Install Python packages with transcription and embedding support
pip install --no-cache-dir -e '.[transcription,embeddings]'

echo "✓ Python dependencies installed"
echo "=========================================="
echo "Build complete!"
echo "=========================================="
