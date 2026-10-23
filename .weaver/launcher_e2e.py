"""Drive the real launcher window from outside (Win32 messages), the way a player would, then check what it wrote.

  python .weaver/launcher_e2e.py settings --launcher D:/.../mpr_launcher.exe --game D:/.../gamedir [--play] [--shots DIR]
      Fresh controls.ini -> change settings in the window (Display, Extras, Controls, a rebound key) -> Save -> read controls.ini and check every value.
      With --play it then presses Play and waits for mpr.exe (window size and the counter are checked by the caller's log/screenshot).
  python .weaver/launcher_e2e.py setup --launcher ... --game FRESH_DIR --setup-args "..." [--timeout 900]
      Opens the launcher on an empty folder, checks the "no game files" state, presses the setup button (the setup tool runs with --setup-args),
      waits for the launcher to show "Ready to play" and checks Play is enabled.
Exit code 0 = every check passed. Windows only; uses only ctypes and the standard library (PIL for screenshots when --shots is given).
"""
import argparse, ctypes, ctypes.wintypes as wt, os, subprocess, sys, time

user32 = ctypes.windll.user32
user32.SetProcessDPIAware()
user32.GetDpiForWindow.argtypes = [wt.HWND]
user32.SendMessageW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
user32.SendMessageW.restype = ctypes.c_ssize_t
user32.PostMessageW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
user32.FindWindowW.restype = wt.HWND
user32.GetParent.restype = wt.HWND
user32.GetParent.argtypes = [wt.HWND]
user32.GetDlgCtrlID.argtypes = [wt.HWND]
user32.IsWindowEnabled.argtypes = [wt.HWND]
user32.SetWindowTextW.argtypes = [wt.HWND, wt.LPCWSTR]
user32.GetWindowTextLengthW.argtypes = [wt.HWND]
user32.GetWindowTextW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
user32.GetClassNameW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
user32.GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
user32.SetForegroundWindow.argtypes = [wt.HWND]
WM_COMMAND, WM_HSCROLL, WM_NOTIFY, WM_KEYDOWN, WM_LBUTTONDBLCLK, WM_LBUTTONDOWN, WM_LBUTTONUP = 0x111, 0x114, 0x4E, 0x100, 0x203, 0x201, 0x202
BM_CLICK, BM_GETCHECK, CB_SETCURSEL, CB_GETCURSEL, TBM_SETPOS, TBM_GETPOS = 0xF5, 0xF0, 0x14E, 0x147, 0x405, 0x400
CBN_SELCHANGE = 1
LVM_GETSUBITEMRECT = 0x1038
LVM_SETITEMSTATE = 0x102B
LVM_ENSUREVISIBLE = 0x1013

fails = []


def check(cond, what):
    print(("ok   " if cond else "FAIL ") + what)
    if not cond:
        fails.append(what)


def text_of(h):
    b = ctypes.create_unicode_buffer(512)
    user32.SendMessageW(h, 0x0D, 512, ctypes.addressof(b))   # WM_GETTEXT (GetWindowText does not read another process's edit control)
    return b.value


def cls_of(h):
    b = ctypes.create_unicode_buffer(64)
    user32.GetClassNameW(h, b, 64)
    return b.value


def kids(h):
    out = []
    CB = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)

    def cb(c, _):
        if user32.GetParent(c) == h:
            out.append(c)
        return True

    user32.EnumChildWindows(h, CB(cb), 0)
    return out


def find_top(cls, pid=None, timeout=20):
    t0 = time.time()
    while time.time() - t0 < timeout:
        h = user32.FindWindowW(cls, None)
        if h:
            return h
        time.sleep(0.2)
    return None


def send_cmd(page, ctl, code):
    cid = user32.GetDlgCtrlID(ctl)
    user32.SendMessageW(page, WM_COMMAND, (code << 16) | (cid & 0xFFFF), ctl)


def set_combo(page, combo, index):
    user32.SendMessageW(combo, CB_SETCURSEL, index, 0)
    send_cmd(page, combo, CBN_SELCHANGE)


def set_slider(page, tb, pos):
    user32.SendMessageW(tb, TBM_SETPOS, 1, pos)
    user32.SendMessageW(page, WM_HSCROLL, 0, tb)


def click(h):
    user32.SendMessageW(h, BM_CLICK, 0, 0)


def set_text(h, s):
    user32.SetWindowTextW(h, s)


def by_class(page, cls):
    return [c for c in kids(page) if cls_of(c) == cls]


def pages_of(main):
    """The five pages in tab order, found by what they hold (the window order changes when a page is shown)."""
    ps = [c for c in kids(main) if cls_of(c) == "MprLauncherPage"]
    def kind(pg):
        n = lambda c: len(by_class(pg, c))
        if n("SysListView32"): return 3
        if n("ComboBox") == 17: return 4
        if n("Edit"): return 0
        if n("msctls_trackbar32") == 3: return 2
        return 1
    return [p for _, p in sorted(((kind(p), p) for p in ps), key=lambda t: t[0])]


def read_ini(path):
    sec, d = None, {}
    for line in open(path, encoding="utf-8").read().splitlines():
        line = line.strip()
        if not line or line[0] in "#;":
            continue
        if line.startswith("["):
            sec = line[1:-1].lower()
            d[sec] = {}
        elif sec is not None and "=" in line:
            k, v = line.rsplit("=", 1) if sec.startswith("bindings") else line.split("=", 1)
            d[sec].setdefault(k.strip().lower(), []).append(v.strip())
    return d


def first(d, sec, key):
    return d[sec][key][0]


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


def select_page(main, i):
    tab = [c for c in kids(main) if cls_of(c) == "SysTabControl32"][0]
    user32.SendMessageW(tab, 0x130C, i, 0)  # TCM_SETCURSEL
    nm = (ctypes.c_byte * 24)()
    ctypes.memmove(nm, ctypes.byref(ctypes.c_void_p(tab)), 8)
    ctypes.memmove(ctypes.addressof(nm) + 8, ctypes.byref(ctypes.c_uint64(user32.GetDlgCtrlID(tab))), 8)
    ctypes.memmove(ctypes.addressof(nm) + 16, ctypes.byref(ctypes.c_int(-551)), 4)  # TCN_SELCHANGE
    user32.SendMessageW(main, WM_NOTIFY, user32.GetDlgCtrlID(tab), ctypes.addressof(nm))


def cmd_settings(a):
    subprocess.run(["taskkill", "/F", "/IM", os.path.basename(a.launcher)], capture_output=True)
    time.sleep(0.5)
    ini = os.path.join(a.game, "controls.ini")
    for f in (ini, ini + ".bak"):
        if os.path.exists(f):
            os.remove(f)
    cfg = os.path.join(os.path.dirname(a.launcher), "mpr_launcher.ini")
    if os.path.exists(cfg):
        os.remove(cfg)
    p = subprocess.Popen([a.launcher, "--game", a.game, "--page", "3"])
    main = find_top("MprLauncherWindow")
    check(bool(main), "launcher window opens")
    time.sleep(1.0)
    pages = pages_of(main)
    check(len(pages) == 5, "five tabs: %d" % len(pages))
    display, extras, controls, keys, pad = pages
    buttons = by_class(main, "Button")
    btn = {text_of(b): b for b in buttons}
    check(user32.IsWindowEnabled(btn["Play"]) != 0, "Play is enabled for a folder with game files")
    check(user32.IsWindowEnabled(btn["Save"]) == 0, "Save is disabled before any change")
    if a.shots:
        os.makedirs(a.shots, exist_ok=True)
        shot(main, os.path.join(a.shots, "launcher_display.png"))

    # Display tab
    combos = by_class(display, "ComboBox")
    edits = by_class(display, "Edit")
    check(len(combos) == 3 and len(edits) == 2, "display tab controls: %d combos %d edits" % (len(combos), len(edits)))
    set_combo(display, combos[1], 3)           # 1920 x 1080
    check(text_of(edits[0]) == "1920" and text_of(edits[1]) == "1080", "size preset fills the boxes (%s x %s)" % (text_of(edits[0]), text_of(edits[1])))
    set_combo(display, combos[2], 6)           # 144 fps
    click([b for b in by_class(display, "Button") if text_of(b) == "VSync"][0])
    tb = by_class(display, "msctls_trackbar32")[0]
    set_slider(display, tb, 10)
    check(user32.IsWindowEnabled(btn["Save"]) != 0, "Save turns on after a change")

    # Extras tab
    ec = by_class(extras, "ComboBox")
    set_combo(extras, ec[0], 0)                # HDR off
    set_combo(extras, ec[1], 1)                # low latency auto
    set_combo(extras, ec[2], 3)                # corner bottom right
    set_combo(extras, ec[3], 2)                # detail 2
    click([b for b in by_class(extras, "Button") if "Show the counter" in text_of(b)][0])

    # Controls tab
    sl = by_class(controls, "msctls_trackbar32")
    set_slider(controls, sl[0], 40)            # horizontal 4.0 (linked: vertical follows)
    cc = by_class(controls, "ComboBox")
    set_combo(controls, cc[0], 1)              # keyboard and mouse icons
    click([b for b in by_class(controls, "Button") if text_of(b) == "Invert vertical aim"][0])

    # Controller tab: the face buttons combo comes first, then one combo per pad button in PadSrc order; south is the first of those
    pc = by_class(pad, "ComboBox")
    set_combo(pad, pc[1], 4)                   # items: Default, Nothing, A, B, X ...: south now presses Switch X
    # Keyboard tab: rebind Jump (row 8 of the list, Key 1) to G through the capture window
    lv = by_class(keys, "SysListView32")[0]
    # The list view's own messages carry pointers and do not cross processes, so the double-click is posted to the list view window itself
    # (client coordinates worked out from its size and the DPI; rows are 29 px at 144 DPI). No global mouse input is used.
    lr = wt.RECT()
    user32.GetWindowRect(lv, ctypes.byref(lr))
    dpi = user32.GetDpiForWindow(main)
    row_h = 29.0 * dpi / 144.0
    head_h = 36.0 * dpi / 144.0
    jump_row = 8
    cx = int(0.42 * (lr.right - lr.left) + 20 * dpi / 144.0)
    cy = int(head_h + row_h * (jump_row + 0.5))
    lparam = (cy << 16) | (cx & 0xFFFF)
    for msg in (WM_LBUTTONDOWN, WM_LBUTTONUP, WM_LBUTTONDBLCLK, WM_LBUTTONUP):
        user32.PostMessageW(lv, msg, 1 if msg in (WM_LBUTTONDOWN, WM_LBUTTONDBLCLK) else 0, lparam)
        time.sleep(0.05)
    cap = find_top("MprLauncherCapture", timeout=5)
    check(bool(cap), "double-click opens the capture window")
    if cap:
        time.sleep(0.3)
        if a.shots:
            shot(cap, os.path.join(a.shots, "launcher_capture.png"))
        user32.SendMessageW(cap, WM_KEYDOWN, 0x47, (0x22 << 16) | 1)   # G (scan 0x22)
        time.sleep(0.5)
    click(btn["Save"])
    time.sleep(0.8)
    check(user32.IsWindowEnabled(btn["Save"]) == 0, "Save turns off after saving")
    check(os.path.exists(ini), "controls.ini written")
    d = read_ini(ini)
    check(first(d, "display", "width") == "1920" and first(d, "display", "height") == "1080", "ini: 1920 x 1080")
    check(first(d, "display", "fps_cap") == "144", "ini: fps_cap 144")
    check(first(d, "display", "vsync") == "1", "ini: vsync on")
    check(first(d, "display", "fov_offset") == "10", "ini: fov_offset 10")
    check(first(d, "hdr", "mode") == "off", "ini: hdr off")
    check(first(d, "latency", "mode") == "auto", "ini: latency auto")
    check(first(d, "fps", "show") == "1" and first(d, "fps", "corner") == "bottom_right" and first(d, "fps", "detail") == "2", "ini: fps counter on, bottom_right, detail 2")
    check(first(d, "fps", "key") == "F2", "ini: fps key F2")
    check(first(d, "prompts", "style") == "keyboard", "ini: prompts keyboard")
    check(first(d, "mouse", "invert_y") == "1", "ini: invert_y")
    yaw = float(first(d, "mouse", "yaw")); pitch = float(first(d, "mouse", "pitch"))
    check(abs(yaw - 4.0 * 0.000383972) < 1e-7 and abs(pitch - yaw) < 1e-9, "ini: sensitivity 4.0 on both axes (linked): %.9f %.9f" % (yaw, pitch))
    jb = [k for k, v in d["bindings.all"].items() if "jump" in v]
    check(jb == ["g"], "ini: jump is bound to G only: %s" % jb)
    padmap = {k: v[0] for k, v in d["padmap"].items()}
    changed = [k for k, v in padmap.items() if v != "default"]
    check(changed == ["south"] and padmap["south"].lower() == "x", "ini: only south is remapped, to X: %s" % padmap)
    if a.play:
        click(btn["Play"])
        t0 = time.time()
        while time.time() - t0 < 10 and p.poll() is None:
            time.sleep(0.2)
        check(p.poll() == 0, "launcher exits after Play")
    else:
        p.kill()
    print("FAILED: %d" % len(fails) if fails else "ALL PASSED")
    return 1 if fails else 0


def cmd_setup(a):
    cfg = os.path.join(os.path.dirname(a.launcher), "mpr_launcher.ini")
    if os.path.exists(cfg):
        os.remove(cfg)
    p = subprocess.Popen([a.launcher, "--game", a.game, "--setup-args", a.setup_args])
    main = find_top("MprLauncherWindow")
    check(bool(main), "launcher window opens")
    time.sleep(1.0)
    status = [c for c in kids(main) if cls_of(c) == "Static" and ("game files" in text_of(c).lower() or "ready" in text_of(c).lower())]
    s0 = text_of(status[0]) if status else ""
    print("status:", s0)
    btn = {text_of(b): b for b in by_class(main, "Button")}
    if a.again:
        check(s0.startswith("Ready to play"), "finished folder says Ready to play")
        check("Run setup again..." in btn, "button reads Run setup again")
    else:
        check("No game files" in s0, "fresh folder says there are no game files")
        check(user32.IsWindowEnabled(btn["Play"]) == 0, "Play is disabled before setup")
    if a.shots:
        os.makedirs(a.shots, exist_ok=True)
        shot(main, os.path.join(a.shots, "launcher_fresh.png"))
    click(btn["Run setup again..." if a.again else "Set up game files..."])
    time.sleep(1.5)
    check(user32.IsWindowEnabled(btn["Play"]) == 0, "Play is disabled while setup runs")
    t0 = time.time()
    ready = False
    while time.time() - t0 < a.timeout:
        time.sleep(2)
        txt = [text_of(c) for c in kids(main) if cls_of(c) == "Static"]
        if any(t.startswith("Ready to play") for t in txt):
            ready = True
            break
    check(ready, "launcher shows Ready to play after setup (%.0f s)" % (time.time() - t0))
    btn = {text_of(b): b for b in by_class(main, "Button")}
    check(user32.IsWindowEnabled(btn["Play"]) != 0, "Play is enabled after setup")
    if a.shots and ready:
        shot(main, os.path.join(a.shots, "launcher_after_setup.png"))
    p.kill()
    print("FAILED: %d" % len(fails) if fails else "ALL PASSED")
    return 1 if fails else 0


ap = argparse.ArgumentParser()
ap.add_argument("mode", choices=["settings", "setup"])
ap.add_argument("--launcher", required=True)
ap.add_argument("--game", required=True)
ap.add_argument("--play", action="store_true")
ap.add_argument("--shots")
ap.add_argument("--setup-args", default="")
ap.add_argument("--timeout", type=int, default=900)
ap.add_argument("--again", action="store_true", help="setup mode on a folder that is already set up: press \"Run setup again...\" and wait (a repeat run only checks sizes)")
args = ap.parse_args()
try:
    rc = cmd_settings(args) if args.mode == "settings" else cmd_setup(args)
finally:
    subprocess.run(["taskkill", "/F", "/IM", os.path.basename(args.launcher)], capture_output=True)
sys.exit(rc)
