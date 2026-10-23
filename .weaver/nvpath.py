import sys; sys.path.insert(0,'D:/AI/Active/Metroid-Prime/.weaver')
import nav, live as L, numpy as np, math
xs,zs,fl,step=nav.load()
g=nav.Graph(xs,zs,fl,step)
st=L.status()
goal=(float(sys.argv[1]),float(sys.argv[3]),float(sys.argv[2]))
p=nav.plan(g,st,goal)
if not p: print('no path'); sys.exit()
last=None
for pos,t in p:
    if t!='walk' or last!='walk': print('%.1f %.1f %.1f %s'%(pos[0],pos[1],pos[2],t))
    last=t
print(len(p),'nodes')
nav.topdown_png(xs,zs,fl,[('goal',goal[0],goal[2]),('me',st['pos'][0],st['pos'][2])],[q[0] for q in p],nav.RUN+'/shots/nav_path.png',scale=int(sys.argv[4]) if len(sys.argv)>4 else 4)
