"""Summarise Vulkan validation messages and device loss in an mpr.log: python vsum.py mpr.log"""
import re, sys, collections
L = open(sys.argv[1], errors='replace').read().splitlines()
vk = [l for l in L if ' vulkan: ' in l]
c = collections.Counter()
first = {}
for l in vk:
    m = re.search(r'vulkan: ((?:VUID|UNASSIGNED|Undefined-Value|WARNING|Validation)[\w-]*)', l)
    k = m.group(1) if m else 'other'
    c[k] += 1
    first.setdefault(k, l[:330])
print('validation messages (logged, each VUID is capped at 10 by the layer):', sum(c.values()))
for k, n in c.most_common():
    print('  %3d %s' % (n, k)); print('      ' + first[k][first[k].find('vulkan:'):][:300])
lost = [l for l in L if 'DEVICE_LOST' in l or 'failed (-4)' in l]
print('device lost lines:', len(lost), lost[0][:120] if lost else '')
for l in L[-3:]: print(l[:200])
