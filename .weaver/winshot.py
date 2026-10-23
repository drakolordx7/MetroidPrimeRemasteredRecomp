"""Start a program, wait for its top-level window, save a PNG of the window (PrintWindow, so other windows on top do not matter), then close it.
  python .weaver/winshot.py OUT.png [--title SUBSTR] [--wait SECONDS] [--keep] -- program args...
Writes OUT.png (client + frame). --keep leaves the program running. Windows only."""
import ctypes, ctypes.wintypes as wt, subprocess, sys, time
from PIL import Image

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
user32.SetProcessDPIAware()


def find_window(pid, title):
    found = []
    EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)

    def cb(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        p = wt.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
        n = user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(n + 1)
        user32.GetWindowTextW(hwnd, buf, n + 1)
        if (pid is None or p.value == pid) and (not title or title.lower() in buf.value.lower()) and buf.value:
            found.append(hwnd)
        return True

    user32.EnumWindows(EnumProc(cb), 0)
    return found[0] if found else None


def shot(hwnd, out):
    r = wt.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    w, h = r.right - r.left, r.bottom - r.top
    hdc = user32.GetWindowDC(hwnd)
    mdc = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
    gdi32.SelectObject(mdc, bmp)
    user32.PrintWindow(hwnd, mdc, 2)  # PW_RENDERFULLCONTENT
    class BIH(ctypes.Structure):
        _fields_ = [("biSize", wt.DWORD), ("biWidth", wt.LONG), ("biHeight", wt.LONG), ("biPlanes", wt.WORD), ("biBitCount", wt.WORD),
                    ("biCompression", wt.DWORD), ("biSizeImage", wt.DWORD), ("a", wt.LONG), ("b", wt.LONG), ("c", wt.DWORD), ("d", wt.DWORD)]
    bi = BIH(ctypes.sizeof(BIH), w, -h, 1, 32, 0, 0, 0, 0, 0, 0)
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(mdc, bmp, 0, h, buf, ctypes.byref(bi), 0)
    img = Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1).convert("RGB")
    img.save(out)
    gdi32.DeleteObject(bmp); gdi32.DeleteDC(mdc); user32.ReleaseDC(hwnd, hdc)
    return w, h


def main():
    a = sys.argv[1:]
    out = a[0]
    title, wait, keep = None, 3.0, False
    i = 1
    while i < len(a) and a[i] != "--":
        if a[i] == "--title": title = a[i + 1]; i += 2
        elif a[i] == "--wait": wait = float(a[i + 1]); i += 2
        elif a[i] == "--keep": keep = True; i += 1
        else: i += 1
    cmd = a[i + 1:]
    p = subprocess.Popen(cmd)
    t0 = time.time()
    hwnd = None
    while time.time() - t0 < 30 and not hwnd:
        time.sleep(0.2)
        hwnd = find_window(p.pid, title)
    if not hwnd:
        print("no window"); p.kill(); sys.exit(1)
    time.sleep(wait)
    print("shot", out, shot(hwnd, out))
    if not keep:
        p.kill()

main()
