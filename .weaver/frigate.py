"""S26 room-to-room traversal on top of nav.py: find the dock that leads to the next area, walk to the door, open it with the beam, walk through.
  python frigate.py cross NEXT_AREA        from where the player stands: cross into NEXT_AREA (name from regions.tsv)
"""
import sys, os, math, json, time
sys.path.insert(0, 'D:/AI/Active/Metroid-Prime/.weaver')
import live as L, nav, survey, numpy as np

GN = None
import combat
TR = combat.Tracker()

def names():
    global GN
    if GN is None:
        GN = {}
        for line in open(L.ROOT + '/tools/test/regions.tsv', encoding='utf-8'):
            p = line.rstrip('\n').split('\t')
            if len(p) >= 3 and p[2] and not p[0].endswith('_start'): GN[p[0]] = p[2].lower()
    return GN

def area_name(st=None):
    st = st or L.status()
    inv = {v: k for k, v in names().items()}
    return inv.get(st['area'].lower(), st['area'])

def live_docks():
    L.send(['@objs dock'])
    return survey.parse_docks(L.RUN + '/out/objs.txt')

def dock_geom(d):
    p0, p1, p2 = [np.array(q) for q in d['plane']]
    # three corners of the door rectangle: p0 -> p1 along one edge, p1 -> p2 along the other
    c = p0 + (p1 - p0) / 2 + (p2 - p1) / 2
    n = np.cross(p1 - p0, p2 - p1)
    n[1] = 0.0
    n = n / (np.linalg.norm(n) + 1e-9)
    floor_y = min(p0[1], p1[1], p2[1])
    return c, n, floor_y

# route hints: waypoints (x, y, z) between the arrival and the exit door of a room, read off the room's height map (colmap.py) and the damage volumes. The planner and the
# straight-line fallback walk each leg. Only for rooms where the planner alone does not find a safe way.
HINTS = {
}

def apply_hazards(g, boxes, per_node=60.0):
    """damage volumes (combat.damage_triggers): every node inside one costs extra, so the planner crosses them by the shortest way only when it has to"""
    n = 0
    for i in range(len(g.nodes)):
        x, y, z = g.pos(i)
        for a, dmg, lo, hi, fl in boxes:
            if lo[0] - 0.3 <= x <= hi[0] + 0.3 and lo[2] - 0.3 <= z <= hi[2] + 0.3 and lo[1] - 3.0 <= y <= hi[1] + 0.5:
                g.penalty[i] = g.penalty.get(i, 0.0) + per_node * min(dmg * 20, 4.0); n += 1; break
    return n

def scan_around(st, goal=None, pad=20.0, step=1.0, half=110, hints=()):
    """scan the box around the player (and the goal when given, with a margin) and build the graph"""
    px, py, pz = st['pos']
    x0, x1, z0, z1 = px - half, px + half, pz - half, pz + half
    if goal is not None:
        xsx = [px, goal[0]] + [h[0] for h in hints]; zsz = [pz, goal[2]] + [h[2] for h in hints]
        x0, x1 = min(xsx) - pad, max(xsx) + pad
        z0, z1 = min(zsz) - pad, max(zsz) + pad
    xs, zs, fl = nav.scan(x0, z0, x1, z1, step)
    g = nav.Graph(xs, zs, fl, step)
    try:
        boxes = combat.damage_triggers()
        g.hazards = boxes
        if boxes: print('  %d damage volumes, %d nodes inside' % (len(boxes), apply_hazards(g, boxes)))
    except Exception as ex:
        print('  (no hazard list: %r)' % (ex,))
    return g

def cross(next_area, fire_tries=14, verbose=True):
    gn = names()
    st = L.status()
    here = area_name(st)
    target_guid = gn[next_area]
    docks = [d for d in live_docks() if d['area'].lower() == target_guid]
    if not docks:
        print('no dock to', next_area); return False
    px, py, pz = st['pos']
    docks.sort(key=lambda d: math.dist(d['pos'], (px, py, pz)))
    d = docks[0]
    c, n, fy = dock_geom(d)
    side = 1.0 if np.dot(np.array([px, py, pz]) - c, n) >= 0 else -1.0
    n = n * side                                   # now points from the door to the player's side
    if verbose: print('door of %s -> %s at (%.1f %.1f %.1f), normal (%.2f %.2f), floor %.2f' % (here, next_area, c[0], c[1], c[2], n[0], n[2], fy))
    stand0 = (c[0] + n[0] * 4.0, fy + 0.05, c[2] + n[2] * 4.0)
    hints = HINTS.get((here, next_area), [])
    g = scan_around(st, stand0, hints=hints)
    stand = (c[0] + n[0] * 4.0, fy + 0.05, c[2] + n[2] * 4.0)
    TR.scan()
    for wp in hints:
        if verbose: print('  hint leg to (%.1f %.1f %.1f)%s' % (wp[:3] + (' straight' if len(wp) == 4 else '',)))
        if len(wp) == 4: nav.greedy(wp[:3], tol=1.3, maxticks=25, hazards=g.hazards)      # straight through a hazard, no dithering
        else: nav.walk(g, wp, tol=1.8, tracker=TR, maxticks=300)
    if not nav.walk(g, stand, tol=1.2, tracker=TR): print('could not reach the door'); return False
    beyond2 = (c[0] - n[0] * 6.0, fy + 0.05, c[2] - n[2] * 6.0)

    def door_is_open():
        # the door object keeps its state in the low bits of the word at +1036 (CScriptDoorMP1::OpenDoor sets bits 1 and 2): open when both are set
        near = [f for a, p, f in combat.door_states() if math.dist(p, tuple(c)) < 3.0]
        return bool(near) and any((f & 6) == 6 for f in near)

    for attempt in range(fire_tries):
        st = L.status()
        if math.hypot(st['pos'][0] - stand[0], st['pos'][2] - stand[2]) > 3.0 or abs(st['pos'][1] - stand[1]) > 3.0:
            g = scan_around(st, stand, step=1.0)
            if not nav.walk(g, stand, tol=1.5, tracker=TR): print('could not get back to the door'); continue
        if not door_is_open():
            nav.fire_at(c[0], c[1], c[2], 1)
            L.send(['wait 80'])
        if not door_is_open():
            if verbose: print('  attempt %d: the door stays shut' % (attempt + 1))
            if attempt >= 1:
                L.send(['wait 400'])          # some scan targets wake up after a delay (the air lock panel, about 50 s after arrival)
                scan_all()
            continue
        g = scan_around(L.status(), beyond2, step=1.0)
        ok = nav.walk(g, beyond2, tol=1.5, maxticks=80, tracker=TR, maxstalls=3)
        L.send(['wait 60'])
        now = area_name()
        if verbose: print('  attempt %d: door open, walked through: %s, now in %s' % (attempt + 1, ok, now))
        if now == next_area or ok: break
    L.send(['wait 120'])
    now = area_name(L.status())
    if verbose: print('now in', now)
    return now == next_area

import rooms

POI = combat.Tracker(['CScriptPointOfInterestMP1'])

def scan_all(radius=30.0, verbose=True):
    """switch to the scan visor and scan every point of interest in reach (a door or a console that is waiting for a scan), then back to the combat visor"""
    st = L.status()
    POI.scan()
    seen = []
    for a, cls, p in POI.live():
        if math.dist((p[0], p[2]), (st['pos'][0], st['pos'][2])) > radius or abs(p[1] - st['pos'][1]) > 12: continue
        if any(math.dist(p, q) < 1.0 for q in seen): continue
        seen.append(p)
    seen.sort(key=lambda p: math.dist((p[0], p[2]), (st['pos'][0], st['pos'][2])))
    if verbose: print('  scanning %d points of interest' % len(seen))
    L.send(['press RIGHT for 6', 'wait 30'])
    for p in seen:
        st = L.status()
        me = st['pos']
        eye = (me[0], me[1] + 1.7, me[2])
        if math.dist((p[0], p[2]), (me[0], me[2])) > 6.0 or not combat.los_clear(eye, p):
            g = scan_around(st, p, pad=15.0, step=1.0)
            tgt = g.nearest(p[0], me[1], p[2], 10.0)
            if tgt is None: continue
            gx, gy, gz = g.pos(tgt)
            nav.walk(g, (gx, gy, gz), tol=3.0, maxticks=120, tracker=TR)
        combat.aim_at(p[0], p[1], p[2])
        L.send(['hold ZL', 'wait 170', 'release ZL', 'wait 8', 'press A for 6', 'wait 20'])
    L.send(['press UP for 6', 'wait 30'])

def run_to(world, target, avoid=(), maxrooms=40):
    """cross room after room along the shortest route to `target`; an edge that fails is avoided from then on"""
    sv = rooms.load(world)
    adj = rooms.edges(sv)
    bad = set(avoid)
    for _ in range(maxrooms):
        here = area_name()
        if here == target: print('arrived in', target); return True
        a2 = {u: {v: l for v, l in nb.items() if (u, v) not in bad} for u, nb in adj.items()}
        path = rooms.bfs(a2, here, target)
        if not path: print('no route from', here); return False
        nxt = path[1]
        print('== %s -> %s   (route: %s)' % (here, nxt, ' > '.join(p.replace(world + '_', '') for p in path)))
        sys.stdout.flush()
        ok = False
        try:
            ok = cross(nxt)
        except Exception as ex:
            print('cross raised', repr(ex))
        if not ok and area_name() == here:
            print('failed, avoiding', here, '->', nxt)
            bad.add((here, nxt))
    return False

if __name__ == '__main__':
    if sys.argv[1] == 'cross': print(cross(sys.argv[2]))
    elif sys.argv[1] == 'run': print(run_to(sys.argv[2], sys.argv[3], [tuple(x.split('>')) for x in sys.argv[4:]]))
