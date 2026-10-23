"""S26 navigation: read the walkable geometry of the loaded areas with the game's own static ray cast (`@rays`), plan a path with A*, walk it.
Uses live.py (the file-driven live script mode). Nothing here reads a game file.

  python nav.py scan X0 Z0 X1 Z1 [STEP]          scan the box, write RUN/out/nav_scan.npz and a top-down PNG RUN/shots/nav_scan.png
  python nav.py path X Z [Y]                     plan from the player to (X, Z) on the last scan, print the path
  python nav.py walk X Z [Y]                     plan and walk (replans when stuck)
"""
import json, math, os, sys, time, heapq
import numpy as np
sys.path.insert(0, 'D:/AI/Active/Metroid-Prime/.weaver')
import live as L

RUN = L.RUN
OUT = RUN + '/out'

# ---- the player's abilities (measured, see docs/S26.md) ----
WALK_UP = 0.45       # (unused now) a step up that needs no jump
WALK_SLOPE = 1.0     # steepest slope walked: rise over run between two neighbouring floor nodes
JUMP_UP = 3.0        # the highest ledge a jump reaches (apex +3.5, measured with .weaver/jtest.py)
JUMP_V, JUMP_G, WALK_SPEED = 14.8, 28.0, 6.8      # take-off speed, gravity, walking speed (units/s); the apex is 3.5 and the air time on level ground 1.06 s
JUMP_REACH = 7.0     # horizontal reach of a jump on level ground
MOUSE_YAW = 0.000768  # radians per mouse count (positive counts turn right, lower yaw)


def jump_reach(dy):
    """horizontal distance covered in the air before the player is at height dy (negative = lower) on the way down, with a 20% margin"""
    disc = JUMP_V * JUMP_V - 2 * JUMP_G * dy
    if disc < 0: return 0.0
    return 0.8 * WALK_SPEED * (JUMP_V + math.sqrt(disc)) / JUMP_G
FALL_MAX = 12.0      # drops we accept
USE_PROBE = os.environ.get('NAVRAYS') is None       # validate edges with the player's collision box (@probe); NAVRAYS=1: the older ray checks
CLEAR = 2.3          # head room needed to stand
WALKABLE_NY = 0.62   # floor if the surface normal's y is at least this


def cast(rays, name='rays'):
    """rays: list of (x,y,z,dx,dy,dz,len). Returns an (n,8) float array: hit t px py pz nx ny nz"""
    os.makedirs(OUT, exist_ok=True)
    fi, fo = OUT + '/%s_in.txt' % name, OUT + '/%s_out.txt' % name
    with open(fi, 'w') as f:
        f.write(''.join('%.4f %.4f %.4f %.5f %.5f %.5f %.3f\n' % r for r in rays))
    if os.path.exists(fo): os.remove(fo)
    st = L.send(['@rays %s %s' % (fi, fo)], 600)
    return np.loadtxt(fo, ndmin=2) if len(rays) else np.zeros((0, 8))


def scan(x0, z0, x1, z1, step=0.5, ytop=None, ybot=None, maxrounds=10):
    st = L.status()
    py = st['pos'][1]
    ytop = py + 40 if ytop is None else ytop
    ybot = py - 60 if ybot is None else ybot
    xs = np.arange(x0, x1 + 1e-6, step)
    zs = np.arange(z0, z1 + 1e-6, step)
    nx, nz = len(xs), len(zs)
    print('scan %dx%d columns' % (nx, nz))
    ix, iz = np.meshgrid(np.arange(nx), np.arange(nz), indexing='ij')
    ix, iz = ix.ravel(), iz.ravel()
    ystart = np.full(len(ix), ytop)
    floors = []          # (ix, iz, y, ny)
    t0 = time.time()
    for rd in range(maxrounds):
        if len(ix) == 0: break
        rays = [(xs[a], y, zs[b], 0, -1, 0, y - ybot) for a, b, y in zip(ix, iz, ystart)]
        r = cast(rays)
        hit = r[:, 0] > 0.5
        for a, b, p, nn in zip(ix[hit], iz[hit], r[hit, 3], r[hit, 6]):
            if nn >= WALKABLE_NY: floors.append((a, b, p, nn))
        ix, iz, ystart = ix[hit], iz[hit], r[hit, 3] - 0.04
        print(' round %d: %d rays, %d hits, %.1fs' % (rd, len(rays), hit.sum(), time.time() - t0))
    fl = np.array(floors) if floors else np.zeros((0, 4))
    # head room: a ray up from each floor
    rays = [(xs[int(a)], y + 0.05, zs[int(b)], 0, 1, 0, 6.0) for a, b, y, _ in fl]
    r = cast(rays, 'rays_up')
    clear = np.where(r[:, 0] > 0.5, r[:, 1] + 0.05, 6.0)
    fl = np.column_stack([fl, clear])
    np.savez(OUT + '/nav_scan.npz', xs=xs, zs=zs, floors=fl, step=step)
    print('floors: %d (clear enough: %d), %.1fs' % (len(fl), (clear >= CLEAR).sum(), time.time() - t0))
    return xs, zs, fl


def load():
    d = np.load(OUT + '/nav_scan.npz')
    return d['xs'], d['zs'], d['floors'], float(d['step'])


def topdown_png(xs, zs, fl, marks=(), path=None, out=None, scale=4):
    from PIL import Image, ImageDraw
    nx, nz = len(xs), len(zs)
    h = np.full((nx, nz), np.nan)
    for a, b, y, ny, c in fl:
        if c >= CLEAR:
            a, b = int(a), int(b)
            if np.isnan(h[a, b]) or y > h[a, b]: h[a, b] = y
    lo, hi = np.nanmin(h), np.nanmax(h)
    img = np.zeros((nz, nx, 3), np.uint8)
    for a in range(nx):
        for b in range(nz):
            if not np.isnan(h[a, b]):
                v = int(40 + 215 * (h[a, b] - lo) / max(hi - lo, 1e-6))
                img[nz - 1 - b, a] = (v, v, v)
    im = Image.fromarray(img).resize((nx * scale, nz * scale), Image.NEAREST)
    d = ImageDraw.Draw(im)
    def px(x, z): return ((x - xs[0]) / (xs[1] - xs[0]) * scale, (zs[-1] - z) / (zs[1] - zs[0]) * scale)
    if path:
        d.line([px(p[0], p[2]) for p in path], fill=(255, 60, 60), width=2)
    for name, x, z in marks:
        p = px(x, z)
        d.ellipse([p[0] - 4, p[1] - 4, p[0] + 4, p[1] + 4], outline=(60, 200, 255))
        d.text((p[0] + 6, p[1] - 5), name, fill=(60, 200, 255))
    out = out or RUN + '/shots/nav_scan.png'
    im.save(out)
    return out



class Graph:
    """walkable nodes from a scan; edges are made on demand (walk / drop / jump)"""
    def __init__(self, xs, zs, fl, step):
        self.xs, self.zs, self.step = xs, zs, step
        self.nodes = [(int(a), int(b), float(y)) for a, b, y, ny, c in fl if c >= CLEAR]
        self.cell = {}
        for i, (a, b, y) in enumerate(self.nodes): self.cell.setdefault((a, b), []).append(i)
        for k in self.cell: self.cell[k].sort(key=lambda i: self.nodes[i][2])
        self.bad = set()                      # (i, j) edges that failed in play
        self.hazards = []                     # damage volumes (combat.damage_triggers)
        self.penalty = {}                     # node -> extra cost (hazards learned from health loss)
        self.blocked = set()                  # nodes blocked by something the static scan cannot see (crates, doors)
        self.edge_cache = {}

    def pos(self, i):
        a, b, y = self.nodes[i]
        return (float(self.xs[a]), y, float(self.zs[b]))

    def nearest(self, x, y, z, maxd=3.0):
        a = int(round((x - self.xs[0]) / self.step)); b = int(round((z - self.zs[0]) / self.step))
        best, bd = None, 1e9
        r = int(maxd / self.step) + 1
        for da in range(-r, r + 1):
            for db in range(-r, r + 1):
                for i in self.cell.get((a + da, b + db), ()):
                    px, py, pz = self.pos(i)
                    d = math.hypot(px - x, pz - z) + 1.5 * abs(py - y)
                    if d < bd: best, bd = i, d
        return best

    def penalize(self, x, z, y, r, amount):
        n = 0
        for i in range(len(self.nodes)):
            px, py, pz = self.pos(i)
            if abs(px - x) <= r and abs(pz - z) <= r and abs(py - y) < 3.0:
                self.penalty[i] = self.penalty.get(i, 0.0) + amount; n += 1
        return n

    def block_near(self, x, z, y, r=1.1):
        n = 0
        for i in range(len(self.nodes)):
            px, py, pz = self.pos(i)
            if abs(px - x) <= r and abs(pz - z) <= r and abs(py - y) < 2.0:
                self.blocked.add(i); n += 1
        return n

    def save_blocked(self, tag):
        json.dump([list(self.pos(i)) for i in self.blocked], open(OUT + '/blocked_%s.json' % tag, 'w'))

    def load_blocked(self, tag):
        try:
            for x, y, z in json.load(open(OUT + '/blocked_%s.json' % tag)):
                i = self.nearest(x, y, z, 0.3)
                if i is not None: self.blocked.add(i)
        except OSError:
            pass

    def edges(self, i):
        if i in self.edge_cache: return self.edge_cache[i]
        a, b, y = self.nodes[i]
        out = []
        full = 0
        have = set()                              # directions in which the next cell has a floor to walk or drop to
        for da in (-1, 0, 1):
            for db in (-1, 0, 1):
                if da == 0 and db == 0: continue
                d = math.hypot(da, db) * self.step
                best = None
                for j in self.cell.get((a + da, b + db), ()):
                    dy = self.nodes[j][2] - y
                    if -FALL_MAX <= dy <= WALK_SLOPE * d and (best is None or dy > self.nodes[best][2] - y): best = j
                if best is not None:
                    have.add((da, db))
                    dy = self.nodes[best][2] - y
                    if dy >= -WALK_SLOPE * d: out.append((best, d + abs(dy) * 0.5, 'walk')); full += 1
                    else:
                        out.append((best, d + 3 + abs(dy) * 0.4, 'drop'))
                        out.append((best, d + 6 + abs(dy) * 0.4, 'jump'))        # a hop over a rail at the edge, then the fall
        if full < 8:      # an edge node: look for jump targets
            r = int(JUMP_REACH / self.step)
            for da in range(-r, r + 1):
                for db in range(-r, r + 1):
                    d = math.hypot(da, db) * self.step
                    if d < 1.2 or d > JUMP_REACH: continue
                    for j in self.cell.get((a + da, b + db), ()):
                        dy = self.nodes[j][2] - y
                        if dy > JUMP_UP or dy < -FALL_MAX: continue            # (a hop down is validated by a level ray over the edge and a vertical ray down the landing column)
                        if abs(da) <= 1 and abs(db) <= 1: continue
                        m = max(abs(da), abs(db))
                        if (int(round(da / m)), int(round(db / m))) in have: continue      # the floor goes on that way: walk, do not jump
                        if d > jump_reach(dy): continue
                        out.append((j, d * 1.6 + 6 + max(dy, 0) * 2, 'jump'))
        self.edge_cache[i] = out
        return out

    def astar(self, s, g):
        gx, gy, gz = self.pos(g)
        openq = [(0.0, s)]
        cost = {s: 0.0}
        prev = {}
        while openq:
            _, i = heapq.heappop(openq)
            if i == g: break
            for j, c, t in self.edges(i):
                if (i, j) in self.bad or j in self.blocked: continue
                nc = cost[i] + c + self.penalty.get(j, 0.0)
                if nc < cost.get(j, 1e18):
                    cost[j] = nc; prev[j] = (i, t)
                    px, py, pz = self.pos(j)
                    heapq.heappush(openq, (nc + math.hypot(px - gx, pz - gz), j))
        if g not in prev and g != s: return None
        seq = [g]
        arrive = {}
        while seq[-1] != s:
            i, t = prev[seq[-1]]
            arrive[seq[-1]] = t
            seq.append(i)
        seq.reverse()
        # entry k = (position of node k, type of the edge that arrives at it); the first is 'start'
        return [(self.pos(n), arrive.get(n, 'start')) for n in seq]


def wrap(a):
    while a > math.pi: a -= 2 * math.pi
    while a < -math.pi: a += 2 * math.pi
    return a


def level():
    """set the view pitch to 0 (positive mouse counts look down)"""
    st = L.status()
    c = int(round(st['pitch'] / MOUSE_YAW))
    if abs(c) > 3: st = L.send(['mouse 0 %d for 1' % c, 'wait 2'])
    return st


def fire_at(x, y, z, n=2):
    """aim at the point (no lock-on) and fire n shots"""
    L.aim(x, y, z)
    cmds = []
    for _ in range(n): cmds += ['press ZR for 6', 'wait 18']
    return L.send(cmds)


def turn_to(yaw):
    st = L.status()
    d = wrap(yaw - st['yaw'])
    counts = int(round(-d / MOUSE_YAW))
    if abs(counts) < 2: return st
    return L.send(['mouse %d 0 for 1' % counts, 'wait 1'])


def probe(points):
    """the player's own collision box against the static world (@probe): True where it collides. points: [(x, y, z)] with the player's origin (feet)."""
    if not points: return []
    os.makedirs(OUT, exist_ok=True)
    fi, fo = OUT + '/probe_in.txt', OUT + '/probe_out.txt'
    with open(fi, 'w') as f: f.write(''.join('%.3f %.3f %.3f\n' % p for p in points))
    if os.path.exists(fo): os.remove(fo)
    L.send(['@probe %s %s' % (fi, fo)], 600)
    return [ln.strip() == '1' for ln in open(fo)]


STEP_UP = 0.4        # a lip this high does not stop the player (feet lifted by this much when probing)


def jump_arcs(dy, d):
    """possible jumps over horizontal distance d to a target dy above the take-off (negative = below): the player presses B, rises for tau seconds in place, then
    runs. Returns [(tau, samples)] with samples = [(horizontal distance, height)] along the arc, best first. tau 0 = run and jump at once."""
    out = []
    for tau in (0.0, 0.1, 0.2, 0.3, 0.4):
        tf = tau + d / WALK_SPEED
        y = JUMP_V * tf - 0.5 * JUMP_G * tf * tf
        if y < dy - 0.1: continue                                      # still below the target when it arrives
        if dy > 0.3 and tf < JUMP_V / JUMP_G: continue                 # a ledge is reached on the way down
        samples = []
        t = 0.0
        while t < tf:
            yy = JUMP_V * t - 0.5 * JUMP_G * t * t
            samples.append((max(0.0, (t - tau) * WALK_SPEED), yy))
            t += 0.05
        samples.append((d, max(dy, y if y > dy else dy)))
        out.append((tau, samples))
    return out


def validate_capsule(g, path, kinds=('walk', 'drop', 'jump'), spacing=0.35):
    """edges of a path tested with the player's real collision box (@probe). walk: samples along the edge, also lifted by the step height; drop: level, then down;
    jump: along the physical arcs of jump_arcs (the first free one is kept in g.jump_tau). Returns the indices of the bad edges."""
    if not hasattr(g, 'jump_tau'): g.jump_tau = {}
    pts, owner = [], []          # owner entries: (edge, variant, group)
    for k in range(len(path) - 1):
        (x0, y0, z0), _ = path[k]
        (x1, y1, z1), t = path[k + 1]
        if t not in kinds: continue
        d = math.hypot(x1 - x0, z1 - z0)
        ux, uz = ((x1 - x0) / d, (z1 - z0) / d) if d > 1e-6 else (0.0, 0.0)
        if t == 'jump':
            arcs = jump_arcs(y1 - y0, d)
            if not arcs:
                pts.append((x0, y0 - 50.0, z0)); owner.append((k, 'x', 0))      # infeasible: never free (a point inside the floor)
                continue
            for gi, (tau, samples) in enumerate(arcs[:4]):
                for h, yy in samples:
                    pts.append((x0 + ux * h, y0 + yy + 0.06, z0 + uz * h)); owner.append((k, 'j', gi))
        else:
            n = max(2, int(d / spacing) + 1)
            for i in range(n + 1):
                u = i / n
                y = y0 + (y1 - y0) * u if t == 'walk' else (y0 if u < 0.5 else y0 + (y1 - y0) * (u - 0.5) * 2)
                x, z = x0 + (x1 - x0) * u, z0 + (z1 - z0) * u
                pts.append((x, y + 0.06, z)); owner.append((k, 'w', i))
                if t == 'walk': pts.append((x, y + 0.06 + STEP_UP, z)); owner.append((k, 'l', i))
    r = probe(pts)
    bad = set()
    byedge = {}
    for (k, kind, gi), hit in zip(owner, r):
        byedge.setdefault(k, []).append((kind, gi, hit))
    for k, items in byedge.items():
        kinds_here = set(i[0] for i in items)
        if 'j' in kinds_here:
            groups = {}
            for kind, gi, hit in items:
                if kind == 'j': groups[gi] = groups.get(gi, False) or hit
            freeg = [gi for gi, h in groups.items() if not h]
            if not freeg: bad.add(k); continue
            (x0, y0, z0), _ = path[k]; (x1, y1, z1), _ = path[k + 1]
            arcs = jump_arcs(y1 - y0, math.hypot(x1 - x0, z1 - z0))
            g.jump_tau[(round(x0, 1), round(z0, 1), round(x1, 1), round(z1, 1))] = arcs[freeg[0]][0]
        elif 'x' in kinds_here:
            bad.add(k)
        else:
            # walk samples: the sample passes when the box is free at the floor or lifted; consecutive (w, l) pairs share the index i
            by_i = {}
            for kind, gi, hit in items: by_i.setdefault(gi, {})[kind] = hit
            for gi, d_ in by_i.items():
                if d_.get('w', False) and d_.get('l', True): bad.add(k); break
    return sorted(bad)


def validate(g, path, kinds=('walk', 'drop', 'jump')):
    """cast rays along the path edges; returns the indices of the first bad edge or None. walk: waist and head height; jump: line at +1.2"""
    rays, owner = [], []
    for k in range(len(path) - 1):
        (x0, y0, z0), _ = path[k]
        (x1, y1, z1), t = path[k + 1]
        dx, dz = x1 - x0, z1 - z0
        d = math.hypot(dx, dz)
        if d < 1e-3 or t not in kinds: continue
        if t == 'drop' or (t == 'jump' and y1 < y0 - 0.5):
            hh = 0.8 if t == 'drop' else 1.9          # a hop clears a rail up to about 1.5
            # walk off the edge, then fall: a level ray over the edge at waist height and a vertical ray down the landing column
            rays.append((x0, y0 + hh, z0, dx / d, 0.0, dz / d, d + 0.3)); owner.append(k)
            if y0 + hh - (y1 + 0.3) > 0.5:
                rays.append((x1, y0 + hh, z1, 0.0, -1.0, 0.0, y0 + hh - (y1 + 0.3))); owner.append(k)
            continue
        hs = (0.45, 1.0, 1.6) if t == 'walk' else ((0.8,) if t == 'drop' else (max(y0, y1) + 1.6 - y0,))
        for h in hs:
            # the ray follows the floor from this node to the next (a slope must not hit itself); a little longer than the edge
            dy = (y1 - y0) if t != 'jump' else (y1 + h - (y0 + h))
            dl = math.sqrt(d * d + dy * dy)
            ex = 0.3 / dl
            rays.append((x0, y0 + h, z0, dx / dl, dy / dl, dz / dl, dl + 0.3))
            owner.append(k)
    if not rays: return []
    r = cast(rays, 'rays_val')
    return sorted(set(k for k, row in zip(owner, r) if row[0] > 0.5))


def plan(g, st, goal_xyz, maxtries=60, goal_tol=1.5, kinds=None):
    kinds = kinds or (('walk', 'drop', 'jump') if USE_PROBE else ('jump',))
    s = g.nearest(st['pos'][0], st['pos'][1], st['pos'][2], 3.0)
    t = g.nearest(goal_xyz[0], goal_xyz[1], goal_xyz[2], goal_tol + 1)
    if s is None or t is None: return None
    for _ in range(maxtries):
        path = g.astar(s, t)
        if path is None: return None
        bad = validate_capsule(g, path, kinds) if USE_PROBE else validate(g, path, kinds)
        if not bad: return path
        for k in bad:
            a = g.nearest(*path[k][0], 0.3); b = g.nearest(*path[k + 1][0], 0.3)
            g.bad.add((a, b)); g.bad.add((b, a))
        print('  blocked %d edge(s), first %s -> %s (%s)' % (len(bad), tuple(round(v, 1) for v in path[bad[0]][0]), tuple(round(v, 1) for v in path[bad[0] + 1][0]), path[bad[0] + 1][1]))
    return None


def in_hazard(g, pos):
    for a, dmg, lo, hi, fl in getattr(g, 'hazards', []):
        if lo[0] - 0.2 <= pos[0] <= hi[0] + 0.2 and lo[2] - 0.2 <= pos[2] <= hi[2] + 0.2 and lo[1] - 1.5 <= pos[1] <= hi[1] + 0.5: return True
    return False


def greedy(goal_xyz, tol=1.5, maxticks=80, verbose=True, hazards=None):
    """no plan: head for the goal, and when stuck feel along the obstacle (strafe either way, then forward). The way a person finds a gap in a wall."""
    stall = 0
    for t in range(maxticks):
        st = L.status()
        px, py, pz = st['pos']
        d = math.hypot(goal_xyz[0] - px, goal_xyz[2] - pz)
        if d < tol: return True
        turn_to(math.atan2(goal_xyz[0] - px, goal_xyz[2] - pz))
        st2 = L.send(['stick left 0 1 for %d' % max(6, min(30, int(d / WALK_SPEED * 60))), 'wait 1'])
        moved = math.hypot(st2['pos'][0] - px, st2['pos'][2] - pz)
        stall = stall + 1 if moved < 0.4 else 0
        if stall >= 2 and hazards is not None and in_hazard(type('G', (), {'hazards': hazards})(), st2['pos']):
            L.send(['stick left 0 1', 'press B for 6', 'wait 30', 'stick left 0 0'])      # in the fire: no feeling about, hop forward
            stall = 0; continue
        if stall >= 2:
            hx, hz = math.sin(st2['yaw']), math.cos(st2['yaw'])
            got = False
            for off in (-1, 1, -2, 2, -3, 3, -4.5, 4.5):
                q0 = L.status()['pos']
                L.send(['stick left %d 0 for %d' % (1 if off > 0 else -1, int(abs(off) / WALK_SPEED * 60) + 2), 'wait 2', 'stick left 0 1 for 22', 'wait 2'])
                q1 = L.status()['pos']
                if (q1[0] - q0[0]) * hx + (q1[2] - q0[2]) * hz > 1.2: got = True; break
            if not got:
                L.send(['stick left 0 1', 'press B for 6', 'wait 40', 'stick left 0 0', 'wait 5'])
            stall = 0
    return False


def walk(g, goal_xyz, tol=1.2, maxticks=900, verbose=True, tracker=None, maxstalls=12):
    """walk the player to the goal; replans after a stall. Returns True when within tol."""
    st = L.status()
    path = plan(g, st, goal_xyz)
    if path is None:
        print('no path: going straight for it'); return greedy(goal_xyz, tol=tol)
    k = 0                     # index of the next node
    stall = 0
    ticks = 0
    last = None
    replans = 0
    while ticks < maxticks:
        ticks += 1
        st = L.status()
        px, py, pz = st['pos']
        gx, gy, gz = goal_xyz
        if math.hypot(gx - px, gz - pz) < tol and abs(gy - py) < 2.0: return True
        fought = False
        if tracker is not None and ticks % 2 == 0:
            import combat
            near = [e for e in tracker.live() if math.dist((px, pz), (e[2][0], e[2][2])) < 16 and abs(e[2][1] - py) < 10 and combat.los_clear((px, py + 1.7, pz), (e[2][0], e[2][1] + 1.3, e[2][2]))]
            if near:
                if verbose: print('  enemies near (%s): fighting' % ', '.join('%s %.0f' % (e[1], math.dist((px, pz), (e[2][0], e[2][2]))) for e in near[:3]))
                combat.fight(tracker, max_frames=1500); fought = True
                st = L.status(); px, py, pz = st['pos']
        # progress along the path: the node closest to the player (window around k) tells how far we are; the next target is the one after it
        lo, hi = max(0, k - 3), min(len(path), k + 80)
        qi = min(range(lo, hi), key=lambda m: math.hypot(path[m][0][0] - px, path[m][0][2] - pz) + 2.0 * abs(path[m][0][1] - py))
        dq = math.hypot(path[qi][0][0] - px, path[qi][0][2] - pz)
        if dq < 2.5 and abs(path[qi][0][1] - py) < 2.0 and qi + 1 > k: k = min(qi + 1, len(path) - 1)
        if k < len(path) - 1 and math.hypot(path[k][0][0] - px, path[k][0][2] - pz) < 0.9: k += 1
        (nx, ny, nz), nt = path[k]
        if os.environ.get('NAVDEBUG'): print('   tick %d pos (%.1f %.1f %.1f) k=%d/%d next (%.1f %.1f %.1f) %s' % (ticks, px, py, pz, k, len(path), nx, ny, nz, nt))
        if k < len(path) - 1 and math.hypot(nx - px, nz - pz) < 0.9: k += 1; (nx, ny, nz), nt = path[k]
        if nt == 'jump' and k > 0 and math.hypot(path[k - 1][0][0] - px, path[k - 1][0][2] - pz) > 1.0:
            tx, ty2, tz = path[k - 1][0]           # first walk to the take-off node
            q = None
        elif nt == 'jump':
            # we are at the take-off node (the previous one): face the landing and jump
            tx, ty, tz = nx, ny, nz
            turn_to(math.atan2(tx - px, tz - pz))
            d = math.hypot(tx - px, tz - pz)
            key = (round(path[k - 1][0][0], 1), round(path[k - 1][0][2], 1), round(tx, 1), round(tz, 1)) if k > 0 else None
            tau = getattr(g, 'jump_tau', {}).get(key, 0.0)
            if tau > 0.01: st = L.send(['press B for 6', 'wait %d' % int(tau * 60), 'stick left 0 1'])        # rise first, then run: clears a rail at the edge
            else: st = L.send(['stick left 0 1', 'wait 6', 'press B for 6'])
            n = 0
            while n < 40:
                st = L.send(['wait 4']); n += 1
                if math.hypot(tx - st['pos'][0], tz - st['pos'][2]) < 1.5 and abs(ty - st['pos'][1]) < 1.0 and abs(st['vel'][1]) < 0.5: break
                if n > 8 and st['vel'][1] == 0 and st['state'] == 0: break
            L.send(['stick left 0 0', 'wait 6'])
            st = L.status()
            ok = math.hypot(tx - st['pos'][0], tz - st['pos'][2]) < 2.2 and abs(ty - st['pos'][1]) < 1.5
            if verbose: print('  jump to (%.1f %.1f %.1f): %s now (%.1f %.1f %.1f)' % (tx, ty, tz, 'ok' if ok else 'MISSED', *st['pos']))
            if not ok:
                a = g.nearest(px, py, pz, 1.5); b = g.nearest(tx, ty, tz, 1.0)
                g.bad.add((a, b))
                path = plan(g, st, goal_xyz)
                if path is None: print('no path after a missed jump: going straight'); return greedy(goal_xyz, tol=tol)
                k = 0
            continue
        # look ahead along the walk edges as long as the way stays straight (all nodes within 0.6 of the line from here to the far node)
        if nt != 'jump' or k == 0 or math.hypot(path[k - 1][0][0] - px, path[k - 1][0][2] - pz) <= 1.0:
            q = k
        while q is not None and q < len(path) - 1 and path[q + 1][1] == 'walk' and math.hypot(path[q + 1][0][0] - px, path[q + 1][0][2] - pz) < 9.0:
            cand = path[q + 1][0]
            ax, az = cand[0] - px, cand[2] - pz
            al = math.hypot(ax, az) + 1e-9
            dev = max(abs((path[m][0][0] - px) * az - (path[m][0][2] - pz) * ax) / al for m in range(k, q + 2))
            if dev > 0.6: break
            q += 1
        if q is not None: tx, ty2, tz = path[q][0][0], path[q][0][1], path[q][0][2]
        yaw = math.atan2(tx - px, tz - pz)
        turn_to(yaw)
        dist = math.hypot(tx - px, tz - pz)
        frames = max(4, min(48, int(dist / WALK_SPEED * 60) - 2))
        hp_before = st['hp']
        st = L.send(['stick left 0 1 for %d' % frames, 'wait 1'])
        if st['hp'] < hp_before - 1.5 and not fought:
            nh = g.penalize((px + st['pos'][0]) / 2, (pz + st['pos'][2]) / 2, py, 3.0, 40.0) + g.penalize(st['pos'][0], st['pos'][2], st['pos'][1], 3.0, 40.0)
            if verbose: print('  health %.0f -> %.0f while walking (%.1f %.1f %.1f): hazard, %d nodes penalised, replanning' % (hp_before, st['hp'], px, py, pz, nh))
            p2 = plan(g, st, goal_xyz)
            if p2 is not None: path, k = p2, 0
        moved = math.hypot(st['pos'][0] - px, st['pos'][2] - pz)
        if last is not None and moved < 0.15: stall += 1
        else: stall = 0
        last = st['pos']
        if stall >= 3:
            # stuck: something the scan does not show is ahead (a crate, a door): block the nodes there and replan
            hx, hz = math.sin(st['yaw']), math.cos(st['yaw'])
            a_ = g.nearest(px, py, pz, 1.5); b_ = g.nearest(nx, ny, nz, 1.0)
            if a_ is not None and b_ is not None: g.bad.add((a_, b_))          # this edge does not work: the planner takes another one (a hop over the rail, a way round)
            nb = 0 if nt == 'drop' else g.block_near(px + hx * 1.0, pz + hz * 1.0, py)
            replans += 1
            if verbose: print('  stalled at (%.1f %.1f %.1f) heading %.2f: blocked %d nodes ahead, replan %d' % (px, py, pz, st['yaw'], nb, replans))
            if replans > maxstalls: return False
            # feel along the obstacle: strafe to either side in growing steps and try forward again (the walls the scan cannot show: lips, rubble, crates)
            hx, hz = math.sin(st['yaw']), math.cos(st['yaw'])
            got = False
            for off in ((-1, 1, -2, 2, -3, 3, -4.5, 4.5) if not in_hazard(g, st['pos']) else (-1, 1)):
                s0 = L.status(); q0 = s0['pos']
                L.send(['stick left %d 0 for %d' % (1 if off > 0 else -1, int(abs(off) / WALK_SPEED * 60) + 2), 'wait 2', 'stick left 0 1 for 22', 'wait 2'])
                q1 = L.status()['pos']
                if (q1[0] - q0[0]) * hx + (q1[2] - q0[2]) * hz > 1.2:
                    got = True; break
                L.send(['stick left 0 0'])
            if verbose: print('  unstick: %s at (%.1f %.1f %.1f)' % ('got through' if got else 'no way along the obstacle', *L.status()['pos']))
            if not got:
                L.send(['stick left 0 1', 'press B for 6', 'wait 40', 'stick left 0 0', 'wait 5'])
            path = plan(g, L.status(), goal_xyz)
            if path is None: print('no path: going straight for it'); return greedy(goal_xyz, tol=tol)
            k = 0; stall = 0
    return False


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[0] == 'scan':
        x0, z0, x1, z1 = map(float, a[1:5])
        xs, zs, fl = scan(x0, z0, x1, z1, float(a[5]) if len(a) > 5 else 0.5)
        print(topdown_png(xs, zs, fl))
    elif a[0] == 'walk':
        xs, zs, fl, step = load()
        g = Graph(xs, zs, fl, step)
        goal = (float(a[1]), float(a[3]) if len(a) > 3 else L.status()['pos'][1], float(a[2]))
        ok = walk(g, goal)
        print('arrived' if ok else 'FAILED', L.fmt(L.status()))
