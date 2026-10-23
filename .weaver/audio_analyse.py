"""Analyse an audio_run.py output folder: mpr.log audio stats, WAV duration/RMS/dropouts/clicks, desync against wall clock and igt.

  tools\\.venv\\Scripts\\python .weaver\\audio_analyse.py [work\\run_play3_audio\\out]
"""
import json, os, re, sys, wave
import numpy as np

ROOT = 'D:/AI/Active/Metroid-Prime'
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'work', 'run_play3_audio', 'out')
SILENT_RUN_S = 0.100
ACTIVE_RMS_DB = -50.0          # a window counts as "non-silent" above this RMS (dBFS)
CLICK_THRESH = 16384           # int16 sample-to-sample jump counted as a click (about half full scale)


def log_lines():
    p = os.path.join(OUT, 'mpr.log')
    lines = open(p, errors='replace').read().splitlines()
    keep = [l for l in lines if re.search(r'sink|underrun|xaudio|audio', l, re.I)]
    return keep


def wav_stats():
    p = os.path.join(OUT, 'audio.wav')
    w = wave.open(p, 'rb')
    ch, sw, sr, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
    raw = w.readframes(n)
    w.close()
    assert sw == 2, 'expected 16-bit PCM'
    a = np.frombuffer(raw, dtype='<i2').reshape(-1, ch).astype(np.float64)
    mono = a.mean(axis=1)
    dur = n / sr
    res = dict(channels=ch, sample_width_bytes=sw, sample_rate=sr, frames=n, duration_s=dur)

    # RMS per second (mono mix), dBFS
    sec = int(np.floor(dur))
    rms = []
    for s in range(sec):
        seg = mono[s * sr:(s + 1) * sr]
        rms.append(float(np.sqrt(np.mean(seg ** 2))) / 32768.0)
    rms = np.array(rms)
    db = 20 * np.log10(np.maximum(rms, 1e-9))
    res['rms_per_second_lin'] = [round(float(x), 4) for x in rms]
    res['rms_per_second_dbfs'] = [round(float(x), 1) for x in db]
    res['active_seconds'] = int(np.sum(db > ACTIVE_RMS_DB))
    res['silent_seconds_below_-50dbfs'] = [i for i, d in enumerate(db) if d <= ACTIVE_RMS_DB]

    # digital silence runs (all channels exactly 0) >= 100 ms, flagged as dropouts when both sides are active
    zero = np.all(a == 0, axis=1)
    edges = np.flatnonzero(np.diff(np.concatenate(([0], zero.astype(np.int8), [0]))))
    runs = list(zip(edges[::2], edges[1::2]))
    min_len = int(SILENT_RUN_S * sr)
    win = int(0.5 * sr)

    def active_around(start, end):
        before = mono[max(0, start - win):start]
        after = mono[end:end + win]
        def act(x):
            return x.size > 0 and 20 * np.log10(max(np.sqrt(np.mean(x ** 2)) / 32768.0, 1e-9)) > ACTIVE_RMS_DB
        return act(before) and act(after)

    long_runs = [(int(s), int(e)) for s, e in runs if e - s >= min_len]
    dropouts = [dict(start_s=round(s / sr, 3), dur_ms=round((e - s) * 1000 / sr, 1)) for s, e in long_runs if active_around(s, e)]
    res['digital_silence_runs_ge_100ms_total'] = len(long_runs)
    res['dropouts_silence_between_active_audio'] = dropouts
    res['dropout_count'] = len(dropouts)

    # clicks: sample-to-sample jumps above CLICK_THRESH on the mono mix, with the largest few
    d = np.abs(np.diff(mono))
    idx = np.flatnonzero(d > CLICK_THRESH)
    res['click_threshold_int16'] = CLICK_THRESH
    res['click_count'] = int(idx.size)
    top = np.argsort(d)[-5:][::-1]
    res['largest_jumps'] = [dict(t_s=round(int(i) / sr, 4), jump=int(d[i])) for i in top]
    res['peak_abs_int16'] = int(np.max(np.abs(mono)))
    return res


def trace_stats(timing):
    p = os.path.join(OUT, 'out', 'trace.jsonl')
    rows = []
    for line in open(p, errors='replace'):
        try:
            rows.append(json.loads(line))
        except ValueError:
            pass
    igt = [r['igt'] for r in rows if 'igt' in r]
    fr = [r['f'] for r in rows if 'f' in r]
    cps = {}
    rp = os.path.join(OUT, 'out', 'result.json')
    if os.path.exists(rp):
        for c in json.load(open(rp)).get('checkpoints', []):
            cps[c['label']] = c['frame']
    return dict(rows=len(rows), frame_first=min(fr) if fr else None, frame_last=max(fr) if fr else None,
                igt_first=min(igt) if igt else None, igt_last=max(igt) if igt else None,
                checkpoints=cps, keys_example=sorted(rows[-1].keys()) if rows else None)


def main():
    timing = json.load(open(os.path.join(OUT, 'timing.json')))
    out = dict(timing=timing, log=log_lines())
    out['trace'] = trace_stats(timing)
    if os.path.exists(os.path.join(OUT, 'audio.wav')):
        out['wav'] = wav_stats()
    json.dump(out, open(os.path.join(OUT, 'analysis.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k not in ('wav',)}, indent=1)[:6000])
    if 'wav' in out:
        w = dict(out['wav'])
        w['rms_per_second_dbfs'] = '%d values' % len(w['rms_per_second_dbfs'])
        w['rms_per_second_lin'] = '%d values' % len(w['rms_per_second_lin'])
        print(json.dumps(w, indent=1)[:6000])


if __name__ == '__main__':
    main()
