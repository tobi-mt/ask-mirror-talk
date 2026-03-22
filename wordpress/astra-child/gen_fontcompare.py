"""
Font comparison for the ASK icon — renders 4 variants at real phone size (120px)
and at 4× zoom side-by-side.
Output: font_compare.png
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

BASE      = os.path.dirname(os.path.abspath(__file__))
HELVETICA = "/System/Library/Fonts/HelveticaNeue.ttc"

FONTS = [
    ("Georgia\n(current)",  "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"),
    ("Futura\n(geometric)", "/System/Library/Fonts/Supplemental/Futura.ttc"),
    ("Impact\n(heavy)",     "/System/Library/Fonts/Supplemental/Impact.ttf"),
    ("Arial Black\n(bold)", "/System/Library/Fonts/Supplemental/Arial Black.ttf"),
]

SS = 4   # supersampling

def make_icon(S, ask_font_path, rounded=True):
    HS = S * SS
    img = _draw(HS, ask_font_path, rounded)
    return img.resize((S, S), Image.LANCZOS)

def _draw(S, ask_font_path, rounded):
    y2d, x2d = np.mgrid[0:S, 0:S].astype(float)

    cx, cy = S * 0.50, S * 0.50
    dist = np.sqrt(((x2d - cx)/(S*0.65))**2 + ((y2d - cy)/(S*0.65))**2)
    t    = np.clip(dist, 0, 1)
    R = np.clip(255 + (148 - 255)*t, 0, 255)
    G = np.clip(195 + ( 62 - 195)*t, 0, 255)
    B = np.clip( 45 + (  8 -  45)*t, 0, 255)
    tl = np.clip(1.0 - np.sqrt((x2d/(S*0.75))**2 + (y2d/(S*0.75))**2), 0, 1)**2.2 * 0.28
    R = np.clip(R + 50*tl, 0, 255)
    G = np.clip(G + 38*tl, 0, 255)
    B = np.clip(B + 18*tl, 0, 255)
    arr = np.stack([R, G, B, np.full((S,S),255.)], 2).astype(np.uint8)
    img = Image.fromarray(arr, 'RGBA')
    draw = ImageDraw.Draw(img)

    ask_size = int(S * 0.418)
    try:    ask_font = ImageFont.truetype(ask_font_path, ask_size)
    except: ask_font = ImageFont.load_default()

    ask_cx = S // 2
    ask_cy = int(S * 0.438)

    shd = max(2, S // 160)
    draw.text((ask_cx+shd, ask_cy+shd), "ASK", fill=(55,18,2,170), font=ask_font, anchor="mm")
    draw.text((ask_cx, ask_cy), "ASK", fill=(22,8,2), font=ask_font, anchor="mm")
    gs = max(2, int(ask_size * 0.042))
    draw.text((ask_cx, ask_cy-gs), "ASK", fill=(255,235,170,52), font=ask_font, anchor="mm")

    sep_y  = int(S * 0.722)
    sep_hw = int(S * 0.210)
    draw.line([(ask_cx-sep_hw, sep_y),(ask_cx+sep_hw, sep_y)],
              fill=(90,38,5,200), width=max(2, S//240))

    mt_size = int(S * 0.076)
    try:    mt_font = ImageFont.truetype(HELVETICA, mt_size)
    except: mt_font = ImageFont.load_default()
    mt_y = int(S * 0.818)
    draw.text((ask_cx, mt_y), "Mirror Talk", fill=(80,32,4), font=mt_font, anchor="mm")

    gloss = np.zeros((S,S,4), dtype=float)
    g_cx, g_cy = S*0.50, S*0.10
    g_rx, g_ry = S*0.44, S*0.20
    gx = (x2d - g_cx)/g_rx
    gy = (y2d - g_cy)/g_ry
    g_str = np.clip(1.0 - np.sqrt(gx**2+gy**2), 0, 1)**2.5 * 0.20
    gloss[:,:,3] = g_str*255
    gloss[:,:,0] = gloss[:,:,1] = gloss[:,:,2] = 255
    gi = Image.fromarray(gloss.astype(np.uint8), 'RGBA')
    gi = gi.filter(ImageFilter.GaussianBlur(max(2, int(S*0.022))))
    img = Image.alpha_composite(img, gi)

    if rounded:
        cr   = int(S*0.218)
        mask = Image.new('L',(S,S),0)
        md   = ImageDraw.Draw(mask)
        md.rectangle([cr,0,S-cr,S],fill=255)
        md.rectangle([0,cr,S,S-cr],fill=255)
        for ox,oy in [(0,0),(S-2*cr,0),(0,S-2*cr),(S-2*cr,S-2*cr)]:
            md.ellipse([ox,oy,ox+2*cr,oy+2*cr],fill=255)
        result = Image.new('RGBA',(S,S),(0,0,0,0))
        result.paste(img, mask=mask)
        return result
    else:
        return img.convert('RGB')

# ── Layout ────────────────────────────────────────────────────────────────
PX_SMALL  = 120   # true phone size
PX_ZOOM   = 300   # large preview
PAD       = 40
GAP       = 32
TXT_H     = 52
try:
    lbl = ImageFont.truetype(HELVETICA, 24)
    hdr = ImageFont.truetype(HELVETICA, 26)
except:
    lbl = hdr = ImageFont.load_default()

N = len(FONTS)
W = PAD + N*(PX_ZOOM + GAP) - GAP + PAD
H = PAD + 34 + GAP + (PX_SMALL + TXT_H + GAP) + (PX_ZOOM + TXT_H) + PAD

sheet = Image.new("RGB", (W, H), (14,14,18))
sd    = ImageDraw.Draw(sheet)

# Header
sd.text((W//2, PAD//2), "Font comparison at real size + 2.5× zoom",
        fill=(180,180,180), font=hdr, anchor="mt")

row1_y = PAD + 34 + GAP
row2_y = row1_y + PX_SMALL + TXT_H + GAP

for i, (name, fpath) in enumerate(FONTS):
    x = PAD + i*(PX_ZOOM + GAP)
    cx = x + PX_ZOOM//2

    # ── Real phone size (120px on dark strip) ────────────────────
    strip = Image.new("RGB", (PX_SMALL+20, PX_SMALL+20), (28,28,30))
    sheet.paste(strip, (cx - (PX_SMALL+20)//2, row1_y-10))

    small = make_icon(PX_SMALL, fpath, rounded=True)
    sheet.paste(small, (cx - PX_SMALL//2, row1_y),
                mask=small.split()[3] if small.mode=='RGBA' else None)

    sd.text((cx, row1_y + PX_SMALL + 8), "← real size",
            fill=(100,100,110), font=lbl, anchor="mt")

    # ── Zoomed version ───────────────────────────────────────────
    zoom = make_icon(PX_ZOOM, fpath, rounded=True)
    sheet.paste(zoom, (x, row2_y),
                mask=zoom.split()[3] if zoom.mode=='RGBA' else None)

    # Font label
    label_lines = name.split('\n')
    for li, line in enumerate(label_lines):
        sd.text((cx, row2_y + PX_ZOOM + 8 + li*22), line,
                fill=(200,200,200), font=lbl, anchor="mt")

out = os.path.join(BASE, "font_compare.png")
sheet.save(out)
print(f"Saved: {out}")
