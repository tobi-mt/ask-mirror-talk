"""
Real-size phone home screen simulation.
Icon rendered at 120×120px (= 60pt @2x retina — the actual size on screen).
Shows it in a home screen grid alongside dummy neighbour icons, with the app
label underneath, on dark and light wallpapers.
Output: realsize_preview.png
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

BASE      = os.path.dirname(os.path.abspath(__file__))
HELVETICA = "/System/Library/Fonts/HelveticaNeue.ttc"

# ── Load our icon and downscale to true phone size ─────────────────────────
ICON_PT   = 60   # iOS home-screen icon = 60pt
SCALE     = 2    # @2x retina
ICON_PX   = ICON_PT * SCALE          # 120px
ICON_R    = int(ICON_PX * 0.218)     # iOS corner radius at this size

def load_icon(px):
    """Load the master 512px icon and downscale with Lanczos."""
    src = Image.open(os.path.join(BASE, "pwa-icon-512.png")).convert("RGBA")
    return src.resize((px, px), Image.LANCZOS)

def rounded_mask(px, r):
    mask = Image.new("L", (px, px), 0)
    d = ImageDraw.Draw(mask)
    d.rectangle([r, 0, px - r, px], fill=255)
    d.rectangle([0, r, px, px - r], fill=255)
    for ox, oy in [(0,0),(px-2*r,0),(0,px-2*r),(px-2*r,px-2*r)]:
        d.ellipse([ox, oy, ox+2*r, oy+2*r], fill=255)
    return mask

def paste_icon(canvas, icon, px, x, y, label, label_font, text_color):
    """Paste icon with rounded mask and label underneath."""
    r    = int(px * 0.218)
    mask = rounded_mask(px, r)
    canvas.paste(icon, (x, y), mask)
    d = ImageDraw.Draw(canvas)
    lx = x + px // 2
    ly = y + px + max(4, int(px * 0.10))
    # label shadow for legibility on any bg
    d.text((lx+1, ly+1), label, fill=(0,0,0,120), font=label_font, anchor="mt")
    d.text((lx,   ly),   label, fill=text_color,  font=label_font, anchor="mt")

def dummy_icon(px, color, letter, font):
    """A simple solid-color placeholder for neighbour icons."""
    img  = Image.new("RGBA", (px, px), color + (255,))
    d    = ImageDraw.Draw(img)
    r    = int(px * 0.218)
    # re-draw with rounded corners via mask
    base = Image.new("RGBA", (px, px), (0,0,0,0))
    base.paste(img, mask=rounded_mask(px, r))
    d2   = ImageDraw.Draw(base)
    fs   = int(px * 0.42)
    try:   f = ImageFont.truetype(HELVETICA, fs)
    except: f = font
    d2.text((px//2, px//2), letter, fill=(255,255,255,220), font=f, anchor="mm")
    return base

# ── Build the preview sheet ────────────────────────────────────────────────
def make_preview():
    try:
        lbl_font  = ImageFont.truetype(HELVETICA, 24)   # @2x = 12pt
        hdr_font  = ImageFont.truetype(HELVETICA, 28)
        note_font = ImageFont.truetype(HELVETICA, 22)
    except:
        lbl_font = hdr_font = note_font = ImageFont.load_default()

    px      = ICON_PX          # 120
    GAP     = int(px * 0.275)  # space between icons
    COL_W   = px + GAP
    GRID_C  = 4                # columns in home screen grid
    GRID_R  = 2                # rows shown
    MARGIN  = 44
    LBL_H   = 36               # space for app label below icon

    GRID_W  = GRID_C * COL_W - GAP
    GRID_H  = GRID_R * (px + LBL_H + GAP // 2)

    WP_W    = GRID_W + MARGIN * 2
    WP_H    = GRID_H + MARGIN * 2

    wallpapers = [
        ("iOS Dark",    (18,  18,  20 ), (235, 235, 245)),
        ("iOS Light",   (242, 242, 247), (50,  50,  60 )),
        ("Blue",        (30,  58, 138 ), (235, 235, 255)),
        ("Photo-style", (62,  42,  28 ), (235, 220, 200)),
    ]

    # neighbour dummy icons (colour, letter, label)
    neighbours = [
        ((41,  128, 185), "P", "Podcasts"),
        ((142,  68, 173), "S", "Spotify"),
        ((231,  76,  60), "Y", "YouTube"),
        ((39,  174,  96), "N", "Notes"),
        ((52,  152, 219), "T", "Twitter"),
        ((243, 156,  18), "M", "Maps"),
    ]

    OUR_ICON = load_icon(px)
    OUR_POS  = (1, 0)   # row 0, col 1 — sits next to others naturally

    SHEET_PAD = 48
    HEADER_H  = 60
    sheet_w   = len(wallpapers) * (WP_W + SHEET_PAD) + SHEET_PAD
    sheet_h   = WP_H + HEADER_H + SHEET_PAD * 2

    sheet = Image.new("RGB", (sheet_w, sheet_h), (14, 14, 18))
    sd    = ImageDraw.Draw(sheet)

    # Title
    sd.text((sheet_w // 2, SHEET_PAD // 2), "Real phone size  ·  60pt @2×retina  ·  120×120px",
            fill=(180, 180, 180), font=hdr_font, anchor="mt")

    for wi, (wp_name, wp_bg, wp_txt) in enumerate(wallpapers):
        ox = SHEET_PAD + wi * (WP_W + SHEET_PAD)
        oy = SHEET_PAD + HEADER_H

        # wallpaper tile
        wp = Image.new("RGB", (WP_W, WP_H), wp_bg)
        sheet.paste(wp, (ox, oy))

        wp_d = ImageDraw.Draw(sheet)

        # place icons in grid
        ni = 0
        for row in range(GRID_R):
            for col in range(GRID_C):
                ix = ox + MARGIN + col * COL_W
                iy = oy + MARGIN + row * (px + LBL_H + GAP // 2)

                if (row, col) == OUR_POS:
                    paste_icon(sheet, OUR_ICON, px, ix, iy,
                               "ASK", lbl_font, wp_txt)
                else:
                    if ni < len(neighbours):
                        nc, nl, nn = neighbours[ni]
                        di = dummy_icon(px, nc, nl, lbl_font)
                        paste_icon(sheet, di, px, ix, iy, nn, lbl_font, wp_txt)
                        ni += 1

        # wallpaper label at bottom
        wp_d.text((ox + WP_W // 2, oy + WP_H - 14), wp_name,
                  fill=(110, 110, 120), font=note_font, anchor="mb")

    # ── Also show a 4× magnified view of just our icon ─────────────────────
    # (so any blur/issue at small size is detectable)
    ZOOM       = 4
    zoom_px    = px * ZOOM
    zoom_icon  = load_icon(zoom_px)
    zoom_mask  = rounded_mask(zoom_px, int(zoom_px * 0.218))
    zoom_out   = Image.new("RGBA", (zoom_px, zoom_px), (0,0,0,0))
    zoom_out.paste(zoom_icon, mask=zoom_mask)

    zoom_x = sheet_w - SHEET_PAD - zoom_px
    zoom_y = SHEET_PAD + HEADER_H

    sheet.paste(zoom_out.convert("RGB"), (zoom_x, zoom_y))
    sd.rectangle([zoom_x-2, zoom_y-2, zoom_x+zoom_px+2, zoom_y+zoom_px+2],
                 outline=(60,60,70), width=1)
    sd.text((zoom_x + zoom_px // 2, zoom_y + zoom_px + 8), f"4× zoom ({zoom_px}px)",
            fill=(110,110,120), font=note_font, anchor="mt")

    # extend sheet height to fit zoom image if needed
    out = os.path.join(BASE, "realsize_preview.png")
    sheet.save(out)
    print(f"Saved: {out}")


make_preview()
