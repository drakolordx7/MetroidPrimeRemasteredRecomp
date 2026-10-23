"""S25: sheet.py out.jpg a.jpg b.jpg ... : contact sheet (2 columns) of preview images."""
import sys
from PIL import Image
out, files = sys.argv[1], sys.argv[2:]
ims = [Image.open(f).convert('RGB').resize((640, 360)) for f in files]
cols = 2
rows = (len(ims) + 1) // 2
sh = Image.new('RGB', (640 * cols, 360 * rows))
for i, im in enumerate(ims):
    sh.paste(im, ((i % cols) * 640, (i // cols) * 360))
sh.save(out, quality=80)
