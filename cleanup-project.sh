#!/bin/bash
#
# Cleanup Ask Mirror Talk Project
# Removes unnecessary files, docs, and archived content
#
# Usage: ./cleanup-project.sh
#

set -e

cd "$(dirname "$0")"

echo "🧹 Cleaning up Ask Mirror Talk project..."
echo ""

# Track what we're removing
removed_count=0

# Function to safely remove with confirmation
safe_remove() {
    local path="$1"
    if [ -e "$path" ]; then
        echo "  ✓ Removing: $path"
        rm -rf "$path"
        removed_count=$((removed_count + 1))
    fi
}

# Remove archived documentation
echo "📁 Removing archived docs..."
safe_remove "docs/"

# Remove .agents directory (skill references not needed in production)
echo "📁 Removing .agents skill references..."
safe_remove ".agents/"

# Remove unnecessary env files (keep .env.example for reference)
echo "🔐 Removing old env files..."
safe_remove ".env.local"
safe_remove ".env.railway"

# Remove unnecessary deployment configs
echo "📦 Removing unused deployment configs..."
safe_remove "render.yaml"
safe_remove "render-build.sh"
safe_remove "nixpacks.toml"
safe_remove "docker-compose.yml"
safe_remove "docker-compose.prod.yml"
safe_remove "Dockerfile.api"  # Using Dockerfile and Dockerfile.worker only

# Remove old setup scripts
echo "🔧 Removing old setup scripts..."
safe_remove "setup-github-mirror.sh"

# Remove virtual environments (can be recreated)
echo "🐍 Removing virtual environments..."
safe_remove ".venv/"
safe_remove "venv/"

# Remove Python egg-info (regenerated on install)
echo "🥚 Removing egg-info..."
safe_remove "ask_mirror_talk.egg-info/"

# Remove .neon file (not needed, using env vars)
echo "💾 Removing .neon config..."
safe_remove ".neon"

# Remove old WordPress parent theme files (using child theme now)
echo "🎨 Cleaning up old WordPress files..."
safe_remove "wordpress/astra/INSTALL.md"
safe_remove "wordpress/astra/README.md"

# Remove .DS_Store files (macOS metadata)
echo "🍎 Removing macOS metadata..."
find . -name ".DS_Store" -type f -delete 2>/dev/null || true

# Remove __pycache__ directories
echo "🐍 Removing Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📊 Summary:"
echo "   - Removed $removed_count directories/files"
echo "   - Removed all __pycache__ and .DS_Store files"
echo ""
echo "📂 Project structure is now clean and production-ready"
echo ""
echo "💡 What was kept:"
echo "   ✓ app/ (core application code)"
echo "   ✓ scripts/ (maintenance scripts)"
echo "   ✓ wordpress/ (child theme)"
echo "   ✓ data/ (audio, transcripts, logs)"
echo "   ✓ reports/ (weekly engagement reports)"
echo "   ✓ tests/ (test files)"
echo "   ✓ Dockerfile, Dockerfile.worker (Railway deployment)"
echo "   ✓ pyproject.toml, requirements.txt (dependencies)"
echo "   ✓ railway.toml, railway.env.example (Railway config)"
echo "   ✓ .env.example (environment template)"
echo "   ✓ README.md (project documentation)"
echo ""
