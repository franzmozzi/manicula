"""Extract the two pointing figures from the reference PNG, drop the
calligraphic text around them, and trace each into a single-colour SVG."""
import sys, re, shutil, tempfile
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
import vtracer

# usage: extract.py [reference.png] [out_dir]   (defaults: tools/reference.png -> src/svg)
ROOT = Path(__file__).resolve().parent.parent
SRC = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "tools" / "reference.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else str(ROOT / "src" / "svg")
TMP = tempfile.mkdtemp(prefix="manicula-")   # intermediate bitmaps and raw traces
INK = "#231a15"
SCALE = 3

img = Image.open(SRC).convert("L")
g = np.asarray(img).astype(np.float32)

FIGS = {
    # crop box (x0, y0, x1, y1) and text zones: drop components whose bbox lies inside
    "left": dict(box=(88, 236, 506, 708),
                 drop=lambda x0, y0, x1, y1: (x0 >= 362 and y1 <= 522) or (x0 >= 340 and y0 >= 600) or y1 <= 244),
    "right": dict(box=(538, 236, 966, 708),
                  drop=lambda x0, y0, x1, y1: y1 <= 244 or y0 >= 704),
}

for name, cfg in FIGS.items():
    x0, y0, x1, y1 = cfg["box"]
    crop = g[y0:y1, x0:x1]
    dark = crop < 170
    lab, n = ndimage.label(dark, structure=np.ones((3, 3)))
    keep = np.zeros_like(dark)
    for i, sl in enumerate(ndimage.find_objects(lab), start=1):
        ys, xs = sl
        bx0, by0, bx1, by1 = xs.start + x0, ys.start + y0, xs.stop + x0, ys.stop + y0
        size = int((lab[sl] == i).sum())
        if size < 6 or cfg["drop"](bx0, by0, bx1, by1):
            continue
        keep |= lab == i
    mask = ndimage.binary_dilation(keep, iterations=2)
    clean = np.where(mask, crop, 255.0)
    # Trim to the ink bounding box with a small margin
    ys, xs = np.nonzero(keep)
    m = 4
    ty0, ty1 = max(ys.min() - m, 0), min(ys.max() + m + 1, clean.shape[0])
    tx0, tx1 = max(xs.min() - m, 0), min(xs.max() + m + 1, clean.shape[1])
    clean = clean[ty0:ty1, tx0:tx1]
    h, w = clean.shape
    big = Image.fromarray(clean.astype(np.uint8)).resize((w * SCALE, h * SCALE), Image.LANCZOS)
    bw = (np.asarray(big) < 125)
    Image.fromarray(np.where(bw, 0, 255).astype(np.uint8)).save(f"{TMP}/{name}_clean.png")
    vtracer.convert_image_to_svg_py(f"{TMP}/{name}_clean.png", f"{TMP}/{name}_raw.svg", colormode="binary", mode="spline",
        filter_speckle=6, corner_threshold=60, length_threshold=4.0, splice_threshold=45, path_precision=1)
    svg = open(f"{TMP}/{name}_raw.svg").read()
    paths = re.findall(r'<path d="([^"]+)"[^>]*?transform="translate\(([-\d.]+),([-\d.]+)\)"', svg)
    out = []
    for d, tx, ty in paths:
        out.append(f'<path transform="translate({tx} {ty})" d="{d.strip()}"/>')
    W, H = w * SCALE, h * SCALE
    doc = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
           f'<g fill="{INK}" fill-rule="evenodd">' + "".join(out) + "</g></svg>")
    open(f"{OUT}/{name}.svg", "w").write(doc)
    print(name, W, H, len(paths), len(doc))

shutil.rmtree(TMP, ignore_errors=True)
