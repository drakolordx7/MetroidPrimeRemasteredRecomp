r"""tex_cost.py TAG... [--skip 20] [--seconds 140] -- texture work on the render thread per run (work/prof/TAG.trace): total and worst single-frame time in
tex.ensure (whole first-use handling), tex.prepare (inline preparation), tex.create (image creation) and tex.prep.wait (waiting for a background job),
and how many frames spent more than 8 ms / 30 ms in tex.ensure. Frames are the intervals between 'frame' marks."""
import argparse, bisect, collections, os, sys
sys.path.insert(0, r'D:\AI\Active\Metroid-Prime\runtime\scripts\prof')
import ftrace_report as fr
ap = argparse.ArgumentParser(); ap.add_argument('tags', nargs='+'); ap.add_argument('--skip', type=float, default=20); ap.add_argument('--seconds', type=float, default=140)
a = ap.parse_args()
print('%-14s %9s %9s %9s %9s | %8s %8s | %6s %6s' % ('run', 'ensure ms', 'prepare', 'create', 'bgwait', 'worst fr', 'worst ev', '>8ms', '>30ms'))
for tag in a.tags:
    z, th, ev = fr.load(os.path.join(r'D:\AI\Active\Metroid-Prime\work\prof', tag + '.trace'))
    fs = sorted(e[0] for e in ev if z[e[3]] == 'frame'); t0 = fs[0] + int(a.skip * 1e9); t1 = t0 + int(a.seconds * 1e9)
    fw = [t for t in fs if t0 <= t <= t1]
    tot = collections.Counter(); per = collections.defaultdict(float); worst_ev = 0
    for t, d, tid, zz, arg in ev:
        n = z[zz]
        if n not in ('tex.ensure', 'tex.prepare', 'tex.create', 'tex.prep.wait') or not (t0 <= t <= t1): continue
        tot[n] += d
        if n == 'tex.ensure':
            per[bisect.bisect(fw, t)] += d; worst_ev = max(worst_ev, d)
    v = list(per.values())
    print('%-14s %9.1f %9.1f %9.1f %9.1f | %8.1f %8.1f | %6d %6d' % (tag, tot['tex.ensure'] / 1e6, tot['tex.prepare'] / 1e6, tot['tex.create'] / 1e6, tot['tex.prep.wait'] / 1e6,
          max(v) / 1e6 if v else 0, worst_ev / 1e6, sum(1 for x in v if x > 8e6), sum(1 for x in v if x > 30e6)))
