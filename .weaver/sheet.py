"""Contact sheet of any PNGs: python .weaver/sheet.py out.png [--cols 4] [--thumb 480x270] file1.png file2.png ... (or a folder)"""
import argparse, glob, os
from PIL import Image, ImageDraw
ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('files', nargs='+'); ap.add_argument('--cols', type=int, default=4); ap.add_argument('--thumb', default='480x270')
a = ap.parse_args(); tw, th = (int(x) for x in a.thumb.split('x'))
fs = []
for f in a.files: fs += sorted(glob.glob(os.path.join(f, '*.png'))) if os.path.isdir(f) else [f]
rows = (len(fs) + a.cols - 1) // a.cols
s = Image.new('RGB', (a.cols * tw, rows * (th + 14)), (30, 30, 30)); d = ImageDraw.Draw(s)
for i, f in enumerate(fs):
    im = Image.open(f).convert('RGB').resize((tw, th)); x, y = (i % a.cols) * tw, (i // a.cols) * (th + 14)
    s.paste(im, (x, y + 14)); d.text((x + 3, y + 1), os.path.basename(f), fill=(255, 255, 0))
s.save(a.out); print(a.out, len(fs))
