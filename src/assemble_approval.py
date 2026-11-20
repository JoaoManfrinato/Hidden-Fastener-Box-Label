"""Embed artwork + mockups into approval/DKT_Hidden-Fastener-Label_Approval.html (needs pillow, fonttools)."""
import base64, io, os, re
from PIL import Image
from fontTools.pens.boundsPen import BoundsPen
from fontTools.svgLib.path import parse_path

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def uri(img, fmt, **kw):
    b = io.BytesIO(); img.save(b, fmt, **kw)
    return f'data:image/{fmt.lower()};base64,' + base64.b64encode(b.getvalue()).decode()

labels = {'a': 'artwork/label_preview_1400.png', **{k: f'artwork/options/option-{k}_preview_1400.png' for k in 'bcd'}}
h = open(os.path.join(P, 'src/approval_template.html')).read()
for k, f in labels.items():
    h = h.replace('{{LABEL_%s}}' % k.upper(), uri(Image.open(os.path.join(P, f)).convert('RGBA').resize((1120, 800), Image.LANCZOS), 'PNG', optimize=True))
    h = h.replace('{{MOCK_%s}}' % k.upper(), uri(Image.open(os.path.join(P, f'mockups/mockup-option-{k}.png')).convert('RGB'), 'JPEG', quality=82))
ref = Image.open(os.path.join(P, 'reference/box-reference-photo.png')).convert('RGB').resize((1124, 1492), Image.LANCZOS)
h = h.replace('{{REF}}', uri(ref, 'JPEG', quality=80))
raw = open(os.path.join(P, '../../Deckotech/05 Assets/Logo/Deckotech_Logo_Horizontal.svg')).read()
ds = re.findall(r'<path d="([^"]+)"', raw); bp = BoundsPen(None)
for d in ds: parse_path(d, bp)
x0, y0, x1, y1 = bp.bounds
h = h.replace('{{LOGO}}', f'<svg viewBox="{x0:.0f} {y0:.0f} {x1-x0:.0f} {y1-y0:.0f}" role="img" aria-label="Deckotech" fill="currentColor">' + ''.join(f'<path d="{d}"/>' for d in ds) + '</svg>')
assert '{{' not in h
out = os.path.join(P, 'approval/DKT_Hidden-Fastener-Label_Approval.html')
open(out, 'w').write(h); print(len(h) // 1024, 'KB ->', out)
