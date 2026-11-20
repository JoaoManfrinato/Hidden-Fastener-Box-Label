"""Three alternative premium layouts for the hidden-fastener label (same copy, same 7 x 5 in die).

    <venv>/bin/python src/build_options.py

Outputs artwork/options/option-{b,c,d}_{print,preview}.svg
  B  Iron      - Iron Black (Black 7 C), centered, tracked caps, orange foot band
  C  Split     - Marshmallow field + orange panel carrying the star badge
  D  Tonal     - Deckotech Orange with an oversized tone-on-tone star badge
Option A is the original layout from build_label.py.
"""
import os
import re

from fontTools.pens.boundsPen import BoundsPen
from fontTools.svgLib.path import parse_path

from build_label import BLEED, PROJECT, RADIUS, TRIM_H, TRIM_W, VAULT, text_path

LOGOS = os.path.join(VAULT, '05 Assets', 'Logo')
OUT = os.path.join(PROJECT, 'artwork', 'options')
W, H = TRIM_W + 2 * BLEED, TRIM_H + 2 * BLEED
OX = OY = BLEED

ORANGE = '#FF5623'
ORANGE_DEEP = '#EC4A17'   # tone-on-tone partner -> CMYK 0 85 100 6
IRON = '#3D3935'          # Black 7 C
PAPER = '#FDFCF4'         # Marshmallow (prints as paper white)
VAPOR = '#ECE8E3'
STONE = '#B3ABA3'
WHITE = '#FFFFFF'


def mark(name, x, y, fill, w=None, h=None):
    raw = open(os.path.join(LOGOS, name)).read()
    ds = re.findall(r'<path d="([^"]+)"', raw)
    bp = BoundsPen(None)
    for d in ds:
        parse_path(d, bp)
    x0, y0, x1, y1 = bp.bounds
    s = (w / (x1 - x0)) if w else (h / (y1 - y0))
    g = (f'<g fill="{fill}" transform="translate({x:.2f} {y:.2f}) scale({s:.5f}) translate({-x0:.2f} {-y0:.2f})">'
         + ''.join(f'<path d="{d}"/>' for d in ds) + '</g>')
    return g, (x1 - x0) * s, (y1 - y0) * s


def txt(s, size, x, base, wght, fill, align='left', tracking=0.0, opsz=32):
    _, w = text_path(s, size, 0, 0, wght, opsz=opsz, tracking=tracking)
    if tracking:  # trailing tracking is not ink
        w -= tracking * size
    if align == 'center':
        x -= w / 2
    elif align == 'right':
        x -= w
    d, _ = text_path(s, size, x, base, wght, opsz=opsz, tracking=tracking)
    return f'<path fill="{fill}" d="{d}"/>', w


def rect(x, y, w, h, fill, rx=0):
    return f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="{rx}" fill="{fill}"/>'


def option_b():
    """Iron: dark, centered, quiet luxury."""
    cx = OX + TRIM_W / 2
    e = [rect(0, 0, W, H, IRON)]
    g, lw, lh = mark('Deckotech_Logo_Horizontal.svg', 0, 0, WHITE, w=176)
    g, lw, lh = mark('Deckotech_Logo_Horizontal.svg', cx - 88, OY + 42, WHITE, w=176)
    e.append(g)
    e.append(rect(cx - 18, OY + 42 + lh + 26, 36, 2, ORANGE))
    e.append(txt('HIDDEN', 46, cx, OY + 190, 600, WHITE, 'center', tracking=0.14)[0])
    e.append(txt('FASTENERS', 46, cx, OY + 242, 600, WHITE, 'center', tracking=0.14)[0])
    e.append(txt('For Deckotech decking', 16, cx, OY + 280, 400, VAPOR, 'center', tracking=0.01)[0])
    band = OY + TRIM_H - 40
    e.append(rect(0, band, W, H - band, ORANGE))
    e.append(txt('DECKOTECH.US', 10, cx, band + 24.5, 600, WHITE, 'center', tracking=0.22, opsz=14)[0])
    return e


def option_c():
    """Split: light editorial field + orange badge panel."""
    split = OX + 326
    e = [rect(0, 0, W, H, PAPER), rect(split, 0, W - split, H, ORANGE)]
    pw = W - split - BLEED
    g, sw, sh = mark('Deckotech_Symbol_Logo.svg', 0, 0, WHITE, h=104)
    g, sw, sh = mark('Deckotech_Symbol_Logo.svg', split + (pw - sw) / 2, OY + (TRIM_H - sh) / 2, WHITE, h=104)
    e.append(g)
    m = 34
    e.append(mark('Deckotech_Logo_Type.svg', OX + m, OY + 38, ORANGE, w=138)[0])
    e.append(txt('Hidden', 50, OX + m - 2, OY + 168, 700, IRON, tracking=-0.025)[0])
    e.append(txt('fasteners', 50, OX + m - 2, OY + 218, 700, IRON, tracking=-0.025)[0])
    e.append(txt('For Deckotech decking', 17, OX + m, OY + 254, 500, ORANGE)[0])
    e.append(rect(OX + m, OY + TRIM_H - 62, split - OX - 2 * m, 0.75, STONE))
    e.append(txt('deckotech.us', 10.5, OX + m, OY + TRIM_H - m, 500, IRON, tracking=0.02, opsz=14)[0])
    return e


def option_d():
    """Tonal: orange on orange, oversized star badge bleeding off the edge."""
    e = [rect(0, 0, W, H, ORANGE)]
    e.append(mark('Deckotech_Symbol_Logo.svg', OX + 168, OY + 40, ORANGE_DEEP, h=360)[0])
    m = 34
    e.append(mark('Deckotech_Logo_Type.svg', OX + m, OY + 36, WHITE, w=150)[0])
    e.append(txt('Hidden fasteners', 46, OX + m - 2, OY + 262, 700, WHITE, tracking=-0.025)[0])
    e.append(rect(OX + m, OY + 284, 28, 2, WHITE))
    e.append(txt('For Deckotech decking', 15, OX + m, OY + TRIM_H - m, 500, WHITE)[0])
    e.append(txt('deckotech.us', 10.5, OX + TRIM_W - m, OY + TRIM_H - m, 600, WHITE, 'right', tracking=0.02, opsz=14)[0])
    return e


def write(key, els):
    art = '\n'.join(els)
    with open(os.path.join(OUT, f'option-{key}_print.svg'), 'w') as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}pt" height="{H}pt" viewBox="0 0 {W} {H}">\n{art}\n</svg>\n')
    with open(os.path.join(OUT, f'option-{key}_preview.svg'), 'w') as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{TRIM_W}pt" height="{TRIM_H}pt" viewBox="{BLEED} {BLEED} {TRIM_W} {TRIM_H}">\n'
                f'<defs><clipPath id="die"><rect x="{BLEED}" y="{BLEED}" width="{TRIM_W}" height="{TRIM_H}" rx="{RADIUS}"/></clipPath></defs>\n'
                f'<g clip-path="url(#die)">\n{art}\n</g>\n</svg>\n')


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for k, fn in (('b', option_b), ('c', option_c), ('d', option_d)):
        write(k, fn())
    print('ok ->', OUT)
