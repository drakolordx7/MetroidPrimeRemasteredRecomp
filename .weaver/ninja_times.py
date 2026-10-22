"""Per-module compile statistics from a build dir's .ninja_log.   python .weaver/ninja_times.py <build dir>"""
import collections, sys, re
rows = []
for l in open(sys.argv[1] + '/.ninja_log'):
    if l.startswith('#'): continue
    s, e, _, out, _ = l.rstrip('\n').split('\t')
    rows.append((int(e) - int(s), out, int(s), int(e)))
cc = [r for r in rows if r[1].endswith('.obj')]
by = collections.defaultdict(list)
for d, o, s, e in cc:
    m = re.search(r'lift[\/]([a-z0-9]+)[\/]', o)
    by[m.group(1) if m else 'other'].append(d)
for m, v in by.items(): print('%-8s %3d units  cpu-sum %5.0fs  avg %5.1fs  max %5.1fs' % (m, len(v), sum(v) / 1e3, sum(v) / len(v) / 1e3, max(v) / 1e3))
for d, o, s, e in sorted(cc, reverse=True)[:3]: print('  slowest: %.1fs %s' % (d / 1e3, o[-40:]))
print('lift steps: ' + ', '.join('%.0fs' % (d / 1e3) for d, o, s, e in rows if not o.endswith(('.obj', '.lib')) and 'c_000' in o))
print('wall span %.0fs' % ((max(r[3] for r in rows) - min(r[2] for r in rows)) / 1e3))
