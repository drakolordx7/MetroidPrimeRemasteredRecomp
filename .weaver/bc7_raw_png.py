"""Decode a raw block-linear 36x36 BC7 sRGB buffer (3072 bytes, block height 1 or 2 GOBs) to PNG: bc7_raw_png.py raw.bin out.png [block_height_gobs=1]"""
import struct
import sys

from PIL import Image

path, out = sys.argv[1], sys.argv[2]
bh = int(sys.argv[3]) if len(sys.argv) > 3 else 1
buf = open(path, 'rb').read()
w = h = 36
bw, bhh = (w + 3) // 4, (h + 3) // 4
gobs_w = (bw * 16 + 63) // 64
lin = bytearray(bw * bhh * 16)
for by in range(bhh):
    for bx in range(bw):
        x = bx * 16
        y = by
        gx = x // 64
        grp = y // (8 * bh)
        gy = (y % (8 * bh)) // 8
        off = (grp * gobs_w + gx) * 512 * bh + gy * 512
        xi, yi = x % 64, y % 8
        off += (xi // 32) * 256 + (yi // 2) * 64 + ((xi % 32) // 16) * 32 + (yi % 2) * 16
        lin[(by * bw + bx) * 16:(by * bw + bx) * 16 + 16] = buf[off:off + 16]
hdr = (b'DDS ' + struct.pack('<7I', 124, 0x1007 | 0x80000, h, w, len(lin), 0, 0) + b'\0' * 44 +
       struct.pack('<2I4s5I', 32, 4, b'DX10', 0, 0, 0, 0, 0) + struct.pack('<5I', 0x1000, 0, 0, 0, 0) + struct.pack('<5I', 99, 3, 0, 1, 0))
open(out + '.dds', 'wb').write(hdr + bytes(lin))
im = Image.open(out + '.dds')
im.load()
im.convert('RGBA').save(out)
