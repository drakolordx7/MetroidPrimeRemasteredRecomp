r"""tx_order.py TRACE -- order of texture events (tx.init, tx.reg, tx.flush, tx.use) per texture id from a frame trace of the S21 marks build.
Prints how many textures saw flush before/after init and reg, the lead time between the last flush before the first use and the first use,
and the same for registration."""
import sys, collections
sys.path.insert(0, r'D:\AI\Active\Metroid-Prime\runtime\scripts\prof')
import ftrace_report as fr
z, th, ev = fr.load(sys.argv[1])
by = collections.defaultdict(lambda: collections.defaultdict(list))
for t, d, tid, zz, a in ev:
    n = z[zz]
    if n.startswith('tx.') or n in ('tex.create',): by[a][n].append(t)
    if n == 'tex.prepare': by[a]['prep_ms'].append(d / 1e6)
n = 0; cnt = collections.Counter(); lead_flush = []; lead_reg = []; gaps = []
for a, d in by.items():
    if 'tx.use' not in d: continue
    n += 1
    use = min(d['tx.use'])
    init = min(d['tx.init']) if d['tx.init'] else None
    reg = min(d['tx.reg']) if d['tx.reg'] else None
    fl = sorted(d['tx.flush'])
    cnt['has_init'] += init is not None; cnt['has_reg'] += reg is not None; cnt['has_flush'] += bool(fl)
    cnt['flushes>1'] += len(fl) > 1
    if fl and init: cnt['flush_before_init'] += fl[0] < init
    if fl and reg: cnt['flush_before_reg'] += fl[0] < reg
    if fl and reg: cnt['flush_after_reg'] += fl[-1] > reg
    pre = [f for f in fl if f <= use]
    if pre: lead_flush.append((use - pre[-1]) / 1e6)
    if reg and reg <= use: lead_reg.append((use - reg) / 1e6)
    if len(d['tx.use']) > 1: cnt['used_more_than_once'] += 1
def pct(v, q): v = sorted(v); return v[int(q * (len(v) - 1))] if v else 0
print('textures used (uploaded):', n, dict(cnt))
print('lead flush->use ms p10/p50/p90:', [round(pct(lead_flush, q), 1) for q in (.1, .5, .9)], 'n', len(lead_flush))
print('lead reg->use ms   p10/p50/p90:', [round(pct(lead_reg, q), 1) for q in (.1, .5, .9)], 'n', len(lead_reg))
li = []; ir = []; prep = []; big = collections.Counter()
for a, d in by.items():
    if 'tx.use' in d and d['tx.init']:
        li.append((min(d['tx.use']) - min(d['tx.init'])) / 1e6)
        if d['tx.reg']: ir.append((min(d['tx.reg']) - min(d['tx.init'])) / 1e6)
    for p in d.get('prep_ms', []): prep.append(p)
print('lead init->use ms p10/p50/p90:', [round(pct(li, q), 1) for q in (.1, .5, .9)])
print('lead init->reg ms p10/p50/p90:', [round(pct(ir, q), 1) for q in (.1, .5, .9)])
print('tex.prepare zones >=30us: n', len(prep), 'total ms', round(sum(prep), 1), 'p50/p90/max', [round(pct(prep, q), 2) for q in (.5, .9, 1)])
