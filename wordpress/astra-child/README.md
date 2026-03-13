# Astra Child Theme - Mirror Talk Edition

This is a child theme for the Astra WordPress theme, containing the Ask Mirror Talk widget with PWA and push notification support.

## Files Included

```
astra-child/
├── style.css              # Child theme header (required)
├── functions.php          # Loads parent theme + Ask Mirror Talk widget
├── ask-mirror-talk.php    # Shortcode, AJAX handlers, PWA setup
├── ask-mirror-talk.js     # Widget frontend logic (v3.9.0)
├── ask-mirror-talk.css    # Widget styles
├── analytics-addon.js     # Citation tracking and feedback
├── manifest.json          # PWA manifest
├── sw.js                  # Service worker for offline + push notifications
├── pwa-icon-192.png       # PWA icon (192x192)
├── pwa-icon-512.png       # PWA icon (512x512)
└── pwa-icon.svg           # Vector icon source
```

## Installation Instructions

### Step 1: Upload to WordPress

1. **Via FTP/SFTP:**
   - Connect to your server
   - Navigate to `/wp-content/themes/`
   - Upload the entire `astra-child` folder

2. **Via WordPress Dashboard:**
   - Zip the `astra-child` folder
   - Go to **Appearance → Themes → Add New → Upload Theme**
   - Upload the zip file
   - Click **Install Now**

### Step 2: Activate the Child Theme

1. Go to **Appearance → Themes**
2. Find **Astra Child - Mirror Talk**
3. Click **Activate**

⚠️ **Important:** Make sure the parent **Astra** theme is installed before activating the child theme.

### Step 3: Verify Installation

1. Edit any page/post
2. Add the shortcode: `[ask_mirror_talk]`
3. View the page — you should see the Ask Mirror Talk widget

### Step 4: Clean Up (Optional)

After confirming the child theme works:

1. **Remove** the custom files from the parent theme (`/wp-content/themes/astra/`):
   - `ask-mirror-talk.php`
   - `ask-mirror-talk.js`
   - `ask-mirror-talk.css`
   - `analytics-addon.js`
   - `manifest.json`
   - `sw.js`
   - PWA icons

2. **Remove** the custom code from the parent theme's `functions.php` if you added it

This ensures you're only using the child theme version.

## Features

- **Ask Mirror Talk Widget:** Semantic search through 471 podcast episodes
- **PWA Support:** Installable as a mobile/desktop app ("Add to Home Screen")
- **Push Notifications:** Daily Question of the Day + new episode alerts
- **Offline Mode:** Service worker caches widget for offline access
- **Analytics:** Citation click tracking and answer feedback
- **Theme-Safe:** Updates to Astra won't affect your customizations

## Updating Custom Code

When you need to update the widget code:

1. Edit files in `/wp-content/themes/astra-child/` (NOT the parent theme)
2. Or update your local files and re-upload the entire child theme folder

## Support

For questions or issues:
- Website: https://mirrortalkpodcast.com
- Email: hello@mirrortalkpodcast.com

## License

GNU General Public License v2 or later
