"""Decode a texdump BC6H texture (t<id>.bin/.txt written by [nvn] trace_dump_tex) to a PNG: all faces of level 0 side by side.  python bc6view.py t5602 out.png [level]"""
import sys, re, texture2ddecoder
from PIL import Image
base, out = sys.argv[1], sys.argv[2]
lvl = int(sys.argv[3]) if len(sys.argv) > 3 else 0
txt = open(base + '.txt').read().splitlines()
head = txt[0].split(); layers = int(head[head.index('layers') + 1]); fmt = int(head[head.index('format') + 1])
lv = [l.split() for l in txt[1:]]
w, h, d = map(int, lv[lvl][1:4]); off = int(lv[lvl][5]); size = int(lv[lvl][7])
data = open(base + '.bin', 'rb').read()
per = size // layers
signed = fmt == 144
tiles = []
for k in range(layers):
    blk = data[off + k * per: off + (k + 1) * per]
    raw = (texture2ddecoder.decode_bc6s(blk, w, h) if signed else texture2ddecoder.decode_bc6(blk, w, h))
    im = Image.frombytes('RGBA', (w, h), raw, 'raw', 'BGRA')
    tiles.append(im)
sheet = Image.new('RGBA', (w * layers, h))
for k, t in enumerate(tiles): sheet.paste(t, (k * w, 0))
sheet.save(out); print(out, sheet.size)
