#!/usr/bin/env python
"""S20 experiment: one sweep (chunks of 3 areas) of the stab exe while normal-priority spinners sit on the processors of its console cores.
  stab_hog_run.py TAG [--hogs 6] [--mask HEX] [--env K=V ...] [--areas REGEX] [--exe PATH] [--no-hogs] [--after-ready] [--stall 240]
Starts sweep.py (own out folder work/exp_TAG), starts the spinners (.weaver/hogs.py) on --mask or, without it, on the mask the game logs
('console cores ... (mask XXXX)'); --after-ready waits for the boot to reach the Frigate first. Waits for the sweep, stops the spinners and
prints one line: statuses and load seconds per area and the longest frame. Pin the game to the same cores with NXRT_SCHED_HOST_CPUS=<mask>."""
import argparse
import glob
import json
import os
import re
import subprocess
import sys
import time

ROOT = r'D:\AI\Active\Metroid-Prime'
SEP = chr(92)
ap = argparse.ArgumentParser()
ap.add_argument('tag')
ap.add_argument('--hogs', type=int, default=6)
ap.add_argument('--no-hogs', action='store_true')
ap.add_argument('--after-ready', action='store_true')
ap.add_argument('--mask', default='')
ap.add_argument('--env', nargs='*', default=[])
ap.add_argument('--exe', default=ROOT + r'\game-build-stab\build\stab\mpr.exe')
ap.add_argument('--areas', default=r'^(magmoor_fiery_shores|magmoor_geothermal_core|magmoor_lake_tunnel|phendrana_chapel_of_the_elders|phendrana_chapel_tunnel|phendrana_canyon_entryway)$')
ap.add_argument('--stall', type=int, default=240)
ap.add_argument('--boot-stall', type=int, default=300)
a = ap.parse_args()
out = ROOT + r'\work\exp_' + a.tag
env = dict(os.environ, MPR_ROOT=ROOT, NXRT_NVN_SHADER_CACHE=ROOT + r'\work\shader_cache\spirv')
for kv in a.env:
    k, v = kv.split('=', 1)
    env[k] = v
cmd = [ROOT + r'\tools\.venv\Scripts\python.exe', ROOT + r'\tools-wt\stab\test\sweep.py', '--exe', a.exe, '--out', out, '--md', out + r'\SWEEP.md',
       '--cache', ROOT + r'\work\sweep_cache_stab\bc7', '--areas', a.areas, '--jobs', '1', '--chunk', '3', '--no-confirm',
       '--area-stall', str(a.stall), '--boot-stall', str(a.boot_stall)]
t0 = time.time()
p = subprocess.Popen(cmd, env=env, stdout=open(ROOT + r'\work\exp_%s.log' % a.tag, 'w'), stderr=subprocess.STDOUT)


def logs():
    return glob.glob(out + SEP + 'runs' + SEP + 'run*' + SEP + 'mpr.log')


def read(path, n=None):
    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            return f.read(n) if n else f.read()
    except OSError:
        return ''


def start_hogs(mask):
    h = subprocess.Popen([sys.executable, '-I', ROOT + r'\.weaver\hogs.py', mask, str(a.hogs), '3000'], stdout=subprocess.DEVNULL)
    print('hogs on mask', mask, flush=True)
    return h


hogs = None
while p.poll() is None:
    if hogs is None and not a.no_hogs:
        ready = (not a.after_ready) or any('SWEEP boot ready' in read(l) for l in logs())
        if ready and a.mask:
            hogs = start_hogs(a.mask)
        elif ready:
            for log in logs():
                m = re.search(r'console cores.*\(mask ([0-9a-f]+)\)', read(log, 20000))
                if m:
                    hogs = start_hogs(m.group(1))
                    break
    time.sleep(5)
if hogs:
    subprocess.run(['taskkill', '/F', '/T', '/PID', str(hogs.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    d = json.load(open(out + r'\results.json'))['areas']
    line = ' '.join('%s=%s/%s' % (k.split('_', 1)[1], v['status'], v.get('load_s')) for k, v in d.items())
except Exception as e:
    line = 'no results (%s)' % e
mx = 0.0
for tr in glob.glob(out + SEP + 'runs' + SEP + 'run*' + SEP + 'trace.jsonl'):
    for l in read(tr).splitlines():
        m = re.search(r'"ms":([\d.]+)', l)
        if m:
            mx = max(mx, float(m.group(1)))
print('%s hogs=%s env=%s wall %.0f s | %s | longest frame %.0f ms' % (a.tag, 0 if a.no_hogs else a.hogs, ' '.join(a.env), time.time() - t0, line, mx))
