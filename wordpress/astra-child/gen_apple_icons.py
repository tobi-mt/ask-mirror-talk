"""
Generate Apple-specific home-screen icons.
These are full-bleed squares (no pre-applied rounded corners / transparency)
so that iOS can apply its own squircle clipping cleanly.

Sizes:
  180x180  — iPhone (all modern: 6, 7, 8, X, 11, 12, 13, 14, 15, 16)
  167x167  — iPad Pro (9.7", 10.5", 11", 12.9")
  152x152  — iPad / iPad mini
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

BASE         = os.path.dirname(os.path.abspath(__file__))
GEORGIA_BOLD = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"
HELVETICA    = "/System/Library/Fonts/HelveticaNeue.ttc"


def create_icon_square(S):
    """Same design as the rounded icon but full-bleed — no corner mask."""
    y2d, x2d = np.mgrid[0:S, 0:S].astype(float)

    # Background
    t = np.clip((x2d * 0.30 + y2d * 0.70) / S, 0.0, 1.0)
    R = 62.0 + (9.0  - 62.0) * t
    G = 46.0 + (6.0  - 46.0) * t
    B = 28.0 + (4.0  - 28.0) * t

    gcx, gcy = S * 0.50, S * 0.43
    grx = (x2d - gcx) / (S * 0.50)
    gry = (y2d - gcy) / (S * 0.50)
    glow = np.clip(1.0 - np.sqrt(grx**2 + gry**2), 0.0, 1.0) ** 1.5 * 0.52
    R = np.clip(R + 100.0 * glow, 0, 255)
    G = np.clip(G +  44.0 * glow, 0, 255)
    B = np.clip(B +  10.0 * glow, 0, 255)

    arr = np.stack([R, G, B, np.full((S, S), 255.0)], axis=2).astype(np.uint8)
    img = Image.fromarray(arr, 'RGBA')
    draw = ImageDraw.Draw(img)

    # Mirror disc
    cx_d   = S // 2
    cy_d   = int(S * 0.430)
    r_gold = int(S * 0.314)
    r_step = max(2, int(S * 0.013))
    r_disc = r_gold - r_step * 4

    for i, col in enumerate([
        (247, 221, 106),
        (226, 170,  60),
        (200, 138,  42),
        (162, 105,  28),
    ]):
        ri = r_gold - i * r_step
        draw.ellipse([cx_d - ri, cy_d - ri, cx_d + ri, cy_d + ri], fill=col)

    draw.ellipse([cx_d - r_disc, cy_d - r_disc, cx_d + r_disc, cy_d + r_disc],
                 fill=(18, 13, 8))

    # Disc highlight
    hl = np.zeros((S, S, 4), dtype=float)
    hcx = cx_d - r_disc * 0.26
    hcy = cy_d - r_disc * 0.28
    hdx = (x2d - hcx) / (r_disc * 0.72)
    hdy = (y2d - hcy) / (r_disc * 0.72)
    h_str = np.clip(1.0 - np.sqrt(hdx**2 + hdy**2), 0.0, 1.0) ** 2.0 * 0.16
    inside = ((x2d - cx_d)**2 + (y2d - cy_d)**2) <= r_disc**2
    h_str[~inside] = 0.0
    hl[:, :, 3] = h_str * 255
    hl[:, :, 0] = hl[:, :, 1] = hl[:, :, 2] = 255
    img = Image.alpha_composite(img, Image.fromarray(hl.astype(np.uint8), 'RGBA'))
    draw = ImageDraw.Draw(img)

    lw = max(1, S // 220)
    for frac, col in ((0.956, (170, 122, 42)), (0.912, (100, 72, 22))):
        ri = int(r_disc * frac)
        draw.ellipse([cx_d - ri, cy_d - ri, cx_d + ri, cy_d + ri],
                     outline=col, width=lw)

    # "M" glyph
    font_size_m = int(S * 0.475)
    try:
        m_font = ImageFont.truetype(GEORGIA_BOLD, font_size_m)
    except Exception:
        m_font = ImageFont.load_default()

    m_y = cy_d + int(r_disc * 0.04)
    glow_img = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_img)
    gd.text((cx_d, m_y), "M", fill=(208, 140, 28, 190), font=m_font, anchor="mm")
    glow_img = glow_img.filter(ImageFilter.GaussianBlur(max(3, int(S * 0.024))))
    img = Image.alpha_composite(img, glow_img)
    img = Image.alpha_composite(img, glow_img)
    draw = ImageDraw.Draw(img)
    draw.text((cx_d, m_y), "M", fill=(228, 168, 58), font=m_font, anchor="mm")

    # Accents
    line_y = cy_d + int(r_disc * 0.72)
    hw = int(r_disc * 0.52)
    draw.line([(cx_d - hw, line_y), (cx_d + hw, line_y)],
              fill=(196, 148, 50), width=max(1, S // 360))

    pip_y = cy_d - int(r_disc * 0.870)
    pip_s = max(3, S // 58)
    pts = [(cx_d, pip_y - pip_s),
           (cx_d + int(pip_s * 0.62), pip_y),
           (cx_d, pip_y + pip_s),
           (cx_d - int(pip_s * 0.62), pip_y)]
    draw.polygon(pts, fill=(246, 218, 102))

    # "ASK"
    ask_size = max(10, int(S * 0.060))
    try:
        ask_font = ImageFont.truetype(HELVETICA, ask_size)
    except Exception:
        ask_font = ImageFont.load_default()
    ask_y = int(S * 0.848)
    draw.text((S // 2, ask_y), "A  S  K", fill=(192, 144, 52), font=ask_font, anchor="mm")
    dot_r   = max(2, S // 120)
    dot_off = int(S * 0.148)
    for dx in (-dot_off, dot_off):
        draw.ellipse([S//2 + dx - dot_r, ask_y - dot_r,
                      S//2 + dx + dot_r, ask_y + dot_r],
                     fill=(192, 136, 44))

    # Glass dome
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

    # NO rounded corner mask — return as full-bleed RGBA, then convert to RGB
    # (apple-touch-icon must be opaque JPEG-compatible; PNG with no transparency)
    bg = Image.new('RGBA', (S, S), (14, 10, 6, 255))
    result = Image.alpha_composite(bg, img)
    return result.convert('RGB')


for size, name in [(180, "pwa-icon-180.png"), (167, "pwa-icon-167.png"), (152, "pwa-icon-152.png")]:
    print(f"Generating {size}x{size} ({name})...")
    create_icon_square(size).save(os.path.join(BASE, name), optimize=True)
print("Done!")
