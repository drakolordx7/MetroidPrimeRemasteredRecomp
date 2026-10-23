"""colour height map of a surveyed area: python colmap.py AREA x0 z0 x1 z1 [scale] -> RUN/shots/colmap.png ; heights as hue, walkable floors only (top-most node with head room), fire boxes outlined red"""
import sys, colorsys; sys.path.insert(0,'D:/AI/Active/Metroid-Prime/.weaver')
import numpy as np, nav, combat, json
from PIL import Image, ImageDraw
area=sys.argv[1]; x0,z0,x1,z1=map(float,sys.argv[2:6]); sc=int(sys.argv[6]) if len(sys.argv)>6 else 12
d=np.load(nav.RUN+'/survey/frigate/%s.npz'%area); xs,zs,fl=d['xs'],d['zs'],d['floors']
W=int((x1-x0)*sc/ (xs[1]-xs[0]) * (xs[1]-xs[0])); 
im=Image.new('RGB',(int((x1-x0)*sc),int((z1-z0)*sc)),(0,0,0)); px=im.load(); dr=ImageDraw.Draw(im)
best={}
for a,b,y,ny,c in fl:
    if c<nav.CLEAR or y>float(sys.argv[7] if len(sys.argv)>7 else 99): continue
    x=xs[int(a)]; z=zs[int(b)]
    if x0<=x<=x1 and z0<=z<=z1:
        k=(int(a),int(b))
        if k not in best or y>best[k][0]: best[k]=(y,x,z)
ymin=min(v[0] for v in best.values()); ymax=max(v[0] for v in best.values())
step=xs[1]-xs[0]
for (a,b),(y,x,z) in best.items():
    h=(y-ymin)/(ymax-ymin+1e-6); r,g,bb=colorsys.hsv_to_rgb(0.7*(1-h),0.9,0.95)
    X=int((x-x0)*sc); Y=int((z1-z)*sc)
    dr.rectangle([X,Y-int(step*sc),X+int(step*sc),Y],fill=(int(r*255),int(g*255),int(bb*255)))
for xx in range(int(x0),int(x1)+1,5):
    dr.text((int((xx-x0)*sc),2),str(xx),fill=(255,255,255))
for zz in range(int(z0),int(z1)+1,5):
    dr.text((2,int((z1-zz)*sc)),str(zz),fill=(255,255,255))
try:
    for a_,dmg,lo,hi,fl_ in json.load(open(nav.RUN+'/out/dmg_%s.json'%area)):
        dr.rectangle([int((lo[0]-x0)*sc),int((z1-hi[2])*sc),int((hi[0]-x0)*sc),int((z1-lo[2])*sc)],outline=(255,0,0),width=2)
except Exception as e: pass
print('heights %.1f..%.1f'%(ymin,ymax)); im.save(nav.RUN+'/shots/colmap.png')
