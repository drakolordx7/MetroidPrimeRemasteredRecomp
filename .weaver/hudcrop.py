"""S25: hudcrop.py out.png a.png b.png ... : the missile counter area (right side) of full-size screenshots side by side"""
import sys
from PIL import Image
out, files = sys.argv[1], sys.argv[2:]
ims = [Image.open(f).convert('RGB').crop((1450, 400, 1700, 560)) for f in files]
sh = Image.new('RGB', (250 * len(ims), 160))
for i, im in enumerate(ims): sh.paste(im, (i * 250, 0))
sh.save(out)
