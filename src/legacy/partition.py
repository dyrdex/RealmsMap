# Splits the finished map into the movable pieces used by the arranger.
import json, numpy as np
from matplotlib.path import Path
from scipy import ndimage as ndi
from skimage import measure
RES=4; X0,X1,Y0,Y1=-130.0,66.0,-118.0,42.0
W,H=int((X1-X0)*RES),int((Y1-Y0)*RES)
yy,xx=np.mgrid[0:H,0:W]; wx=xx/RES+X0+0.5/RES; wy=yy/RES+Y0+0.5/RES
PTS=np.column_stack([wx.ravel(),wy.ravel()])
def inpoly(poly): return Path(np.array(poly)).contains_points(PTS).reshape(H,W)
def inpolys(polys):
    m=np.zeros((H,W),bool)
    for p in polys: m^=inpoly(p)
    return m
def box(x0,y0,x1,y1): return [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
def build(w, strip_poly):
    lake=inpolys(w['geo']['water'])|inpoly(strip_poly)
    lake=ndi.binary_dilation(lake,iterations=int(1.2*RES))
    pieces=[
     ('darkhaven','Darkhaven',  inpoly(box(-8.8,-12,8.8,15.0)) | inpoly(box(-17.5,3.5,-8.8,15.5))),
     ('lake','Lake Tich',       lake),
     ('midennir',"Miden'nir",   inpoly(box(-14,15,31,42)) | inpoly(box(8.8,8,31,15))),
     ('grove','Shadow Grove',   inpoly([(-14,-17.4),(28,-17.4),(28,8),(8.8,8),(8.8,-12),(-8.8,-12),(-8.8,-8),(-14,-8)])),
     ('woods','Forgotten Woods',inpoly(box(-130,-118,66,-26)) | inpoly(box(-24,-118,66,-17.4))),
     ('forest','Forest of Tears',inpoly(box(-130,-26,-8.8,42))),
    ]
    owner=np.full((H,W),-1,int)
    for k,(pid,name,m) in enumerate(pieces): owner[(owner<0)&m]=k
    return pieces,owner
def clip_path(mask):
    """the outline(s) of a piece, as one SVG path (even-odd), slightly smoothed"""
    m=ndi.gaussian_filter(mask.astype(float),1.0); m=np.pad(m,1)
    d=''; box=[1e9,1e9,-1e9,-1e9]
    for c in measure.find_contours(m,0.5):
        if len(c)<8: continue
        c=measure.approximate_polygon(c,0.6)
        pts=[((x-1)/RES+X0,(y-1)/RES+Y0) for y,x in c[:-1]]
        if abs(sum(pts[i][0]*pts[(i+1)%len(pts)][1]-pts[(i+1)%len(pts)][0]*pts[i][1] for i in range(len(pts))))/2<1.0: continue
        d+='M'+'L'.join(f'{x:.2f} {y:.2f}' for x,y in pts)+'Z'
        for x,y in pts: box=[min(box[0],x),min(box[1],y),max(box[2],x),max(box[3],y)]
    return d,box

LABELS={'darkhaven':[0,4.5],'grove':[15,-13.5],'midennir':[7,26],'lake':[-33,-30],'woods':[12,-62],'forest':[-68,6]}
def pieces_json(w, strip_poly):
    pieces,owner=build(w,strip_poly)
    land=inpolys(w['geo']['land']); water=inpolys(w['geo']['water'])
    visible=ndi.binary_dilation(land|water,iterations=3)            # land and water, with a margin for coast strokes and trees that overhang
    order=['forest','woods','lake','grove','midennir','darkhaven']          # drawing order, bottom to top
    colors={'darkhaven':'#d9534f','lake':'#4a90d9','midennir':'#8e6bbf','grove':'#e0a030','woods':'#3f9e5a','forest':'#2aa198'}
    out=[]
    for pid in order:
        k=[p[0] for p in pieces].index(pid); name=pieces[k][1]
        mask=ndi.binary_dilation(owner==k,iterations=1)&visible     # a touch of overlap so no hairline shows at the joins
        d,box=clip_path(mask)
        out.append(dict(id=pid,name=name,d=d,box=[round(float(v),2) for v in box],color=colors[pid],locked=(pid=='darkhaven'),lab=LABELS[pid]))
    return out
