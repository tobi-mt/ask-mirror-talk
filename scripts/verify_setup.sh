#!/usr/bin/env bash
# Verify Railway + Neon setup files are complete
# Run this to check if all setup files are present

set -e

echo "🔍 Verifying Railway + Neon Setup Files"
echo "========================================"
echo ""

MISSING=0
TOTAL=0

check_file() {
    local file=$1
    local desc=$2
    TOTAL=$((TOTAL + 1))
    
    if [ -f "$file" ]; then
        echo "✓ $desc"
    else
        echo "✗ $desc (MISSING: $file)"
        MISSING=$((MISSING + 1))
    fi
}

echo "Configuration Files:"
check_file "railway.toml" "Railway configuration"
check_file ".env.railway" "Environment variables template"
check_file "railway-build.sh" "Railway build script"
check_file "Dockerfile" "Docker configuration"

echo ""
echo "Scripts:"
check_file "scripts/setup_neon.py" "Neon database initialization"
check_file "scripts/init_neon.sql" "SQL setup commands"
check_file "scripts/quick_deploy.sh" "Quick deployment helper"

echo ""
echo "Documentation:"
check_file "RAILWAY_NEON_SETUP.md" "Main deployment guide"
check_file "DEPLOYMENT_CHECKLIST.md" "Deployment checklist"
check_file "README_QUICK_START.md" "Quick start guide"
check_file "SETUP_COMPLETE.md" "Setup summary"
check_file "RAILWAY_NEON_FILES.txt" "File index"

echo ""
echo "Core Application:"
check_file "app/api/main.py" "FastAPI application"
check_file "app/core/config.py" "Configuration"
check_file "app/core/db.py" "Database setup"
check_file "pyproject.toml" "Python dependencies"

echo ""
echo "========================================"
echo "Results: $((TOTAL - MISSING))/$TOTAL files present"
echo ""

if [ $MISSING -eq 0 ]; then
    echo "✅ All setup files are present!"
    echo ""
    echo "Next steps:"
    echo "1. Read: RAILWAY_NEON_SETUP.md"
    echo "2. Follow: DEPLOYMENT_CHECKLIST.md"
    echo "3. Deploy to Railway + Neon"
    echo ""
    echo "Happy deploying! 🚀"
    exit 0
else
    echo "⚠️  $MISSING files are missing!"
    echo "Please check the setup or re-run the setup process."
    exit 1
fi
