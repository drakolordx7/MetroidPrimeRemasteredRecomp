"""warm2_launcher_shot.py -- S24: start the launcher on a private game folder, let it run the Prepare shaders step, and save PNGs of the launcher window only
(PrintWindow of that one window; nothing else on the screen is read) while it runs and when it is done.
  python .weaver/warm2_launcher_shot.py [--programs work/warm2/programs_6000.bin] [--page 1]
Needs game-build-warm2/build/warm2/mpr.exe and runtime-wt/warm2/build/release/mpr_launcher.exe. Output: work/shots_wip/warm_launcher_*.png"""
import argparse, ctypes, ctypes.wintypes as wt, os, shutil, subprocess, sys, time


ROOT = r'D:\AI\Active\Metroid-Prime'
user32 = ctypes.windll.user32
user32.SetProcessDPIAware()
user32.GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
user32.GetWindowDC.restype = wt.HDC
user32.GetWindowDC.argtypes = [wt.HWND]


def shot(h, path):
    """Save a PNG of one window with PrintWindow (only that window's own pixels; nothing else on the screen is read)."""
    from PIL import Image
    gdi32 = ctypes.windll.gdi32
    r = wt.RECT()
    user32.GetWindowRect(h, ctypes.byref(r))
    w, hh = r.right - r.left, r.bottom - r.top
    hdc = user32.GetWindowDC(h)
    mdc = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, w, hh)
    gdi32.SelectObject(mdc, bmp)
    user32.PrintWindow(h, mdc, 2)

    class BIH(ctypes.Structure):
        _fields_ = [("biSize", wt.DWORD), ("biWidth", wt.LONG), ("biHeight", wt.LONG), ("biPlanes", wt.WORD), ("biBitCount", wt.WORD),
                    ("biCompression", wt.DWORD), ("biSizeImage", wt.DWORD), ("a", wt.LONG), ("b", wt.LONG), ("c", wt.DWORD), ("d", wt.DWORD)]
    bi = BIH(ctypes.sizeof(BIH), w, -hh, 1, 32, 0, 0, 0, 0, 0, 0)
    buf = ctypes.create_string_buffer(w * hh * 4)
    gdi32.GetDIBits(mdc, bmp, 0, hh, buf, ctypes.byref(bi), 0)
    Image.frombuffer("RGBA", (w, hh), buf, "raw", "BGRA", 0, 1).convert("RGB").save(path)
    gdi32.DeleteObject(bmp); gdi32.DeleteDC(mdc); user32.ReleaseDC(h, hdc)


def windows_of(pid):
    out = []
    cb = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)(lambda h, l: (out.append(h) if _owner(h) == pid and user32.IsWindowVisible(h) else None) or True)
    user32.EnumWindows(cb, 0)
    return out


def _owner(h):
    p = wt.DWORD()
    user32.GetWindowThreadProcessId(h, ctypes.byref(p))
    return p.value


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--programs', default=os.path.join(ROOT, 'work', 'warm2', 'programs_6000.bin'))
    ap.add_argument('--page', default='1')
    ap.add_argument('--mid', type=float, default=25.0)
    a = ap.parse_args()
    d = os.path.join(ROOT, 'work', 'run_warm2_launcher')
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(os.path.join(d, 'shader_cache'))
    for src in (os.path.join(ROOT, 'game-build-warm2', 'build', 'warm2'), os.path.join(ROOT, 'runtime-wt', 'warm2', 'build', 'release')):
        for f in os.listdir(src):
            if f in ('mpr.exe', 'mpr_launcher.exe') or f.endswith('.dll'):
                shutil.copy2(os.path.join(src, f), d)
    for n, t in (('exefs', 'game/exefs'), ('romfs', 'game/romfs'), ('bc7_cache', 'work/run/bc7_cache')):
        subprocess.run(['cmd', '/c', 'mklink', '/J', os.path.join(d, n), os.path.join(ROOT, *t.split('/'))], capture_output=True)
    subprocess.run(['cmd', '/c', 'mklink', '/J', os.path.join(d, 'shader_cache', 'spirv'), os.path.join(ROOT, 'work', 'shader_cache', 'spirv')], capture_output=True)
    shutil.copy2(os.path.join(ROOT, 'work', 'shader_cache', 'spirv', 'results.tsv'), os.path.join(d, 'shader_cache', 'results.tsv')) if False else None
    shutil.copy2(a.programs, os.path.join(d, 'shader_cache', 'programs.bin'))
    open(os.path.join(d, 'mpr.ini'), 'w').write('[fs]\nromfs = romfs\n[nvn]\nbc7_cache = bc7_cache\nshader_cache = shader_cache/spirv\n')
    shutil.copy2(os.path.join(ROOT, 'work', 'run_launcher', 'gamedir', 'setup_state.tsv'), os.path.join(d, 'setup_state.tsv'))
    shutil.copy2(os.path.join(ROOT, 'work', 'run_launcher', 'gamedir', 'controls.ini'), os.path.join(d, 'controls.ini'))
    env = dict(os.environ, NXRT_NVN_SPIRV_SALT='lshot%d' % int(time.time()))
    p = subprocess.Popen([os.path.join(d, 'mpr_launcher.exe'), '--game', d, '--page', a.page, '--auto-prepare'], cwd=d, env=env)
    out = os.path.join(ROOT, 'work', 'shots_wip')
    os.makedirs(out, exist_ok=True)
    time.sleep(a.mid)
    ws = windows_of(p.pid)
    if ws:
        shot(ws[0], os.path.join(out, 'warm_launcher_prepare_progress.png'))
        print('saved progress shot')
    t0 = time.time()
    while time.time() - t0 < 240:
        if os.path.exists(os.path.join(d, 'shader_cache', 'prepare.state')):
            break
        time.sleep(2)
    time.sleep(3)
    ws = windows_of(p.pid)
    if ws:
        shot(ws[0], os.path.join(out, 'warm_launcher_prepare_done.png'))
        print('saved done shot')
    p.terminate()


if __name__ == '__main__':
    main()
