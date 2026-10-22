"""igt/pos/area progress at the end of a trace: python .weaver/igtstat.py trace.jsonl [n_samples]"""
import json, sys
rows = []
for l in open(sys.argv[1], errors='replace'):
    try: rows.append(json.loads(l))
    except ValueError: pass
rows = [r for r in rows if 'f' in r]
n = int(sys.argv[2]) if len(sys.argv) > 2 else 8
step = max(1, len(rows) // (n * 8))
print(len(rows), 'frames; last', n, 'samples every', step * 8, 'frames')
for r in rows[-n * step * 8::step * 8]:
    print(r['f'], r.get('area', '')[:8], 'igt', r.get('igt'), 'pos', [round(x) for x in r.get('pos', [])], 'ms', r.get('ms'))
