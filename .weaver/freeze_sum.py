#!/usr/bin/env python
"""Summarise a watchdog freeze report: per thread the kernel call it sits in and the guest call stack. freeze_sum.py stderr.txt|mpr.log [--all]"""
import re, sys
path = sys.argv[1]
lines = open(path, encoding='utf-8', errors='replace').read().splitlines()
# take the last report (header 'FREEZE')
idx = [i for i, l in enumerate(lines) if 'watchdog: FREEZE' in l]
start = idx[-1] if idx else 0
cur = None
threads = []
for l in lines[start:]:
    m = re.search(r'watchdog: (FREEZE.*)', l)
    if m and not cur: print(m.group(1))
    m = re.search(r'watchdog: thread (\S+) tid=\d+ guest_tid=(\d+)', l)
    if m:
        cur = {'name': m.group(1), 'gid': m.group(2), 'host': [], 'guest': ''}
        threads.append(cur); continue
    if cur is None: continue
    m = re.search(r'guest call stack: (.*)', l)
    if m: cur['guest'] = m.group(1); continue
    m = re.search(r'watchdog:\s+#\d+ (.*)', l)
    if m and 'mpr.exe' in m.group(1) and '(' in m.group(1):
        cur['host'].append(re.sub(r'^mpr.exe\+0x[0-9a-f]+ \(', '', m.group(1))[:90])
    m = re.search(r'sync|WaitForAddress|process-wide|mutex hand', l)
for t in threads:
    k = [h for h in t['host'] if 'nxrt::' in h][:2]
    print(f"{t['name']:12} g{t['gid']:>3} | {' / '.join(k) or '-'}")
    print(f"      guest: {t['guest'][:200]}")
for l in lines[start:]:
    if 'kernel sync' in l or ('  WaitForAddress' in l or 'process-wide key' in l or 'mutex hand-over' in l or 'WaitSynchronization waiters' in l):
        print(l[:200])
