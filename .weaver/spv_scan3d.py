"""List fragment-stage SPIR-V files in the shader cache that sample 3D images (tone-map / colour-grade candidates).
   python -I .weaver/spv_scan3d.py [dir]   -> hash, number of 3D sampled images, number of 2D sampled images, size"""
import struct, sys, os, glob
d = sys.argv[1] if len(sys.argv) > 1 else r'D:\AI\Active\Metroid-Prime\work\shader_cache\spirv'
out = []
for f in glob.glob(os.path.join(d, '*.spv')):
    b = open(f, 'rb').read()
    if len(b) < 20: continue
    w = struct.unpack('<%dI' % (len(b) // 4), b[:len(b) // 4 * 4])
    i = 5; frag = False; n3 = n2 = 0
    while i < len(w):
        op = w[i] & 0xffff; n = w[i] >> 16
        if n == 0: break
        if op == 15 and w[i + 1] == 4: frag = True        # OpEntryPoint Fragment
        if op == 25 and w[i + 3] == 2 and w[i + 7] == 1: n3 += 1   # OpTypeImage Dim=3D sampled=1
        if op == 25 and w[i + 3] == 1 and w[i + 7] == 1: n2 += 1
        i += n
    if frag and n3: out.append((os.path.basename(f)[:-4], n3, n2, len(b)))
for r in sorted(out): print(*r)
print(len(out), 'files')
