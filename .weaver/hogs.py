#!/usr/bin/env python
"""Busy-loop processes at normal priority pinned to a processor mask, to recreate a loaded machine for the processors a game's console cores use.
  hogs.py MASK_HEX COUNT SECONDS     e.g. hogs.py 15000 6 900  (6 spinners on processors 12,14,16 for 15 minutes; they end by themselves)
The game's own mask is in its log: 'sched: console cores: slot N ... (mask XXXX)'. Kill: taskkill /F /FI "WINDOWTITLE eq nothing" is not needed, they exit at the deadline."""
import ctypes, subprocess, sys, time
if len(sys.argv) >= 2 and sys.argv[1] == '--child':
    mask, until = int(sys.argv[2], 16), time.time() + float(sys.argv[3])
    k = ctypes.windll.kernel32
    k.GetCurrentProcess.restype = ctypes.c_void_p
    k.SetProcessAffinityMask.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    if not k.SetProcessAffinityMask(k.GetCurrentProcess(), mask):
        sys.exit(3)
    x = 0
    while time.time() < until:
        for _ in range(200000): x += 1
    sys.exit(0)
mask, count, secs = sys.argv[1], int(sys.argv[2]), sys.argv[3]
ps = [subprocess.Popen([sys.executable, '-I', __file__, '--child', mask, secs]) for _ in range(count)]
print('started', [p.pid for p in ps], flush=True)
for p in ps: p.wait()
