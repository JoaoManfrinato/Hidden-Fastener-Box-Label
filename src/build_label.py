"""Build the Deckotech hidden-fastener box label artwork.

    <venv-with-uharfbuzz>/bin/python src/build_label.py

Outputs (in ../artwork):
  label_print.svg    - full-bleed artwork (7.25 x 5.25 in), all text outlined. Imported by make_print_files.jsx
  label_preview.svg  - trim size (7 x 5 in) with rounded corners, used by the mockups

Units: points (72 pt = 1 in). Label trim 7 x 5 in, bleed 0.125 in, corner radius 0.125 in.
"""
import os
import re

import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib.path import parse_path

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
VAULT = os.path.abspath(os.path.join(PROJECT, '..', '..', 'Deckotech'))
FONT = os.path.join(VAULT, '05 Assets', 'Fonts', 'Inter', 'Inter-VariableFont_opsz,wght.ttf')
LOGO = os.path.join(VAULT, '05 Assets', 'Logo', 'Deckotech_Logo_Horizontal.svg')
OUT = os.path.join(PROJECT, 'artwork')

# ---- geometry (pt)
TRIM_W, TRIM_H = 504, 360        # 7 x 5 in
BLEED = 9                        # 0.125 in
RADIUS = 9                       # 0.125 in die-cut corner
M = 32                           # outer margin inside trim (safe zone is 9 pt; we keep well inside)

# ---- colours (screen values; make_print_files.jsx maps them to CMYK swatches)
ORANGE = '#FF5623'   # Deckotech Orange  -> Pantone 172 C / CMYK 0 80 95 0
BOARD = '#FF6B3D'    # tint for the deck-board motif -> CMYK 0 68 80 0
WHITE = '#FFFFFF'    # paper white (no ink)

blob = hb.Blob.from_file_path(FONT)
face = hb.Face(blob)
UPEM = face.upem


def text_path(s, size, x, baseline, wght, opsz=32, tracking=0.0):
    """Shape `s` with HarfBuzz (kerning on) and return (svg path d, advance width in pt)."""
    font = hb.Font(face)
    font.set_variations({'wght': wght, 'opsz': opsz})
    buf = hb.Buffer()
    buf.add_str(s)
    buf.guess_segment_properties()
    hb.shape(font, buf, {'kern': True, 'liga': True})
    scale = size / UPEM
    pen = SVGPathPen(None, ntos=lambda v: f'{v:.2f}')
    cx = 0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        tp = TransformPen(pen, (scale, 0, 0, -scale, x + (cx + pos.x_offset) * scale, baseline - pos.y_offset * scale))
        font.draw_glyph_with_pen(info.codepoint, tp)
        cx += pos.x_advance + tracking * UPEM
    return pen.getCommands(), cx * scale


def logo_paths():
    raw = open(LOGO).read()
    ds = re.findall(r'<path d="([^"]+)"', raw)
    bp = BoundsPen(None)
    for d in ds:
        parse_path(d, bp)
    return ds, bp.bounds  # (xmin, ymin, xmax, ymax) in logo units, y down


def build():
    os.makedirs(OUT, exist_ok=True)
    ox = oy = BLEED  # trim origin inside the bleed canvas
    els = []

    # background, full bleed
    els.append(f'<rect id="bg" x="0" y="0" width="{TRIM_W + 2 * BLEED}" height="{TRIM_H + 2 * BLEED}" fill="{ORANGE}"/>')

    # deck-board motif (echoes the stacked bars of the Deckotech symbol), bleeding off the right edge
    n, gap = 6, 9.0
    full_h = TRIM_H + 2 * BLEED
    bh = (full_h - gap * (n - 1)) / n
    bx = ox + 396
    boards = []
    for i in range(n):
        y = i * (bh + gap)
        boards.append(f'<rect x="{bx:.2f}" y="{y:.2f}" width="{TRIM_W + 2 * BLEED - bx:.2f}" height="{bh:.2f}" rx="3" fill="{BOARD}"/>')
    els.append('<g id="boards">' + ''.join(boards) + '</g>')

    # logo, white, top-left
    ds, (lx0, ly0, lx1, ly1) = logo_paths()
    logo_w = 232
    s = logo_w / (lx1 - lx0)
    logo_h = (ly1 - ly0) * s
    els.append(f'<g id="logo" fill="{WHITE}" transform="translate({ox + M:.2f} {oy + M:.2f}) scale({s:.5f}) translate({-lx0:.2f} {-ly0:.2f})">'
               + ''.join(f'<path d="{d}"/>' for d in ds) + '</g>')

    # headline + subline + footer
    tx = ox + M
    d1, w1 = text_path('Hidden', 62, tx - 3, oy + 172, 700, tracking=-0.02)
    d2, w2 = text_path('fasteners', 62, tx - 3, oy + 232, 700, tracking=-0.02)
    d3, w3 = text_path('For Deckotech decking', 20, tx - 1, oy + 272, 500)
    d4, w4 = text_path('deckotech.us', 11.5, tx, oy + TRIM_H - M, 600, opsz=14, tracking=0.02)
    assert tx + max(w1, w2, w3) < bx - 12, 'headline collides with board motif'
    els.append(f'<g id="text" fill="{WHITE}"><path id="headline1" d="{d1}"/><path id="headline2" d="{d2}"/>'
               f'<path id="subline" d="{d3}"/><path id="url" d="{d4}"/></g>')
    # thin rule above the URL
    ry = oy + TRIM_H - M - 22
    els.append(f'<rect id="rule" x="{tx:.2f}" y="{ry:.2f}" width="{w3 + 1:.2f}" height="1" fill="{WHITE}"/>')

    art = '\n'.join(els)
    W, H = TRIM_W + 2 * BLEED, TRIM_H + 2 * BLEED

    with open(os.path.join(OUT, 'label_print.svg'), 'w') as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}pt" height="{H}pt" viewBox="0 0 {W} {H}">\n{art}\n</svg>\n')

    with open(os.path.join(OUT, 'label_preview.svg'), 'w') as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{TRIM_W}pt" height="{TRIM_H}pt" viewBox="{BLEED} {BLEED} {TRIM_W} {TRIM_H}">\n'
                f'<defs><clipPath id="die"><rect x="{BLEED}" y="{BLEED}" width="{TRIM_W}" height="{TRIM_H}" rx="{RADIUS}"/></clipPath></defs>\n'
                f'<g clip-path="url(#die)">\n{art}\n</g>\n</svg>\n')
    print(f'logo {logo_w}x{logo_h:.1f}pt | headline {max(w1, w2):.1f}pt | sub {w3:.1f}pt -> {OUT}')


if __name__ == '__main__':
    build()
