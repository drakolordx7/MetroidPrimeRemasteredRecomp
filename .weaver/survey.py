"""S26 survey (development aid, uses @warp): for each area of a world: warp there, list the docks (connected area + plane), scan the static geometry, save both.
  python survey.py frigate [area ...]       results in RUN/survey/<world>/<area>.json and .npz"""
import sys, os, json, time, math, shutil
sys.path.insert(0, 'D:/AI/Active/Metroid-Prime/.weaver')
import live as L, nav, numpy as np

def parse_docks(path):
    docks = []
    for ln in open(path):
        p = ln.split()
        if len(p) < 6 or p[1] == '-' or not p[5].startswith('area='): continue
        pl = [tuple(map(float, q.split(','))) for q in p[6][6:].split(';')]
        docks.append(dict(pos=[float(p[1]), float(p[2]), float(p[3])], addr=p[4], area=p[5][5:], plane=pl))
    return docks

def run(world, areas, half=150):
    reg = L.regions()
    outd = L.RUN + '/survey/' + world
    os.makedirs(outd, exist_ok=True)
    for a in areas:
        t0 = time.time()
        st = L.send(['@warp %s %s' % (world, a), '@sleep 3000', 'wait 120'], 300)
        st = L.status()
        if reg.get(st['area'].lower(), '?') != a:
            print(a, 'warp ended in', st['area'], '(expected', a, ')')
        L.send(['@objs dock'])
        docks = parse_docks(L.RUN + '/out/objs.txt')
        px, py, pz = st['pos']
        # keep the first sighting of every dock address
        xs, zs, fl = nav.scan(px - half, pz - half, px + half, pz + half, 1.0)
        np.savez(outd + '/%s.npz' % a, xs=xs, zs=zs, floors=fl, step=1.0)
        json.dump(dict(area=a, player=st['pos'], yaw=st['yaw'], docks=docks), open(outd + '/%s.json' % a, 'w'), indent=1)
        print('%s: %d docks, %d floors, %.0fs' % (a, len(docks), len(fl), time.time() - t0))
        sys.stdout.flush()

if __name__ == '__main__':
    world = sys.argv[1]
    reg = L.regions()
    names = sys.argv[2:] or sorted(set(v for v in reg.values() if v.startswith(world + '_') and v != world + '_start'))
    run(world, names)
