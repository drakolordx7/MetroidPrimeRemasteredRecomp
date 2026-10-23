"""Nsight Graphics frame capture of mpr.exe (window mode) running a test script:
  python .weaver/n4ngfx.py NAME SCRIPT.nxs [--exe path] [--timer-ms 90000]
Output: work/n4/NAME/ (mpr.log and the .ngfx-capture file)."""
import argparse, os, subprocess, shutil
ROOT = r'D:\AI\Active\Metroid-Prime'
ap = argparse.ArgumentParser()
ap.add_argument('name'); ap.add_argument('script')
ap.add_argument('--exe', default=os.path.join(ROOT, 'game-build-nvn4', 'build', 'nvn4', 'mpr.exe'))
ap.add_argument('--timer-ms', type=int, default=90000)
ap.add_argument('--seconds', type=int, default=400)
a = ap.parse_args()
out = os.path.join(ROOT, 'work', 'n4', a.name)
shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
save = os.path.join(out, 'save'); os.makedirs(save)
env = dict(os.environ)
env.update({'NXRT_FS_ROMFS': os.path.join(ROOT, 'game', 'romfs'), 'NXRT_FS_SAVE_DIR': save,
            'NXRT_NVN_SHADER_CACHE': 'D:/AI/Active/Metroid-Prime/work/shader_cache/spirv',
            'NXRT_NVN_BC7_CACHE': os.path.join(ROOT, 'work', 'sweep_cache', 'bc7'),
            'NXRT_TEST_SCRIPT': os.path.abspath(a.script), 'NXRT_TEST_OUT': out, 'NXRT_TEST_DETERMINISTIC': '0',
            'NXRT_LOG_PATH': os.path.join(out, 'mpr.log'), 'NXRT_TEST_REGIONS': os.path.join(ROOT, 'tools', 'test', 'regions.tsv')})
ngfx = r'C:\Program Files\NVIDIA Corporation\Nsight Graphics 2026.3.1\host\windows-desktop-nomad-x64\ngfx-capture.exe'
cmd = [ngfx, '--exe', a.exe, '--working-dir', out, '--args', '--max-seconds', str(a.seconds), '--output-dir', out, '--capture-countdown-timer', str(a.timer_ms), '-n', '1', '--no-hud', '--terminate-after-capture']
r = subprocess.run(cmd, env=env, cwd=out, capture_output=True, text=True, timeout=a.seconds + 120)
print(r.returncode); print(r.stdout[-3000:]); print(r.stderr[-2000:])
