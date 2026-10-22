"""Latency A/B in one run (so other load on the machine hits both states alike): python -I .weaver/lat_ab.py LABEL [--seconds 120] [--toggle 8] [--from 40] [--env K=V ...]
Runs the extras build in window mode with [latency] mode on and ab_toggle_s, which flips the low-latency mode every N seconds, then compares the once-per-second log
lines of the two states (skipping the first 3 s after each flip)."""
import argparse, os, re, statistics, subprocess
ap = argparse.ArgumentParser()
ap.add_argument('label'); ap.add_argument('--seconds', type=int, default=120); ap.add_argument('--toggle', type=float, default=8); ap.add_argument('--from', dest='t0', type=float, default=40)
ap.add_argument('--env', action='append', default=[])
a = ap.parse_args()
root = r'D:\AI\Active\Metroid-Prime'
cmd = ['C:/Program Files/Git/usr/bin/bash.exe', '.weaver/boot_extras.sh', '--no-build', '--seconds', str(a.seconds), '--env', 'NXRT_BOOT_GFX=window', '--env', 'NXRT_LATENCY_LOG_TIMINGS=1',
       '--env', 'NXRT_LATENCY_MODE=on', '--env', 'NXRT_LATENCY_AB_TOGGLE_S=%g' % a.toggle, '--env', 'NXRT_HDR_MODE=off', '--env', 'NXRT_GFX_LOG_FPS=1',
       '--env', 'NXRT_BOOT_PRESS=A@12,A@22,A@30,A@38,A@46,A@54,A@62,A@70,A@80']
for e in a.env: cmd += ['--env', e]
subprocess.run(cmd, cwd=root, env=dict(os.environ, MSYS2_ARG_CONV_EXCL='*'), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
st = {'on': [], 'off': []}
fps = []
for l in open(root + r'\work\run_extras\mpr.log', errors='replace'):
    m = re.match(r'\[\s*([\d.]+) I .*lowlat: .*?state (on|off) since ([\d.]+) s: input->present ([\d.]+) ms, sleep ([\d.]+) ms, input->gpu end ([\d.]+) ms, sim->present ([\d.]+) ms', l)
    if m and float(m.group(1)) >= a.t0 and float(m.group(3)) >= 3:
        st[m.group(2)].append(tuple(float(m.group(i)) for i in (4, 5, 6, 7)))
    m = re.match(r'\[\s*([\d.]+) I .*gfx: fps ([\d.]+)', l)
    if m and float(m.group(1)) >= a.t0: fps.append(float(m.group(2)))
print('%s (toggle %.0f s, from %.0f s; fps median %.1f)' % (a.label, a.toggle, a.t0, statistics.median(fps) if fps else 0))
for k in ('off', 'on'):
    v = st[k]
    if not v: print('  %-3s no samples' % k); continue
    print('  %-3s n=%-3d input->present median %.2f mean %.2f ms | sleep %.2f | input->gpu end (Reflex) %.2f | sim->present (Reflex) %.2f' % (
        k, len(v), statistics.median(x[0] for x in v), statistics.mean(x[0] for x in v), statistics.mean(x[1] for x in v), statistics.mean(x[2] for x in v), statistics.mean(x[3] for x in v)))
