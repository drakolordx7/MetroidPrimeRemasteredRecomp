"""S14 upscaling oracle: python -I .weaver/fsr_matrix.py [--out work/shots_s14] [--only NAME ...]
Runs the extras build in window mode at 3840x2160 through the opening cutscene for each variant and reports the presented frame rate and the GPU time
of the present pass (output pass / FSR 1) averaged over the last 20 s, with a screenshot at 110 s per variant copied to --out.
Variants: native (internal 4K), bilinear 67 / 50 (Display render_scale, no FSR), fsr1 67 / 50 (render_scale + FSR 1 at present), scene67 / scene50 (the game's
dynamic-resolution path, tone-map input upscaled by FSR 1, HUD native)."""
import argparse, os, re, shutil, statistics, subprocess, sys

ROOT = r'D:\AI\Active\Metroid-Prime'
RUN = ROOT + r'\work\run_extras'
BASH = 'C:/Program Files/Git/usr/bin/bash.exe'
VARIANTS = {
    'native':     dict(render_scale=100, env={}),
    'bilinear67': dict(render_scale=67,  env={}),
    'fsr1_67':    dict(render_scale=67,  env={'NXRT_UPSCALE_MODE': 'fsr1'}),
    'bilinear50': dict(render_scale=50,  env={}),
    'fsr1_50':    dict(render_scale=50,  env={'NXRT_UPSCALE_MODE': 'fsr1'}),
    'scene67':    dict(render_scale=100, env={'NXRT_UPSCALE_MODE': 'fsr1', 'NXRT_UPSCALE_SCENE_SCALE': '67'}),
    'scene50':    dict(render_scale=100, env={'NXRT_UPSCALE_MODE': 'fsr1', 'NXRT_UPSCALE_SCENE_SCALE': '50'}),
}


def set_display(scale):
    p = RUN + r'\controls.ini'
    s = open(p).read()
    for k, v in (('width', 3840), ('height', 2160), ('fps_cap', 0), ('render_scale', scale)):
        s = re.sub(r'(?m)^%s = .*$' % k, '%s = %d' % (k, v), s, count=1)
    open(p, 'w').write(s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=ROOT + r'\work\shots_s14')
    ap.add_argument('--only', nargs='*')
    ap.add_argument('--seconds', type=int, default=130)
    ap.add_argument('--shot-at', type=int, default=110)
    ap.add_argument('--press', default='A@12,A@22,A@30,A@38,A@46,A@54,A@62,A@70,A@80')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for name, v in VARIANTS.items():
        if a.only and name not in a.only:
            continue
        set_display(v['render_scale'])
        for f in os.listdir(RUN):
            if f.startswith('shot_'):
                os.remove(os.path.join(RUN, f))
        cmd = [BASH, '.weaver/boot_extras.sh', '--no-build', '--seconds', str(a.seconds), '--env', 'NXRT_BOOT_GFX=window', '--env', 'NXRT_GFX_LOG_FPS=1',
               '--env', 'NXRT_HDR_MODE=off', '--env', 'NXRT_BOOT_SCREENSHOT_AT=%d' % a.shot_at, '--env', 'NXRT_BOOT_PRESS=%s' % a.press]
        for k, val in v['env'].items():
            cmd += ['--env', '%s=%s' % (k, val)]
        subprocess.run(cmd, cwd=ROOT, env=dict(os.environ, MSYS2_ARG_CONV_EXCL='*'), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        rows = []
        for l in open(RUN + r'\mpr.log', errors='replace'):
            m = re.match(r'\[\s*([\d.]+) I .*gfx: fps ([\d.]+), present pass GPU ([\d.]+) ms', l)
            if m:
                rows.append(tuple(float(x) for x in m.groups()))
        w = [r for r in rows if r[0] >= a.seconds - 22]
        if w:
            print('%-11s fps mean %.1f median %.1f   present-pass GPU %.3f ms   (%d samples)' % (name, statistics.mean(r[1] for r in w), statistics.median(r[1] for r in w),
                                                                                           statistics.mean(r[2] for r in w), len(w)))
        else:
            print('%-11s no samples (%d rows)' % (name, len(rows)))
        sys.stdout.flush()
        s0 = RUN + r'\shot_0.png'
        if os.path.exists(s0):
            shutil.copy(s0, os.path.join(a.out, name + '.png'))


main()
