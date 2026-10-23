"""List every 36x36 one-mip TXTR of the extracted paks (work/survey/paks, not Worlds) with the FNV-1a hash of its tiled buffer
(the hash src/gfx/play/prompts.cpp uses), so the button textures the game really draws can be found.
python find_icon_txtrs.py [hash_to_find_hex]"""
import glob
import os
import sys

sys.path.insert(0, r'D:\AI\Active\Metroid-Prime\tools\survey')
from txtr_decode import load


def fnv(b):
    h = 0xcbf29ce484222325
    for c in b:
        h ^= c
        h = (h * 0x100000001b3) & 0xFFFFFFFFFFFFFFFF
    return h


want = int(sys.argv[1], 16) if len(sys.argv) > 1 else None
for path in sorted(glob.glob(r'D:\AI\Active\Metroid-Prime\work\survey\paks\**\*.TXTR', recursive=True)):
    if 'Worlds' in path:
        continue
    try:
        head, buf = load(path)
    except Exception:
        continue
    if head['w'] != 36 or head['h'] != 36:
        continue
    h = fnv(bytes(buf[:3072]))
    nz = sum(1 for c in buf[:3072] if c)
    print(os.path.relpath(path, r'D:\AI\Active\Metroid-Prime\work\survey\paks'), head['fmt'], len(buf), '%016x' % h, 'nz', nz, '<== MATCH' if h == want else '')
