"""Run mpr.exe (nvn4 build) with a test script, headless, in work/n4/<name>:
  python .weaver/n4run.py NAME SCRIPT.nxs [--exe path] [--seconds N] [--env K=V ...]
Sets the shader cache and the real RomFS like the sweep does. Prints the exit code; log is work/n4/NAME/mpr.log, shots in work/n4/NAME/shots."""
import argparse, os, subprocess, sys, time, shutil
ROOT = r'D:\AI\Active\Metroid-Prime'
ap = argparse.ArgumentParser()
ap.add_argument('name'); ap.add_argument('script')
ap.add_argument('--exe', default=os.path.join(ROOT, 'work', 'n4', 'exe_base', 'mpr.exe'))
ap.add_argument('--seconds', type=int, default=600)
ap.add_argument('--env', action='append', default=[])
ap.add_argument('--window', action='store_true', help='real window instead of headless')
ap.add_argument('--set', action='append', default=[], help='section.key=value written into controls.ini before the run (template work/n4/controls_template.ini)')
a = ap.parse_args()
out = os.path.join(ROOT, 'work', 'n4', a.name)
shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
save = os.path.join(out, 'save'); os.makedirs(save)
if a.set:
    import re
    ini = open(os.path.join(ROOT, 'work', 'n4', 'controls_template.ini')).read().split(chr(10))
    for kv in a.set:
        sk, v = kv.split('=', 1); sec, key = sk.split('.', 1)
        cur = None
        for i, l in enumerate(ini):
            m = re.match(r'\[(\w+)\]', l)
            if m: cur = m.group(1)
            elif cur == sec and re.match(r'%s\s*=' % re.escape(key), l): ini[i] = '%s = %s' % (key, v)
    open(os.path.join(out, 'controls.ini'), 'w').write(chr(10).join(ini))
env = dict(os.environ)
env.update({'NXRT_FS_ROMFS': os.path.join(ROOT, 'game', 'romfs'), 'NXRT_FS_SAVE_DIR': save,
            'NXRT_NVN_SHADER_CACHE': 'D:/AI/Active/Metroid-Prime/work/shader_cache/spirv',
            'NXRT_NVN_BC7_CACHE': os.path.join(ROOT, 'work', 'sweep_cache', 'bc7'),
            'NXRT_TEST_SCRIPT': os.path.abspath(a.script), 'NXRT_TEST_OUT': out, 'NXRT_TEST_DETERMINISTIC': '0',
            'NXRT_LOG_PATH': os.path.join(out, 'mpr.log'), 'NXRT_TEST_REGIONS': os.path.join(ROOT, 'tools', 'test', 'regions.tsv'),
            'NXRT_DIAG_WATCHDOG_SECONDS': '60', 'NXRT_TEST_WALL_TIMEOUT_S': str(a.seconds)})
if not a.window:
    env.update({'NXRT_GFX_HEADLESS': '1', 'NXRT_BOOT_GFX': 'headless'})
for kv in a.env:
    k, v = kv.split('=', 1); env[k] = v
t = time.time()
p = subprocess.Popen([a.exe, '--max-seconds', str(a.seconds - 5)], cwd=out, env=env, stdout=open(os.path.join(out, 'stdout.txt'), 'wb'), stderr=open(os.path.join(out, 'stderr.txt'), 'wb'))
try:
    rc = p.wait(timeout=a.seconds + 30)
except subprocess.TimeoutExpired:
    p.kill(); rc = 124
print('exit', rc, 'after %.0fs' % (time.time() - t))
