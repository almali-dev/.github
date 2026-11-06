"""Build the Almali brand kit: the master mark and one asset set per product.

Usage: python build_brand.py SpaceGrotesk.ttf BRAND_DIR

Writes the master files at BRAND_DIR (same names as before, so existing README
links keep working) and one folder per product: BRAND_DIR/<product>/.
Space Grotesk is licensed under the SIL Open Font License 1.1; it is not stored here.
"""
import re
import sys
from pathlib import Path

import resvg_py
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

FONT_PATH, OUT = Path(sys.argv[1]), Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

INK, PAPER, MUTED, MUTED_DARK = "#17191F", "#F7F6F3", "#4D5260", "#B9BCC6"
ACCENT, ACCENT_DARK = "#2F6FEB", "#6B9BFF"

# ---------------------------------------------------------------- master mark
# 100x100 design space, stroke 11, round caps. Signature gap 2: the hook is
# lowered (never lengthened) so 56 - 43 - 11 = 2 units separate hook and stem.
HOOK = "M30 41 C35 31 49 28 59 29 C68 31 72 37 72 43"
STEM = "M72 56 L72 84"
BOWL = "M60 57 L50 57 C37 57 29 62 29 71 C29 80 37 85 46 85 C52 85 57 83 60 80"
# Hook curve top is y=28.82 (cap top 23.32); 24.0 keeps the original optical rounding.
MARK_BOUNDS = (23.5, 24.0, 77.5, 90.5)  # left, top, right, bottom


def stroke_group(inner):
    return f'<g fill="none" stroke-width="11" stroke-linecap="round" stroke-linejoin="round">{inner}</g>'


def master(ink, acc):
    return stroke_group(f'<path d="{HOOK}" stroke="{acc}"/><path d="{STEM}" stroke="{ink}"/><path d="{BOWL}" stroke="{ink}"/>')


# ------------------------------------------------------------ product glyphs
# Rule: an ink base plus one accent element, drawn in the same design space.
def mask(mid, shape, cuts, fill):
    return (f'<mask id="{mid}" maskUnits="userSpaceOnUse" x="0" y="0" width="100" height="110">'
            f'<rect x="0" y="0" width="100" height="110" fill="#fff"/>{cuts}</mask>'
            f'<g mask="url(#{mid})" fill="{fill}">{shape}</g>')


def smart_cache(ink, acc):
    """Content moving up to the fast tier: an accent arrow over the storage tiers."""
    return stroke_group(f'<path d="M28 80 L72 80" stroke="{ink}"/><path d="M28 64 L72 64" stroke="{ink}"/>'
                        f'<path d="M28 48 L52 48" stroke="{acc}"/><path d="M64 50 L64 24" stroke="{acc}"/>'
                        f'<path d="M54 33 L64 23 L74 33" stroke="{acc}"/>')


def llartv(ink, acc):
    """A calm home screen: a TV with a dock of favourite apps."""
    dock = "".join(f'<rect x="{x}" y="57" width="10" height="10" rx="3" fill="{acc}"/>' for x in (32, 45, 58))
    return (f'<rect x="20" y="30" width="60" height="46" rx="10" fill="none" stroke="{ink}" stroke-width="9"/>'
            + dock + stroke_group(f'<path d="M40 89 L60 89" stroke="{ink}"/>'))


def library_curator(ink, acc):
    """Movies and series (clapperboard) looked into (accent magnifier)."""
    stripes = ('<path d="M28 24 L37 24 L30 46 L21 46 Z M47 22 L56 22 L49 44 L40 44 Z" fill="#000"/>')
    lens = ('<circle cx="66" cy="66" r="21" fill="#000"/>'
            '<path d="M76 76 L86 86" stroke="#000" stroke-width="18" stroke-linecap="round"/>')
    board = mask("lc-board", '<rect x="14" y="46" width="60" height="38" rx="7"/>'
                 '<rect x="14" y="29" width="60" height="11" rx="4" transform="rotate(-10 14 40)"/>', lens + stripes, ink)
    return board + (f'<g fill="none" stroke="{acc}" stroke-linecap="round"><circle cx="66" cy="66" r="13" stroke-width="8"/>'
                    f'<path d="M76 76 L84 84" stroke-width="10"/></g>')


PRODUCTS = {
    "smart-cache": dict(name="Smart Cache", desc="for Plex · Unraid", draw=smart_cache,
                        bounds=(22.5, 17.5, 79.5, 85.5), light="#0891B2", dark="#00D2FF",
                        tagline="Moves Plex media between HDD and SSD based on viewing patterns."),
    "llartv": dict(name="LlarTV", desc="for Android TV", draw=llartv,
                   bounds=(15.5, 25.5, 84.5, 94.5), light="#E0533D", dark="#FF8A73",
                   tagline="A light, fast home screen for Android TV."),
    "library-curator": dict(name="Library Curator", desc="for Plex", draw=library_curator,
                            bounds=(12.0, 18.5, 89.0, 89.0), light="#7C4DDB", dark="#B49BFF",
                            tagline="Shows what nobody watches in a Plex library, and why."),
}

# ---------------------------------------------------------------- typography
VF = TTFont(FONT_PATH)
FONTS = {w: instantiateVariableFont(TTFont(FONT_PATH), {"wght": w}) for w in (500, 600)}
TRACKING = -0.03


def text_path(text, weight, size, x, baseline, fill):
    """Outline `text` in Space Grotesk; returns (svg path element, advance width)."""
    font = FONTS[weight]
    gs, cmap, hmtx, upm = font.getGlyphSet(), font.getBestCmap(), font["hmtx"], font["head"].unitsPerEm
    s = size / upm
    pen, cx = SVGPathPen(gs), 0.0
    for i, ch in enumerate(text):
        g = cmap[ord(ch)]
        gs[g].draw(TransformPen(pen, (s, 0, 0, -s, x + cx, baseline)))
        cx += hmtx[g][0] * s + (TRACKING * size if i < len(text) - 1 else 0)
    return f'<path d="{pen.getCommands()}" fill="{fill}"/>', cx


def text_bounds(text, weight):
    """Glyph bounds of `text` at size 1000, y down."""
    font = FONTS[weight]
    gs, cmap, hmtx = font.getGlyphSet(), font.getBestCmap(), font["hmtx"]
    s = 1000 / font["head"].unitsPerEm
    pen, cx = BoundsPen(gs), 0.0
    for i, ch in enumerate(text):
        g = cmap[ord(ch)]
        gs[g].draw(TransformPen(pen, (s, 0, 0, -s, cx, 0)))
        cx += hmtx[g][0] * s + (TRACKING * 1000 if i < len(text) - 1 else 0)
    return pen.bounds


# ------------------------------------------------------------------- helpers
def svg(w, h, body, vb=None, label="Almali", extra=""):
    vb = vb or f"0 0 {w:g} {h:g}"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" width="{w:g}" height="{h:g}"'
            f' role="img" aria-label="{label}">{extra}{body}</svg>\n')


def place(body, bounds, x, y, side, pad=0.0):
    """Fit a design-space drawing with `bounds` centred in a side x side box at (x, y)."""
    l, t, r, b = bounds
    ext = max(r - l, b - t)
    s = (side - 2 * pad) / ext
    tx = x + pad + (ext - (r - l)) / 2 * s - l * s
    ty = y + pad + (ext - (b - t)) / 2 * s - t * s
    return f'<g transform="translate({tx:.3f} {ty:.3f}) scale({s:.5f})">{body}</g>'


def theme_css(pairs):
    """Favicon CSS: dark-mode overrides keyed on the light colours (CSS beats presentation attributes)."""
    rules = "".join(f'[stroke="{a}"]{{stroke:{b}}}[fill="{a}"]{{fill:{b}}}' for a, b in pairs)
    return f"<style>@media (prefers-color-scheme: dark){{{rules}}}</style>"


files = {}  # relative path -> svg text
renders = []  # (svg relative path, png relative path, width)


def add(rel, content, *pngs):
    files[rel] = content
    for png_rel, width in pngs:
        renders.append((rel, png_rel, width))


# ------------------------------------------------------------- master files
ml, mt, mr, mb = MARK_BOUNDS
mark_h, pad = mb - mt, 8.0
side = mark_h + 2 * pad
mcx = (ml + mr) / 2
vb_sym = f"{mcx - side / 2:.2f} {mt - pad:.2f} {side:.2f} {side:.2f}"
add("almali-symbol.svg", svg(256, 256, master(INK, ACCENT), vb=vb_sym), ("png/almali-symbol.png", 512), ("png/favicon-32.png", 32))
add("almali-symbol-dark.svg", svg(256, 256, master(PAPER, ACCENT_DARK), vb=vb_sym), ("png/almali-symbol-dark.png", 512))

wb = text_bounds("almali", 600)
w_h_1000 = wb[3] - wb[1]


def almali_word(fill, glyph_h, x, y_top):
    """The almali wordmark with its glyph bounds `glyph_h` tall, top-left at (x, y_top)."""
    size = glyph_h * 1000 / w_h_1000
    baseline = y_top - wb[1] * size / 1000
    path, adv = text_path("almali", 600, size, x - wb[0] * size / 1000, baseline, fill)
    return path, (wb[2] - wb[0]) * size / 1000


for suffix, ink, acc in (("", INK, ACCENT), ("-dark", PAPER, ACCENT_DARK)):
    gap = 0.27 * mark_h
    wpath, ww = almali_word(ink, mark_h * 0.78, mr + gap, mt + mark_h * 0.22)
    total_w = (mr + gap + ww + pad) - (ml - pad)
    vb = f"{ml - pad:.2f} {mt - pad:.2f} {total_w:.2f} {mark_h + 2 * pad:.2f}"
    add(f"almali-horizontal{suffix}.svg", svg(round(total_w * 4), round((mark_h + 2 * pad) * 4), master(ink, acc) + wpath, vb=vb),
        (f"png/almali-horizontal{suffix}.png", 1200))
    wh = mark_h * 0.42
    ww = (wb[2] - wb[0]) * (wh / w_h_1000)
    y_word = mb + 0.16 * mark_h
    wpath, _ = almali_word(ink, wh, mcx - ww / 2, y_word)
    width = max(ww, mr - ml) + 2 * pad
    height = (y_word + wh + pad) - (mt - pad)
    vb = f"{mcx - width / 2:.2f} {mt - pad:.2f} {width:.2f} {height:.2f}"
    add(f"almali-vertical{suffix}.svg", svg(round(width * 4), round(height * 4), master(ink, acc) + wpath, vb=vb),
        (f"png/almali-vertical{suffix}.png", 600))

avatar = f'<rect width="512" height="512" fill="{INK}"/>' + place(master(PAPER, ACCENT_DARK), MARK_BOUNDS, 0, 0, 512, pad=97)
add("almali-avatar.svg", svg(512, 512, avatar), ("almali-avatar.png", 512), ("png/apple-touch-icon.png", 180))
add("favicon.svg", svg(32, 32, master(INK, ACCENT), vb=vb_sym, extra=theme_css([(INK, PAPER), (ACCENT, ACCENT_DARK)])))


def lockup(key, dark, scale=1.0):
    """Endorsed by-line lockup: symbol, product name, and 'desc · by [a] almali'. Returns (body, w, h)."""
    p = PRODUCTS[key]
    ink, acc = (PAPER, p["dark"]) if dark else (INK, p["light"])
    sub, blue = (MUTED_DARK, ACCENT_DARK) if dark else (MUTED, ACCENT)
    S = 96
    body = place(p["draw"](ink, acc), p["bounds"], 0, 0, S)
    x = S + 22
    name, nw = text_path(p["name"], 600, 56, x, 52, ink)
    by_text = f'{p["desc"]} · by ' if p["desc"] else "by "
    by, bw = text_path(by_text, 500, 21, x + 2, 86, sub)
    mini = place(master(ink, blue), MARK_BOUNDS, x + 2 + bw + 1, 68, 22)
    word, ww = text_path("almali", 600, 21, x + 2 + bw + 26, 86, ink)
    width = x + max(nw, 2 + bw + 26 + ww) + 8
    return body + name + by + mini + word, width, S


for key, p in PRODUCTS.items():
    draw, bounds = p["draw"], p["bounds"]
    light = (INK, p["light"])
    dark = (PAPER, p["dark"])
    add(f"{key}/symbol.svg", svg(256, 256, place(draw(*light), bounds, 0, 0, 256, pad=16), label=f"Almali {p['name']}"),
        (f"{key}/png/symbol.png", 512))
    add(f"{key}/symbol-dark.svg", svg(256, 256, place(draw(*dark), bounds, 0, 0, 256, pad=16), label=f"Almali {p['name']}"),
        (f"{key}/png/symbol-dark.png", 512))
    fav = place(draw(*light), bounds, 0, 0, 32, pad=1)
    add(f"{key}/favicon.svg", svg(32, 32, fav, label=f"Almali {p['name']}",
                                  extra=theme_css([(INK, PAPER), (p["light"], p["dark"])])),
        (f"{key}/png/favicon-32.png", 32))
    for suffix, is_dark in (("", False), ("-dark", True)):
        body, w, h = lockup(key, is_dark)
        add(f"{key}/lockup{suffix}.svg", svg(round(w * 2), round(h * 2), body, vb=f"0 0 {w:.2f} {h:.2f}", label=f"Almali {p['name']}"),
            (f"{key}/png/lockup{suffix}.png", 1200))
    tile = (f'<rect width="512" height="512" rx="112" fill="{INK}"/>'
            + place(draw(*dark), bounds, 0, 0, 512, pad=96))
    add(f"{key}/app-icon.svg", svg(512, 512, tile, label=f"Almali {p['name']}"),
        (f"{key}/png/app-icon-512.png", 512), (f"{key}/png/app-icon-256.png", 256), (f"{key}/png/apple-touch-icon.png", 180))
    # GitHub social preview, 1280x640 (upload by hand: repository Settings > Social preview).
    body, w, h = lockup(key, False)
    s = 820 / w
    tag, tw = text_path(p["tagline"], 500, 34, 0, 0, MUTED)
    social = (f'<rect width="1280" height="640" fill="{PAPER}"/>'
              f'<g transform="translate({(1280 - w * s) / 2:.2f} {250 - h * s / 2:.2f}) scale({s:.4f})">{body}</g>'
              f'<g transform="translate({(1280 - tw) / 2:.2f} 470)">{tag}</g>')
    add(f"{key}/social-preview.svg", svg(1280, 640, social, label=f"Almali {p['name']}"), (f"{key}/png/social-preview.png", 1280))

# Organization social preview.
wpath, ww = almali_word(INK, 150, 0, 0)
org = (f'<rect width="1280" height="640" fill="{PAPER}"/>'
       + place(master(INK, ACCENT), MARK_BOUNDS, 300, 210, 200)
       + f'<g transform="translate(530 235)">{wpath}</g>')
tag, tw = text_path("Self-hosted tools for a better home media setup.", 500, 34, 0, 0, MUTED)
org += f'<g transform="translate({(1280 - tw) / 2:.2f} 520)">{tag}</g>'
add("almali-social-preview.svg", svg(1280, 640, org), ("png/almali-social-preview.png", 1280))

# Android (LlarTV): legacy launcher icons, adaptive icon foreground and the Android TV banner.
lt = PRODUCTS["llartv"]
ANDROID = "llartv/android/res"
for dpi, px in (("mdpi", 48), ("hdpi", 72), ("xhdpi", 96), ("xxhdpi", 144), ("xxxhdpi", 192)):
    renders.append(("llartv/app-icon.svg", f"{ANDROID}/mipmap-{dpi}/ic_launcher.png", px))
    renders.append(("llartv/adaptive-foreground.svg", f"{ANDROID}/mipmap-{dpi}/ic_launcher_foreground.png", round(px * 108 / 48)))
# Adaptive foreground: 108dp canvas, content kept inside the 66dp safe zone.
files["llartv/adaptive-foreground.svg"] = svg(108, 108, place(lt["draw"](PAPER, lt["dark"]), lt["bounds"], 0, 0, 108, pad=27),
                                              label="Almali LlarTV")
banner_name, nw = text_path(lt["name"], 600, 50, 132, 98, PAPER)
banner_by, bw = text_path("by ", 500, 18, 134, 130, MUTED_DARK)
banner = (f'<rect width="320" height="180" fill="{INK}"/>'
          + place(lt["draw"](PAPER, lt["dark"]), lt["bounds"], 26, 44, 92)
          + banner_name + banner_by
          + place(master(PAPER, ACCENT_DARK), MARK_BOUNDS, 134 + bw, 114, 19)
          + text_path("almali", 600, 18, 134 + bw + 22, 130, PAPER)[0])
add("llartv/android-tv-banner.svg", svg(320, 180, banner, label="Almali LlarTV"), (f"{ANDROID}/drawable-xhdpi/banner.png", 320))
files[f"{ANDROID}/mipmap-anydpi-v26/ic_launcher.xml"] = (
    '<?xml version="1.0" encoding="utf-8"?>\n'
    '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
    '    <background android:drawable="@color/ic_launcher_background" />\n'
    '    <foreground android:drawable="@mipmap/ic_launcher_foreground" />\n'
    '</adaptive-icon>\n')
files[f"{ANDROID}/values/ic_launcher_background.xml"] = (
    '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
    f'    <color name="ic_launcher_background">{INK}</color>\n</resources>\n')

# ---------------------------------------------------------------------- write
for rel, content in files.items():
    path = OUT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
for src, dst, width in renders:
    path = OUT / dst
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(resvg_py.svg_to_bytes(svg_string=files[src], width=width)))

print("\n".join(sorted(p.relative_to(OUT).as_posix() for p in OUT.rglob("*")
                       if p.is_file() and "scripts" not in p.parts and not p.name.endswith(".md"))))
