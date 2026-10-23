"""Contact sheet: contact.py out.png img1 img2 ... (each scaled to 480 wide, 3 columns, labelled with the file name)."""
import os
import sys

from PIL import Image, ImageDraw

out, files = sys.argv[1], sys.argv[2:]
W = int(os.environ.get("CW", 480))
cols = int(os.environ.get("CC", 3))
ims = []
for f in files:
    im = Image.open(f).convert('RGB')
    h = int(im.height * W / im.width)
    im = im.resize((W, h))
    ImageDraw.Draw(im).text((4, 4), os.path.basename(f), fill=(255, 255, 0))
    ims.append(im)
rows = (len(ims) + cols - 1) // cols
H = max(i.height for i in ims)
sheet = Image.new('RGB', (W * cols, H * rows))
for i, im in enumerate(ims):
    sheet.paste(im, ((i % cols) * W, (i // cols) * H))
sheet.save(out)
