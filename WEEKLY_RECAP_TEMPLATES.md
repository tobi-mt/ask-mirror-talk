# Weekly Recap Card Templates

## Overview
The weekly recap cards now feature **8 beautiful, vibrant templates** that automatically rotate each week, ensuring variety and high shareability on social media.

## 🎨 Template Gallery

### 1. Gradient Vibrant
**Colors:** Red → Orange → Gold  
**Mood:** Bold, energetic, transformative  
**Best For:** Courage, passion, breakthrough moments  
**Quote Accent:** Hot pink (#ff3366)

### 2. Prismatic Rainbow
**Colors:** Multi-color spectrum (Pink → Orange → Turquoise → Purple → Blue)  
**Mood:** Celebratory, diverse, joyful  
**Best For:** Growth, diversity of experience, celebration  
**Quote Accent:** Magenta (#ff0080)

### 3. Neon Modern
**Colors:** Dark background with cyan and pink neon accents  
**Mood:** Sophisticated, contemporary, introspective  
**Best For:** Deep reflection, modern aesthetics  
**Quote Accent:** Cyan (#00d9ff)

### 4. Sunset Warmth
**Colors:** Pink → Orange → Sky Blue  
**Mood:** Comforting, hopeful, peaceful  
**Best For:** Healing, gratitude, gentle reflection  
**Quote Accent:** Coral pink (#ff6b9d)

### 5. Ocean Depths
**Colors:** Deep blue → Bright turquoise  
**Mood:** Calm, flowing, meditative  
**Best For:** Clarity, peace, flow states  
**Quote Accent:** Turquoise (#00bcd4)

### 6. Purple Dream
**Colors:** Royal purple → Lavender → Pink  
**Mood:** Dreamy, spiritual, elegant  
**Best For:** Wisdom, intuition, spiritual growth  
**Quote Accent:** Medium purple (#ab47bc)

### 7. Forest Vitality
**Colors:** Deep green → Light green  
**Mood:** Fresh, grounding, vital  
**Best For:** Growth, renewal, nature connection  
**Quote Accent:** Forest green (#43a047)

### 8. Golden Hour
**Colors:** Amber → Orange → Peach  
**Mood:** Radiant, uplifting, grateful  
**Best For:** Gratitude, warmth, abundance  
**Quote Accent:** Amber orange (#ff8f00)

## 🔄 Rotation System

Templates rotate automatically based on the week number of the year:
- **Week 0-7:** Gradient Vibrant
- **Week 8-15:** Prismatic Rainbow
- **Week 16-23:** Neon Modern
- **Week 24-31:** Sunset Warmth
- **Week 32-39:** Ocean Depths
- **Week 40-47:** Purple Dream
- **Week 48-55:** Forest Vitality
- **Week 56+:** Golden Hour (then cycles back)

## 📐 Card Layout

All templates maintain consistent, well-positioned elements:

### Top Section (Header)
- **Position:** 96px from top
- **Elements:**
  - "ASK MIRROR TALK" branding (left)
  - "Your weekly reflection recap" subtitle (left)
  - Theme pill badge (top right)
- **Styling:** White text with drop shadows for visibility

### Main Headline
- **Position:** 278px from top
- **Font:** Georgia Bold, 64px
- **Width:** 860px max
- **Lines:** Up to 3 lines
- **Styling:** White text with strong shadow

### Metrics Panel (Stats)
- **Position:** 520px from top
- **Size:** 860px × 190px
- **Background:** White glass panel (96% opacity)
- **Shadow:** Deep shadow for depth
- **Content:**
  - QUESTIONS count
  - SAVED count
  - SHARED count
- **Text:** Dark gray on white (#2a2a2a)

### Supporting Text
- **Position:** 52px below metrics panel (762px from top)
- **Content:** "Strongest day" or momentum message
- **Styling:** White text with shadow

### Optional Quote Panel
- **Position:** 70px below supporting text (if present)
- **Size:** 860px × 170px
- **Background:** White glass panel (95% opacity)
- **Content:**
  - Large opening quote mark (template accent color)
  - Latest saved insight text
- **Text:** Dark gray on white (#2e3a38)

### Footer (QR Code)
- **Position:** 188px from bottom
- **Content:**
  - QR code to mirrortalktpodcast.com/ask-mirror-talk
  - "Scan to reflect" text
- **Styling:** Centered, consistent branding

## 🎯 Design Principles

### Visibility
- All text has drop shadows for readability on vibrant backgrounds
- White panels provide strong contrast for data and quotes
- Consistent spacing ensures nothing feels cramped

### Visual Hierarchy
1. Theme pill (immediate context)
2. Main headline (primary message)
3. Metrics panel (engagement data)
4. Supporting text (encouragement)
5. Quote (optional inspiration)
6. Footer (action/scan)

### Shareability
- Instagram-ready 1080×1350 aspect ratio
- Vibrant, eye-catching gradients
- Professional but approachable design
- QR code for easy engagement

## 🧪 Testing

To test all templates, open `test_weekly_recap_templates.html` in a browser:
- View all 8 templates side-by-side
- See the current week's active template
- Verify positioning and visibility across all designs

## 🔧 Technical Implementation

### Function: `getWeeklyRecapTemplate()`
Returns the current week's template key based on week number.

### Function: `buildWeeklyRecapShareCard(recap, scale)`
Generates the complete card with:
- Template-specific background gradients
- Consistent white panel overlays
- Shadow effects for all text elements
- Template-matched accent colors

### Canvas Specifications
- **Dimensions:** 1080×1350px (Instagram portrait)
- **Scale Factor:** Configurable (0.35 for thumbnails, 1.0 for full)
- **Format:** PNG with transparency support

## 📱 Usage

Weekly recap cards are automatically generated with the current week's template. No manual selection needed - the system ensures variety by rotating through all 8 templates.

Users see a fresh, beautiful design every week while maintaining brand consistency and high shareability.
