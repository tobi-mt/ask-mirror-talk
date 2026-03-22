"""
Compare current dark icon vs. new bold-amber icon at real phone sizes.
Outputs:  icon_compare.png  (not a theme file — for preview only)
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

BASE         = os.path.dirname(os.path.abspath(__file__))
GEORGIA_BOLD = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"
HELVETICA    = "/System/Library/Fonts/HelveticaNeue.ttc"
SS           = 4   # supersampling factor


# ─────────────────────────────────────────────────────────────────
#  DESIGN A: current dark/espresso (existing design, load from disk)
# ─────────────────────────────────────────────────────────────────
def design_a(S, rounded=True):
    """Load the current icon from pwa-icon-180.png and resize."""
    src = Image.open(os.path.join(BASE, "pwa-icon-180.png")).convert("RGBA")
    return src.resize((S, S), Image.LANCZOS)


# ─────────────────────────────────────────────────────────────────
#  DESIGN B: new bold-amber
# ─────────────────────────────────────────────────────────────────
def design_b(S, rounded=True):
    HS = S * SS
    img = _draw_amber(HS, rounded)
    return img.resize((S, S), Image.LANCZOS)


def _draw_amber(S, rounded):
    y2d, x2d = np.mgrid[0:S, 0:S].astype(float)

    # ── Background: warm amber radial gradient ────────────────────
    cx, cy = S * 0.50, S * 0.50
    dist = np.sqrt(((x2d - cx) / (S * 0.65)) ** 2 +
                   ((y2d - cy) / (S * 0.65)) ** 2)
    t = np.clip(dist, 0.0, 1.0)
    # centre: bright warm gold  →  edge: deep burnt amber
    R = np.clip(255 + (148 - 255) * t, 0, 255)
    G = np.clip(195 + ( 62 - 195) * t, 0, 255)
    B = np.clip( 45 + (  8 -  45) * t, 0, 255)

    # Top-left gloss warmth
    tl = np.clip(1.0 - np.sqrt((x2d / (S * 0.75)) ** 2 +
                                (y2d / (S * 0.75)) ** 2), 0, 1) ** 2.2 * 0.28
    R = np.clip(R + 50 * tl, 0, 255)
    G = np.clip(G + 38 * tl, 0, 255)
    B = np.clip(B + 18 * tl, 0, 255)

    arr = np.stack([R, G, B, np.full((S, S), 255.0)], axis=2).astype(np.uint8)
    img = Image.fromarray(arr, 'RGBA')
    draw = ImageDraw.Draw(img)

    # ── Subtle mirror disc watermark ─────────────────────────────
    disc_r  = int(S * 0.365)
    disc_cx = S // 2
    disc_cy = int(S * 0.445)
    ring = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    rd   = ImageDraw.Draw(ring)
    # outer ring glow
    for i, (dr, alpha) in enumerate([(0, 35), (int(S*0.012), 22), (int(S*0.024), 10)]):
        rd.ellipse([disc_cx - disc_r - dr, disc_cy - disc_r - dr,
                    disc_cx + disc_r + dr, disc_cy + disc_r + dr],
                   outline=(100, 40, 5, alpha),
                   width=max(2, S // 160))
    img = Image.alpha_composite(img, ring)
    draw = ImageDraw.Draw(img)

    # ── "ASK" ─────────────────────────────────────────────────────
    ask_size = int(S * 0.418)
    try:   ask_font = ImageFont.truetype(GEORGIA_BOLD, ask_size)
    except: ask_font = ImageFont.load_default()

    ask_cx = S // 2
    ask_cy = int(S * 0.438)

    # Drop shadow (subtle warmth, offset)
    shd = max(2, S // 160)
    draw.text((ask_cx + shd, ask_cy + shd), "ASK",
              fill=(80, 28, 4, 160), font=ask_font, anchor="mm")

    # Main dark espresso — maximum contrast on gold
    draw.text((ask_cx, ask_cy), "ASK", fill=(28, 12, 3), font=ask_font, anchor="mm")

    # Inner gloss — very subtle bright highlight on top edge of letters
    gloss_shift = max(2, int(ask_size * 0.042))
    draw.text((ask_cx, ask_cy - gloss_shift), "ASK",
              fill=(255, 240, 180, 55), font=ask_font, anchor="mm")

    # ── Separator ─────────────────────────────────────────────────
    sep_y  = int(S * 0.722)
    sep_hw = int(S * 0.210)
    draw.line([(ask_cx - sep_hw, sep_y), (ask_cx + sep_hw, sep_y)],
              fill=(100, 42, 6, 200), width=max(2, S // 240))

    # ── "mirror talk" small label ─────────────────────────────────
    mt_size = int(S * 0.076)
    try:   mt_font = ImageFont.truetype(HELVETICA, mt_size)
    except: mt_font = ImageFont.load_default()
    mt_y = int(S * 0.818)
    draw.text((ask_cx, mt_y), "Mirror Talk", fill=(95, 40, 6), font=mt_font, anchor="mm")

    # ── Glass dome highlight (top) ────────────────────────────────
    gloss = np.zeros((S, S, 4), dtype=float)
    g_cx, g_cy = S * 0.50, S * 0.10
    g_rx, g_ry = S * 0.44, S * 0.20
    gx = (x2d - g_cx) / g_rx
    gy = (y2d - g_cy) / g_ry
    g_str = np.clip(1.0 - np.sqrt(gx**2 + gy**2), 0.0, 1.0) ** 2.5 * 0.20
    gloss[:, :, 3] = g_str * 255
    gloss[:, :, 0] = gloss[:, :, 1] = gloss[:, :, 2] = 255
    gloss_img = Image.fromarray(gloss.astype(np.uint8), 'RGBA')
    gloss_img = gloss_img.filter(ImageFilter.GaussianBlur(max(2, int(S * 0.022))))
    img = Image.alpha_composite(img, gloss_img)

    # ── Corner mask ───────────────────────────────────────────────
    if rounded:
        cr   = int(S * 0.218)
        mask = Image.new('L', (S, S), 0)
        md   = ImageDraw.Draw(mask)
        md.rectangle([cr, 0,    S - cr, S      ], fill=255)
        md.rectangle([0,  cr,   S,      S - cr ], fill=255)
        for ox, oy in [(0,0),(S-2*cr,0),(0,S-2*cr),(S-2*cr,S-2*cr)]:
            md.ellipse([ox, oy, ox+2*cr, oy+2*cr], fill=255)
        result = Image.new('RGBA', (S, S), (0,0,0,0))
        result.paste(img, mask=mask)
        return result
    else:
        return img.convert('RGB')


# ─────────────────────────────────────────────────────────────────
#  Comparison sheet
# ─────────────────────────────────────────────────────────────────
def make_compare():
    try:
        label_font = ImageFont.truetype(HELVETICA, 22)
        wallpaper_font = ImageFont.truetype(HELVETICA, 18)
    except:
        label_font = wallpaper_font = ImageFont.load_default()

    ICON   = 120   # simulated phone icon size (points × 2 for retina feel)
    PAD    = 32
    GAP    = 48    # gap between icons
    COL_W  = ICON + 80
    ROWS   = 3     # dark wallpaper, light wallpaper, colorful wallpaper
    ROW_H  = ICON + 90
    W      = PAD * 2 + COL_W * 2 + GAP
    H      = PAD * 2 + ROW_H * ROWS + 50  # extra for title

    wallpapers = [
        ("Dark wallpaper",    (28,  28,  30 )),   # iOS dark
        ("Light wallpaper",   (220, 218, 210)),   # cream/beige
        ("Colourful wallpaper",(42,  82, 152)),   # deep blue
    ]

    sheet = Image.new('RGB', (W, H), (18, 18, 20))
    sd    = ImageDraw.Draw(sheet)

    # Title
    sd.text((W // 2, PAD), "Icon Comparison  —  tap-appeal test",
            fill=(200, 200, 200), font=label_font, anchor="mt")

    # Column headers
    header_y = PAD + 28
    sd.text((PAD + COL_W // 2,             header_y), "Current (dark)",
            fill=(160, 140, 100), font=label_font, anchor="mt")
    sd.text((PAD + COL_W + GAP + COL_W//2, header_y), "New (amber)",
            fill=(255, 195, 50),  font=label_font, anchor="mt")

    for row_i, (wp_label, wp_color) in enumerate(wallpapers):
        row_top = PAD + 60 + row_i * ROW_H

        for col_i, (gen_fn, rounded) in enumerate([(design_a, True), (design_b, True)]):
            col_x = PAD + col_i * (COL_W + GAP) + (COL_W - ICON) // 2

            # wallpaper tile
            wp = Image.new('RGB', (ICON + 24, ICON + 24), wp_color)
            sheet.paste(wp, (col_x - 12, row_top))

            # icon
            icon = gen_fn(ICON, rounded=True).convert("RGBA")
            # paste with alpha
            sheet.paste(icon, (col_x, row_top + 0),
                        mask=icon.split()[3] if icon.mode == 'RGBA' else None)

        # wallpaper label on right
        sd.text((W - PAD, row_top + ICON // 2), wp_label,
                fill=(130, 130, 130), font=wallpaper_font, anchor="rm")

    out = os.path.join(BASE, "icon_compare.png")
    sheet.save(out)
    print(f"Saved: {out}")


make_compare()
