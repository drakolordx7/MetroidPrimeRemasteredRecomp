r"""stall_attr.py TRACE [--skip 20] [--seconds 140] [--factor 2.0] [--min-ms 0] -- attribute frame intervals longer than factor x median to the zones that overlap them.
For each stall the longest overlapping zone (>= 1 ms) that is not a pure wait names the cause; waits (svc Wait*/Sleep*, limiter, present.call, hle:nvnQueuePresentTexture, ...) are skipped.
Prints the cause table (count, total stall ms) and the worst stalls with their zone list."""
import argparse, collections, sys
sys.path.insert(0, r'D:\AI\Active\Metroid-Prime\runtime\scripts\prof')
import ftrace_report as fr

WAITS = ('limiter', 'present.call', 'present', 'frame', 'main.update', 'lat.', 'hle:nvnQueuePresentTexture', 'hle:nvnQueueSubmitCommands', 'svc')
SVC_WAIT = {'WaitSynchronization', 'SleepThread', 'WaitProcessWideKeyAtomic', 'WaitForAddress', 'ArbitrateLock', 'ReplyAndReceive', 'WaitForAddressTimeout'}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('trace'); ap.add_argument('--skip', type=float, default=20); ap.add_argument('--seconds', type=float, default=140)
    ap.add_argument('--factor', type=float, default=2.0); ap.add_argument('--min-ms', type=float, default=0); ap.add_argument('--top', type=int, default=8)
    a = ap.parse_args()
    z, th, ev = fr.load(a.trace)
    name = lambda e: fr.zname(z, e[3], e[4])
    fs = sorted(e[0] for e in ev if z[e[3]] == 'frame')
    t0 = fs[0] + int(a.skip * 1e9); t1 = t0 + int(a.seconds * 1e9)
    fw = [t for t in fs if t0 <= t <= t1]
    iv = [(fw[i - 1], fw[i]) for i in range(1, len(fw))]
    med = sorted(b - a_ for a_, b in iv)[len(iv) // 2] / 1e6
    thr = max(a.factor * med, a.min_ms)
    stalls = [(a_, b) for a_, b in iv if (b - a_) / 1e6 > thr]
    evs = sorted(ev)
    cause = collections.Counter(); cause_ms = collections.Counter(); rows = []
    for a_, b in stalls:
        best = None; zs = collections.Counter()
        for t, d, tid, zz, arg in evs:
            if t > b: break
            if t + d < a_ or d < 1e6: continue
            n = fr.zname(z, zz, arg)
            if n.startswith(WAITS[:-1]) and not n.startswith('svc'): continue
            if n.startswith('svc:') and n[4:] in SVC_WAIT: continue
            if n == 'svc': continue
            if n.startswith('hle:') and n[4:] in ('nvnSyncWait',): n = 'sync.wait(hle)'
            zs[(th[tid][1], n)] += min(t + d, b) - max(t, a_)
            if best is None or zs[(th[tid][1], n)] > zs[best]: best = (th[tid][1], n)
        c = '%s/%s' % best if best else 'none (waits only)'
        cause[c] += 1; cause_ms[c] += (b - a_) / 1e6
        rows.append(((b - a_) / 1e6, (a_ - fs[0]) / 1e9, c, zs.most_common(3)))
    print('window %.0f..%.0f s after first frame: %d frame intervals, median %.2f ms, threshold %.1f ms, %d stalls (%.2f%%)' % (a.skip, a.skip + a.seconds, len(iv), med, thr, len(stalls), 100.0 * len(stalls) / max(1, len(iv))))
    for c, n in cause.most_common(): print('  %-44s %4d stalls %9.1f ms' % (c, n, cause_ms[c]))
    for ms, at, c, zl in sorted(rows, reverse=True)[:a.top]:
        print('  worst %.1f ms at %.1fs: %s | %s' % (ms, at, c, '; '.join('%s/%s %.1f' % (k[0], k[1], v / 1e6) for k, v in zl)))

main()
