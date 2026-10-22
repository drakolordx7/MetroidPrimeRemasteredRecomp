"""Per-thread guest call stacks of a freeze report in an mpr log, names resolved: python .weaver/freezesum.py <mpr.log> [depth]"""
import sys, re
sys.path.insert(0, 'tools/boot')
import addrname
depth = int(sys.argv[2]) if len(sys.argv) > 2 else 9
sample = 0
for l in open(sys.argv[1], errors='replace'):
    m = re.search(r'watchdog: (FREEZE.*)', l)
    if m: print('==', m.group(1)); continue
    m = re.search(r'watchdog: thread (\S+) tid=\d+ guest_tid=(\d+)', l)
    if m: print('thread', m.group(1), 'guest', m.group(2)); continue
    m = re.search(r'guest call stack: (.*)', l)
    if m:
        fr = m.group(1).split(' <- ')[:depth]
        print('   ' + ' <- '.join(re.sub(r'<(.*?)(\(.*)?\+0x0>', r'\1', addrname.annotate(f)) for f in fr))
