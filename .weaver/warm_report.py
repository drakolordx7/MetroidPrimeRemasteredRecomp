r"""warm_report.py TAG[=label] ... [--skip 20] [--seconds 140] -- S24: pipeline creation on the render thread per run (work/prof/TAG.trace).
One row per run: render-thread pipe.* zones (count, total ms, worst), how many are over 16 / 50 / 100 ms, and how many frame intervals over 50 ms
are mostly pipeline work (the pipe.* zones cover more than half of the interval). Also worker-thread build totals (prewarm.build, lib.build)."""
import argparse, collections, os, sys
sys.path.insert(0, r'D:\AI\Active\Metroid-Prime\runtime\scripts\prof')
import ftrace_report as fr

ap = argparse.ArgumentParser(); ap.add_argument('tags', nargs='+'); ap.add_argument('--skip', type=float, default=20); ap.add_argument('--seconds', type=float, default=140)
ap.add_argument('--list', type=int, default=0, help='print the N worst render-thread pipe zones')
a = ap.parse_args()
print('%-14s %5s %7s %7s | %4s %4s %4s | %5s %7s | %5s %8s' % ('run', 'pipes', 'tot ms', 'max ms', '>16', '>50', '>100', 'fr>50', 'fr>50pp', 'wkr', 'wkr ms'))
for t in a.tags:
    tag, _, label = t.partition('=')
    p = os.path.join(r'D:\AI\Active\Metroid-Prime\work\prof', tag + '.trace')
    z, th, ev = fr.load(p)
    fs = sorted(e[0] for e in ev if z[e[3]] == 'frame')
    if not fs: print(label or tag, 'no frames'); continue
    t0 = fs[0] + int(a.skip * 1e9); t1 = t0 + int(a.seconds * 1e9)
    name = lambda e: fr.zname(z, e[3], e[4])
    # the render thread: the thread that records the frame zones
    ftid = collections.Counter(e[2] for e in ev if z[e[3]] == 'frame').most_common(1)[0][0]
    pz = [(e[0], e[1] / 1e6) for e in ev if e[2] == ftid and name(e) in ('pipe.create', 'pipe.link') and t0 <= e[0] <= t1]
    wk = [e[1] / 1e6 for e in ev if e[2] != ftid and name(e) in ('prewarm.build', 'lib.build') and t0 <= e[0] <= t1]
    fw = [x for x in fs if t0 <= x <= t1]
    iv = [(fw[i - 1], fw[i]) for i in range(1, len(fw))]
    n50 = npp = 0
    for a_, b in iv:
        if (b - a_) / 1e6 <= 50: continue
        n50 += 1
        cov = sum(max(0, min(s + d * 1e6, b) - max(s, a_)) for s, d in pz)
        if cov > 0.5 * (b - a_): npp += 1
    ds = [d for _, d in pz]
    print('%-14s %5d %7.0f %7.1f | %4d %4d %4d | %5d %7d | %5d %8.0f' % (label or tag, len(ds), sum(ds), max(ds) if ds else 0, sum(d > 16 for d in ds), sum(d > 50 for d in ds), sum(d > 100 for d in ds), n50, npp, len(wk), sum(wk)))
    if a.list:
        for s, d in sorted(pz, key=lambda x: -x[1])[:a.list]: print('    %.1f ms at %.1f s' % (d, (s - fs[0]) / 1e9))
