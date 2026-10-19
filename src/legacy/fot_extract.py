import json, math, re, sys
import numpy as np
from scipy import ndimage as ndi
from skimage import measure
exec(open('../parse_world.py').read())
from collections import deque, defaultdict, Counter
R=lambda v:rooms[v]
DV={1:(0,-1,0),2:(1,0,0),4:(0,1,0),8:(-1,0,0),3:(1,-1,0),9:(-1,-1,0),6:(1,1,0),12:(-1,1,0),16:(0,0,1),32:(0,0,-1)}
rng=np.random.default_rng(11)

def layout(area,start,at):
    S={v for v,r in rooms.items() if r['area']==area}
    pos={start:at}; q=deque([start])
    while q:
        v=q.popleft(); x,y,z=pos[v]
        for e in exits.get(v,[]):
            t=e['to']
            if not (t in S or (R(t)['flags']&8 and R(t)['area']=='')) or e['dir'] not in DV or t in pos: continue
            dx,dy,dz=DV[e['dir']]; pos[t]=(x+dx,y+dy,z+dz); q.append(t)
    return S,pos

def theme(v):
    r=R(v); n=r['name']
    if r['flags']&8: return 'void'
    if re.search(r'^Along the Silver Lake',n): return 'water'
    if r['terrain']=='Mountains' or re.search(r'Cliff|Wall|Edge|Rockslide|Canyon|Fault|Sandstone|Dry|Terrain',n): return 'cliff'
    if r['terrain']=='Swamp' or re.search(r'Swamp|Marsh|Drowning|Glade|Deep Waters',n): return 'bog'
    if re.search(r'Sparse|Bare|Clearcut',n): return 'sparse'
    if re.search(r'Lost Between|Darker Forests|Dead Man|Path to the Cliffs|Tracking the Cliffs|West of Silver Lake',n): return 'npath'
    if re.search(r'Misery|Weeping|Darker|Thick|Blood|Burial|Roots',n): return 'deep'
    return 'wood'
def is_trail(v):
    r=R(v); n=r['name']
    return bool(r['flags']&8) or bool(re.search(r'Trail|Path|Route|Cross|Road|Lost Between|Along|Tracking|Hop|Northward|Racing|Up the|Into',n))

# ---------- Forest of Tears ----------
S,pos=layout('Forest of Tears',820,(-9,0,0))
pts=[(v,p) for v,p in pos.items() if p[2]==0 or v in S]
ndS={v for v,r in rooms.items() if r['area']=='New Darkhaven'}
ndpos={764:(0,0,0)}; q=deque([764])
while q:
    v=q.popleft(); x,y,z=ndpos[v]
    for e in exits.get(v,[]):
        t_=e['to']
        if not (t_ in ndS or R(t_)['area'] in ('','visual')) or e['dir'] not in DV or t_ in ndpos: continue
        dx,dy,dz=DV[e['dir']]; ndpos[t_]=(x+dx,y+dy,z+dz); q.append(t_)
townpts=[(v,p) for v,p in ndpos.items() if p[2]==0 and abs(p[0])<=9 and -11<=p[1]<=14]
X0,X1,Y0,Y1=-76,76,-122,33; RES=4
GW,GH=(X1-X0)*RES,(Y1-Y0)*RES
def grid(): return np.zeros((GH,GW))
fields=defaultdict(grid)
for v,(x,y,z) in pts:
    th=theme(v)
    i,j=int((x-X0)*RES),int((y-Y0)*RES)
    if 0<=i<GW and 0<=j<GH:
        fields['land'][j,i]+=1 if th!='void' else .6
        if th!='void': fields[th][j,i]+=1
# ---- the Lost Between Woods pathway, as the TinTin map has it ----
# east stretch: from Silver Lake west along the north edge, then a hidden exit drops it into the
# deep woods' northern lobe, a few rooms east of the V'laresch entrance.
# west stretch: a separate run from the Forgotten Woods link west to Path to the Cliffs,
# where it rejoins the forest (and a spur climbs onto the Fog Cliffs).
_lbw=[(pos[v][0],pos[v][1]) for v in pos if pos[v][2]==0 and re.search(r'Lost Between|West of Silver Lake|Darker Forests|Path to the Cliffs|Tracking the Cliffs',R(v)['name'])]
def _envelope(x0,x1):
    bx=defaultdict(list)
    for x,y in _lbw:
        if x1<=x<=x0: bx[x].append(y)
    xs=np.arange(x0,x1-0.01,-0.5); kn=sorted((x,min(ys)) for x,ys in bx.items())
    ky=ndi.gaussian_filter1d(np.interp(xs,[k[0] for k in kn],[k[1] for k in kn]),3)
    return [[round(float(x),2),round(float(y),2)] for x,y in zip(xs,ky)]
eastR=[[-15.8,-9.2]]+_envelope(-16,-34)+[[-34.6,-10.6],[-35.4,-9.7],[-36.0,-8.7]]
westR=[[-48.7,-9.1]]+_envelope(-49,-57)+[[-57.4,-8.9]]
westJ=[[-57.0,-9.0],[-56.4,-8.3]]
cliffR=[[-57.2,-9.0],[-58.0,-8.2],[-59.0,-7.3]]
ribbons=[eastR,westR,westJ,cliffR]
junctions=[[-36.0,-8.6],[-56.3,-8.2]]
ribbon=[p for r_ in ribbons for p in r_]
for x,y in ribbon:
    i,j=int((x-X0)*RES),int((y-Y0)*RES)
    if 0<=i<GW and 0<=j<GH: fields['land'][j,i]+=1.2
# ---- the Western Trade Route: its own winding road, anchored to the forest where they meet ----
WT={v for v,r in rooms.items() if r['area']=='Western Trade Route'}
wpos=dict(pos); _q=deque(pos.keys()); _wp=set()
while _q:
    v=_q.popleft(); x,y,z=wpos[v]
    for e in exits.get(v,[]):
        t_=e['to']
        if e['dir'] not in DV or t_ in wpos: continue
        if not (t_ in WT or (R(t_)['flags']&8 and v in _wp)): continue
        dx,dy,dz=DV[e['dir']]; wpos[t_]=(x+dx,y+dy,z+dz); _wp.add(t_); _q.append(t_)
wpos[831]=(-10,1,0)
_ok=lambda t_: t_ in WT or t_==1952 or (R(t_)['flags']&8 and t_ in _wp)   # 1952-ish crossing room added below
_cross=[v for v in pos if R(v)['name']=='A Crossing of Roads Amidst the Darkened Forest']
_prev={831:None}; _q=deque([831])
while _q:
    v=_q.popleft()
    if v==2365: break
    for e in exits.get(v,[]):
        t_=e['to']
        if t_ in _prev or not (t_ in WT or t_ in _cross or (R(t_)['flags']&8 and t_ in _wp)): continue
        _prev[t_]=v; _q.append(t_)
_chain=[];_x=2365
while _x is not None: _chain.append(_x); _x=_prev[_x]
_chain=_chain[::-1]
_WTCHAIN=list(_chain)
_pts=[]
_north=False
for v in _chain:
    x,y,z=wpos[v]
    n=R(v)['name']
    if v==2015: _north=True
    if v==2350: _north=False
    dy=-2.6 if _north else (-1.4 if v in (2350,2351,2352) else 0)
    _pts.append([float(x),float(y)+dy])
# densify the long unmapped stretch across the north (the TinTin map leaves a jump there)
road=[]
for k in range(len(_pts)-1):
    a_,b_=_pts[k],_pts[k+1]; L=math.hypot(b_[0]-a_[0],b_[1]-a_[1]); n_=max(1,int(L/0.6))
    for s_ in range(n_):
        tt=s_/n_; road.append([a_[0]+(b_[0]-a_[0])*tt, a_[1]+(b_[1]-a_[1])*tt + (math.sin(tt*math.pi)*-1.2 if L>6 else 0)])
road.append(_pts[-1])
_rx=ndi.gaussian_filter1d(np.array([p[0] for p in road]),1.6); _ry=ndi.gaussian_filter1d(np.array([p[1] for p in road]),1.6)
road=[[round(float(x)+float(rng.uniform(-.06,.06)),2),round(float(y)+float(rng.uniform(-.06,.06)),2)] for x,y in zip(_rx,_ry)]
road=[[-8.2,0.15],[-9.0,0.85]]+road
wdisp={v:(p[0],p[1]) for v,p in zip(_chain,_pts)}
_dyof={v:p[1]-wpos[v][1] for v,p in zip(_chain,_pts)}
for v in WT:
    if v in wdisp or v not in wpos: continue
    nb=[e['to'] for e in exits.get(v,[]) if e['to'] in _dyof]
    dy_=_dyof[nb[0]] if nb else (-2.6 if wpos[v][1]<=-13 else 0)
    wdisp[v]=(float(wpos[v][0]),float(wpos[v][1])+dy_)
# the little village by the tavern: Falcon's Nest Tavern, The Falcon's Talon, Jelarid's Track Shoppe
def _push(x,y,minD=1.05):
    best=min(road,key=lambda p:math.hypot(p[0]-x,p[1]-y)); d=math.hypot(best[0]-x,best[1]-y) or 1e-6
    if d<minD: x,y=best[0]+(x-best[0])/d*minD, best[1]+(y-best[1])/d*minD
    return round(x,2),round(y,2)
_tav=[wdisp[v] for v in WT if re.search(r'Tavern|Stage|Bar of the Wild Boar',R(v)['name']) and 'Before' not in R(v)['name'] and v in wdisp]
_tx,_ty=_push(sum(p[0] for p in _tav)/len(_tav),sum(p[1] for p in _tav)/len(_tav),1.15)
_sx,_sy=_push(*wdisp[2347]); _jx,_jy=_push(*wdisp[2338])
buildings=[dict(name="Falcon's Nest Tavern",x=_tx,y=_ty,w=1.25,h=.85),dict(name="The Falcon's Talon",x=_sx,y=_sy,w=.8,h=.6),dict(name="Jelarid's Track Shoppe",x=_jx,y=_jy,w=.8,h=.6)]
print('buildings',buildings)
# round the sharp corner in the trade route just north of the tavern (room 2348): cut the corner with a curve, using the largest
# rounding that still keeps the road clear of the village buildings and the tavern's marker
def _round_corner(pts,corner,r):
    ic=min(range(len(pts)),key=lambda i:math.hypot(pts[i][0]-corner[0],pts[i][1]-corner[1]))
    ia=ic; s=0.0
    while ia>0 and s<r: s+=math.hypot(pts[ia][0]-pts[ia-1][0],pts[ia][1]-pts[ia-1][1]); ia-=1
    ib=ic; s=0.0
    while ib<len(pts)-1 and s<r: s+=math.hypot(pts[ib+1][0]-pts[ib][0],pts[ib+1][1]-pts[ib][1]); ib+=1
    A,C,B=pts[ia],corner,pts[ib]
    arc=[[(1-u)**2*A[0]+2*(1-u)*u*C[0]+u*u*B[0],(1-u)**2*A[1]+2*(1-u)*u*C[1]+u*u*B[1]] for u in [i/20 for i in range(21)]]
    return pts[:ia]+[[round(p[0],2),round(p[1],2)] for p in arc]+pts[ib+1:]
def _clear_of_village(pts):
    boxes=[(b_['x']-b_['w']/2-.4,b_['y']-b_['h']/2-.4,b_['x']+b_['w']/2+.4,b_['y']+b_['h']/2+.4) for b_ in buildings]
    boxes.append((buildings[0]['x']-.6,buildings[0]['y']+buildings[0]['h']/2+.45-.6,buildings[0]['x']+.6,buildings[0]['y']+buildings[0]['h']/2+.45+.6))
    return not any(bx[0]<p[0]<bx[2] and bx[1]<p[1]<bx[3] for p in pts for bx in boxes)
_corner=list(wdisp[2348]); _y0=buildings[0]['y']; _opts=[]
for _sh in (0.0,0.5,1.0,1.5,2.0):
    buildings[0]['y']=round(_y0+_sh,2)
    for _r in (7,6.5,6,5.5,5,4.5,4,3.5,3,2.5,2):
        _cand=_round_corner(road,_corner,_r)
        _fine=[]
        for _a,_b in zip(_cand[:-1],_cand[1:]):
            _n=max(1,int(math.dist(_a,_b)/0.15)); _fine+=[[_a[0]+(_b[0]-_a[0])*i/_n,_a[1]+(_b[1]-_a[1])*i/_n] for i in range(_n)]
        if _clear_of_village(_fine): _opts.append((_sh,_r,_cand)); break
# the smallest nudge of the tavern building that allows a clearly rounded corner (radius 5 or more), else the best available
_pick=next((o for o in _opts if o[1]>=5),None) or (max(_opts,key=lambda o:(o[1],-o[0])) if _opts else None)
if _pick:
    buildings[0]['y']=round(_y0+_pick[0],2); road=_pick[2]
    print('trade route: corner north of the tavern rounded with radius',_pick[1],'| tavern building nudged south by',_pick[0])
else:
    buildings[0]['y']=_y0; print('trade route: could not round the corner without touching the village')
# the trade route stops where it passes the V'laresch marker (the road is cut at its closest point to that marker)
_vl=[pos[v][:2] for v in pos if R(v)['name']=='The Misery of Mourning' and any(R(e['to'])['area']=='Asgard Nexus' for e in exits.get(v,[]))]
if _vl:
    _vx,_vy=_vl[0]
    _ic=min(range(len(road)),key=lambda i:math.hypot(road[i][0]-_vx,road[i][1]-_vy))
    print('trade route: cut at',road[_ic],'next to V\'laresch at',(_vx,_vy),'| dropped',len(road)-_ic-1,'of',len(road),'points')
    road=road[:_ic+1]
print('trade route chain',len(_chain),'rooms; road points',len(road),'from',road[0],'to',road[-1])
for x,y in road:
    i,j=int((x-X0)*RES),int((y-Y0)*RES)
    if 0<=i<GW and 0<=j<GH:
        fields['land'][j,i]+=0.9
        if y<-12.5: fields['wood'][j,i]+=0.6
for v,(x,y,z) in townpts:
    i,j=int((x-X0)*RES),int((y-Y0)*RES)
    fields['land'][j,i]+=1
    inside=(-7<=x<=7 and -9<=y<=9)
    fields['meadow'][j,i]+=0.4 if inside else 1
noise=ndi.gaussian_filter(rng.standard_normal((GH,GW)),2.2*RES); noise/=noise.std()
fine=ndi.gaussian_filter(rng.standard_normal((GH,GW)),0.7*RES); fine/=fine.std()
def smooth(a,s): 
    b=ndi.gaussian_filter(a,s*RES); m=b.max() or 1; return b/ndi.gaussian_filter(np.ones_like(a)*0+ (a>0)*1.0+1e-9, s*RES).max()
def field(name,s):
    return ndi.gaussian_filter(fields[name],s*RES)*(2*math.pi*(s*RES)**2)  # ~ room count density, 1 inside dense area
def contours(F,level,step=2,minarea=0.8):
    out=[]
    for c in measure.find_contours(np.pad(F,1),level):
        c=c-1
        if len(c)<8: continue
        a=0.5*abs(np.dot(c[:,0],np.roll(c[:,1],1))-np.dot(c[:,1],np.roll(c[:,0],1)))/RES/RES
        if a<minarea: continue
        c=c[::step]
        pts_=[(round(p[1]/RES+X0,2),round(p[0]/RES+Y0,2)) for p in c]
        out.append(pts_)
    return out
# ---- Miden'nir: across the rusted bridge south of Darkwall ----
MD={v for v,r in rooms.items() if r['area']=="Miden'nir"}
mpos={1028:(0,14,0)}; _q=deque([1028])
while _q:
    v=_q.popleft(); x,y,z=mpos[v]
    for e in exits.get(v,[]):
        t_=e['to']
        if not (t_ in MD or (R(t_)['flags']&8 and R(t_)['area']=='')) or e['dir'] not in DV or t_ in mpos: continue
        dx,dy,dz=DV[e['dir']]; mpos[t_]=(x+dx,y+dy,z+dz); _q.append(t_)
def mtheme(v):
    n=R(v)['name']
    if R(v)['flags']&8: return 'void'
    if 'Heart of the Black Forest' in n: return 'blackheart'
    if re.search(r'Black Forest|Edge of the Woods',n): return 'black'
    if 'Bramble' in n: return 'bramble'
    if re.search(r'Tunnel|Slop|Doom|Ladder|Passage|Alcove|Skull|Landing|Goblin',n): return 'doom'
    return 'mland'
for v,(x,y,z) in mpos.items():
    if z!=0: continue
    th=mtheme(v)
    i,j=int((x-X0)*RES),int((y-Y0)*RES)
    if not(0<=i<GW and 0<=j<GH) or th=='void' and y<15.5: continue
    fields['land'][j,i]+=1 if th!='void' else .5
    if th in ('black','blackheart'): fields['black'][j,i]+=1
    if th=='blackheart': fields['blackheart'][j,i]+=1
    if th=='bramble': fields['bramble'][j,i]+=1
    if th=='doom': fields['doom'][j,i]+=1
# Mount Doom rises over the cavern tunnels to the south of the forest
for k in range(40):
    a_=rng.uniform(0,2*math.pi); r_=rng.uniform(0,2.6)
    x,y=2.4+r_*math.cos(a_)*1.1,26.2+r_*math.sin(a_)
    i,j=int((x-X0)*RES),int((y-Y0)*RES); fields['land'][j,i]+=.8; fields['doom'][j,i]+=.8
print("Miden'nir rooms placed",len([v for v in mpos if v in MD]))
# ---- Along the Forest Path & Shattered Refuge: the ground between the forest, the town and Miden'nir ----
AF={v for v,r in rooms.items() if r['area']=='Along the Forest Path'}
SR={v for v,r in rooms.items() if r['area']=='Shattered Refuge'}
_known=dict(pos); _known.update(ndpos); _known.update(mpos)
lp={}; _q=deque()
for v in list(_known):
    for e in exits.get(v,[]):
        t_=e['to']
        if (t_ in AF or t_ in SR) and e['dir'] in DV and R(v)['area'] not in ('Along the Forest Path','Shattered Refuge') and t_ not in lp:
            dx,dy,dz=DV[e['dir']]; lp[t_]=(_known[v][0]+dx,_known[v][1]+dy,_known[v][2]+dz); _q.append(t_)
while _q:
    v=_q.popleft(); x,y,z=lp[v]
    for e in exits.get(v,[]):
        t_=e['to']
        if not (t_ in AF or t_ in SR or (R(t_)['flags']&8 and R(t_)['area']=='' and t_ not in _known)) or e['dir'] not in DV or t_ in lp: continue
        dx,dy,dz=DV[e['dir']]; lp[t_]=(x+dx,y+dy,z+dz); _q.append(t_)
# draw the Refuge's village a little more compactly: pull its southern lanes and homes north
for v in list(lp):
    if v in SR and lp[v][0]<=-4.5 and lp[v][1]>18:
        x,y,z=lp[v]; lp[v]=(x,round(18+(y-18)*0.45,2),z)
# the Refuge's own layout also places some passages under Mount Doom; only its surface west of Miden'nir is drawn
def _surface(v): return lp[v][2]==0 and (v in AF or (v in SR and lp[v][0]<=-2))
for v in lp:
    if v not in AF and v not in SR or not _surface(v): continue
    x,y,_z=lp[v]; i,j=int((x-X0)*RES),int((y-Y0)*RES)
    fields['land'][j,i]+=1
    tr_=R(v)['terrain']
    if v in AF: fields['land'][j,i]-=1; continue
    elif tr_=='Field': fields['meadow'][j,i]+=0.9
    elif tr_=='Forest': fields['wood'][j,i]+=0.8
print('AFP/SR placed',len([v for v in lp if v in AF or v in SR]))
# ---- Shadow Grove: fields and hills wrapped around the north of the town ----
SGr={v for v,r in rooms.items() if r['area']=='Shadow Grove'}
sgp={}; _q=deque()
for v in list(_known):
    for e in exits.get(v,[]):
        t_=e['to']
        if t_ in SGr and e['dir'] in DV and R(v)['area']!='Shadow Grove' and t_ not in sgp:
            dx,dy,dz=DV[e['dir']]; sgp[t_]=(_known[v][0]+dx,_known[v][1]+dy,_known[v][2]+dz); _q.append(t_)
while _q:
    v=_q.popleft(); x,y,z=sgp[v]
    for e in exits.get(v,[]):
        t_=e['to']
        if not (t_ in SGr or (R(t_)['flags']&8 and R(t_)['area']=='' and t_ not in _known)) or e['dir'] not in DV or t_ in sgp: continue
        dx,dy,dz=DV[e['dir']]; sgp[t_]=(x+dx,y+dy,z+dz); _q.append(t_)
for v,(x,y,z) in sgp.items():
    if z: continue
    i,j=int((x-X0)*RES),int((y-Y0)*RES)
    if v not in SGr:
        fields['land'][j,i]+=.5; fields['sg'][j,i]+=.4; continue
    tr_=R(v)['terrain']
    fields['land'][j,i]+=1; fields['sg'][j,i]+=1
    if tr_=='Hills': fields['sghill'][j,i]+=1
    if tr_=='Forest': fields['sgwood'][j,i]+=1
print('Shadow Grove placed',len([v for v in sgp if v in SGr]))
# ---- The Forgotten Woods: arranged by hand in the layout editor, then placed north of the Shadow Grove ----
FWr={v for v,r in rooms.items() if r['area']=='The Forgotten Woods'}
import os as _os
_fwf=next(p for p in ('fw_final.json','/home/claude/fwbench/fw_final.json') if _os.path.exists(p))
_FL=json.load(open(_fwf))
_cr=1211                                       # the Grove room the way in leaves from
_fwr={r['id']:r for r in _FL['rooms']}
_sp=_fwr[_FL['link']['spacer']]; ENT=_FL['link']['entrance']
_tx=sgp[_cr][0]-_sp['x']; _ty=(sgp[_cr][1]-1)-_sp['y']          # slide the whole Woods so its spacer room sits one step north of that Grove room
fwp={v:(round(r['x']+_tx,2),round(r['y']+_ty,2),0) for v,r in _fwr.items()}
print('Forgotten Woods placed',len(fwp),'rooms; entrance at',fwp[ENT][:2],'; shifted by',(round(_tx,2),round(_ty,2)))
def fwtheme(v):
    r=_fwr[v]
    if r['void']: return 'void'
    return {'Mountains':'mtn','Field':'plain','Swamp':'bog','Desert':'sand','Hills':'hill'}.get(r['terrain'],'wood')
_fwmap={'sand':'sand','bog':'bog','mtn':'mtn','hill':'sghill','plain':'fwplain','wood':'fwwood'}
fwpts=[]
for v,(x,y,z) in fwp.items():
    i,j=int((x-X0)*RES),int((y-Y0)*RES)
    if not(0<=i<GW and 0<=j<GH): continue
    th=fwtheme(v)
    fields['land'][j,i]+=1 if th!='void' else .5
    if th!='void':
        fields[_fwmap[th]][j,i]+=1
        fwpts.append((x,y,th))
# the mazes: one shaded shape each, over all of their rooms
def _hull2(P):
    P=sorted(set(P))
    if len(P)<3: return P
    cr_=lambda o,a,b:(a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0]); lo=[];up=[]
    for p in P:
        while len(lo)>=2 and cr_(lo[-2],lo[-1],p)<=0: lo.pop()
        lo.append(p)
    for p in reversed(P):
        while len(up)>=2 and cr_(up[-2],up[-1],p)<=0: up.pop()
        up.append(p)
    return lo[:-1]+up[:-1]
fwmazes=[]
for g in _FL['groups']:
    ps=[fwp[v][:2] for v in g['rooms']]
    H=_hull2([(x+.85*math.cos(a*math.pi/6),y+.85*math.sin(a*math.pi/6)) for x,y in ps for a in range(12)])
    fwmazes.append(dict(id=g['id'],name=g['name'],cx=round(sum(p[0] for p in ps)/len(ps),2),cy=round(sum(p[1] for p in ps)/len(ps),2),
                        poly=[[round(a,2),round(b,2)] for a,b in H],rooms=set(g['rooms'])))
def _inp(x,y,P):
    c=False; n=len(P)
    for i in range(n):
        x1,y1=P[i]; x2,y2=P[(i+1)%n]
        if (y1>y)!=(y2>y) and x<(x2-x1)*(y-y1)/(y2-y1)+x1: c=not c
    return c
_inany=lambda x,y: any(_inp(x,y,m['poly']) for m in fwmazes)
# its paths: every real exit between two walkable rooms (two-way, up/down climbs and one-way drops), except steps inside a maze
_ing={v:m['id'] for m in fwmazes for v in m['rooms']}
_DT={v for v,r in _fwr.items() if r['terrain']=='DT'}
_E=[]; _long=0
for a,b,k in _FL['edges']:
    if a in _DT or b in _DT or a not in fwp or b not in fwp: continue
    if _ing.get(a) and _ing.get(a)==_ing.get(b): continue
    if math.dist(fwp[a][:2],fwp[b][:2])>9: _long+=1; continue
    _E.append((a,b))
# in open grids (every room joined to all eight neighbours) a diagonal exit only repeats what two straight links already show
def _pdirs(a,b): return [e['dir'] for e in exits.get(a,[]) if e['to']==b]+[e['dir'] for e in exits.get(b,[]) if e['to']==a]
_diagE={(a,b) for a,b in _E if _pdirs(a,b) and all(d in (3,9,6,12) for d in _pdirs(a,b))}
_orth=defaultdict(set)
for a,b in _E:
    if (a,b) not in _diagE: _orth[a].add(b); _orth[b].add(a)
_dropd={(a,b) for a,b in _diagE if _orth[a]&_orth[b]}
_E=[(a,b) for a,b in _E if (a,b) not in _dropd]
print('diagonal shortcuts left out of the grids:',len(_dropd))
_G=defaultdict(set)
for a,b in _E: _G[a].add(b); _G[b].add(a)
_chains=[]; _seen=set()
for v in [v for v in _G if len(_G[v])!=2]+list(_G):
    for w_ in _G[v]:
        k_=(min(v,w_),max(v,w_))
        if k_ in _seen: continue
        ch=[v,w_]; _seen.add(k_)
        while len(_G[ch[-1]])==2:
            nx=[u for u in _G[ch[-1]] if u!=ch[-2]][0]; k_=(min(ch[-1],nx),max(ch[-1],nx))
            if k_ in _seen: break
            _seen.add(k_); ch.append(nx)
        _chains.append(ch)
def _bis(pout,pin):
    lo,hi=0.0,1.0
    for _ in range(18):
        m=(lo+hi)/2; x=pout[0]+(pin[0]-pout[0])*m; y=pout[1]+(pin[1]-pout[1])*m
        if _inany(x,y): hi=m
        else: lo=m
    return [pout[0]+(pin[0]-pout[0])*lo,pout[1]+(pin[1]-pout[1])*lo]
fwtracks=[]
for ch in _chains:
    p=[[float(fwp[u][0]),float(fwp[u][1])] for u in ch]
    if len(p)>=4:
        xs_=ndi.gaussian_filter1d(np.array([q[0] for q in p]),0.8,mode='nearest'); ys_=ndi.gaussian_filter1d(np.array([q[1] for q in p]),0.8,mode='nearest')
        q_=[[float(a_),float(b_)] for a_,b_ in zip(xs_,ys_)]; q_[0]=p[0]; q_[-1]=p[-1]; p=q_
    for end in (0,1):                                  # paths stop at a maze's edge instead of running through it
        if end: p=p[::-1]
        if p and _inany(*p[0]):
            gone=None
            while len(p)>1 and _inany(*p[0]): gone=p.pop(0)
            if gone is not None and not _inany(*p[0]) : p.insert(0,_bis(p[0],gone))
        if end: p=p[::-1]
    if len(p)>=2 and not all(_inany(*q) for q in p): fwtracks.append([[round(a,2),round(b,2)] for a,b in p])
# the way in: Darktrail, up through the Grove, then the spacer room and the entrance room
fwtracks.append([[0.0,-10.0],[float(sgp[_cr][0]),float(sgp[_cr][1])],[float(fwp[_FL['link']['spacer']][0]),float(fwp[_FL['link']['spacer']][1])],[float(fwp[ENT][0]),float(fwp[ENT][1])]])
print('Forgotten Woods paths:',len(_E),'exits drawn in',len(fwtracks),'trails;',_long,'left out for being longer than 9 rooms; mazes',[m['name'] for m in fwmazes])
_fwm=np.zeros((GH,GW),bool)
for v,(x,y,z) in fwp.items():
    i,j=int((x-X0)*RES),int((y-Y0)*RES)
    if 0<=i<GW and 0<=j<GH: _fwm[j,i]=True
for p in fwtracks:
    for k_ in range(len(p)-1):
        for s_ in np.linspace(0,1,max(2,int(math.dist(p[k_],p[k_+1])*RES)+1)):
            x=p[k_][0]+(p[k_+1][0]-p[k_][0])*s_; y=p[k_][1]+(p[k_+1][1]-p[k_][1])*s_
            i,j=int((x-X0)*RES),int((y-Y0)*RES)
            if 0<=i<GW and 0<=j<GH: _fwm[j,i]=True
# the Woods' land: a wide band around every room and path, closed up across the gaps between them, then filled in
_Rd,_Rc=3.6*RES,4.5*RES
_fwm=ndi.distance_transform_edt(~_fwm)<=(_Rd+_Rc)
_fwm=ndi.distance_transform_edt(_fwm)>_Rc
_fwm=ndi.binary_fill_holes(_fwm)
_FWL=ndi.gaussian_filter(_fwm.astype(float),1.0*RES)
for p in fwtracks:
    for x,y in p:
        i,j=int((x-X0)*RES),int((y-Y0)*RES)
        if 0<=i<GW and 0<=j<GH: fields['land'][j,i]+=.4
_fwx=[p[0] for p in fwpts]; _fwy=[p[1] for p in fwpts]
fwlabel=dict(x0=round(float(np.median(_fwx))-7,1),x1=round(float(np.median(_fwx))+7,1),y=round(float(np.median(_fwy))-1,1))


afp_c=(-13.2,11.2)
for k in range(260):
    a_=rng.uniform(0,2*math.pi); r_=2.6*math.sqrt(rng.uniform(0,1))
    x,y=afp_c[0]+math.cos(a_)*r_*1.15,afp_c[1]+math.sin(a_)*r_*0.9
    i,j=int((x-X0)*RES),int((y-Y0)*RES); fields['land'][j,i]+=0.35; fields['wood'][j,i]+=0.35
_allk=dict(_known); _allk.update(lp)
def track(a_,b_,allowed):
    prev={a_:None}; q_=deque([a_])
    while q_:
        v=q_.popleft()
        if v==b_: break
        for e in exits.get(v,[]):
            t_=e['to']
            if t_ in prev or t_ not in _allk or _allk[t_][2]!=0 or not allowed(t_) or e['dir'] not in DV: continue
            prev[t_]=v; q_.append(t_)
    if b_ not in prev: return []
    p_=[];x=b_
    while x is not None: p_.append([float(_allk[x][0]),float(_allk[x][1])]); x=prev[x]
    return p_[::-1]
_okA=lambda t_: R(t_)['area'] in ('Along the Forest Path','New Darkhaven','Forest of Tears') or (R(t_)['flags']&8 and R(t_)['area']=='')
_okS=lambda t_: R(t_)['area'] in ('Shattered Refuge',"Miden'nir") or (R(t_)['flags']&8 and R(t_)['area']=='')
sw_tracks=[track(1485,1468,_okS),track(1498,1499,_okS),track(1485,1498,_okS)]
sw_tracks.append([[-12.6,5.4],[-13.4,7.6],[-13.6,9.6],[-13.0,11.4],[-11.8,13.2],[-10.4,15.0],[-9.0,17.0]])
sw_tracks=[p for p in sw_tracks if len(p)>1]
sw_tracks.append([[-3.0,21.0],[-2.0,21.0],[-1.2,20.6]])          # field by the river into the Black Forest
print('sw tracks',[(p[0],p[-1],len(p)) for p in sw_tracks])
for p in sw_tracks:
    for x,y in p:
        i,j=int((x-X0)*RES),int((y-Y0)*RES); fields['land'][j,i]+=0.6
_lab=[(lp[v][0],lp[v][1]) for v in SR if v in lp and _surface(v) and re.search(r'lab|Gears|storage|office|beakers|garden',R(v)['name'],re.I)]
_home=[(lp[v][0],lp[v][1]) for v in SR if v in lp and _surface(v) and re.search(r'home|abode|hut|classroom|Workshop|Pandemonium|jumble|Green thumb|Light and color',R(v)['name'],re.I)]
precarious=None
bigtree=[-14.4,11.9]

_f=field('land',2.0);_f=np.maximum(_f,_FWL);land=_f+(0.22*noise+0.08*fine)*np.clip(_f*2.5,0,1)
_f=field('deep',1.0);deep=_f+(0.25*noise+0.1*fine)*np.clip(_f*2.5,0,1)
_f=field('bog',0.9);bog=_f+(0.25*noise+0.12*fine)*np.clip(_f*2.5,0,1)
_f=field('water',1.25);water=_f+0.15*noise*np.clip(_f*2.5,0,1)
# Lake of Tich'Pyga: drawn a little larger than its shore rooms suggest, but kept clear of the town's outer trail
_yy0,_xx0=np.mgrid[0:GH,0:GW]; _WX0=_xx0/RES+X0; _WY0=_yy0/RES+Y0
water=np.where((_WX0>-9.5)|(_WX0<-17.6),np.minimum(water,0.2),water)
_lk=water>0.38
lakelabel=None
if _lk.any():
    _ys,_xs=np.where(_lk); _px=_xs/RES+X0; _py=_ys/RES+Y0
    _cx,_cy=float(_px.mean()),float(_py.mean())
    _cov=np.cov(np.vstack([_px-_cx,_py-_cy])); _ev,_evec=np.linalg.eigh(_cov); _v=_evec[:,1]
    _ang=math.degrees(math.atan2(_v[1],_v[0]))
    if _ang>90: _ang-=180
    if _ang<-90: _ang+=180
    lakelabel=dict(x=round(_cx,2),y=round(_cy,2),a=round(_ang,1))
    print('lake label',lakelabel)
_f=field('cliff',0.8);cliff=_f+0.2*noise*np.clip(_f*2.5,0,1)
_f=field('sparse',1.1);sparse=_f+0.2*noise*np.clip(_f*2.5,0,1)
_f=field('meadow',1.6);meadow=_f+(0.18*noise+0.06*fine)*np.clip(_f*2.5,0,1)
wood=(field('wood',1.0)+field('deep',1.0)*0.4)+0.2*noise
_lm=ndi.binary_fill_holes(land>0.36)
land=np.where(_lm&(land<=0.36),0.5,land)
geo=dict(
  land=contours(land,0.36,minarea=6),
  deep=contours(deep,0.55),
  bog=contours(bog,0.5),
  water=contours(water,0.38,1),
  cliff=contours(cliff,0.5),
  sparse=contours(sparse,0.45),
  black=contours(field('black',0.9)+0.2*noise*np.clip(field('black',0.9)*2.5,0,1),0.5),
  blackheart=contours(field('blackheart',0.8),0.5),
  bramble=contours(field('bramble',0.9)+0.2*noise*np.clip(field('bramble',0.9)*2.5,0,1),0.45),
  doom=contours(ndi.gaussian_filter(fields['doom'],1.0*RES)*(2*math.pi*(1.0*RES)**2),0.45),
  sg=contours(field('sg',1.3)+0.18*noise*np.clip(field('sg',1.3)*2.5,0,1),0.42),
  sg2=contours(field('sg',1.0)+0.18*noise*np.clip(field('sg',1.0)*2.5,0,1),0.7),
  sand=contours(field('sand',0.8)+0.15*noise*np.clip(field('sand',0.8)*2.5,0,1),0.45),
  blight=contours(field('blight',0.9)+0.2*noise*np.clip(field('blight',0.9)*2.5,0,1),0.45),
  fwwood=contours(field('fwwood',1.2)+0.12*noise*np.clip(field('fwwood',1.2)*2.5,0,1),0.4),
  fwplain=contours(field('fwplain',1.0)+0.12*noise*np.clip(field('fwplain',1.0)*2.5,0,1),0.45),
  meadow1=contours(meadow,0.30),meadow2=contours(meadow,0.55),meadow3=contours(meadow,0.85),
)
# trees: poisson-ish sampling
def sample(F,thr,spacing,n,kind):
    out=[];cand=rng.uniform([X0,Y0],[X1,Y1],size=(n,2))
    cell={}
    for x,y in cand:
        i,j=int((x-X0)*RES),int((y-Y0)*RES)
        if not(0<=i<GW and 0<=j<GH) or F[j,i]<thr: continue
        key=(int(x/spacing),int(y/spacing)); ok=True
        for a in (-1,0,1):
            for b in (-1,0,1):
                for (px,py) in cell.get((key[0]+a,key[1]+b),()):
                    if (px-x)**2+(py-y)**2<spacing**2: ok=False;break
                if not ok:break
            if not ok:break
        if ok:
            cell.setdefault(key,[]).append((x,y))
            out.append([round(x,2),round(y,2),round(float(rng.uniform(.8,1.25)),2),kind,int(rng.integers(0,3))])
    return out
landmask=land>0.36
notwet=(bog<0.5)&(water<0.3)&(cliff<0.5)
trees=[]
trees+=sample(np.where(notwet&landmask,deep,0),0.6,0.48,90000,'d')
trees+=sample(np.where(notwet&landmask&(deep<0.6),np.maximum(wood,sparse*0.8),0),0.35,0.75,40000,'w')
reeds=sample(np.where(landmask,bog,0),0.55,0.55,30000,'r')
yy,xx=np.mgrid[0:GH,0:GW]; WX=xx/RES+X0; WY=yy/RES+Y0
clear=~((WX>-8.9)&(WX<8.9)&(WY>-10.9)&(WY<11.9))            # walls, ring trail and verge
clear&=~((WY>12.6)&(WY<15.4)&(WX>-12.5)&(WX<12.5))          # river
clear&=~((np.abs(WY)<0.9)&(WX>-11.2)&(WX<-8))               # road out of Darkguard
def _dist(x,y,poly):
    return min(math.hypot(x-p[0],y-p[1]) for p in poly)
trees=[tr for tr in trees if _dist(tr[0],tr[1],ribbon)>0.85]
trees=[tr for tr in trees if _dist(tr[0],tr[1],road)>0.55]
sep=[[p[0],p[1]+1.25] for r_ in (eastR,westR) for p in r_ if min(math.hypot(p[0]-j_[0],p[1]+1.25-j_[1]) for j_ in junctions)>1.6]
septrees=[]
for k in range(len(sep)-1):
    for s_ in range(3):
        x=sep[k][0]+rng.uniform(-.3,.3); y=sep[k][1]+rng.uniform(-.55,.55)
        septrees.append([round(x,2),round(y,2),round(float(rng.uniform(.9,1.3)),2),'x',int(rng.integers(0,3))])
trees=[tr for tr in trees if _dist(tr[0],tr[1],sep)>0.55]+septrees
trees=[tr for tr in trees if _dist(tr[0],tr[1],road)>0.55]
darkfog_skip=True
trees=[tr for tr in trees if min(math.hypot(tr[0]-b_['x'],tr[1]-b_['y']) for b_ in buildings)>1.1]
darkfog=[[round(p[0]+float(rng.uniform(-.3,.3)),2),round(p[1]+float(rng.uniform(-.2,.4)),2),round(float(rng.uniform(1.3,2.1)),2)] for p in sep[::3]]
mtrees=sample(np.where(clear&landmask&(deep<0.5),meadow,0),0.55,1.25,6000,'w')
trees+=mtrees
tufts=sample(np.where(clear&landmask,meadow,0),0.3,0.7,12000,'g')
# fill bare ground in the forest (spacer-room stretches with no terrain of their own) with light woodland
_content=np.maximum(deep,0)+np.maximum(bog,0)+np.maximum(water,0)+np.maximum(cliff,0)+np.maximum(sparse,0)+np.maximum(wood,0)*0.7+np.maximum(meadow,0)
_n2=ndi.gaussian_filter(rng.standard_normal((GH,GW)),1.6*RES); _n2/=_n2.std()
_bare=landmask&(_content<0.3)&((WX<-11)|(WY<-17))&(field('fwwood',1.2)<0.2)
_bareS=ndi.gaussian_filter(_bare.astype(float),1.0*RES)
fillF=np.where(landmask&((WX<-11)|(WY<-17)),_bareS*(0.75+0.35*_n2),0)
geo['fill']=contours(fillF,0.42,minarea=1.0)
geo['fill2']=contours(fillF,0.75,minarea=0.8)
trees+=sample(np.where(fillF>0.45,1.0,0),0.5,0.62,40000,'w')
trees+=sample(np.where((fillF>0.6)&(_n2>0.35),1.0,0),0.5,0.55,12000,'d')
tufts+=sample(np.where((fillF>0.3)&(_n2<0.4),1.0,0),0.5,0.8,12000,'g')
_black=field('black',0.9); _heart=field('blackheart',0.8); _br=field('bramble',0.9)
_mdclear=np.ones_like(_black,dtype=bool)
trees=[tr for tr in trees if not (tr[1]>15.2 and -4.5<tr[0]<12)]   # the Miden'nir side gets its own planting
tufts=[tr for tr in tufts if not (tr[1]>15.2 and -4.5<tr[0]<12)]
trees+=sample(np.where(_black>0.45,1.0,0),0.5,0.42,9000,'k')
thorns=sample(np.where(_br>0.4,1.0,0),0.5,0.4,6000,'t')
_inn=[(mpos[v][0],mpos[v][1]) for v in MD if mpos[v][2]==0 and re.search(r'Inn|Saloon|Jed|Dark Corner',R(v)['name'])]
buildings.append(dict(name='A Mysterious Inn',x=round(sum(p[0] for p in _inn)/len(_inn)-0.2,2),y=round(sum(p[1] for p in _inn)/len(_inn)-0.15,2),w=1.15,h=.8))
trees=[tr for tr in trees if math.hypot(tr[0]-buildings[-1]['x'],tr[1]-buildings[-1]['y'])>1.0]
def _cluster(ps,k):
    ps=sorted(ps); out=[]
    if not ps: return out
    xs=[p[0] for p in ps]; ys=[p[1] for p in ps]; cx,cy=sum(xs)/len(xs),sum(ys)/len(ys)
    for i_ in range(k):
        a_=i_*2*math.pi/k+0.4; out.append((cx+math.cos(a_)*0.95,cy+math.sin(a_)*0.8))
    return out
for (x,y) in _cluster(_lab,3): buildings.append(dict(name='',x=round(x,2),y=round(y,2),w=.7,h=.52))
for (x,y) in _cluster(_home,4): buildings.append(dict(name='',x=round(x,2),y=round(y,2),w=.7,h=.52))
trees=[tr for tr in trees if min([math.hypot(tr[0]-b_['x'],tr[1]-b_['y']) for b_ in buildings]+[9])>0.8]
trees=[tr for tr in trees if min([_dist(tr[0],tr[1],p) for p in sw_tracks]+[9])>0.5]
trees=[tr for tr in trees if math.hypot(tr[0]-bigtree[0],tr[1]-bigtree[1])>1.2]
# ---- south of the walls: the old path to Miden'nir and the Darkhaven Marina ----
southpath=[[-8.0,10.0],[-8.0,11.0],[-7.9,11.9],[-7.3,12.5],[-6.3,12.7],[-5.2,12.75],[-4.1,12.75],[-3.3,12.95],[-3.0,13.5],[-3.0,14.3],[-3.0,15.2],[-3.0,16.2]]
southpath=[[round(p[0]+float(rng.uniform(-.08,.08)),2),round(p[1]+float(rng.uniform(-.06,.06)),2)] for p in southpath]
southpath[0]=[-8.0,10.0]
precarious=[-8.0,11.0]
crumbling=[-3.0,13.35,15.0]
ruins=None
elm=[-4.7,11.95]
marina=dict(x=1.55,y=12.15,pier=[1.25,12.6,13.75],boats=[])
trees=[tr for tr in trees if _dist(tr[0],tr[1],southpath)>0.6 and math.hypot(tr[0]-elm[0],tr[1]-elm[1])>1.0 and math.hypot(tr[0]-marina['x'],tr[1]-marina['y'])>1.0]
tufts=[tr for tr in tufts if _dist(tr[0],tr[1],southpath)>0.4]
_mtn=field('mtn',0.8); _bl=field('blight',0.9)
peaks=sample(np.where(_mtn>0.45,1.0,0),0.5,0.95,6000,'m')
_fww=field('fwwood',1.0); _fwpl=field('fwplain',1.0)
for tr_ in sample(np.where(_fww>0.4,1.0,0),0.5,0.72,60000,'w'):
    if rng.random()<0.4: tr_[3]='d'
    trees.append(tr_)
tufts+=sample(np.where(_fwpl>0.4,1.0,0),0.5,0.7,8000,'g')
fwhach=[]
for x,y,th in []:
    if th=='cliff':
        for k_ in range(2):
            yy_=y-0.25+k_*0.5+rng.uniform(-.08,.08)
            fwhach.append([round(x+0.3,2),round(yy_,2),round(x-0.3-rng.uniform(0,.2),2),round(yy_+rng.uniform(-.1,.1),2)])
trees=[tr for tr in trees if not any(math.hypot(tr[0]-pk[0],tr[1]-pk[1])<0.7 for pk in peaks[:0])]
_sg=field('sg',1.0); _sgh=field('sghill',0.9); _sgw=field('sgwood',0.8)
_sgzone=lambda x,y: _sg[min(GH-1,max(0,int((y-Y0)*RES))),min(GW-1,max(0,int((x-X0)*RES)))]>0.35
trees=[tr for tr in trees if not _sgzone(tr[0],tr[1])]
tufts=[tr for tr in tufts if not _sgzone(tr[0],tr[1])]
hills=sample(np.where(_sgh>0.45,1.0,0),0.5,0.95,4000,'h')
trees+=sample(np.where((_sgw>0.4),1.0,0),0.5,0.5,3000,'d')
trees+=[tr for tr in sample(np.where((_sg>0.5)&(_sgh<0.4)&(_sgw<0.3),1.0,0),0.5,1.6,3000,'w')]
tufts+=sample(np.where((_sg>0.4)&(_sgh<0.5),1.0,0),0.5,0.75,6000,'g')
_gal=[(sgp[v][0],sgp[v][1]) for v in SGr if R(v)['name']=='Gallow Hill']
gallows=[_gal[0][0],_gal[0][1]] if _gal else None
_her=[(sgp[v][0],sgp[v][1]) for v in SGr if R(v)['name']=="The Hermit's Hut"]
if _her: buildings.append(dict(name="The Hermit's Hut",x=_her[0][0]+0.15,y=_her[0][1],w=.72,h=.52))
hills=[h_ for h_ in hills if not gallows or math.hypot(h_[0]-gallows[0],h_[1]-gallows[1])>0.9]
trees=[tr for tr in trees if not gallows or math.hypot(tr[0]-gallows[0],tr[1]-gallows[1])>0.9]
trees=[tr for tr in trees if not _her or math.hypot(tr[0]-_her[0][0],tr[1]-_her[0][1])>0.9]
sglabel=dict(x0=-7.5,x1=7.5,y=-14.9)
mountain=dict(x=2.4,y=26.0,w=5.2,h=3.6,cave=[2.0,22.9])
bridge=[[0,12.9],[0,15.2]]
midlink=[[0,11.6],[0,12.9]],[[0,15.2],[0,16.6]]
_mx=[mpos[v][0] for v in MD if mpos[v][2]==0]; 
midlabel=dict(x0=-3.5,x1=6.5,y=20.3)
# cliff hachures: for each cliff room, short strokes pointing away from land centre (west side cliffs -> strokes west)
hach=[]
for v,(x,y,z) in pts:
    if theme(v)=='cliff':
        for k in range(3):
            yy=y-0.35+k*0.35+rng.uniform(-.08,.08)
            hach.append([round(x+0.25,2),round(yy,2),round(x-0.35-rng.uniform(0,.25),2),round(yy+rng.uniform(-.1,.1),2)])
# trails: graph among trail rooms (plus voids), z=0
tset={v for v,p in pts if p[2]==0 and is_trail(v)}
adj=defaultdict(set)
for v in tset:
    for e in exits.get(v,[]):
        if e['to'] in tset and e['dir'] in DV: adj[v].add(e['to']); adj[e['to']].add(v)
seen=set(); chains=[]
def key(a,b): return (min(a,b),max(a,b))
for v in adj:
    if len(adj[v])!=2:
        for w in adj[v]:
            if key(v,w) in seen: continue
            ch=[v,w]; seen.add(key(v,w))
            while len(adj[ch[-1]])==2:
                nx=[u for u in adj[ch[-1]] if u!=ch[-2]][0]
                if key(ch[-1],nx) in seen: break
                seen.add(key(ch[-1],nx)); ch.append(nx)
            chains.append(ch)
trails=[]
for ch in chains:
    p=[[pos[v][0],pos[v][1]] for v in ch]
    # jitter interior points slightly for a hand-drawn line
    for k in range(1,len(p)-1): p[k]=[round(p[k][0]+rng.uniform(-.18,.18),2),round(p[k][1]+rng.uniform(-.18,.18),2)]
    trails.append(p)
trails.append([[-7,0],[-8,0],[-9,0]])  # from Darkguard gate into the forest
# mist banks over the weeping / fog areas
mist=[]
for v,(x,y,z) in pts:
    n=R(v)['name']
    if re.search(r'\bFog\b',n) and rng.random()<.6:
        mist.append([round(x+rng.uniform(-.5,.5),2),round(y+rng.uniform(-.5,.5),2),round(float(rng.uniform(1.2,2.4)),2)])
# label arc through the middle of the deep forest
ys=[p[1] for v,p in pts if theme(v)=='deep']; xs=[p[0] for v,p in pts if theme(v)=='deep']
label=dict(x0=-58,x1=-30,y=round(float(np.median(ys)),1)-0.5)
# ---------- the northern path ----------
NP=re.compile(r"Lost Between|Darker Forests|Dead Man|Path to the Cliffs|Tracking the Cliffs|West of Silver Lake")
nn={v for v,p in pos.items() if p[2]==0 and (NP.search(R(v)['name']) or (R(v)['flags']&8 and R(v)['area']=='' and p[1]<=-6 and p[0]<=-15))}
nadj=defaultdict(set)
for v in nn:
    for e in exits.get(v,[]):
        if e['to'] in nn and e['dir'] in DV: nadj[v].add(e['to']); nadj[e['to']].add(v)
# drop spacer rooms that are not part of the path
ch_=True
while ch_:
    ch_=False
    for v in list(nadj):
        if R(v)['flags']&8 and len(nadj[v])<=1 and not any(R(e['to'])['area']=='Forest of Tears' and not R(e['to'])['flags']&8 and e['to'] not in nn for e in exits.get(v,[])):
            for w_ in nadj[v]: nadj[w_].discard(v)
            del nadj[v]; ch_=True
# attach the rooms where the path meets the forest / lake / cliffs
for v in list(nadj):
    for e in exits.get(v,[]):
        t_=e['to']
        if t_ in pos and t_ not in nadj and pos[t_][2]==0 and R(t_)['area']=='Forest of Tears' and e['dir'] in DV:
            nadj[v].add(t_); nadj[t_]={v}
npath=[]; seen=set()
for v in nadj:
    if len(nadj[v])!=2:
        for w_ in nadj[v]:
            k=(min(v,w_),max(v,w_))
            if k in seen: continue
            ch=[v,w_]; seen.add(k)
            while len(nadj[ch[-1]])==2:
                nx=[u for u in nadj[ch[-1]] if u!=ch[-2]][0]
                k=(min(ch[-1],nx),max(ch[-1],nx))
                if k in seen: break
                seen.add(k); ch.append(nx)
            npath.append([[pos[u][0],pos[u][1]] for u in ch])
npath=[[c[0]]+[[round(q[0]+float(rng.uniform(-.14,.14)),2),round(q[1]+float(rng.uniform(-.14,.14)),2)] for q in c[1:-1]]+[c[-1]] for c in npath]
print('north path chains',[(c[0],c[-1],len(c)) for c in npath])

# ---------- trail around the walls ----------
pat=re.compile(r'Trail Rounding Darkhaven|Trail (North|South|East|West) of Dark|Outside Dark|Before the Precarious')
ringS={v for v,p in ndpos.items() if p[2]==0 and R(v)['area']=='New Darkhaven' and pat.search(R(v)['name']) and p[0]<=8}
gateS={v for v,p in ndpos.items() if p[2]==0 and re.match(r'Inside Dark\w+, \w+ Gate',R(v)['name'])}
nodes=ringS|gateS|{v for v,p in ndpos.items() if p[2]==0 and R(v)['flags']&8 and R(v)['area']=='' and p[0]<=8}
radj=defaultdict(set)
for v in nodes:
    for e in exits.get(v,[]):
        if e['to'] in nodes and e['dir'] in DV: radj[v].add(e['to']); radj[e['to']].add(v)
ch_=True
while ch_:
    ch_=False
    for v in list(radj):
        if v not in ringS and v not in gateS and len(radj[v])<=1:
            for w_ in radj[v]: radj[w_].discard(v)
            del radj[v]; ch_=True
seen=set(); ring=[]
for v in radj:
    if len(radj[v])!=2:
        for w_ in radj[v]:
            if (min(v,w_),max(v,w_)) in seen: continue
            ch=[v,w_]; seen.add((min(v,w_),max(v,w_)))
            while len(radj[ch[-1]])==2:
                nx=[u for u in radj[ch[-1]] if u!=ch[-2]][0]
                if (min(ch[-1],nx),max(ch[-1],nx)) in seen: break
                seen.add((min(ch[-1],nx),max(ch[-1],nx))); ch.append(nx)
            ring.append([[ndpos[u][0],ndpos[u][1]] for u in ch])
link=[[-8,0],[pos[820][0],pos[820][1]]]
cur=820; prevv=733
for _ in range(9):
    nx=[e['to'] for e in exits.get(cur,[]) if e['to'] in pos and e['to']!=prevv and e['dir'] in (8,9,12) and pos[e['to']][2]==0]
    nx=sorted(nx,key=lambda u:(0 if R(u)['flags']&8 else 1, pos[u][0]))
    if not nx: break
    prevv,cur=cur,(([u for u in nx if exits and any(e2['dir']==8 for e2 in exits.get(cur,[]) if e2['to']==u)] or nx)[0])
    link.append([pos[cur][0],pos[cur][1]])
link=link[:4]
print('link',link,[R(v)['name'] for v in [cur]])

ndS={v for v,r in rooms.items() if r['area']=='New Darkhaven'}
ndpos={764:(0,0,0)}; q=deque([764])
while q:
    v=q.popleft(); x,y,z=ndpos[v]
    for e in exits.get(v,[]):
        t_=e['to']
        if not (t_ in ndS or R(t_)['area'] in ('','visual')) or e['dir'] not in DV or t_ in ndpos: continue
        dx,dy,dz=DV[e['dir']]; ndpos[t_]=(x+dx,y+dy,z+dz); q.append(t_)
TX0,TX1,TY0,TY1=-16,22,-18,22
TW,TH=(TX1-TX0)*RES,(TY1-TY0)*RES
tf=np.zeros((TH,TW))
for v,(x,y,z) in ndpos.items():
    if z!=0 or abs(x)>9 or y<-11 or y>13: continue
    i,j=int((x-TX0)*RES),int((y-TY0)*RES); tf[j,i]+=1
tn=ndi.gaussian_filter(rng.standard_normal((TH,TW)),2*RES); tn/=tn.std()
tF=ndi.gaussian_filter(tf,1.4*RES)*(2*math.pi*(1.4*RES)**2)+0.2*tn
town=[]
for c in measure.find_contours(np.pad(tF,1),0.35):
    c=c-1
    if len(c)<8: continue
    town.append([(round(p[1]/RES+TX0,2),round(p[0]/RES+TY0,2)) for p in c[::2]])
geo['town']=town
trees=[tr for tr in trees if not (abs(tr[1])<0.6 and -12.2<tr[0]<-7.5)]
def _wet(x,y):
    i,j=int((x-X0)*RES),int((y-Y0)*RES)
    return 0<=i<GW and 0<=j<GH and water[j,i]>0.3
trees=[tr for tr in trees if not _wet(tr[0],tr[1])]
tufts=[tr for tr in tufts if not _wet(tr[0],tr[1])]
trees=[tr for tr in trees if tr[1]>-11 or min([_dist(tr[0],tr[1],p) for p in fwtracks]+[9])>0.45]
def _inpoly(x,y,P):
    c=False; n=len(P)
    for i in range(n):
        x1,y1=P[i]; x2,y2=P[(i+1)%n]
        if (y1>y)!=(y2>y) and x<(x2-x1)*(y-y1)/(y2-y1)+x1: c=not c
    return c
trees=[tr for tr in trees if not any(_inpoly(tr[0],tr[1],m['poly']) for m in fwmazes)]
tufts=[tr for tr in tufts if not any(_inpoly(tr[0],tr[1],m['poly']) for m in fwmazes)]
_hy=[b_['y'] for b_ in buildings if not b_['name'] and b_['x']<-5 and b_['y']>18.5]
if _hy:
    _lim=sum(_hy)/len(_hy)+0.05
    _clipped=[]
    for p in sw_tracks:
        q=[]
        for k_,pt in enumerate(p):
            if pt[0]<-5 and pt[1]>_lim:
                if q and k_>0:
                    a_=p[k_-1]; f_=(_lim-a_[1])/(pt[1]-a_[1]) if pt[1]!=a_[1] else 0
                    q.append([round(a_[0]+(pt[0]-a_[0])*f_,2),round(_lim,2)])
                break
            q.append(pt)
        if len(q)>1: _clipped.append(q)
    sw_tracks=_clipped
    print('refuge road clipped at',round(_lim,2))
hach+=fwhach
json.dump(dict(fwmazes=[dict(name=m['name'],cx=m['cx'],cy=m['cy'],poly=m['poly']) for m in fwmazes],fwtracks=fwtracks,peaks=peaks,fwlabel=fwlabel,lakelabel=lakelabel,hills=hills,gallows=gallows,sglabel=sglabel,southpath=southpath,crumbling=crumbling,ruins=ruins,elm=elm,marina=marina,swtracks=sw_tracks,precarious=precarious,bigtree=bigtree,thorns=thorns,mountain=mountain,bridge=bridge,midlink=midlink,midlabel=midlabel,buildings=buildings,road=road,ribbons=ribbons,darkfog=darkfog,ring=ring,link=link,tufts=tufts,geo=geo,trees=trees,reeds=reeds,hach=hach,trails=trails,mist=mist,label=label,bounds=[X0,Y0,X1,Y1]),open('fot.json','w'),separators=(',',':'))
print({k:len(v) for k,v in geo.items()},'trees',len(trees),'reeds',len(reeds),'trails',len(trails),'mist',len(mist),label)

# ---------- sub-areas of the Forest of Tears: trace the original directions ----------
sys.path.insert(0,'.'); from data import AREAS
routes={l.split('|',1)[0]:l.split('|',1)[1] for l in AREAS.strip().splitlines()}
SUB={"Lake of Tich'Pyga":"Lake of Tich'Pyga","Treetops and Canopy":"Treetops and Canopy","Major Oak":"Major Oak","Bartok Grove":"Bartok Grove",
     "The Shire":"The Shire","Sentinel":"The Sentinel","Graveyard":"The Graveyard","Kontaur":"Kontaur","D'Morian Lands":"D'Morian's Lands",
     "Florebit in Imm.":"Florebit In Immortalis Iuvenis","Tree of Life":"The Tree of Life","Silvermoon Outpost":"Silvermoon Outpost","Along the Forest Path":"Along the Forest Path"}
allpos=dict(ndpos); allpos.update(pos); allpos.update({v:(p[0],p[1],0) for v,p in wdisp.items()})
OK={'New Darkhaven','Forest of Tears','','visual','Western Trade Route'}
def walkroute(route,target):
    v=764; out=[allpos[v][:2]]; last=None
    toks=[x.strip() for x in route.replace(',',';').split(';') if x.strip()]
    for tok in toks:
        m=re.match(r'^#\s*(\d+)\s*(\w+)$',tok); n,dd=(int(m.group(1)),m.group(2)) if m else (1,tok)
        dd={'west':'w','east':'e','north':'n','south':'s'}.get(dd,dd)
        if dd not in ('n','s','e','w','ne','nw','se','sw','u','d'): continue
        for _ in range(n):
            nxt=[e for e in exits.get(v,[]) if e['name']==dd or e['cmd'].split(';')[-1]==dd]
            if not nxt: return out,v,last,'stuck'
            e=nxt[0]
            if R(e['to'])['area'] not in OK: return out,v,dd,R(e['to'])['area']
            v=e['to']
            if v not in allpos: return out,v,dd,'unplaced'
            out.append(allpos[v][:2])
            g=0
            while R(v)['flags']&8 and g<20:
                g+=1; c=[e2['to'] for e2 in exits.get(v,[]) if e2['name']==dd]
                if not c: break
                v=c[0]
                if R(v)['area'] not in OK: return out,v,dd,R(v)['area']
                out.append(allpos[v][:2])
    return out,v,last,'end'
fplaces=[]
for name,area in SUB.items():
    path,v,dd,res=walkroute(routes[name],area)
    print(f"{name:24} -> {res:28} at {allpos.get(v,('?',))[:2]} via {dd} | {R(v)['name']}")
    fplaces.append(dict(name=name if name not in ('Sentinel','Graveyard',"D'Morian Lands",'Florebit in Imm.') else {'Sentinel':'The Sentinel','Graveyard':'The Graveyard',"D'Morian Lands":"D'Morian's Lands",'Florebit in Imm.':'Florebit in Immortalis Iuvenis'}[name],
        route=routes[name].strip().rstrip(';'),room=R(v)['name'],dir=dd,path=path,note=None,group='fot',ok=(res==area)))
d=json.load(open('fot.json')); d['places']=fplaces; json.dump(d,open('fot.json','w'),separators=(',',':'))
# repair the two whose directions detour through the Western Trade Route: mark their forest entrance instead
def bfs(goal):
    prev={764:None}; q=deque([764])
    while q:
        v=q.popleft()
        if v==goal: break
        for e in exits.get(v,[]):
            t_=e['to']
            if t_ in prev or t_ not in allpos or allpos[t_][2]!=0 or R(t_)['area'] not in OK or e['dir'] not in DV: continue
            prev[t_]=v; q.append(t_)
    p=[];v=goal
    while v is not None: p.append(list(allpos[v][:2])); v=prev[v]
    return p[::-1]
DN={1:'n',2:'e',4:'s',8:'w',3:'ne',9:'nw',6:'se',12:'sw',16:'u',32:'d'}
for fp_ in fplaces:
    if fp_['ok']: continue
    area=SUB[[k for k in SUB if fp_['name'] in (k,)][0]] if fp_['name'] in SUB else None
    cands=[(v,e) for v in pos if v in S for e in exits.get(v,[]) if R(e['to'])['area']==area and e['dir'] in DN]
    v,e=sorted(cands,key=lambda c:-pos[c[0]][0])[0]
    fp_['path']=bfs(v); fp_['dir']=DN[e['dir']]; fp_['room']=R(v)['name']
    fp_['note']='Your directions reach it by way of the Western Trade Route; the pin marks where it meets the Forest of Tears.'
    print('repaired',fp_['name'],fp_['path'][-1],fp_['dir'])
d=json.load(open('fot.json')); d['places']=fplaces; json.dump(d,open('fot.json','w'),separators=(',',':'))
# landmark: V'laresch ('vla'), inside the Asgard Nexus, entered north from the deep woods
_r="#42 w;#7 n;cauldron;s;w"
_p,_v,_dd,_res=walkroute(_r,'Asgard Nexus')
print("V'laresch entrance",_p[-1],_dd,_res,R(_v)['name'])
fplaces.append(dict(name="V'laresch",route=_r,room=R(_v)['name'],dir=_dd,path=_p,kind='structure',group='fot',
    note="North into the Platform of Sacrifice (Asgard Nexus), then cauldron, s, w to The Eyes of Evil.",ok=_res=='Asgard Nexus'))
d=json.load(open('fot.json')); d['places']=fplaces; json.dump(d,open('fot.json','w'),separators=(',',':'))

# ---------- places reached from the Western Trade Route ----------
def bfsroute(goal_area=None,goal_room=None):
    prev={764:None}; q=deque([764]); hit=None
    while q:
        v=q.popleft()
        if (goal_room and v==goal_room) or (goal_area and R(v)['area']==goal_area): hit=v; break
        for e in exits.get(v,[]):
            t_=e['to']
            if t_ in prev: continue
            if not (R(t_)['area'] in OK or (goal_area and R(t_)['area']==goal_area)): continue
            if R(t_)['area']=='' and not R(t_)['flags']&8: continue
            prev[t_]=(v,e); q.append(t_)
    seq=[];x=hit
    while prev[x]: a_,e=prev[x]; seq.append((a_,e)); x=a_
    seq=seq[::-1]
    cmds=[e['cmd'] for a_,e in seq if not R(a_)['flags']&8]
    out=[];i=0
    while i<len(cmds):
        j=i
        while j<len(cmds) and cmds[j]==cmds[i]: j+=1
        out.append(cmds[i] if j-i==1 else f"#{j-i} {cmds[i]}"); i=j
    path=[list(allpos[a_][:2]) for a_,e in seq if a_ in allpos]
    last=[a_ for a_,e in seq if R(a_)['area']!=goal_area][-1] if goal_area else seq[-1][0]
    le=[e for a_,e in seq if a_==last][0]
    return ';'.join(out),path,last,le
DN2={1:'n',2:'e',4:'s',8:'w',3:'ne',9:'nw',6:'se',12:'sw',16:'u',32:'d',0:'here'}
WPL=[("Ezard's Fields","Ezard's Fields","Ezard's Fields"),("Old Thalos","Old Thalos","Old Thalos"),("Haven of Everlasting Light","Haven of Everlasting Light","Haven of Everlasting Light"),
     ("Blackcoggle Manor","Blackcoggle Manor",None),("The Grimdog Port Authority","The Grimdog Port Authority",None)]
for disp_,area,orig in WPL:
    if orig and orig in routes:
        r_=routes[orig].strip().rstrip(';'); pth,v,dd,res=walkroute(r_,area)
        ok=res==area
        if ok:
            fplaces.append(dict(name=disp_,route=r_,room=R(v)['name'],dir=dd,path=pth,note=None,group='wtr'))
        else:
            print('walk went via',res,'for',disp_)
            _r2,pth2,last,le=bfsroute(goal_area=area)
            fplaces.append(dict(name=disp_,route=r_,room=R(last)['name'],dir=DN2.get(le['dir'],'here'),path=pth2,group='wtr',
                note=f"Your directions reach it through {res}; it also opens off the trade route here, at {R(last)['name']} ({_r2})."))
    else:
        r_,pth,last,le=bfsroute(goal_area=area)
        note="Directions worked out from your map file." if area!='The Grimdog Port Authority' else "Pay the driver 300 coins, then go north into the port. Directions worked out from your map file."
        fplaces.append(dict(name=disp_,route=r_,room=R(last)['name'],dir=DN2.get(le['dir'],'here'),path=pth,note=note,group='wtr'))
    print('WTR place',disp_,fplaces[-1]['path'][-1],fplaces[-1]['dir'],fplaces[-1]['route'])
# Falcon's Nest Tavern landmark ('fal', room 2340)
r_,pth,last,le=bfsroute(goal_room=2340)
fplaces.append(dict(name="Falcon's Nest Tavern",route=r_,room=R(2340)['name'],dir='here',path=pth+[[buildings[0]['x'],round(buildings[0]['y']+buildings[0]['h']/2+0.45,2)]],kind='structure',group='wtr',
    note="A wooden tavern beside the trade route, with The Falcon's Talon and Jelarid's Track Shoppe across the lane. Directions worked out from your map file."))
print('tavern',r_)
d=json.load(open('fot.json')); d['places']=fplaces; json.dump(d,open('fot.json','w'),separators=(',',':'))

# ---------- places reached from Miden'nir ----------
allpos.update({v:p for v,p in mpos.items() if p[2]==0})
OK.add("Miden'nir")
def pin_at(room,exitdir):
    _,p,_,_=bfsroute(goal_room=room)
    return p+[list(allpos[room][:2])], DN2.get(exitdir,'here')
mplaces=[]
for name,area in [("Intrigues of the Miden'nir","Intrigues of the Miden'nir"),("Shattered Refuge","Shattered Refuge")]:
    r_=routes[name].strip().rstrip(';'); pth,v,dd,res=walkroute(r_,area)
    print('mid walk',name,res,pth[-1],dd,R(v)['name'])
    mplaces.append(dict(name=name,route=r_,room=R(v)['name'],dir=dd,path=pth,note=None,group='mid'))
# Southern Plains: say "story" at Jed's Desk, inside the inn
r_=routes['Southern Plains'].strip(); pth,v,dd,res=walkroute(r_,'Southern Plains')
mplaces.append(dict(name='Southern Plains',route=r_,room=R(v)['name'],dir='here',path=pth,group='mid',note="Say 'story' at Jed's Desk, inside the inn, to be taken there."))
print('mid SP',pth[-1],R(v)['name'])
# Moria and the Southern Mountain Range also open off Miden'nir, though your usual routes go another way
for name,room,ed,how in [('Moria',3422,6,"through the brambles (open brambles, then southeast)"),('Southern Mountain Range',1060,16,"by climbing up from Gazing Upon Mount Doom")]:
    pth,dd=pin_at(room,ed)
    mplaces.append(dict(name=name,route=routes[name].strip().rstrip(';'),room=R(room)['name'],dir=dd,path=pth,group='mid',
        note=f"Your directions reach it another way; it also opens off Miden'nir here, {how}."))
    print('mid link',name,pth[-1],dd)
for p_ in fplaces:
    if p_['name']=='Along the Forest Path':
        p_['path']=p_['path']+[[-12.4,6.0],[-13.0,9.0],[-12.6,10.8]]; p_['dir']='here'
        p_['note']="Placed roughly: the path runs between the Forest of Tears and the Shattered Refuge."
_r,_p,_l,_e=bfsroute(goal_room=695)
mplaces.append(dict(name='Darkhaven Marina',route=_r,room=R(695)['name'],dir='here',path=_p+[[2.45,12.3]],kind='structure',
    note="A boathouse and pier on the Darkhaven River, just outside Darkwall. Directions worked out from your map file."))
print('marina route',_r)
d=json.load(open('fot.json')); d['places']=fplaces+mplaces; json.dump(d,open('fot.json','w'),separators=(',',':'))

# ---------- places reached from the Shadow Grove ----------
allpos.update({v:p for v,p in sgp.items() if p[2]==0})
OK.add('Shadow Grove')
TULL="n;n;n;n;n;n;nw;nw;nw;n;n;nw;nw;sw;n"
SGL=[('Wendle Mansion','Wendle Mansion',routes.get('Wendle Mansion')),('Ofcol','Ofcol',routes.get('Ofcol')),
     ('Keep of Lomar','Keep of Lomar',HOMETOWNS_R.get('Keep of Lomar (Human)') if 'HOMETOWNS_R' in dir() else None),
     ('Tullfuhrzky Manor','Tullfuhrzky Manor',TULL),('Green Forest','Green Forest',routes.get('Green Forest')),
     ('Northern Trade Route','Northern Trade Route',None),('The Ashen Forest','The Ashen Forest',routes.get('Ashen Forest')),
     ('The Forgotten Woods','The Forgotten Woods',routes.get('Forgotten Woods'))]
try:
    from directions import HOMETOWNS as _HT
except ImportError:
    from data import HOMETOWNS as _HT
_ht={l.split('|',1)[0]:l.split('|',1)[1] for l in _HT.strip().splitlines()}
SGL[2]=('Keep of Lomar','Keep of Lomar',_ht['Keep of Lomar (Human)'])
_prefer={'The Ashen Forest':(1384 if False else None)}
splaces=[]
def sg_links(area):
    out=[]
    for v in SGr:
        for e in exits.get(v,[]):
            if R(e['to'])['area']==area and e['dir'] in DN2 and v in sgp: out.append((v,e))
    return out
for name,area,orig in SGL:
    done=False
    if orig:
        r_=orig.strip().rstrip(';'); pth,v,dd,res=walkroute(r_,area)
        if res==area and R(v)['area']=='Shadow Grove':
            splaces.append(dict(name=name,route=r_,room=R(v)['name'],dir=dd,path=pth,group='sg',note=None)); done=True
            print('sg ok',name,pth[-1],dd)
    if not done:
        L=sg_links(area)
        if area=='The Ashen Forest': L=sorted(L,key=lambda ve: sgp[ve[0]][0])   # the hut-side link first
        v,e=L[0]
        _r,_p,_l,_e=bfsroute(goal_room=v)
        how=f"opens off the Shadow Grove here ({R(v)['name']}, {e['cmd']})"
        if orig:
            note=f"Your directions reach it another way; it also {how}."
            r_=orig.strip().rstrip(';')
        else:
            note=f"Directions worked out from your map file; it {how}."
            r_=_r+';'+e['cmd']
        splaces.append(dict(name=name,route=r_,room=R(v)['name'],dir=DN2.get(e['dir'],'here'),path=_p+[list(allpos[v][:2])],group='sg',note=note))
        print('sg link',name,sgp[v][:2],DN2.get(e['dir']),'orig' if orig else 'bfs')
splaces=[p_ for p_ in splaces if p_['name']!='Northern Trade Route']
_r,_p,_l,_e=bfsroute(goal_room=720)
_ex=[e for e in exits[720] if R(e['to'])['area']=='Northern Trade Route'][0]
splaces.append(dict(name='Northern Trade Route',route=_r+';'+_ex['cmd'],room=R(720)['name'],dir=DN2.get(_ex['dir'],'here'),path=_p+[list(allpos[720][:2])],group='sg',
    note="Its entrance is just outside Darktrail, the north gate. Directions worked out from your map file."))
print('ntr',_r+';'+_ex['cmd'],allpos[720][:2])
splaces=[p_ for p_ in splaces if p_['name']!='The Forgotten Woods']
# ---------- places reached from the Forgotten Woods ----------
allpos.update({v:(x,y,0) for v,(x,y,z) in fwp.items()})
OK.add('The Forgotten Woods')
_RT=dict(routes); _RT.update({k:v for k,v in _ht.items()})
def _comp(cmds):
    out=[];i=0
    while i<len(cmds):
        j=i
        while j<len(cmds) and cmds[j]==cmds[i]: j+=1
        out.append(cmds[i] if j-i==1 else f"#{j-i} {cmds[i]}"); i=j
    return ';'.join(out)
def bfsseq(goal_area,extra=()):
    prev={764:None}; q=deque([764]); hit=None
    while q:
        v=q.popleft()
        if R(v)['area']==goal_area: hit=v; break
        for e in exits.get(v,[]):
            t_=e['to']
            if t_ in prev: continue
            a=R(t_)['area']
            if not (a in OK or a==goal_area or a in extra): continue
            if a=='' and not R(t_)['flags']&8: continue
            prev[t_]=(v,e); q.append(t_)
    if hit is None: return None
    seq=[];x=hit
    while prev[x]: a_,e=prev[x]; seq.append((a_,e)); x=a_
    return seq[::-1]
WT=[("Pixie Forest","Pixie Forest","Pixie Forest",()),
    ("Nevermore","Nevermore","Nevermore",()),
    ("Corruption of Anciastra","Corruption of Anciastra","Corruption of Anciastra",()),
    ("Vale of Nidaros","Vale of Nidaros","Vale of Nidaros (Gnome)",()),
    ("Valley of Mysts","Valley of Mysts","Valley of Mysts",()),
    ("The Tower of Zenothir","The Tower of Zenothir","Tower of Zenothir",()),
    ("Wyvern's Tower","Wyvern's Tower","Wyvern's Tower",()),
    ("La Chute D'eau De L'ancients","La Chute D'eau De L'ancients","La Chute D'eau De L'ancients",()),
    ("Raven Tor","Raven Tor","Raven Tor",()),
    ("New Ofcol","New Ofcol","New Ofcol",()),
    ("Gnarlwood Forest","Gnarlwood Forest",None,()),
    ("Keep of Mahn-Tor (Ogre Village)","The Keep of Mahn-Tor","Keep of Mahn-Tor (Ogre Village)",()),
    ("Reomyr Village","Reomyr Village","Reomyr Village (Pixie)",("Pixie Forest",))]
wplaces=[]
for disp_,area,key,extra in WT:
    user=_RT.get(key).strip().rstrip(';') if key and _RT.get(key) else None
    seq=bfsseq(area,extra)
    if seq is None: print('WOODS PLACE NOT FOUND',disp_); continue
    wi=[i for i,(a_,e) in enumerate(seq) if R(a_)['area']=='The Forgotten Woods']
    if not wi: print('route to',disp_,'does not pass the Woods'); continue
    pin,pe=seq[wi[-1]]
    path=[list(allpos[a_][:2]) for a_,e in seq[:wi[-1]+1] if a_ in allpos]
    worked=_comp([e['cmd'] for a_,e in seq if not R(a_)['flags']&8])
    # the exit your own directions take out of the Woods (walked over the whole map, mapped areas or not)
    ux=None
    if user:
        v_=764; trail=[v_]; ok_=True
        for tok in [x.strip() for x in user.split(';') if x.strip()]:
            m_=re.match(r'^#\s*(\d+)\s*(.+)$',tok); n_,dd2=(int(m_.group(1)),m_.group(2)) if m_ else (1,tok)
            for _ in range(n_):
                nx_=[e for e in exits.get(v_,[]) if e['name']==dd2 or e['cmd'].split(';')[-1]==dd2 or e['cmd']==tok]
                if not nx_: ok_=False; break
                v_=nx_[0]['to']; trail.append(v_)
                g_=0
                while R(v_)['flags']&8 and g_<30:
                    c_=[e['to'] for e in exits.get(v_,[]) if e['name']==dd2]
                    if not c_: break
                    v_=c_[0]; trail.append(v_); g_+=1
            if not ok_: break
        tgt_=extra[0] if extra else area
        ks=[k for k,r_ in enumerate(trail) if R(r_)['area']==tgt_]
        if ks and ks[0]>0:
            k0=ks[0]; back=[k for k in range(k0-1,-1,-1) if R(trail[k])['area']=='The Forgotten Woods']
            nxa=next((R(trail[j])['area'] for j in range(back[0]+1,len(trail)) if R(trail[j])['area'] not in ('',)),None) if back else None
            if back and nxa==tgt_ and trail[back[0]] in fwp:
                ux=trail[back[0]]; nxt=trail[back[0]+1]
                ex_=[e for e in exits[ux] if e['to']==nxt]
                if ex_: pin,pe=ux,ex_[0]
        if ux is not None:
            _r2,_p2,_l2,_e2=bfsroute(goal_room=ux)
            path=_p2+[list(allpos[ux][:2])]
    # does your own directions walk straight from placed areas into it?
    direct=False
    if user:
        pth,v_,dd_,res_=walkroute(user,area)
        direct=(res_==area and R(v_)['area']=='The Forgotten Woods')
        if direct: path=pth; pin=v_; pe=dict(dir=next((k for k,n in DN2.items() if n==dd_),0))
    if user and direct: note=None
    elif user and extra: note=f"Your directions go through {extra[0]}, which opens off the Forgotten Woods here; this pin marks that exit."
    elif user: note="Your directions reach it by another route; this pin marks where it opens off the Forgotten Woods, and the traced route follows the way in from the Shadow Grove."
    else: note="Directions worked out from your map file; it opens off the Forgotten Woods here."
    wplaces.append(dict(name=disp_,route=user or worked,room=R(pin)['name'] or 'a spacer room',dir=DN2.get(pe['dir'],'here'),path=path,group='fw',note=note))
    print('fw place',disp_,'|',R(pin)['name'][:28],allpos[pin][:2],DN2.get(pe['dir']),'| yours' if user else '| worked out','| direct' if direct else '')
# ---------- mobs in the Forgotten Woods, found by walking your directions ----------
def walk_full(route):
    v=764; prev=None
    for tok in [x.strip() for x in route.split(';') if x.strip()]:
        nx=[e for e in exits.get(v,[]) if e['name']==tok or e['cmd'].split(';')[-1]==tok or e['cmd']==tok]
        if not nx: return None
        prev,v=v,nx[0]['to']; g=0
        while R(v)['flags']&8 and g<40:                      # spacer rooms: follow the chain, round bends too
            c=[e for e in exits.get(v,[]) if e['to']!=prev]
            if not c: break
            c.sort(key=lambda e:0 if e['name']==tok else 1)
            prev,v=v,c[0]['to']; g+=1
    return v
MOBS=[("Dobra","n;n;n;n;n;n;e;e;n;ne;ne;ne;se;e;se;e;nw;n;n;ne;ne;w;nw;nw;e;n;n;ne;n;ne;w;w;se;sw;w;w;s;sw;w;nw;w;w;nw;w;nw;sw;n",
       "Your directions pass briefly through the Northern Trade Route (not drawn yet); the traced route stays inside the Woods."),
      ("Catobeplas","n;n;n;n;n;n;nw;nw;nw;w;n;e;e;e;e;s;w;sw;s;sw;s;s;sw;sw;s;s;ne;ne;n;nw;w;nw;nw;w;nw;s;e;ne;ne;u;se;w",
       "Your directions come in through Ofcol and New Ofcol (not drawn yet); the traced route follows the way in from the Shadow Grove.")]
for name,route,note in MOBS:
    v=walk_full(route)
    if v is None or v not in fwp: print('MOB NOT PLACED',name,v); continue
    _r,_p,_l,_e=bfsroute(goal_room=v)
    wplaces.append(dict(name=name,route=route,room=R(v)['name'],dir='here',path=_p+[list(allpos[v][:2])],kind='mob',group='fw',note=note))
    print('fw mob',name,'|',R(v)['name'],allpos[v][:2])
# routes cross a maze as one step through its middle, not room by room
def _collapse_mazes(path):
    out=[]; i=0
    while i<len(path):
        k=next((j for j,m in enumerate(fwmazes) if _inp(path[i][0],path[i][1],m['poly'])),None)
        if k is None: out.append(path[i]); i+=1; continue
        j=i
        while j<len(path) and _inp(path[j][0],path[j][1],fwmazes[k]['poly']): j+=1
        out.append([fwmazes[k]['cx'],fwmazes[k]['cy']]); i=j
    return out
for p_ in wplaces: p_['path']=_collapse_mazes(p_['path'])
# ---------- directions policy: cards show only directions that came from you ----------
try: import directions as _dm
except ImportError: import data as _dm
def _exp(route):
    out=[]
    for tok in (route or '').split(';'):
        tok=tok.strip()
        if not tok: continue
        m=re.match(r'^#\s*(\d+)\s*(.+)$',tok)
        out+=([m.group(2).strip()]*int(m.group(1))) if m else [tok]
    return out
_USERR=set()
for _k in dir(_dm):
    _v=getattr(_dm,_k)
    if _k.isupper() and isinstance(_v,str):
        if '|' in _v:
            for _l in _v.strip().splitlines():
                if '|' in _l: _USERR.add(';'.join(_exp(_l.split('|',1)[1])))
        else: _USERR.add(';'.join(_exp(_v)))                  # the painting routes
_USERR|={';'.join(_exp(r_)) for _n,r_,_x in MOBS}              # Dobra and Catobeplas, as you typed them
def _is_user(route): return ';'.join(_exp(route)) in _USERR
def _walk_trail(route):
    v=764; prev=None; trail=[v]
    for tok in _exp(route):
        nx=[e for e in exits.get(v,[]) if e['name']==tok or e['cmd'].split(';')[-1]==tok or e['cmd']==tok]
        if not nx: continue                                   # a command (open, give, say...), not a step
        prev,v=v,nx[0]['to']; trail.append(v); g=0
        while R(v)['flags']&8 and g<40:
            c=[e for e in exits.get(v,[]) if e['to']!=prev]
            if not c: break
            c.sort(key=lambda e:0 if e['name']==tok else 1)
            prev,v=v,c[0]['to']; trail.append(v); g+=1
    return trail
def _segments(trail):
    segs=[]; cur=[]
    for r_ in trail:
        p_=allpos.get(r_)
        if p_ is None:
            if cur: segs.append(cur); cur=[]
            continue
        q_=[round(float(p_[0]),2),round(float(p_[1]),2)]
        if not cur or cur[-1]!=q_: cur.append(q_)
    if cur: segs.append(cur)
    return segs
_PARENT={'fw':'the Forgotten Woods','sg':'the Shadow Grove','mid':"Miden'nir",'wtr':'the Western Trade Route'}
_NOTE={"V'laresch":"Inside the Asgard Nexus. The pin marks where it opens off the deep woods of the Forest of Tears.",
  "Ezard's Fields":"Your directions reach it through The Shire; this pin marks where it also opens off the Western Trade Route, at A Stone Covered Roadway.",
  'Blackcoggle Manor':None,'Thalos':None,'The Grimdog Port Authority':None,
  "Falcon's Nest Tavern":"A wooden tavern beside the trade route, with The Falcon's Talon and Jelarid's Track Shoppe across the lane.",
  'Moria':"This pin marks where it also opens off Miden'nir, through the brambles.",
  'Southern Mountain Range':"This pin marks where it also opens off Miden'nir, by climbing up from Gazing Upon Mount Doom.",
  'Darkhaven Marina':"A boathouse and pier on the Darkhaven River, just outside Darkwall.",
  'Northern Trade Route':"Its entrance is just outside Darktrail, the north gate.",
  'Gnarlwood Forest':"This pin marks where it opens off the Forgotten Woods.",
  'Dobra':None,'Catobeplas':None}
_GAP=" Part of your directions passes through areas that aren't drawn yet, so the traced line breaks there."
_MORE={}
for _l in (getattr(_dm,'MORE_DIRECTIONS','') or '').strip().splitlines():
    if '|' in _l: _n,_r=_l.split('|',1); _MORE[_n.strip()]=_r.strip()
_ALT={}
for _l in (getattr(_dm,'ALT_DIRECTIONS','') or '').strip().splitlines():
    if '|' in _l: _n,_r=_l.split('|',1); _ALT[_n.strip()]=_r.strip()
for p_ in fplaces+mplaces+splaces+wplaces:                    # directions you have since given
    if p_['name'] in _MORE: p_['route']=_MORE[p_['name']]
    elif p_['name'] in _RT and not (p_.get('route') and _is_user(p_['route'])): p_['route']=_RT[p_['name']].strip().rstrip(';')
    if p_['name'] in _ALT and ';'.join(_exp(_ALT[p_['name']]))!=';'.join(_exp(p_.get('route') or '')): p_['alt']=[_ALT[p_['name']]]
_nodir=[]
for p_ in fplaces+mplaces+splaces+wplaces:
    r_=p_.get('route')
    if p_['name'] in _NOTE: p_['note']=_NOTE[p_['name']]
    elif (p_.get('note') or '').startswith('Your directions reach') and p_.get('group') in _PARENT: p_['note']=f"This pin marks where it opens off {_PARENT[p_['group']]}."
    if not r_ or not _is_user(r_):
        _nodir.append(p_['name']); p_['route']=None; p_['noroute']=True; p_['path']=p_['path'][-1:]; continue
    segs=[_collapse_mazes(s) for s in _segments(_walk_trail(r_))]
    segs=[s for s in segs if s]
    pin=p_['path'][-1]
    if segs:
        last=segs[-1][-1]
        if last!=pin:
            if math.dist(last,pin)<3: segs[-1].append(pin)
            else: segs.append([pin])
    else: segs=[[pin]]
    p_['segs']=segs
    if len(segs)>1: p_['note']=((p_.get('note') or '')+_GAP).strip()
print('cards with no directions from you:',_nodir)
# ---------- anchors for the Ashen Forest: where each room that touches an already-mapped room has to sit ----------
_ASH={v for v,r in rooms.items() if r['area']=='The Ashen Forest'}
_known={}
for _nm,_d in (('town',ndpos),('grove',sgp),('woods',fwp)):
    for _v,_p in _d.items(): _known.setdefault(_v,(_nm,_p))
_ASHLINKS=[]
for _v in _ASH:
    for _e in exits.get(_v,[]):
        _t=_e['to']
        if _t not in _ASH and _t in _known and _e['dir'] in DV:
            _dx,_dy,_dz=DV[_e['dir']]; _px,_py=_known[_t][1][:2]; _ASHLINKS.append(dict(ash=_v,partner=_t,area=_known[_t][0],x=_px-_dx,y=_py-_dy,px=_px,py=_py))
for _t,_l in exits.items():
    if _t in _ASH or _t not in _known: continue
    for _e in _l:
        if _e['to'] in _ASH and _e['dir'] in DV:
            _dx,_dy,_dz=DV[_e['dir']]; _px,_py=_known[_t][1][:2]; _ASHLINKS.append(dict(ash=_e['to'],partner=_t,area=_known[_t][0],x=_px+_dx,y=_py+_dy,px=_px,py=_py))
_TRACK={}
_isspacer=lambda v: bool(rooms[v]['flags']&8) and rooms[v]['area']==''
_rev=defaultdict(list)
for _v,_l in exits.items():
    for _e in _l: _rev[_e['to']].append(_v)
for _i,_a in enumerate(_ASHLINKS):
    _TRACK[f"ash{_i}"]=[_a['x'],_a['y']]; _TRACK[f"partner{_i}"]=[_a['px'],_a['py']]
    # where the partner is a spacer room, follow the chain of spacer rooms on to the real room beyond it (every one of them is on the map already)
    _chain=[]; _cur=_a['partner']
    if _isspacer(_cur):
        _seen={_a['ash']}
        while True:
            _chain.append(_cur); _seen.add(_cur)
            _nx=[n for n in [e['to'] for e in exits.get(_cur,[])]+_rev[_cur] if n not in _seen and n in _known]
            if not _nx: break
            _cur=_nx[0]
            if not _isspacer(_cur): _chain.append(_cur); break
    else: _chain=[_a['partner']]
    _a['chain']=_chain
    for _k,_r in enumerate(_chain): _TRACK[f"chain{_i}_{_k}"]=list(_known[_r][1][:2])
print('Ashen Forest anchors:',len(_ASHLINKS),Counter(a['area'] for a in _ASHLINKS))
d=json.load(open('fot.json')); d['places']=fplaces+mplaces+splaces+wplaces; _DHX=[1230,2832,1236,20899,1239]
for _k,_r in enumerate(_DHX): _TRACK[f"dhx{_k}"]=list(ndpos[_r][:2])
# every room already on the map in Darkhaven, the Shadow Grove and the Forgotten Woods, tracked to where it ends up on the finished map (used by the layout editors)
_CTX={}
for _src,_dd in (('DH',ndpos),('Grove',sgp),('FW',fwp)):
    for _v,_p in _dd.items():
        if _v in _CTX or R(_v)['area']=='visual': continue                # (the "visual" rooms are decoration, not rooms)
        _CTX[_v]=_src; _TRACK[f"cx{_v}"]=[_p[0],_p[1]]
# the Forest of Tears' own layout (rooms, other levels, the spacer rooms hanging off it) and the Western Trade Route's drawn road, tracked the same way (used by the Forest of Tears layout editor)
for _v,_p in pos.items(): _TRACK[f"ft{_v}"]=[_p[0],_p[1]]
for _v in _WTCHAIN: _TRACK[f"wt{_v}"]=[wpos[_v][0],wpos[_v][1]]
d['ctxsrc']={str(k):v for k,v in _CTX.items()}
d['track']=_TRACK; d['ashlinks']=_ASHLINKS; d['dhx']=_DHX; json.dump(d,open('fot.json','w'),separators=(',',':'))
