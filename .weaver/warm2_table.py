"""warm2_table.py -- S24: median [min-max] over the runs of each matrix condition (work/prof/mx_<cond><round>): frame rate, p99, intervals over 2x median / 50 ms,
render-thread pipeline creation (count, total ms, worst ms), frames over 50 ms that are mostly pipeline work, worker time, input to present p95."""
import glob, json, os, re, statistics, subprocess, sys
P = r'D:\AI\Active\Metroid-Prime\work\prof'
args = sys.argv[1:]
prefix = 'mx'
if args[:1] == ['--prefix']: prefix = args[1]; args = args[2:]
conds = args or ['A', 'B', 'C', 'D']
def rows(tag):
    out = {}
    s = open(os.path.join(P, tag + '.sum.txt')).read().split('\n')
    w = open(os.path.join(P, tag + '.warm.txt')).read().split('\n')
    a = [l for l in s if l.startswith(tag)]
    b = [l for l in w if l.startswith(tag)]
    if not a or not b: return None
    x = a[0].split(); y = b[0].split()
    # sum: run fps p50 p99 max | >2x >50 >100 | in>pres in>gpu
    out['fps'] = float(x[1]); out['p99'] = float(x[3]); out['max'] = float(x[4]); out['2x'] = int(x[6]); out['50'] = int(x[7]); out['100'] = int(x[8])
    ip = x[10].split('/'); out['in95'] = float(ip[1])
    # warm: run pipes tot max | >16 >50 >100 | fr>50 fr>50pp | wkr wkr_ms
    out['pipes'] = int(y[1]); out['pms'] = float(y[2]); out['pmax'] = float(y[3]); out['p16'] = int(y[5]); out['fr50'] = int(y[9]); out['fr50pp'] = int(y[10]); out['wms'] = float(y[13])
    return out
def med(v): return '%.1f [%.1f-%.1f]' % (statistics.median(v), min(v), max(v))
keys = [('fps', 'fps'), ('p99', 'p99 ms'), ('2x', 'intervals >2x'), ('50', 'intervals >50 ms'), ('in95', 'input>present p95'), ('pms', 'pipeline ms on render thread'), ('pmax', 'worst pipeline zone ms'),
        ('fr50pp', 'frames >50 ms mostly pipeline'), ('wms', 'worker ms')]
print('%-34s' % '', *['%-22s' % c for c in conds])
data = {c: [r for r in (rows(os.path.basename(f)[:-8]) for f in sorted(glob.glob(os.path.join(P, prefix + '_%s[0-9]*.sum.txt' % c)))) if r] for c in conds}
print('%-34s' % 'runs', *['%-22d' % len(data[c]) for c in conds])
for k, label in keys:
    print('%-34s' % label, *['%-22s' % (med([r[k] for r in data[c]]) if data[c] else '-') for c in conds])
