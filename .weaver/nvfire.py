import sys; sys.path.insert(0,'D:/AI/Active/Metroid-Prime/.weaver')
import nav
pts=[tuple(map(float,a.split(','))) for a in sys.argv[1:]]
for p in pts: st=nav.fire_at(*p)
nav.level(); print(nav.L.fmt(nav.L.status()))
