"""S25: flood-fill the walkable cells around the player by walking to neighbours; progress and the final ASCII map go to the output file.
  python explore.py OUT [cells] [xmin xmax zmin zmax]    cell = 2.5 units, bounds optional. '.' reached, '#' blocked, '@' start. An area change ends the search."""
import math, sys
sys.path.insert(0, 'D:/AI/Active/Metroid-Prime/.weaver')
import live

out = open(sys.argv[1], 'w')
def log(*a):
    print(*a, file=out); out.flush()
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 120
bounds = [float(x) for x in sys.argv[3:7]] if len(sys.argv) >= 7 else [-1e9, 1e9, -1e9, 1e9]
S = 2.5
st = live.status()
x0, z0 = st['pos'][0], st['pos'][2]
area0 = st['area']
seen = {(0, 0): '@'}
queue = [(0, 0)]
n = 0
def world(c): return x0 + c[0] * S, z0 + c[1] * S
while queue and n < limit:
    c = queue.pop(0)
    for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nb = (c[0] + d[0], c[1] + d[1])
        if nb in seen: continue
        gx, gz = world(nb)
        if not (bounds[0] <= gx <= bounds[1] and bounds[2] <= gz <= bounds[3]): seen[nb] = ' '; continue
        tx, tz = world(c)
        st = live.status()
        if math.hypot(st['pos'][0] - tx, st['pos'][2] - tz) > 1.5:
            st = live.goto(tx, tz)
        st = live.goto(gx, gz)
        n += 1
        if st['area'] != area0:
            log('AREA CHANGED at', nb, live.fmt(st)); seen[nb] = 'A'; queue = []; break
        ok = math.hypot(st['pos'][0] - gx, st['pos'][2] - gz) < 1.7
        seen[nb] = '.' if ok else '#'
        if ok: queue.append(nb)
        log('cell', nb, 'world (%.1f,%.1f)' % (gx, gz), seen[nb], 'n=%d' % n)
xs = [k[0] for k in seen]; zs = [k[1] for k in seen]
for z in range(min(zs), max(zs) + 1):
    log(''.join(seen.get((x, z), ' ') for x in range(min(xs), max(xs) + 1)), ' z=%.0f' % (z0 + z * S))
log('x from %.1f step %.1f' % (x0 + min(xs) * S, S))
