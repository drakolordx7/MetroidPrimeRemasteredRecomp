r"""st_summary.py TAG[=label] ... [--skip 20] [--seconds 140] -- one table row per run (work/prof/TAG.trace): frame time p50/p99/max, hitch counts (over 2x the
median, over 50 ms, over 100 ms) over all frames of the window, and input-to-present / input-to-GPU-done p50 / p95 over the frames the player controls."""
import argparse, os, sys
sys.path.insert(0, r'D:\AI\Active\Metroid-Prime\.weaver')
import lat_report as lr
ap = argparse.ArgumentParser(); ap.add_argument('tags', nargs='+'); ap.add_argument('--skip', type=float, default=20); ap.add_argument('--seconds', type=float, default=140)
a = ap.parse_args()
print('%-16s %6s %6s %6s %7s | %5s %5s %5s | %-11s %-11s' % ('run', 'fps', 'p50', 'p99', 'max', '>2x', '>50', '>100', 'in>pres', 'in>gpu'))
for t in a.tags:
    tag, _, label = t.partition('=')
    p = os.path.join(r'D:\AI\Active\Metroid-Prime\work\prof', tag + '.trace')
    r = lr.analyse(p, a.skip, a.seconds)
    if not r.get('frames'): print(label or tag, 'no frames'); continue
    import ftrace_report as fr
    z, th, ev = fr.load(p)
    fs = sorted(e[0] for e in ev if z[e[3]] == 'frame'); t0 = fs[0] + int(a.skip * 1e9); t1 = t0 + int(a.seconds * 1e9)
    fw = [x for x in fs if t0 <= x <= t1]; iv = [(fw[i] - fw[i - 1]) / 1e6 for i in range(1, len(fw))]
    h100 = sum(1 for d in iv if d > 100)
    print('%-16s %6.1f %6.2f %6.2f %7.1f | %5d %5d %5d | %4.1f/%-6.1f %4.1f/%-6.1f' % (label or tag, r['fps'], r['ft_p50'], r['ft_p99'], r['ft_max'], r['stalls_2x'], r['stalls_50'], h100,
          r['ctrl_in2present_p50'], r['ctrl_in2present_p95'], r['ctrl_in2gpu_p50'], r['ctrl_in2gpu_p95']))
