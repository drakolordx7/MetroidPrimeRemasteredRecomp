"""S25 live play driver. The game runs a scripted run in live mode (NXRT_TEST_LIVE): it executes the lines appended to live.nxs and, when it has
none left, waits (the game stands still) and writes live.nxs.status. This tool starts the game and sends lines.

  python live.py start [--exe DIR] [--run DIR] [--gfx headless|window] [--env K=V ...]   start the game (detached), steps: @rate 60
  python live.py send "line" "line" ...      append the lines, wait until the game has run them, print the status
  python live.py shot NAME [--view]          screenshot (written to RUN/shots/NAME.png after 4 frames), prints the path
  python live.py status                      print the last status
  python live.py stop                        @end the run (the game exits)
Lines are the script DSL of runtime/include/nxrt/tt_script.h (press A, stick left 0 1 for 60, mouse 10 0 for 30, wait 120, @run 3, ...).
"""
import json, math, os, subprocess, sys, time

ROOT = 'D:/AI/Active/Metroid-Prime'
RUN = os.environ.get('LIVE_RUN', ROOT + '/work/run_play2')
EXE = os.environ.get('LIVE_EXE', ROOT + '/game-build-play2/build/play2')
LIVE = RUN + '/live/live.nxs'


def count_lines(path):
    try:
        return open(path, 'rb').read().count(b'\n')
    except OSError:
        return 0


def status():
    try:
        return json.load(open(LIVE + '.status'))
    except (OSError, ValueError):
        return None


def regions():
    r = {}
    for line in open(ROOT + '/tools/test/regions.tsv', encoding='utf-8'):
        p = line.rstrip('\n').split('\t')
        if len(p) >= 3 and p[2]:
            r[p[2].lower()] = p[0]
    return r


def fmt(st):
    if st is None:
        return 'no status yet'
    a = regions().get(st['area'].lower(), st['area'][:8])
    return ('f=%d igt=%.1f area=%s hp=%.0f pos=(%.1f,%.1f,%.1f) yaw=%.2f pitch=%.2f vel=(%.1f,%.1f,%.1f) st=%d cam=%d morph=%d orbit=%d beam=%d visor=%d msl=%d %s' %
            (st['frame'], st['igt'], a, st['hp'], st['pos'][0], st['pos'][1], st['pos'][2], st['yaw'], st['pitch'], st['vel'][0], st['vel'][1], st['vel'][2],
             st['state'], st['cam'], st['morph'], st['orbit'], st['beam'], st['visor'], st['missiles'], '' if st['note'] in ('idle', 'ok') else '[' + st['note'] + ']'))


def start(argv):
    gfx, extra = 'headless', {'NXRT_SCHED_CONSOLE_CORES': os.environ.get('LIVE_PIN', 'false')}
    exe = EXE
    i = 0
    while i < len(argv):
        if argv[i] == '--gfx': gfx = argv[i + 1]; i += 2
        elif argv[i] == '--exe': exe = argv[i + 1]; i += 2
        elif argv[i] == '--env': k, v = argv[i + 1].split('=', 1); extra[k] = v; i += 2
        else: i += 1
    os.makedirs(RUN + '/live', exist_ok=True)
    cwd = RUN + '/cwd'
    os.makedirs(cwd, exist_ok=True)
    os.makedirs(RUN + '/shots', exist_ok=True)
    cache = os.path.join(cwd, 'bc7_cache')
    if not os.path.exists(cache):
        subprocess.run('mklink /J "%s" "%s"' % (os.path.normpath(cache), os.path.normpath(ROOT + '/work/run/bc7_cache')), shell=True, capture_output=True)
    for f in (LIVE, LIVE + '.status'):
        if os.path.exists(f): os.remove(f)
    open(LIVE, 'w').write('@timeout 0\n@rate 60\n')
    open(RUN + '/live/boot.nxs', 'w').write('@timeout 0\n')
    e = dict(os.environ)
    e.update(NXRT_TEST_SCRIPT=RUN + '/live/boot.nxs', NXRT_TEST_LIVE=LIVE, NXRT_TEST_OUT=RUN + '/out', NXRT_TEST_SHOT_DIR=RUN + '/shots',
             NXRT_TEST_REGIONS=ROOT + '/tools/test/regions.tsv', NXRT_BOOT_GFX=gfx, NXRT_FS_ROMFS=ROOT + '/game/romfs', NXRT_FS_SAVE_DIR=cwd + '/save',
             NXRT_TEST_WALL_TIMEOUT_S='86400', NXRT_TEST_FREEZE_EXIT='0', NXRT_TIME_MODE='real', NXRT_DIAG_WATCHDOG_SECONDS='0',
             NXRT_TEST_VTABLES=RUN + '/vtables.txt', NXRT_NVN_SHADER_CACHE=ROOT + '/work/shader_cache/spirv', NXRT_AUDIO_SINK=os.environ.get('NXRT_AUDIO_SINK', 'null'))
    if gfx == 'headless': e['NXRT_GFX_HEADLESS'] = '1'
    e.update(extra)
    import shutil
    bindir = RUN + '/bin'
    os.makedirs(bindir, exist_ok=True)
    for fn in os.listdir(exe):
        if fn.endswith(('.exe', '.dll', '.map')) and (fn == 'mpr.exe' or fn.endswith('.dll') or fn == 'mpr.map'):
            shutil.copy2(exe + '/' + fn, bindir + '/' + fn)
    exe = bindir
    log = open(RUN + '/live/mpr_stdout.log', 'w')
    p = subprocess.Popen([exe + '/mpr.exe', '--log', RUN + '/live/mpr.log'], cwd=cwd, env=e, stdout=log, stderr=log,
                         creationflags=0x00000008 | 0x00000200)      # DETACHED_PROCESS | NEW_PROCESS_GROUP
    open(RUN + '/live/pid', 'w').write(str(p.pid))
    print('started pid', p.pid)


def send(lines, timeout=100):
    before = count_lines(LIVE)
    with open(LIVE, 'a', newline='\n') as f:
        for ln in lines:
            f.write(ln.replace('\n', ' ') + '\n')
    want = before + len(lines)
    t0 = time.time()
    while time.time() - t0 < timeout:
        st = status()
        if st and st['lines'] >= want:
            return st
        time.sleep(0.05)
    st = status()
    if st: st = dict(st, note='BUSY: still running the lines (frame %d); use `wait` to keep waiting' % st['frame'])
    return st


def wrap(a):
    while a > math.pi: a -= 2 * math.pi
    while a < -math.pi: a += 2 * math.pi
    return a


def face(target, tol=0.03):
    st = status()
    for _ in range(12):
        d = wrap(target - st['yaw'])
        if abs(d) < tol: break
        mag = 1.0 if abs(d) > 0.5 else max(0.25, min(1.0, abs(d) / 0.5))
        frames = max(2, int(abs(d) / (2.5 * mag) * 60))
        st = send(['stick right %.3f 0 for %d' % (-mag if d > 0 else mag, frames), 'wait 3'])
    return st


EYE = 1.9
SENS = 0.000767945


def aim(x, y, z):
    # face the point (right stick for yaw) and set the pitch with mouse counts; returns the status
    st = status()
    st = face(math.atan2(x - st['pos'][0], z - st['pos'][2]), 0.01)
    hd = math.hypot(x - st['pos'][0], z - st['pos'][2])
    tp = math.atan2(y - (st['pos'][1] + EYE), hd)
    for _ in range(3):
        dy = int(round((st['pitch'] - tp) / SENS))
        if abs(dy) < 6: break
        st = send(['mouse 0 %d for 1' % dy, 'wait 6'])
    return st


def go(x, z, steps=60, tol=2.5):
    """goto with a player's habits: when blocked, jump forward, then side-step to one side and then the other (growing), then try again"""
    st = status()
    side = 1
    spread = 20
    for i in range(steps):
        dx, dz = x - st['pos'][0], z - st['pos'][2]
        dist = math.hypot(dx, dz)
        if dist < tol: break
        st = face(math.atan2(dx, dz), 0.08)
        p0 = (st['pos'][0], st['pos'][1], st['pos'][2])
        st = send(['stick left 0 1 for %d' % max(8, min(90, int(dist / 10.0 * 60))), 'wait 3'])
        moved = math.hypot(st['pos'][0] - p0[0], st['pos'][2] - p0[2])
        if moved > 2.0 and dist - math.hypot(x - st['pos'][0], z - st['pos'][2]) > 0.5: continue
        # blocked or sliding along a wall: jump forward
        st = send(['stick left 0 1', 'press B for 14', 'wait 50', 'stick left 0 0', 'wait 5'])
        if math.hypot(x - st['pos'][0], z - st['pos'][2]) < dist - 1.5: continue
        # side-step
        st = send(['stick left %d 0 for %d' % (side, spread), 'wait 3'])
        side = -side
        spread = min(90, spread + 8)
    return st


def goto(x, z, maxstep=240):
    st = status()
    for _ in range(40):
        dx, dz = x - st['pos'][0], z - st['pos'][2]
        dist = math.hypot(dx, dz)
        if dist < 1.5: break
        st = face(math.atan2(dx, dz), 0.05)
        p0 = (st['pos'][0], st['pos'][2])
        frames = max(6, min(maxstep, int((dist - 0.5) / 10.0 * 60)))
        st = send(['stick left 0 1 for %d' % frames, 'wait 3'])
        if math.hypot(st['pos'][0] - p0[0], st['pos'][2] - p0[1]) < 0.5:
            break            # not moving: a wall or a door
    return st


def look(name='look', nview=4):
    """nview views (every 360/nview degrees from the current heading) as one contact sheet; ends facing the start heading"""
    from PIL import Image
    y0 = status()['yaw']
    files = []
    for i in range(nview):
        face(wrap(y0 + i * 2 * math.pi / nview))
        nm = 'look%d' % i
        send(['@shot ' + nm, 'wait 4'])
        for _ in range(100):
            if os.path.exists(RUN + '/shots/' + nm + '.png') and os.path.getsize(RUN + '/shots/' + nm + '.png') > 1000: break
            time.sleep(0.1)
        time.sleep(0.2)
        files.append(RUN + '/shots/' + nm + '.png')
    face(y0)
    cols = 2 if nview <= 4 else 3
    tw = 640 if nview <= 4 else 480
    th = tw * 9 // 16
    ims = [Image.open(f).convert('RGB').resize((tw, th), Image.LANCZOS) for f in files]
    sh = Image.new('RGB', (tw * cols, th * ((nview + cols - 1) // cols)))
    for i, im in enumerate(ims): sh.paste(im, ((i % cols) * tw, (i // cols) * th))
    out = RUN + '/shots/' + name + '.jpg'
    sh.save(out, quality=78)
    for f in files: os.remove(f)
    return out


def main():
    a = sys.argv[1:]
    if not a: print(__doc__); return
    if a[0] == 'start': start(a[1:])
    elif a[0] == 'send':
        st = send(a[1:])
        print(fmt(st))
    elif a[0] == 'shot':
        name = a[1]
        p = RUN + '/shots/' + name + '.png'
        if os.path.exists(p): os.remove(p)
        st = send(['@shot ' + name, 'wait 4'])
        for _ in range(100):
            if os.path.exists(p) and os.path.getsize(p) > 1000: break
            time.sleep(0.1)
        sp = p[:-4] + '.s.jpg'
        try:
            from PIL import Image
            im = Image.open(p).convert('RGB')
            im.resize((960, int(960 * im.height / im.width)), Image.LANCZOS).save(sp, quality=80)
            p = sp
        except Exception:
            pass
        print(p, fmt(st))
    elif a[0] == 'newgame':        # title -> ... -> opening cutscene -> first control (Normal difficulty: A is mashed through every front-end screen)
        send(['@sleep 25000', '@mashuntil A every 300 until igt >= 1', '@area frigate_exterior_docking_hangar', '@run 112 soft'], 900)
        print(fmt(status()))
    elif a[0] == 'abort':          # drop the pending steps of a stuck wait
        open(LIVE + '.abort', 'w').write('x')
        time.sleep(1)
        print('abort requested')
    elif a[0] == 'look':
        print(look(a[1] if len(a) > 1 else 'look', int(a[2]) if len(a) > 2 else 4), fmt(status()))
    elif a[0] == 'objs':           # objs door dock pickup special ...: list live objects of those classes, nearest first, with the distance and the bearing (yaw to face it)
        vt = json.load(open(RUN + '/vtables.json'))
        short = ('door', 'dock', 'pickup', 'special', 'actor', 'platform', 'trigger', 'relay', 'player')
        toks, back = [], {}
        for t in a[1:]:
            if t in short: toks.append(t); continue
            hit = [k for k in vt if k == t or k == t + 'MP1' or k == 'C' + t + 'MP1' or k == 'CScript' + t + 'MP1']
            if not hit: hit = [k for k in vt if t.lower() in k.lower() and 'GOC' not in k and 'Ldr' not in k][:6]
            for k in hit:
                h = hex(vt[k]); toks.append(h); back[h] = k
        send(['@objs ' + ' '.join(toks)])
        st = status()
        rows = []
        for ln in open(RUN + '/out/objs.txt'):
            p_ = ln.split()
            if len(p_) < 5 or p_[1] == '-': continue
            x, y, z = float(p_[1]), float(p_[2]), float(p_[3])
            d = math.hypot(x - st['pos'][0], z - st['pos'][2])
            rows.append((d, back.get(p_[0], p_[0]), x, y, z, math.atan2(x - st['pos'][0], z - st['pos'][2])))
        rows.sort()
        print(fmt(st))
        for d, c, x, y, z, yaw in rows[:int(os.environ.get('N', '40'))]:
            print('%-8s (%.1f, %.1f, %.1f)  dist %.1f  yaw %.2f' % (c, x, y, z, d, yaw))
    elif a[0] == 'look':           # four views (every 90 degrees from the current heading), one contact sheet; ends facing the start heading
        st0 = status(); y0 = st0['yaw']; files = []
        nview = int(a[2]) if len(a) > 2 else 4
        for i in range(nview):
            face(wrap(y0 + i * 2 * math.pi / nview))
            nm = 'look%d' % i
            send(['@shot ' + nm, 'wait 4'])
            for _ in range(100):
                if os.path.exists(RUN + '/shots/' + nm + '.png') and os.path.getsize(RUN + '/shots/' + nm + '.png') > 1000: break
                time.sleep(0.1)
            time.sleep(0.2)
            files.append(RUN + '/shots/' + nm + '.png')
        face(y0)
        from PIL import Image
        cols = 2 if nview <= 4 else 3
        tw = 640 if nview <= 4 else 480
        th = tw * 9 // 16
        ims = [Image.open(f).convert('RGB').resize((tw, th), Image.LANCZOS) for f in files]
        sh = Image.new('RGB', (tw * cols, th * ((nview + cols - 1) // cols)))
        for i, im in enumerate(ims): sh.paste(im, ((i % cols) * tw, (i // cols) * th))
        out = RUN + '/shots/' + (a[1] if len(a) > 1 else 'look') + '.jpg'
        sh.save(out, quality=78)
        for f in files: os.remove(f)
        print(out, fmt(status()))
    elif a[0] == 'note':           # note TEXT [shotname]: append a timestamped line to route/route.md, copy the shot (full size png) to route/
        import shutil, datetime
        os.makedirs(RUN + '/route', exist_ok=True)
        st = status()
        line = '%s  f=%d igt=%.0f %s  %s' % (datetime.datetime.now().strftime('%H:%M:%S'), st['frame'], st['igt'], regions().get(st['area'].lower(), '?'), a[1])
        if len(a) > 2:
            src = RUN + '/shots/' + a[2] + '.png'
            if os.path.exists(src):
                shutil.copy2(src, RUN + '/route/' + a[2] + '.png'); line += '  [' + a[2] + '.png]'
        open(RUN + '/route/route.md', 'a').write(line + chr(10))
        print(line)
    elif a[0] == 'shoot':          # shoot X Y Z [n]: aim at the point, lock on (ZL) and fire n times
        x, y, z = float(a[1]), float(a[2]), float(a[3])
        n = int(a[4]) if len(a) > 4 else 1
        aim(x, y, z)
        cmds = ['hold ZL', 'wait 25']
        for _ in range(n): cmds += ['press ZR for 8', 'wait 25']
        cmds += ['release ZL', 'wait 15']
        print(fmt(send(cmds)))
    elif a[0] == 'aim':            # aim X Y Z: face the point, set the pitch
        print(fmt(aim(float(a[1]), float(a[2]), float(a[3]))))
    elif a[0] == 'face':           # face YAW (radians, + = left; forward = (sin yaw, 0, cos yaw))
        print(fmt(face(float(a[1]))))
    elif a[0] == 'turn':           # turn DEG (+ = left)
        st = status()
        print(fmt(face(st['yaw'] + math.radians(float(a[1])))))
    elif a[0] == 'go':
        print(fmt(go(float(a[1]), float(a[2]))))
    elif a[0] == 'goto':           # goto X Z [frames-limit]: face the point and walk to it (stops when within 1.5 units or stuck)
        print(fmt(goto(float(a[1]), float(a[2]))))
    elif a[0] == 'now':             # screenshot at once (express lane: works while a long step is running)
        name = a[1]
        p = RUN + '/shots/' + name + '.png'
        if os.path.exists(p): os.remove(p)
        open(LIVE + '.shot', 'w').write(name + chr(10))
        for _ in range(300):
            if os.path.exists(p) and os.path.getsize(p) > 1000: break
            time.sleep(0.1)
        time.sleep(0.3)
        try:
            from PIL import Image
            im = Image.open(p).convert('RGB')
            sp = p[:-4] + '.s.jpg'
            im.resize((960, int(960 * im.height / im.width)), Image.LANCZOS).save(sp, quality=80)
            p = sp
        except Exception as ex:
            print('(no preview: %s)' % ex)
        print(p)
    elif a[0] == 'wait':
        t0 = time.time()
        want = count_lines(LIVE)
        while time.time() - t0 < 100:
            st = status()
            if st and st['lines'] >= want: break
            time.sleep(0.1)
        print(fmt(status()))
    elif a[0] == 'status': print(fmt(status()))
    elif a[0] == 'stop': send(['@end'], 5)


if __name__ == '__main__':
    main()
