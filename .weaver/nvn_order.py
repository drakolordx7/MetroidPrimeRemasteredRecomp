"""nvn_order.py [mpr.log] [--n 60] [--skip RE]: first-seen order and counts of the hle-trace lines (run with NXRT_HLE_TRACE=nvn); with
--seq prints the first N calls in call order instead (name + args)."""
import re, sys, collections
a = sys.argv[1:]
log = 'work/run/mpr.log'
n = 60
skip = r'GetProcAddress|BootstrapLoader'
seq = False
i = 0
while i < len(a):
    if a[i] == '--n': n = int(a[i+1]); i += 2
    elif a[i] == '--skip': skip = a[i+1]; i += 2
    elif a[i] == '--seq': seq = True; i += 1
    else: log = a[i]; i += 1
order, cnt, calls = [], collections.Counter(), []
for l in open(log, errors='replace'):
    m = re.search(r'hle-trace: #(\d+) (\w+)\((.*?)\) lr=(0x[0-9a-f]+)(?: -> (0x[0-9a-f]+))?', l)
    if not m: continue
    nm = m.group(2)
    if re.search(skip, nm): continue
    if nm not in cnt: order.append(nm)
    cnt[nm] += 1
    calls.append((m.group(1), nm, m.group(3), m.group(4), m.group(5)))
print('%d traced calls, %d distinct functions' % (len(calls), len(order)))
if seq:
    for c in calls[:n]: print('#%s %s(%s) lr=%s -> %s' % c)
else:
    for k, nm in enumerate(order[:n]): print('%3d %-48s x%d' % (k + 1, nm, cnt[nm]))
