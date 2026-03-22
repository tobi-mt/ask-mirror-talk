"""
Regenerate all PWA icon PNGs with "MT" glyph.
Uses 4× supersampling for crisp, noise-free text at all sizes.

Outputs:
  pwa-icon-512.png  — Android/manifest large
  pwa-icon-192.png  — Android/manifest small (with rounded corners)
  pwa-icon-180.png  — iPhone
  pwa-icon-167.png  — iPad Pro
  pwa-icon-152.png  — iPad / iPad mini
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

BASE         = os.path.dirname(os.path.abspath(__file__))
FUTURA       = "/System/Library/Fonts/Supplemental/Futura.ttc"
HELVETICA    = "/System/Library/Fonts/HelveticaNeue.ttc"

SUPERSAMPLE  = 4   # render at 4× then Lanczos-downscale → crisp text


def create_icon(S, rounded=True):
    """Render at S*SUPERSAMPLE then downscale to S for maximum sharpness."""
    HS = S * SUPERSAMPLE
    img = _draw(HS, rounded)
    return img.resize((S, S), Image.LANCZOS)


def _draw(S, rounded):
    """All drawing happens at the high-res canvas size S."""
    y2d, x2d = np.mgrid[0:S, 0:S].astype(float)

    # ── Background: warm amber radial gradient ────────────────────
    cx, cy = S * 0.50, S * 0.50
    dist = np.sqrt(((x2d - cx) / (S * 0.65)) ** 2 +
                   ((y2d - cy) / (S * 0.65)) ** 2)
    t = np.clip(dist, 0.0, 1.0)
    # centre: bright warm gold → edge: deep burnt amber
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

    # ── Subtle mirror disc watermark ──────────────────────────────
    disc_r  = int(S * 0.365)
    disc_cx = S // 2
    disc_cy = int(S * 0.445)
    ring = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    rd   = ImageDraw.Draw(ring)
    for dr, alpha in [(0, 38), (int(S*0.012), 24), (int(S*0.025), 10)]:
        rd.ellipse([disc_cx - disc_r - dr, disc_cy - disc_r - dr,
                    disc_cx + disc_r + dr, disc_cy + disc_r + dr],
                   outline=(90, 35, 4, alpha), width=max(2, S // 160))
    img = Image.alpha_composite(img, ring)
    draw = ImageDraw.Draw(img)

    # ── "ASK" — dominant, bold ────────────────────────────────────
    ask_size = int(S * 0.390)   # Futura is wider than Georgia; slight size reduction
    try:   ask_font = ImageFont.truetype(FUTURA, ask_size)
    except: ask_font = ImageFont.load_default()

    ask_cx = S // 2
    ask_cy = int(S * 0.438)

    # Drop shadow
    shd = max(2, S // 160)
    draw.text((ask_cx + shd, ask_cy + shd), "ASK",
              fill=(55, 18, 2, 170), font=ask_font, anchor="mm", spacing=int(ask_size*0.04))

    # Main dark espresso — maximum contrast on gold
    draw.text((ask_cx, ask_cy), "ASK", fill=(22, 8, 2), font=ask_font, anchor="mm")

    # Gloss highlight — top-edge specular
    gloss_shift = max(2, int(ask_size * 0.042))
    draw.text((ask_cx, ask_cy - gloss_shift), "ASK",
              fill=(255, 235, 170, 52), font=ask_font, anchor="mm")

    # ── Thin separator ────────────────────────────────────────────
    sep_y  = int(S * 0.722)
    sep_hw = int(S * 0.210)
    draw.line([(ask_cx - sep_hw, sep_y), (ask_cx + sep_hw, sep_y)],
              fill=(90, 38, 5, 200), width=max(2, S // 240))

    # ── "mirror talk" sub-label ───────────────────────────────────
    mt_size = int(S * 0.076)
    try:   mt_font = ImageFont.truetype(FUTURA, mt_size)
    except: mt_font = ImageFont.load_default()
    mt_y = int(S * 0.818)
    draw.text((ask_cx, mt_y), "Mirror Talk", fill=(80, 32, 4), font=mt_font, anchor="mm")

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

    # ── Glass dome highlight ──────────────────────────────────────
    dome = np.zeros((S, S, 4), dtype=float)
    e_cx, e_cy = S * 0.50, S * 0.245
    e_rx, e_ry = S * 0.470, S * 0.370
    ex = (x2d - e_cx) / e_rx
    ey = (y2d - e_cy) / e_ry
    d_str = np.clip(1.0 - np.sqrt(ex**2 + ey**2), 0.0, 1.0) ** 1.1 * 0.26
    v_fade = np.clip((e_cy + e_ry * 0.62 - y2d) / (e_ry * 0.62), 0.0, 1.0)
    d_str *= v_fade
    dome[:, :, 3] = d_str * 255
    dome[:, :, 0] = dome[:, :, 1] = dome[:, :, 2] = 255
    dome_img = Image.fromarray(dome.astype(np.uint8), 'RGBA')
    dome_img = dome_img.filter(ImageFilter.GaussianBlur(max(2, int(S * 0.042))))
    img = Image.alpha_composite(img, dome_img)

    spec = np.zeros((S, S, 4), dtype=float)
    sp_cx, sp_cy = S * 0.50, S * 0.095
    sp_rx, sp_ry = S * 0.255, S * 0.115
    spx = (x2d - sp_cx) / sp_rx
    spy = (y2d - sp_cy) / sp_ry
    s_str = np.clip(1.0 - np.sqrt(spx**2 + spy**2), 0.0, 1.0) ** 2.2 * 0.15
    spec[:, :, 3] = s_str * 255
    spec[:, :, 0] = spec[:, :, 1] = spec[:, :, 2] = 255
    spec_img = Image.fromarray(spec.astype(np.uint8), 'RGBA')
    spec_img = spec_img.filter(ImageFilter.GaussianBlur(max(1, int(S * 0.018))))
    img = Image.alpha_composite(img, spec_img)

    # ── Corner mask (rounded) or full-bleed square (Apple) ───────
    if rounded:
        cr   = int(S * 0.218)
        mask = Image.new('L', (S, S), 0)
        md   = ImageDraw.Draw(mask)
        md.rectangle([cr, 0,    S - cr, S],      fill=255)
        md.rectangle([0,  cr,   S,      S - cr], fill=255)
        for ox, oy in [(0, 0), (S - 2*cr, 0), (0, S - 2*cr), (S - 2*cr, S - 2*cr)]:
            md.ellipse([ox, oy, ox + 2*cr, oy + 2*cr], fill=255)
        result = Image.new('RGBA', (S, S), (0, 0, 0, 0))
        result.paste(img, mask=mask)
        return result
    else:
        bg = Image.new('RGBA', (S, S), (148, 62, 8, 255))
        result = Image.alpha_composite(bg, img)
        return result.convert('RGB')


configs = [
    (512, True,  "pwa-icon-512.png"),
    (192, True,  "pwa-icon-192.png"),
    (180, False, "pwa-icon-180.png"),
    (167, False, "pwa-icon-167.png"),
    (152, False, "pwa-icon-152.png"),
]

for size, rounded, name in configs:
    print(f"Generating {size}x{size}  ({name})  [rendering at {size*SUPERSAMPLE}x{size*SUPERSAMPLE}]...")
    create_icon(size, rounded).save(os.path.join(BASE, name), optimize=True)

print("All done!")
