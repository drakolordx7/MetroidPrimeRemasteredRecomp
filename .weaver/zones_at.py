r"""zones_at.py TRACE T_SECONDS [--len 1.0] [--min-ms 0.5] -- zone totals per thread in the window [T, T+len] (seconds after the first frame).
Shows where a long frame spent its time: per (thread, zone) count, total and max ms (clipped to the window)."""
import argparse, collections, sys
sys.path.insert(0, r'D:\AI\Active\Metroid-Prime\runtime\scripts\prof')
import ftrace_report as fr
ap = argparse.ArgumentParser(); ap.add_argument('trace'); ap.add_argument('t', type=float); ap.add_argument('--len', type=float, default=1.0); ap.add_argument('--min-ms', type=float, default=0.5)
a = ap.parse_args()
z, th, ev = fr.load(a.trace)
fs = sorted(e[0] for e in ev if z[e[3]] == 'frame')
t0 = fs[0] + int(a.t * 1e9); t1 = t0 + int(a.len * 1e9)
agg = collections.defaultdict(lambda: [0, 0, 0])
for t, d, tid, zz, arg in ev:
    if t + d < t0 or t > t1: continue
    n = fr.zname(z, zz, arg)
    if n.startswith('lat.'): continue
    c = min(t + d, t1) - max(t, t0)
    k = (th[tid][1], n); v = agg[k]; v[0] += 1; v[1] += c; v[2] = max(v[2], c)
for k, v in sorted(agg.items(), key=lambda kv: -kv[1][1]):
    if v[1] / 1e6 >= a.min_ms: print('%-14s %-52s n=%-5d total %9.1f ms  max %8.1f ms' % (k[0], k[1][:52], v[0], v[1] / 1e6, v[2] / 1e6))
