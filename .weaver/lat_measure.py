"""Latency proxy measurement of the extras build: python -I .weaver/lat_measure.py LABEL [--seconds 150] [--from 110] [--env K=V ...]
Runs mpr.exe (window mode, 1920x1080 window, internal 3840x2160) through .weaver/boot_extras.sh with [latency] log_timings on, then averages the
once-per-second log lines ('input->present', 'input->gpu end', 'sleep') over the window from --from to the end and reports presents per second."""
import argparse, re, subprocess, sys, os, statistics
ap = argparse.ArgumentParser()
ap.add_argument('label'); ap.add_argument('--seconds', type=int, default=150); ap.add_argument('--from', dest='t0', type=float, default=110)
ap.add_argument('--env', action='append', default=[])
a = ap.parse_args()
root = r'D:\AI\Active\Metroid-Prime'
env = dict(os.environ, MSYS2_ARG_CONV_EXCL='*')
cmd = ['C:/Program Files/Git/usr/bin/bash.exe', '.weaver/boot_extras.sh', '--no-build', '--seconds', str(a.seconds), '--env', 'NXRT_BOOT_GFX=window', '--env', 'NXRT_LATENCY_LOG_TIMINGS=1',
       '--env', 'NXRT_BOOT_PRESS=A@12,A@22,A@30,A@38,A@46,A@54,A@62,A@70,A@80']
for e in a.env: cmd += ['--env', e]
subprocess.run(cmd, cwd=root, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
log = open(root + r'\work\run_extras\mpr.log', errors='replace').read().splitlines()
rows = []
for l in log:
    m = re.match(r'\[\s*([\d.]+) I .*lowlat: .*?input->present ([\d.]+) ms, sleep ([\d.]+) ms, input->gpu end ([\d.]+) ms, sim->present ([\d.]+) ms', l)
    if m: rows.append(tuple(float(x) for x in m.groups()))
w = [r for r in rows if r[0] >= a.t0]
pres = [l for l in log if 'nvn back end at the deadline' in l]
n = int(re.search(r'presents (\d+)', pres[-1]).group(1)) if pres else 0
print('%s: %d samples in window (>= %.0f s) of %d' % (a.label, len(w), a.t0, len(rows)))
if w:
    for i, name in ((1, 'input->present ms'), (2, 'sleep ms'), (3, 'input->gpu end ms (Reflex reports)'), (4, 'sim->present ms')):
        v = [r[i] for r in w]
        print('  %-36s mean %.2f  median %.2f  min %.2f  max %.2f' % (name, statistics.mean(v), statistics.median(v), min(v), max(v)))
print('  presents total', n)
