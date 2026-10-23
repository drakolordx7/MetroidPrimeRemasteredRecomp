r"""Input-to-GPU-done latency from a frame trace written by the S18 probe (marks lat.input / lat.sim / lat.present / lat.present_end / lat.gpudone,
arg = frame id; lat.inflight = frames simulated and not presented at each simulation start, lat.gpuq = GPU submissions unfinished).

  python lat_report.py work\prof\x.trace [--skip 60] [--seconds 90] [--json out.json]

Per frame id: input = the last input sample of the id (the one ProcessInput took), done = the GPU finished the id's present command buffer.
Prints median / p95 / max of input->present returned and input->GPU done, the in-flight counts, and the frame-time percentiles / stalls
(> 2 x median) in the same window."""
import argparse, collections, json, os, sys
sys.path.insert(0, os.path.join(r'D:\AI\Active\Metroid-Prime\runtime\scripts\prof'))
import ftrace_report as fr


def pct(v, q):
    if not v: return 0.0
    v = sorted(v); return v[min(len(v) - 1, int(q * len(v)))]


def analyse(path, skip=60.0, seconds=90.0):
    zones, threads, ev = fr.load(path)
    name = {k: v for k, v in zones.items()}
    by = collections.defaultdict(list)
    for t, d, th, z, a in ev: by[name.get(z, '?')].append((t, a))
    frames = sorted(t for t, _ in by['frame'])
    if len(frames) < 10: return {'frames': 0}
    t0 = frames[0] + int(skip * 1e9); t1 = t0 + int(seconds * 1e9)
    inp = {}; ninp = collections.Counter()
    for t, a in sorted(by['lat.input']): inp[a] = t; ninp[a] += 1          # last sample of the id wins; two samples = ProcessInput ran = the player is in control
    ctrl = {a for a, n in ninp.items() if n >= 2}
    pres = {a: t for t, a in by['lat.present']}
    pend = {a: t for t, a in by['lat.present_end']}
    done = {a: t for t, a in by['lat.gpudone']}
    i2p, i2d, p2d = [], [], []
    for a, ti in inp.items():
        if not (t0 <= ti <= t1): continue
        if a in pend: i2p.append((pend[a] - ti) / 1e6)
        if a in done: i2d.append((done[a] - ti) / 1e6); 
        if a in done and a in pend: p2d.append((done[a] - pend[a]) / 1e6)
    infl = [a for t, a in by['lat.inflight'] if t0 <= t <= t1]
    gq = [a for t, a in by['lat.gpuq'] if t0 <= t <= t1]
    fw = [t for t in frames if t0 <= t <= t1]
    iv = [(fw[i] - fw[i - 1]) / 1e6 for i in range(1, len(fw))]
    med = pct(iv, .5)
    # same numbers over the frames the player controls (ProcessInput ran)
    c_i2d = [(done[a] - inp[a]) / 1e6 for a in ctrl if a in done and t0 <= inp[a] <= t1]
    c_i2p = [(pend[a] - inp[a]) / 1e6 for a in ctrl if a in pend and t0 <= inp[a] <= t1]
    ct = sorted((pres[a], a) for a in ctrl if a in pres and t0 <= pres[a] <= t1)
    civ = [(ct[i][0] - ct[i - 1][0]) / 1e6 for i in range(1, len(ct)) if ct[i][1] == ct[i - 1][1] + 1]
    cmed = pct(civ, .5)
    r = {'ctrl_frames': len(c_i2d), 'ctrl_in2present_p50': round(pct(c_i2p, .5), 1), 'ctrl_in2present_p95': round(pct(c_i2p, .95), 1),
         'ctrl_in2gpu_p50': round(pct(c_i2d, .5), 1), 'ctrl_in2gpu_p95': round(pct(c_i2d, .95), 1), 'ctrl_in2gpu_max': round(max(c_i2d), 1) if c_i2d else 0,
         'ctrl_ft_p50': round(cmed, 2), 'ctrl_ft_p99': round(pct(civ, .99), 2), 'ctrl_ft_max': round(max(civ), 1) if civ else 0,
         'ctrl_stalls_2x': sum(1 for d in civ if d > 2 * cmed), 'ctrl_stalls_50': sum(1 for d in civ if d > 50),
         'frames': len(iv), 'fps': round(len(iv) / ((fw[-1] - fw[0]) / 1e9), 1) if len(fw) > 1 else 0,
         'ft_p50': round(med, 2), 'ft_p99': round(pct(iv, .99), 2), 'ft_max': round(max(iv), 1) if iv else 0,
         'stalls_2x': sum(1 for d in iv if d > 2 * med), 'stalls_50': sum(1 for d in iv if d > 50),
         'n_lat': len(i2d),
         'in2present_p50': round(pct(i2p, .5), 1), 'in2present_p95': round(pct(i2p, .95), 1),
         'in2gpu_p50': round(pct(i2d, .5), 1), 'in2gpu_p95': round(pct(i2d, .95), 1), 'in2gpu_max': round(max(i2d), 1) if i2d else 0,
         'present2gpu_p50': round(pct(p2d, .5), 1),
         'inflight_p50': pct(infl, .5), 'inflight_max': max(infl) if infl else 0, 'gpuq_p50': pct(gq, .5), 'gpuq_max': max(gq) if gq else 0}
    return r


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('trace'); ap.add_argument('--skip', type=float, default=60); ap.add_argument('--seconds', type=float, default=90)
    ap.add_argument('--json')
    a = ap.parse_args()
    r = analyse(a.trace, a.skip, a.seconds)
    for k, v in r.items(): print('%-16s %s' % (k, v))
    if a.json: json.dump(r, open(a.json, 'w'), indent=1)
