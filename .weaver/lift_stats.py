"""Discovery / jump table / LSDA / size statistics of one module, as the lifter sees it (no code generated).
python .weaver/lift_stats.py <nso> <name> <base> [--game mpr]      run with the tools .venv python from recomp/ (cwd)"""
import sys, collections, bisect
sys.path.insert(0, '.')
from nxrecomp import program, funcs, jumptables
from nxrecomp.config import load_game

path, name, base = sys.argv[1], sys.argv[2], int(sys.argv[3], 16)
game = sys.argv[5] if len(sys.argv) > 5 else 'mpr'
spec = {'kind': 'nso', 'path': path, 'base': base, 'name': name, 'game': game, 'patches': None, 'sites': None, 'index': 0}
img = program.open_image(spec)
cfg = load_game(game)
rows, st = funcs.analyse(img)
ev = collections.Counter(r['src'] for r in rows)
print('== %s: text 0x%x (%d insns)' % (name, img.text_size, img.text_size // 4))
print('functions (discovery): %d' % len(rows))
ex = sum(1 for r in rows if 'E' in r['src']); sy = sum(1 for r in rows if 'S' in r['src'])
print('  evidence: eh_frame(E) %d, symbol(S) %d, both %d, E-or-S %d, heuristic-only (B/R/T only) %d'
      % (ex, sy, sum(1 for r in rows if 'E' in r['src'] and 'S' in r['src']), sum(1 for r in rows if 'E' in r['src'] or 'S' in r['src']),
         sum(1 for r in rows if not ('E' in r['src'] or 'S' in r['src']))))
print('  heuristic-only breakdown: ' + ', '.join('%s=%d' % (k, v) for k, v in sorted(ev.items()) if 'E' not in k and 'S' not in k))
print('  named by symbols: %d; E/S end disagreements: %d; secondary entries: %d; end_from next: %d'
      % (st['named_by_symbols'], st['E_S_end_disagree'], st['secondary_entries'], st['only_heuristic']))
env = program.Env(img, cfg)
env.compute_starts()
fdes = env.load_eh()
jumptables.resolve(env)
n_lsda = sum(1 for f in fdes if f.lsda)
sites = sum(len(v[1]) for v in env.eh_data.values())
print('FDEs %d, with LSDA %d, call sites %d, landing pads %d, catcher functions (nx_catch_call) %d'
      % (len(fdes), n_lsda, sites, len(env.pads), len(env.catchers)))
import struct
words = img.words(); ts = env.text_lo
br_at = [ts + 4 * i for i, w in enumerate(words) if (w & 0xfffffc1f) == 0xd61f0000]
starts = env.starts
res = fb = plt = tail = 0
fb_fn = collections.Counter()
for b in br_at:
    k = bisect.bisect_right(starts, b) - 1
    s = starts[k]
    if env.plt_symbol(s):
        plt += 1; continue
    if b in env.jt: res += 1
    elif b in env.tailbr: tail += 1
    else: fb += 1; fb_fn[s] += 1
print('br xN: %d total = %d in PLT stubs + %d jump tables resolved + %d indirect tail calls + %d unresolved (fallback dispatch)'
      % (len(br_at), plt, res, tail, fb))
fsz = [(env.extent(s) - s) // 4 for s in fb_fn]
print('  functions with a fallback br: %d, total insns %d, largest %d' % (len(fsz), sum(fsz), max(fsz) if fsz else 0))
for s in sorted(fb_fn, key=lambda s: -(env.extent(s) - s))[:12]:
    print('    f_%x  %d insns, %d fallback br' % (s, (env.extent(s) - s) // 4, fb_fn[s]))
sizes = sorted(((env.extent(s) - s) // 4, s) for s in starts)
tot = sum(a for a, _ in sizes)
print('instruction total (extent): %d; functions > 20000 insns (optnone): %d; > 5000: %d; > 2000: %d; > 1000: %d'
      % (tot, *(sum(1 for a, _ in sizes if a > t) for t in (20000, 5000, 2000, 1000))))
print('  largest: ' + ', '.join('f_%x=%d' % (s, a) for a, s in sizes[-8:][::-1]))
print('  fallthrough-listed starts (from lifter): see lift log "extra branch targets"')
# gaps: .text bytes not inside any function extent
cov = []
for s in starts:
    cov.append((s, env.extent(s)))
cov.sort()
gaps = []; last = env.text_lo
for s, e in cov:
    if s > last: gaps.append((last, s))
    last = max(last, e)
if last < env.text_hi: gaps.append((last, env.text_hi))
gz = [(a, b) for a, b in gaps if any(img.word(x) not in (0, 0xd503201f) for x in range(a, b, 4))]
print('text gaps outside any function: %d (%d bytes), of which with words other than 0 and nop: %d (%d bytes)'
      % (len(gaps), sum(b - a for a, b in gaps), len(gz), sum(b - a for a, b in gz)))
for a, b in gz[:10]: print('    gap %x..%x (%d bytes)' % (a, b, b - a))
