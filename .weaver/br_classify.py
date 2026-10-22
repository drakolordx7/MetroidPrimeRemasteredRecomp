"""Classify the unresolved `br xN` of a module by how xN was produced.  python .weaver/br_classify.py <nso> <name> <base> [N examples]"""
import sys, collections, bisect, re
sys.path.insert(0, '.')
from nxrecomp import program, jumptables
from nxrecomp.jumptables import _Fn, _find_def, _ops, _regno
import capstone
from nxrecomp.config import load_game
path, name, base = sys.argv[1], sys.argv[2], int(sys.argv[3], 16)
nex = int(sys.argv[4]) if len(sys.argv) > 4 else 3
spec = {'kind': 'nso', 'path': path, 'base': base, 'name': name, 'game': 'mpr', 'patches': None, 'sites': None, 'index': 0}
img = program.open_image(spec); env = program.Env(img, load_game('mpr')); env.compute_starts(); env.load_eh(); jumptables.resolve(env)
cs = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)
words = img.words(); ts = env.text_lo
cls = collections.Counter(); ex = collections.defaultdict(list)
for i, w in enumerate(words):
    if (w & 0xfffffc1f) != 0xd61f0000: continue
    b = ts + 4 * i
    if b in env.jt: continue
    s = env.starts[bisect.bisect_right(env.starts, b) - 1]
    if env.plt_symbol(s): continue
    e = env.extent(s)
    insns = {}
    for a in range(s, e, 4):
        l = list(cs.disasm(img.mem[a - img.base:a - img.base + 4], a))
        if l: insns[a] = (l[0].mnemonic, l[0].op_str)
    f = _Fn(s, e, insns)
    if b not in insns: cls['OUTSIDE-extent'] += 1; continue
    reg = _regno(insns[b][1])
    d = _find_def(f, b, reg)
    if not d: k = 'no-def-in-fn(param/reg)'
    else:
        a, mn, ops = d
        if mn.startswith('ldr') and len(ops) > 1:
            m = ops[1]
            k = 'ldr[%s]' % ('idx' if re.search(r'\[\w+, [xw]\d+', m) else 'imm/base')
            k += '-lit' if mn=='ldr' and not '[' in m else ''
        elif mn == 'add': k = 'add(table-like, unmatched)'
        else: k = mn
    cls[k] += 1
    if len(ex[k]) < nex: ex[k].append((b, s, [insns.get(b - 4 * j, ('', ''))[0] + ' ' + insns.get(b - 4 * j, ('', ''))[1] for j in range(6, -1, -1)]))
for k, n in cls.most_common():
    print(n, k)
    for b, s, lines in ex[k]:
        print('   br@%x in f_%x:' % (b, s)); [print('       ' + l) for l in lines]

# ---- second pass: ldr[idx] whose base is a static (adrp/adr-derived) table
from nxrecomp.jumptables import _const
static = 0
for i, w in enumerate(words):
    if (w & 0xfffffc1f) != 0xd61f0000: continue
    b = ts + 4 * i
    if b in env.jt: continue
    s = env.starts[bisect.bisect_right(env.starts, b) - 1]
    if env.plt_symbol(s): continue
    e = env.extent(s)
    if not (s <= b < e): continue
    insns = {}
    for a in range(s, e, 4):
        l = list(cs.disasm(img.mem[a - img.base:a - img.base + 4], a))
        if l: insns[a] = (l[0].mnemonic, l[0].op_str)
    f = _Fn(s, e, insns)
    d = _find_def(f, b, _regno(insns[b][1]))
    if d and d[1].startswith('ldr'):
        m = re.match(r'\[(\w+), ([xw]\d+)', d[2][1]) if len(d[2]) > 1 else None
        if m:
            c = _const(f, d[0], _regno(m.group(1)))
            if c is not None:
                static += 1; print('STATIC-table br@%x f_%x base=%x' % (b, s, c))
print('ldr[idx] with a static base:', static)
