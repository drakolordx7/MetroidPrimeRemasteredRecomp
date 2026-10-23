"""S25: jump peak and air time of a stall run (trace rows between the checkpoints start and end): python air.py DIR..."""
import json, sys
sys.path.insert(0, 'D:/AI/Active/Metroid-Prime/tools/test')
import phys_table as pt
for d in sys.argv[1:]:
    rows = pt.load_trace(d)
    cps = {r['label']: r['f'] for r in rows if 'label' in r}
    pl = [r for r in rows if 'pos' in r and cps['start'] <= r['f'] <= cps['end']]
    # the stall: a row inside the flight whose y equals the previous row's while airborne
    y0 = pl[0]['pos'][1]
    stalls = [pl[i]['f'] for i in range(1, len(pl)) if pl[i]['pos'][1] > y0 + 0.3 and pl[i]['pos'][1] == pl[i - 1]['pos'][1]]
    print(d.split('/')[-1], pt.jump_metrics(pl), 'stall frames:', stalls)
