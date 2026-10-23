"""fps_timeline.py TAG... : per-10 s average fps / max frame ms of work/prof/TAG.trace"""
import sys, collections
sys.path.insert(0, r'D:\AI\Active\Metroid-Prime\runtime\scripts\prof')
import ftrace_report as fr
for tag in sys.argv[1:]:
    z, th, ev = fr.load(r'D:\AI\Active\Metroid-Prime\work\prof\%s.trace' % tag)
    fs = sorted(e[0] for e in ev if z[e[3]] == 'frame'); t0 = fs[0]
    b = collections.defaultdict(list)
    for i in range(1, len(fs)): b[int((fs[i] - t0) / 1e9 // 10)].append((fs[i] - fs[i - 1]) / 1e6)
    print(tag, ' '.join('%d:%.0f/%.0f' % (k * 10, len(v) / 10, max(v)) for k, v in sorted(b.items())))
