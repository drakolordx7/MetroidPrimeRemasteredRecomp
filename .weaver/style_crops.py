"""Crops of the title prompt and the menu footer for each prompt style, stacked in one picture.
python style_crops.py OUT.png TITLE_SHOT_N FOOTER_SHOT_N style1 style2 ...   (reads work/polish_shots/<style>_shot_<N>.png)"""
import sys

from PIL import Image, ImageDraw

out, tn, fn, styles = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
rows = []
for st in styles:
    t = Image.open(f'D:/AI/Active/Metroid-Prime/work/polish_shots/{st}_shot_{tn}.png')
    w, h = t.size
    c1 = t.crop((int(w * 0.33), int(h * 0.80), int(w * 0.67), int(h * 0.90)))
    f = Image.open(f'D:/AI/Active/Metroid-Prime/work/polish_shots/{st}_shot_{fn}.png')
    c2 = f.crop((int(w * 0.02), int(h * 0.94), int(w * 0.30), int(h * 0.995)))
    c1 = c1.resize((c1.width * 2, c1.height * 2), Image.LANCZOS)
    c2 = c2.resize((c2.width * 2, c2.height * 2), Image.LANCZOS)
    row = Image.new('RGB', (c1.width + c2.width + 10, max(c1.height, c2.height) + 16), (30, 30, 30))
    row.paste(c1, (0, 16))
    row.paste(c2, (c1.width + 10, 16))
    ImageDraw.Draw(row).text((4, 2), st, fill=(255, 255, 0))
    rows.append(row)
W = max(r.width for r in rows)
H = sum(r.height for r in rows)
s = Image.new('RGB', (W, H))
y = 0
for r in rows:
    s.paste(r, (0, y))
    y += r.height
s.save(out)
print(s.size)
