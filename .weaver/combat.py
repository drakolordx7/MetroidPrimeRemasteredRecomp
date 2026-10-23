"""S26 combat helper: find enemies with @objs, follow them with @peek, aim with mouse counts, fire. Used by nav.walk and the boss script."""
import sys, os, math, struct, json, time
sys.path.insert(0, 'D:/AI/Active/Metroid-Prime/.weaver')
import live as L
import nav

ENEMY_CLASSES = ['CSpacePirateMP1', 'CParasiteMP1', 'CBeetleMP1', 'CElitePirateMP1', 'CWallCrawlerMP1', 'CDroneMP1', 'CPufferMP1', 'CMetroidMP1',
                 'CNewIntroBossMP1', 'CIntroBossMP1', 'CGarBeetleMP1', 'CWallCrawlerSwarmMP1', 'COmegaPirateMP1', 'CMetroidBetaMP1']
_vt = None

def vtables():
    global _vt
    if _vt is None: _vt = json.load(open(L.RUN + '/vtables.json'))
    return _vt

def vptr_of(cls):
    return L_game_base() + vtables()[cls] + 16

_base = None
def L_game_base():
    global _base
    if _base is None: _base = 0x7100000000
    return _base

def peek(reqs):
    """reqs: list of (addr, length, [offsets]) -> list of bytes or None"""
    os.makedirs(nav.OUT, exist_ok=True)
    fi, fo = nav.OUT + '/peek_in.txt', nav.OUT + '/peek_out.txt'
    with open(fi, 'w') as f:
        for a, n, offs in reqs: f.write('%x %d %s\n' % (a, n, ' '.join(str(o) for o in offs)))
    if os.path.exists(fo): os.remove(fo)
    L.send(['@peek %s %s' % (fi, fo)], 120)
    out = []
    for ln in open(fo):
        ln = ln.strip()
        out.append(None if ln == '-' else bytes.fromhex(ln))
    return out

def obj_positions(addrs):
    r = peek([(a, 48, [8, 0x20, 0x40]) for a in addrs])
    out = []
    for b in r:
        if b is None: out.append(None); continue
        m = struct.unpack('<12f', b)
        out.append((m[3], m[7], m[11]) if all(math.isfinite(v) for v in (m[3], m[7], m[11])) else None)
    return out

def still_alive(addrs, vptrs):
    r = peek([(a, 8, []) for a in addrs])
    return [b is not None and struct.unpack('<Q', b)[0] == v for b, v in zip(r, vptrs)]

class Tracker:
    def __init__(self, classes=None):
        self.classes = classes or ENEMY_CLASSES
        self.cls_of = {}
        self.objs = {}            # addr -> (cls, vptr)
        self.last_scan = 0

    def scan(self):
        toks = [c for c in self.classes if c in vtables()]
        L.send(['@objs ' + ' '.join('0x%x' % vtables()[c] for c in toks)])
        back = {'0x%x' % vtables()[c]: c for c in toks}
        self.objs = {}
        for ln in open(L.RUN + '/out/objs.txt'):
            p = ln.split()
            if len(p) < 5: continue
            cls = back.get(p[0], p[0])
            addr = int(p[4], 16)
            self.objs[addr] = (cls, vptr_of(cls) if cls in vtables() else 0)
        self.last_scan = time.time()
        return self.objs

    def live(self):
        """[(addr, cls, (x,y,z))] of the tracked objects that are still alive and have a position"""
        if not self.objs: return []
        addrs = list(self.objs)
        alive = still_alive(addrs, [self.objs[a][1] for a in addrs])
        pos = obj_positions(addrs)
        return [(a, self.objs[a][0], p) for a, al, p in zip(addrs, alive, pos) if al and p is not None]

def los_clear(frm, to):
    dx, dy, dz = to[0] - frm[0], to[1] - frm[1], to[2] - frm[2]
    d = math.sqrt(dx * dx + dy * dy + dz * dz)
    if d < 0.5: return True
    r = nav.cast([(frm[0], frm[1], frm[2], dx / d, dy / d, dz / d, d)], 'los')
    return r[0][0] < 0.5 or r[0][1] > d - 0.8

def aim_at(x, y, z, eye=1.7):
    """turn and tilt towards the point with mouse counts (exact), one frame"""
    st = L.status()
    px, py, pz = st['pos']
    yaw = math.atan2(x - px, z - pz)
    hd = math.hypot(x - px, z - pz)
    pitch = math.atan2(y - (py + eye), hd)
    dxc = int(round(-nav.wrap(yaw - st['yaw']) / nav.MOUSE_YAW))
    dyc = int(round((st['pitch'] - pitch) / nav.MOUSE_YAW))
    if abs(dxc) > 1 or abs(dyc) > 1:
        return L.send(['mouse %d %d for 1' % (dxc, dyc), 'wait 1'])
    return st

def fight(tracker, radius=28.0, max_frames=3600, verbose=True, aim_height=1.3):
    """shoot every tracked enemy in range and with a clear line, nearest first, until none is left or the time is up. Returns the number of shots volleys fired."""
    t_end = L.status()['frame'] + max_frames
    volleys = 0
    miss = 0
    shots = tracker.__dict__.setdefault('shots', {})
    while L.status()['frame'] < t_end:
        st = L.status()
        me = st['pos']
        ens = tracker.live()
        cand = []
        for a, cls, p in ens:
            d = math.dist((me[0], me[2]), (p[0], p[2]))
            if shots.get(a, 0) < 12 and d <= radius and abs(p[1] - me[1]) < 14 and los_clear((me[0], me[1] + 1.7, me[2]), (p[0], p[1] + aim_height, p[2])):
                cand.append((d, a, cls, p))
        if not cand:
            miss += 1
            if miss >= 2: break
            L.send(['wait 8']); continue
        miss = 0
        cand.sort()
        d, a, cls, p = cand[0]
        aim_at(p[0], p[1] + aim_height, p[2])
        L.send(['press ZR for 4', 'wait 6', 'press ZR for 4', 'wait 6'])
        volleys += 1
        shots[a] = shots.get(a, 0) + 1
        if verbose and volleys % 5 == 1:
            s2 = L.status()
            print('  fight: %s at %.1f, hp %.0f' % (cls, d, s2['hp']))
    return volleys

def heal(hp=99.0):
    """development aid (@poke): set the player's health; the player state is at *(*(main + 0x459cc70) + 0x20), health at +0xc"""
    import struct
    os.makedirs(nav.OUT, exist_ok=True)
    fi = nav.OUT + '/poke_in.txt'
    open(fi, 'w').write('%x 0 0x20 +0xc : %s\n' % (L_game_base() + 0x459cc70, struct.pack('<f', hp).hex()))
    L.send(['@poke ' + fi, 'wait 2'])


def damage_triggers():
    """damage volumes of the loaded areas: CScriptTriggerMP1 objects whose damage info holds a damage value. Returns [(addr, damage, (x0,y0,z0), (x1,y1,z1), flags)] in world space.
    Layout from CScriptTriggerMP1::CScriptTriggerMP1: damage info at +528 (weapon type, damage, ...), flags +592, local bounds +596..+619, transform via the usual chain."""
    tr = Tracker(['CScriptTriggerMP1'])
    objs = tr.scan()
    addrs = list(objs)
    if not addrs: return []
    info = peek([(a + 528, 64, []) for a in addrs])
    flg = peek([(a + 592, 4, []) for a in addrs])
    bnd = peek([(a + 596, 24, []) for a in addrs])
    pos = obj_positions(addrs)
    out = []
    for a, i, f, b, p in zip(addrs, info, flg, bnd, pos):
        if i is None or b is None or p is None: continue
        w, dmg = struct.unpack('<If', i[:8])
        if not (0.0 < dmg < 1000.0) or not math.isfinite(dmg): continue
        bb = struct.unpack('<6f', b)
        if not all(math.isfinite(v) for v in bb): continue
        out.append((a, dmg, (p[0] + bb[0], p[1] + bb[1], p[2] + bb[2]), (p[0] + bb[3], p[1] + bb[4], p[2] + bb[5]), struct.unpack('<I', f)[0] if f else 0))
    return out


def force_triggers():
    """CScriptTriggerMP1 objects with a force vector (wind): [(addr, force(x,y,z), magnitude, lo, hi, flags, active)]"""
    tr = Tracker(['CScriptTriggerMP1'])
    objs = tr.scan()
    addrs = list(objs)
    if not addrs: return []
    f = peek([(a + 576, 16, []) for a in addrs])
    flg = peek([(a + 592, 4, []) for a in addrs])
    bnd = peek([(a + 596, 24, []) for a in addrs])
    pos = obj_positions(addrs)
    act = peek([(a + 0x1fc, 8, []) for a in addrs])        # unknown: raw bytes near the active flags, kept for inspection
    out = []
    for a, fb, fl, b, p, ac in zip(addrs, f, flg, bnd, pos, act):
        if fb is None or b is None or p is None: continue
        fx, fy, fz, mag = struct.unpack('<4f', fb)
        if not all(math.isfinite(v) for v in (fx, fy, fz, mag)) or mag < 0.01: continue
        bb = struct.unpack('<6f', b)
        out.append((a, (fx, fy, fz), mag, (p[0] + bb[0], p[1] + bb[1], p[2] + bb[2]), (p[0] + bb[3], p[1] + bb[4], p[2] + bb[5]), struct.unpack('<I', fl)[0], ac.hex() if ac else ''))
    return out


def door_states():
    """CScriptDoorMP1 objects: [(addr, (x,y,z), flags)] with the flag word at +1036 (0x80 = locked; bits 1-2 = state; 6 = open, see CScriptDoorMP1::OpenDoor)"""
    tr = Tracker(['CScriptDoorMP1'])
    objs = tr.scan()
    addrs = list(objs)
    if not addrs: return []
    pos = obj_positions(addrs)
    fl = peek([(a + 1036, 2, []) for a in addrs])
    out = []
    for a, p, f in zip(addrs, pos, fl):
        if p is None or f is None: continue
        out.append((a, p, struct.unpack('<H', f)[0]))
    return out
