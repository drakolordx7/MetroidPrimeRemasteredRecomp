#!/usr/bin/env python
"""Load time per warp split into BC7 transcode time on the render thread and the rest: load_attr.py RUNS_DIR [more dirs]. Reads every runNNN/mpr.log:
from 'SWEEP begin X' to 'SWEEP arrived X', sums the 'ASTC -> BC7 ... N ms' lines (render thread, cold bc7 cache) and counts cache hits."""
import re, sys, glob, os
B = re.compile(r'^\[\s*([\d.]+) \w \S+ [^\]]*\] script: SWEEP (begin|arrived) (\S+)')
T = re.compile(r'^\[\s*([\d.]+) .*ASTC -> (?:BC7|RGBA8).*: ([\d.]+) ms')
H = re.compile(r'BC7 data from cache')
rows = []
for d in sys.argv[1:]:
    for log in sorted(glob.glob(os.path.join(d, 'run*', 'mpr.log'))):
        begin = {}; cur = None; enc = 0.0; n_enc = 0; hits = 0
        for ln in open(log, encoding='utf-8', errors='replace'):
            m = B.match(ln)
            if m:
                t, what, key = float(m.group(1)), m.group(2), m.group(3)
                if what == 'begin': cur = key; begin[key] = t; enc = 0.0; n_enc = 0; hits = 0
                elif key == cur:
                    rows.append((key, t - begin[key], enc / 1000, n_enc, hits, os.path.basename(os.path.dirname(log)))); cur = None
                continue
            if cur:
                m = T.match(ln)
                if m: enc += float(m.group(2)); n_enc += 1
                elif H.search(ln): hits += 1
print(f"{'area':45} {'load s':>7} {'encode s':>8} {'#enc':>5} {'#cache':>6}  run")
tot = [0, 0]
for r in sorted(rows, key=lambda r: -r[1]):
    print(f"{r[0]:45} {r[1]:7.1f} {r[2]:8.1f} {r[3]:5d} {r[4]:6d}  {r[5]}")
    tot[0] += r[1]; tot[1] += r[2]
print(f"{len(rows)} areas, load {tot[0]:.0f} s, of which render-thread encode {tot[1]:.0f} s")
