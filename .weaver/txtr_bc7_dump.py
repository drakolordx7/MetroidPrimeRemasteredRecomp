"""Decode a 1-mip block-linear BC7 TXTR (e.g. the 36x36 button icons) to PNG with Pillow (untile gob_y given): txtr_bc7_dump.py <file.TXTR> <out.png> [block_height_gobs=2]"""
import sys, struct
sys.path.insert(0, r'D:\AI\Active\Metroid-Prime\tools\survey')
from txtr_decode import load
from PIL import Image
path, out = sys.argv[1], sys.argv[2]
bh = int(sys.argv[3]) if len(sys.argv) > 3 else 2
head, buf = load(path)
w, h = head['w'], head['h']
bw, bhh = (w + 3) // 4, (h + 3) // 4
gobs_w = (bw * 16 + 63) // 64
lin = bytearray(bw * bhh * 16)
for by in range(bhh):
    for bx in range(bw):
        x = bx * 16; y = by
        gx = x // 64; grp = y // (8 * bh); gy = (y % (8 * bh)) // 8
        off = (grp * gobs_w + gx) * 512 * bh + gy * 512
        xi, yi = x % 64, y % 8
        off += (xi // 32) * 256 + (yi // 2) * 64 + ((xi % 32) // 16) * 32 + (yi % 2) * 16
        lin[(by * bw + bx) * 16:(by * bw + bx) * 16 + 16] = buf[off:off + 16]
print(head['fmt'], w, h, len(buf))
# DDS DX10 header
DXGI = 99 if 'Srgb' in head['fmt'] else 98
hdr = b'DDS ' + struct.pack('<7I', 124, 0x1007 | 0x80000, h, w, len(lin), 0, 0) + b'\0' * 44 + struct.pack('<2I4s5I', 32, 4, b'DX10', 0, 0, 0, 0, 0) + struct.pack('<5I', 0x1000, 0, 0, 0, 0) + struct.pack('<5I', DXGI, 3, 0, 1, 0)
open(out + '.dds', 'wb').write(hdr + bytes(lin))
im = Image.open(out + '.dds'); im.load(); im.convert('RGBA').save(out); print('ok', im.size)
