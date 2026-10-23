"""offline: plan inside a surveyed area from its spawn to the door towards NEXT; draw the picture. python explain.py AREA NEXT [scale]"""
import sys, math, json
sys.path.insert(0,'D:/AI/Active/Metroid-Prime/.weaver')
import numpy as np, nav, rooms, frigate, live as L
area, nxt = sys.argv[1], sys.argv[2]
sv = rooms.load('frigate'); j = sv[area]
d = np.load(nav.RUN + '/survey/frigate/%s.npz' % area)
g = nav.Graph(d['xs'], d['zs'], d['floors'], float(d['step']))
adj = rooms.edges(sv)
dk = adj[area][nxt][0]
c, n, fy = frigate.dock_geom(dk)
print('spawn', j['player'], 'door', c, 'normal', n, 'floor', fy)
pl = np.array(j['player'])
side = 1.0 if np.dot(pl - c, n) >= 0 else -1.0
n = n * side
stand = (c[0] + n[0] * 4.0, fy + 0.05, c[2] + n[2] * 4.0)
print('stand', stand)
st = dict(pos=j['player'])
# validate needs the game; plan without it
s = g.nearest(*j['player'], 3.0); t = g.nearest(*stand, 3.0)
print('nodes', len(g.nodes), 'start node', None if s is None else g.pos(s), 'goal node', None if t is None else g.pos(t))
p = g.astar(s, t) if s is not None and t is not None else None
print('path', None if p is None else len(p))
nav.topdown_png(d['xs'], d['zs'], d['floors'], [('spawn', pl[0], pl[2]), ('stand', stand[0], stand[2]), ('door', c[0], c[2])], [q[0] for q in p] if p else None, nav.RUN + '/shots/explain.png', scale=int(sys.argv[3]) if len(sys.argv) > 3 else 3)
