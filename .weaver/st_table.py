"""Compare groups of gameplay-run traces in one table: median [min-max] per label.

  python .weaver/st_table.py "old=f60_old1,f60_old2,f60_old3" "new=f60_new1,f60_new2,f60_new3" [--skip 20] [--seconds 140]

Each positional argument is label=tag1,tag2,... ; a tag names work\\prof\\<tag>.trace.
Metrics come from lat_report.analyse; hitches > 100 ms are counted here from the frame marks,
in the same window (skip / seconds) as lat_report.
"""
import argparse, os, statistics, sys

sys.path.insert(0, r'D:\AI\Active\Metroid-Prime\.weaver')
sys.path.insert(0, r'D:\AI\Active\Metroid-Prime\runtime\scripts\prof')
import lat_report as lr
import ftrace_report as fr

PROF = r'D:\AI\Active\Metroid-Prime\work\prof'

# (row name, key in lat_report result or 'over100' for the local count, integer metric?)
ROWS = [
    ('fps', 'fps', False),
    ('frame p50 ms', 'ft_p50', False),
    ('frame p99 ms', 'ft_p99', False),
    ('hitches >2x median', 'stalls_2x', True),
    ('hitches >50 ms', 'stalls_50', True),
    ('hitches >100 ms', 'over100', True),
    ('input to present p50 ms', 'ctrl_in2present_p50', False),
    ('input to present p95 ms', 'ctrl_in2present_p95', False),
    ('input to GPU done p50 ms', 'ctrl_in2gpu_p50', False),
    ('input to GPU done p95 ms', 'ctrl_in2gpu_p95', False),
]


def over100(path, skip, seconds):
    zones, threads, ev = fr.load(path)
    frames = sorted(e[0] for e in ev if zones.get(e[3]) == 'frame')
    if len(frames) < 2:
        return 0
    t0 = frames[0] + int(skip * 1e9)
    t1 = t0 + int(seconds * 1e9)
    w = [t for t in frames if t0 <= t <= t1]
    return sum(1 for i in range(1, len(w)) if (w[i] - w[i - 1]) / 1e6 > 100)


def parse_group(arg):
    if '=' not in arg:
        raise SystemExit('bad group %r: want label=tag1,tag2' % arg)
    label, tags = arg.split('=', 1)
    tags = [t.strip() for t in tags.split(',') if t.strip()]
    return label.strip(), tags


def run_metrics(tag, skip, seconds):
    path = os.path.join(PROF, tag + '.trace')
    if not os.path.exists(path):
        print('note: missing trace %s, run skipped' % path)
        return None
    r = lr.analyse(path, skip, seconds)
    if not r.get('frames'):
        print('note: no frames in %s, run skipped' % tag)
        return None
    r['over100'] = over100(path, skip, seconds)
    return r


def fmt(vals, is_int):
    if not vals:
        return '-'
    if is_int:
        if len(vals) == 1:
            return '%d' % vals[0]
        return '%.0f [%d-%d]' % (statistics.median(vals), min(vals), max(vals))
    if len(vals) == 1:
        return '%.1f' % vals[0]
    return '%.1f [%.1f-%.1f]' % (statistics.median(vals), min(vals), max(vals))


def main():
    ap = argparse.ArgumentParser(description='One table of median [min-max] per label over gameplay traces.')
    ap.add_argument('groups', nargs='+', help='label=tag1,tag2,...')
    ap.add_argument('--skip', type=float, default=20)
    ap.add_argument('--seconds', type=float, default=140)
    a = ap.parse_args()

    groups = [parse_group(g) for g in a.groups]
    data, listed = {}, {}
    for label, tags in groups:
        data[label] = [m for m in (run_metrics(t, a.skip, a.seconds) for t in tags) if m]
        listed[label] = len(tags)
    labels = [l for l, _ in groups]

    table = [['metric'] + labels]
    for name, key, is_int in ROWS:
        row = [name]
        for l in labels:
            row.append(fmt([r[key] for r in data[l]], is_int))
        table.append(row)

    widths = [max(len(r[c]) for r in table) for c in range(len(labels) + 1)]
    for i, r in enumerate(table):
        print('  '.join(r[c].ljust(widths[c]) if c == 0 else r[c].rjust(widths[c]) for c in range(len(r))))
        if i == 0:
            print('  '.join('-' * widths[c] for c in range(len(r))))

    print()
    print('runs per label (used / listed): ' + ', '.join('%s %d/%d' % (l, len(data[l]), listed[l]) for l in labels))


if __name__ == '__main__':
    main()
