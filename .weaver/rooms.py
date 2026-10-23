"""S26: the room graph of a world from the survey (survey.py). Docks that sit at the same place pair two areas.
  python rooms.py frigate [FROM TO]     print the adjacency and the shortest room path"""
import sys, os, json, math, collections
sys.path.insert(0, 'D:/AI/Active/Metroid-Prime/.weaver')
import live as L

def load(world):
    d = L.RUN + '/survey/' + world
    out = {}
    for f in os.listdir(d):
        if f.endswith('.json'):
            j = json.load(open(d + '/' + f))
            out[j['area']] = j
    return out

def guid_names():
    r = {}
    for line in open(L.ROOT + '/tools/test/regions.tsv', encoding='utf-8'):
        p = line.rstrip('\n').split('\t')
        if len(p) >= 3 and p[2] and not p[0].endswith('_start'): r[p[2].lower()] = p[0]
    return r

def edges(survey):
    """returns {area: {neighbor_area: [dock dict of area's own dock]}}; a dock of area A that points at N is the one whose partner (same place) points at A"""
    gn = guid_names()
    g2n = {v: k for k, v in gn.items()}
    adj = collections.defaultdict(lambda: collections.defaultdict(list))
    for a, j in survey.items():
        gA = [k for k, v in gn.items() if v == a][0]
        docks = j['docks']
        seen = set()
        for d in docks:
            if d['addr'] in seen: continue
            seen.add(d['addr'])
            if d['area'].lower() == gA: continue          # a dock in a neighbor pointing back at A
            # the partner: a dock at the same place pointing at A
            for e in docks:
                if e is d: continue
                if e['area'].lower() == gA and math.dist(e['pos'], d['pos']) < 1.0:
                    n = gn.get(d['area'].lower(), d['area'])
                    if not any(math.dist(x['pos'], d['pos']) < 0.5 for x in adj[a][n]):
                        adj[a][n].append(d)
                    break
    return adj

def bfs(adj, s, t):
    prev = {s: None}; q = collections.deque([s])
    while q:
        u = q.popleft()
        if u == t: break
        for v in adj.get(u, {}):
            if v not in prev: prev[v] = u; q.append(v)
    if t not in prev: return None
    p = [t]
    while prev[p[-1]] is not None: p.append(prev[p[-1]])
    return p[::-1]

if __name__ == '__main__':
    sv = load(sys.argv[1]); adj = edges(sv)
    for a in sorted(adj): print(a, '->', ', '.join('%s(%d)' % (n, len(l)) for n, l in sorted(adj[a].items())))
    if len(sys.argv) > 3: print(bfs(adj, sys.argv[2], sys.argv[3]))
