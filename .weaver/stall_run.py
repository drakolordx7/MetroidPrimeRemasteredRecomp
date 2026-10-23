"""S25: standing jump at 240 steps/s with the hardware write watch on the player's velocity.y and position.y around the stall frame.
  python stall_run.py [--rate 240] [--from 140] [--to 170] [--out DIR]"""
import argparse, os, sys
sys.path.insert(0, 'D:/AI/Active/Metroid-Prime/tools/test')
import gameplay as gp
ap = argparse.ArgumentParser()
ap.add_argument('--rate', type=int, default=240)
ap.add_argument('--from', dest='a', type=int, default=140)
ap.add_argument('--to', dest='b', type=int, default=170)
ap.add_argument('--out', default='D:/AI/Active/Metroid-Prime/work/run_play2/stall/r1')
ap.add_argument('--area', default='tallon_canyon_cavern')
ap.add_argument('--nowatch', action='store_true')
a = ap.parse_args()
press = int(round(0.4 * a.rate))
lines = ['# stall watch'] + gp.prologue(timeout_ms=600000) + gp.warp('tallon', a.area) + ['@rate %d' % a.rate, '@hash start']
lines += ['press B for %d' % press, 'wait %d' % (a.a - press)]
if not a.nowatch: lines.append('@watch on both')
lines += ['wait %d' % (a.b - a.a)]
if not a.nowatch: lines.append('@watch off')
lines += ['@run 2', '@hash end', '@pass', '']
env = {'NXRT_NVN_SHADER_CACHE': gp.ROOT + '/work/shader_cache/spirv', 'NXRT_NVN_BC7_CACHE': gp.ROOT + '/work/bc7_cache_polish', 'NXRT_AUDIO_SINK': 'null'}
r = gp.run(lines, a.out, env=env, seconds=900, exe_dir=gp.ROOT + '/game-build-play2/build/play2')
print(r)
