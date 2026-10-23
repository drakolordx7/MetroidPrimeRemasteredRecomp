"""Noise blocks per area for a sweep output folder: python .weaver/n4noise.py work/n4/<out> [--all]
Reads every <area>_b.png (and _a.png) under <out>/runs/*/shots, prints area, blocks (b, a) sorted worst first; with no --all only areas with >0."""
import sys, glob, os, collections
sys.path.insert(0, os.path.dirname(__file__))
from noisescore import noise_score
out = sys.argv[1]; show_all = '--all' in sys.argv
res = collections.defaultdict(dict)
for p in glob.glob(os.path.join(out, 'runs', '*', 'shots', '*_[ab].png')):
    n = os.path.basename(p)[:-4]
    res[n[:-2]][n[-1]] = noise_score(p)[1]
rows = sorted(res.items(), key=lambda kv: -max(kv[1].values()))
tot = sum(1 for _, v in rows if max(v.values()) >= 3)
for a, v in rows:
    if show_all or max(v.values()) > 0:
        print(f"{a:50s} b={v.get('b','-'):>5} a={v.get('a','-'):>5}")
print(f"areas {len(rows)}, with >=3 noise blocks (sweep flag): {tot}")
