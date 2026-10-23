"""Repeat measurement of the morph-ball roll speed (phys_table scenario `ball`) at 60, 120, 144 and 240 steps per second.

One mpr.exe process per rate and pass. Each process runs K repeats of the ball scenario in one script: title -> New Game -> Frigate once
(gp.prologue), then per repeat i: gp.warp to tallon_canyon_cavern, `@rate R`, phys_table.pre('ball'), `@hash ball_<R>_<i>_start`,
phys_table.actions('ball', R), `@hash ball_<R>_<i>_end`, `@rate 0`. Finally `@pass`.
Metric per repeat: phys_table.walk_metrics(window, 'ball')['steady'] (position-difference steady speed, last 1.5 s of the 3 s hold).

Passes: pass 1 = 60,120,144,240; pass 2 = 240,144,120,60. Processes run one after another. Before each process the script waits
while any other mpr.exe is running (the PC is shared); it never kills anything.

  tools\\.venv\\Scripts\\python.exe .weaver\\phys_ball_rep.py [--k 10] [--no-run]
  --no-run  re-analyse the run folders that already exist (no game started)

Output: work\\run_play3_ball\\out\\p<pass>_r<rate>\\ (script.nxs, mpr.log, out\\trace.jsonl, out\\result.json)
        work\\run_play3_ball\\ball_results.json (rewritten after every process)
"""
import argparse, json, os, statistics, subprocess, sys, time

ROOT = 'D:/AI/Active/Metroid-Prime'
sys.path.insert(0, ROOT + '/tools/test')
import phys_table as pt  # noqa: E402  (read only; not edited)
import gameplay as gp    # noqa: E402

EXE = ROOT + '/work/run_play3_ball/exe'
OUT = ROOT + '/work/run_play3_ball/out'
RESULTS = ROOT + '/work/run_play3_ball/ball_results.json'
SCEN = 'ball'
ORDERS = {1: (60, 120, 144, 240), 2: (240, 144, 120, 60)}
RATES = (60, 120, 144, 240)
SECONDS = 3600          # wall budget per process (game-side timeout)


def label(rate, i):
    return 'ball_%d_%d' % (rate, i)


def script(rate, k):
    lines = ['# ball repeats, rate %d, %d repeats' % (rate, k)] + gp.prologue(timeout_ms=600000)
    for i in range(k):
        lines += gp.warp('tallon', pt.AREA.get(SCEN, pt.DEFAULT_AREA))
        lines.append('@rate %d' % rate)
        lines += pt.pre(SCEN)
        lines.append('@hash %s_start' % label(rate, i))
        lines += pt.actions(SCEN, rate)
        lines.append('@hash %s_end' % label(rate, i))
        lines.append('@rate 0')
    lines.append('@pass')
    return lines + ['']


def window(rows, cps, lab):
    """same as phys_table.window, with the per-repeat labels"""
    fs, fe = cps.get(lab + '_start'), cps.get(lab + '_end')
    if fs is None or fe is None:
        return []
    pl = [r for r in rows if 'pos' in r and 'igt' in r and fs <= r['f'] <= fe]
    out = []
    for r in pl:
        if not out or r['igt'] > out[-1]['igt']:
            out.append(r)
    return out


def other_mpr():
    txt = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq mpr.exe', '/FO', 'CSV', '/NH'], capture_output=True, text=True).stdout
    return [l for l in txt.splitlines() if 'mpr.exe' in l.lower()]


def wait_idle():
    """one other mpr.exe may run alongside ours (another session's live run); wait only while more than one is running"""
    while True:
        busy = other_mpr()
        if len(busy) <= 1:
            return
        print('  waiting: %d other mpr.exe running (not ours, not touched)' % len(busy), flush=True)
        time.sleep(20)


def run_one(pas, rate, k, do_run):
    d = os.path.join(OUT, 'p%d_r%d' % (pas, rate))
    t = time.time()
    exit_code = None
    if do_run:
        wait_idle()
        env = {'NXRT_NVN_SHADER_CACHE': pt.SHADERS, 'NXRT_NVN_BC7_CACHE': pt.BC7, 'NXRT_AUDIO_SINK': 'null'}
        r = gp.run(script(rate, k), d, rate=None, env=env, seconds=SECONDS, exe_dir=EXE, gfx='headless')
        exit_code = r.get('exit')
    wall = time.time() - t
    rows = pt.load_trace(d)
    cps = pt.checkpoints(d, rows)
    recs, samples = [], []
    for i in range(k):
        pl = window(rows, cps, label(rate, i))
        m = pt.metrics(SCEN, pl) if pl else None
        rec = dict(**{'pass': pas, 'repeat': i, 'rate': rate, 'samples': len(pl),
                      'steady': m['steady'] if m else None,
                      'rise': m.get('rise') if m else None, 'total': m.get('total') if m else None,
                      'morph_start': pl[0].get('morph') if pl else None,
                      'morph_end': pl[-1].get('morph') if pl else None})
        recs.append(rec)
        samples.append(len(pl))
    run = dict(pass_=pas, rate=rate, dir=d, exit=exit_code, wall_s=round(wall, 1), samples=samples)
    return recs, run


def median_of(vals):
    return statistics.median(vals) if vals else None


def print_table(values, title, passes):
    base_vals = [r['steady'] for r in values.get(60, []) if r['pass'] in passes and r['steady'] is not None]
    base = median_of(base_vals)
    print('\n== %s' % title)
    print('%-5s %3s %10s %10s %10s %10s' % ('Hz', 'n', 'median', 'min', 'max', 'vs 60 (%)'))
    for rate in RATES:
        vals = [r['steady'] for r in values.get(rate, []) if r['pass'] in passes and r['steady'] is not None]
        if not vals:
            print('%-5d %3d  no values' % (rate, 0))
            continue
        med = median_of(vals)
        diff = (med - base) / base * 100 if base else float('nan')
        print('%-5d %3d %10.4f %10.4f %10.4f %+10.2f' % (rate, len(vals), med, min(vals), max(vals), diff))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--k', type=int, default=10)
    ap.add_argument('--no-run', action='store_true')
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    values, runs = {r: [] for r in RATES}, []
    for pas in (1, 2):
        for rate in ORDERS[pas]:
            print('pass %d, rate %d: start %s' % (pas, rate, time.strftime('%H:%M:%S')), flush=True)
            recs, run = run_one(pas, rate, a.k, not a.no_run)
            runs.append(run)
            values[rate].extend(recs)
            ok = [r for r in recs if r['steady'] is not None]
            print('  exit %s wall %.0f s samples %s steady ok %d/%d' % (run['exit'], run['wall_s'], run['samples'], len(ok), a.k), flush=True)
            out = {'scenario': SCEN, 'metric': 'phys_table.walk_metrics steady (position difference, last 1.5 s of the 3 s hold)',
                   'k': a.k, 'passes': {'1': [60, 120, 144, 240], '2': [240, 144, 120, 60]},
                   'values': {str(r): [{k2: v for k2, v in x.items()} for x in values[r]] for r in RATES}, 'runs': runs}
            with open(RESULTS, 'w') as f:
                json.dump(out, f, indent=1)
    print_table(values, 'both passes (20 values per rate)', (1, 2))
    print_table(values, 'pass 1, order 60,120,144,240', (1,))
    print_table(values, 'pass 2, order 240,144,120,60', (2,))
    print('\nper-repeat steady values (pass 1 | pass 2):')
    for rate in RATES:
        p1 = [('%.4f' % r['steady']) if r['steady'] is not None else 'FAIL' for r in values[rate] if r['pass'] == 1]
        p2 = [('%.4f' % r['steady']) if r['steady'] is not None else 'FAIL' for r in values[rate] if r['pass'] == 2]
        print('%4d: %s | %s' % (rate, ' '.join(p1), ' '.join(p2)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
