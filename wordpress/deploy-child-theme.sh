#!/bin/bash
#
# Deploy Astra Child Theme to WordPress
# Usage: ./deploy-child-theme.sh
#

set -e

cd "$(dirname "$0")"

THEME_DIR="astra-child"
ZIP_NAME="astra-child-mirror-talk.zip"

echo "📦 Packaging Astra Child Theme for WordPress..."
echo ""

# Remove old zip if exists
rm -f "$ZIP_NAME"

# Create zip (exclude hidden files, .DS_Store, etc.)
cd "$THEME_DIR"
zip -r "../$ZIP_NAME" . -x "*.DS_Store" -x "__MACOSX/*" -x ".git/*" -x "*.md"
cd ..

echo "✓ Created: $ZIP_NAME"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Upload to WordPress:"
echo "   - Go to: Appearance → Themes → Add New → Upload Theme"
echo "   - Choose: $ZIP_NAME"
echo "   - Click: Install Now"
echo ""
echo "2. Activate the theme:"
echo "   - Go to: Appearance → Themes"
echo "   - Find: 'Astra Child - Mirror Talk'"
echo "   - Click: Activate"
echo ""
echo "3. Test the widget:"
echo "   - Edit any page/post"
echo "   - Add shortcode: [ask_mirror_talk]"
echo "   - View the page"
echo ""
echo "4. Clean up (optional):"
echo "   - Remove custom files from parent Astra theme"
echo "   - Remove custom code from parent functions.php"
echo ""
