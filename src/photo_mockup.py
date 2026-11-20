"""Apply the label to the reference box photo (perspective-correct).

    <venv with pillow+numpy>/bin/python src/photo_mockup.py <label_png_at_trim_size>

Lid top face measured on reference/box-reference-photo.png (562 x 746 px).
Box lid = 8.75 in (front/back edge) x 7.25 in (side edge). Label 7 x 5 in, centred:
0.875 in clearance left/right, 1.125 in clearance to the back hinge and to the front tuck fold.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
PHOTO = os.path.join(PROJECT, 'reference', 'box-reference-photo.png')
OUT = os.path.join(PROJECT, 'mockups')

LID_W, LID_D = 8.75, 7.25
LBL_W, LBL_H = 7.0, 5.0
# lid corners in photo px: back-left, back-right, front-right, front-left
LID_PX = [(27.5, 257.5), (345.0, 156.0), (550.0, 275.0), (167.5, 462.5)]
SS = 4  # supersample


def homography(src, dst):
    A = []
    for (x, y), (u, v) in zip(src, dst):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y, -u])
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y, -v])
    _, _, vt = np.linalg.svd(np.array(A))
    H = vt[-1].reshape(3, 3)
    return H / H[2, 2]


def main(label_png, name='mockup-on-reference-photo.png'):
    os.makedirs(OUT, exist_ok=True)
    photo = Image.open(PHOTO).convert('RGB')
    W, H = photo.size
    big = photo.resize((W * SS, H * SS), Image.LANCZOS)

    lid_in = [(0, 0), (LID_W, 0), (LID_W, LID_D), (0, LID_D)]
    lid_px = [(x * SS, y * SS) for x, y in LID_PX]
    H_in2px = homography(lid_in, lid_px)

    label = Image.open(label_png).convert('RGBA')
    lw, lh = label.size
    x0, y0 = (LID_W - LBL_W) / 2, (LID_D - LBL_H) / 2
    # label px -> lid inches -> photo px
    S = np.array([[LBL_W / lw, 0, x0], [0, LBL_H / lh, y0], [0, 0, 1]])
    Hl = H_in2px @ S
    inv = np.linalg.inv(Hl)
    inv = inv / inv[2, 2]
    warped = label.transform(big.size, Image.PERSPECTIVE, tuple(inv.flatten()[:8]), Image.BICUBIC)

    # carry the photo's light falloff + kraft texture onto the label
    lum = np.asarray(big.convert('L'), dtype=np.float32)
    alpha = np.asarray(warped.split()[3], dtype=np.float32) / 255
    mean = (lum * alpha).sum() / max(alpha.sum(), 1)
    shade = np.clip((lum / mean) ** 0.75, 0.6, 1.25)[..., None]
    lab = np.asarray(warped.convert('RGB'), dtype=np.float32) * shade
    grain = np.asarray(big.filter(ImageFilter.GaussianBlur(1)).convert('L'), dtype=np.float32)
    lab *= (1 + (lum - grain)[..., None] / 255 * 0.6)  # keep fine paper texture

    # soft contact shadow just outside the label edge
    sh = Image.fromarray((alpha * 255).astype('uint8')).filter(ImageFilter.GaussianBlur(SS * 1.2))
    sha = np.asarray(sh, dtype=np.float32)[..., None] / 255 * 0.22
    base = np.asarray(big, dtype=np.float32) * (1 - sha)

    a = alpha[..., None]
    out = base * (1 - a) + np.clip(lab, 0, 255) * a
    res = Image.fromarray(out.astype('uint8')).resize((W * 2, H * 2), Image.LANCZOS)
    res.save(os.path.join(OUT, name))
    print('saved', os.path.join(OUT, name), res.size)


if __name__ == '__main__':
    main(*sys.argv[1:3])
