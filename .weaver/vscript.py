"""S13: run one scripted run on the verify build.  python .weaver/vscript.py SCRIPT.nxs --out work/verify/NAME [--det] [--step TICKS] [--seconds 300]
[--gfx headless|window] [--env K=V ...] [--exe DIR].  Writes <out>/{mpr.log,out/(trace.jsonl,result.json,shots)}; prints exit code, result verdict, frame count."""
import argparse, json, os, subprocess, sys, time
ROOT = 'D:/AI/Active/Metroid-Prime'
ap = argparse.ArgumentParser()
ap.add_argument('script'); ap.add_argument('--out', required=True)
ap.add_argument('--det', action='store_true'); ap.add_argument('--step', type=int, help='clock_step_ticks (19.2e6/rate)')
ap.add_argument('--seconds', type=int, default=300); ap.add_argument('--gfx', default='headless')
ap.add_argument('--env', action='append', default=[]); ap.add_argument('--exe', default=ROOT + '/game-build-verify/build/snap')
ap.add_argument('--regions', default=ROOT + '/tools/test/regions.tsv'); ap.add_argument('--level')
a = ap.parse_args()
out = os.path.abspath(a.out); os.makedirs(out, exist_ok=True)
env = dict(os.environ)
env.update(NXRT_TEST_SCRIPT=os.path.abspath(a.script), NXRT_TEST_OUT=os.path.join(out, 'out'), NXRT_TEST_REGIONS=a.regions,
           NXRT_BOOT_GFX=a.gfx, NXRT_FS_ROMFS=ROOT + '/game/romfs', NXRT_FS_SAVE_DIR=ROOT + '/work/run_verify/save',
           NXRT_TEST_WALL_TIMEOUT_S=str(a.seconds), NXRT_TIME_MODE='real', NXRT_DIAG_WATCHDOG_SECONDS='60')
if a.gfx == 'headless': env['NXRT_GFX_HEADLESS'] = '1'
if a.det: env['NXRT_TEST_DETERMINISTIC'] = '1'
if a.step: env['NXRT_TEST_CLOCK_STEP_TICKS'] = str(a.step)
if a.level: env['NXRT_LOG_LEVEL'] = a.level
for kv in a.env:
    k, v = kv.split('=', 1); env[k] = v
cmd = [a.exe + '/mpr.exe', '--log', os.path.join(out, 'mpr.log'), '--max-seconds', str(a.seconds)]
t = time.time()
try:
    p = subprocess.run(cmd, cwd=ROOT + '/work/run_verify', env=env, capture_output=True, text=True, timeout=a.seconds + 60)
    rc = p.returncode
except subprocess.TimeoutExpired:
    rc = 124
print('exit %d in %.0f s' % (rc, time.time() - t))
rp = os.path.join(out, 'out', 'result.json')
if os.path.exists(rp):
    r = json.load(open(rp)); print({k: r[k] for k in r if k in ('verdict', 'frames', 'message', 'failed_line', 'final_hash', 'exit_code')})
sys.exit(rc)
