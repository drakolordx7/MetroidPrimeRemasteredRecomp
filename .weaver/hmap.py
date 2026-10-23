import sys; sys.path.insert(0,'D:/AI/Active/Metroid-Prime/.weaver')
import nav, numpy as np
x0,x1,z0,z1=map(float,sys.argv[1:5]); ytop=float(sys.argv[5]); step=float(sys.argv[6]) if len(sys.argv)>6 else 0.5
xs=np.arange(x0,x1+1e-6,step); zs=np.arange(z0,z1+1e-6,step)
rays=[(x,ytop,z,0,-1,0,40.0) for z in zs for x in xs]
r=nav.cast(rays,'hm')
print('top-hit height below y=%.1f; columns x %.1f..%.1f step %.2f; rows z from %.1f'%(ytop,x0,x1,step,z1))
print('       '+''.join('%5.0f'%x for x in xs[::2]))
for j in range(len(zs)-1,-1,-1):
    row=r[j*len(xs):(j+1)*len(xs)]
    print('%7.1f'%zs[j]+''.join(('   . ' if q[0]<0.5 else '%5.1f'%q[3]) for q in row))
