import json, re, sys
sys.path.insert(0,'.')
exec(open('parse_world.py').read())
from collections import deque, defaultdict, Counter
AREA='New Darkhaven'
DV={1:(0,-1,0),2:(1,0,0),4:(0,1,0),8:(-1,0,0),3:(1,-1,0),9:(-1,-1,0),6:(1,1,0),12:(-1,1,0),16:(0,0,1),32:(0,0,-1)}
DN={1:'north',2:'east',4:'south',8:'west',3:'northeast',9:'northwest',6:'southeast',12:'southwest',16:'up',32:'down',0:'special'}
nd={v for v,r in rooms.items() if r['area']==AREA}
inside=lambda t: t in nd or rooms[t]['area'] in ('','visual')
pos={764:(0,0,0)}; q=deque([764])
while q:
    v=q.popleft(); x,y,z=pos[v]
    for e in exits.get(v,[]):
        t=e['to']
        if not inside(t) or e['dir'] not in DV or t in pos: continue
        dx,dy,dz=DV[e['dir']]; pos[t]=(x+dx,y+dy,z+dz); q.append(t)
R=lambda v:rooms[v]
# ground-level path network (rooms of this area + spacer rooms), as edges
edges=set()
for v,(x,y,z) in pos.items():
    if z!=0 or R(v)['area']=='visual': continue
    for e in exits.get(v,[]):
        t=e['to']
        if t in pos and pos[t][2]==0 and e['dir'] in DV and R(t)['area']!='visual':
            a,b=(x,y),pos[t][:2]
            kind='trail' if (R(v)['terrain'] not in ('City','DH','Inside') and R(t)['terrain'] not in ('City','DH','Inside')) else 'street'
            edges.add((min(a,b),max(a,b),kind))
# terrain patches outside the streets
patch=defaultdict(list)
for v,(x,y,z) in pos.items():
    t=R(v)['terrain']
    if z==0 and R(v)['area']==AREA and t in ('Forest','Water','Field','Desert','Hills','Mountains'):
        patch[t].append((x,y))
# streets
streets=defaultdict(set)
SN=['Justice Road','Horizon Road','Market Street','Law Avenue','Park Avenue','Thieves Alley','Falcon Road','Vertic Avenue','Hawk Street']
for v,(x,y,z) in pos.items():
    if z or R(v)['area']!=AREA: continue
    for s in SN:
        if s in R(v)['name']: streets[s].add((x,y))
# districts by room-name patterns
D=[('Temple of Thoric','Notre Dame|Altar|Hall of the Blessed|Hall of the Fallen|Charity|Alms','temple'),
   ('Castle Darkhawk','Castle Darkhawk|Barracks|Throne Room|A Stairway|A Staircase','castle'),
   ('Town grove','Forested Path|Under the Trees','grove'),
   ('Inns & taverns','Grim Smile|Sleeping Dragon|Warm Fire','inn'),
   ('Magic shops','Poshir|Zelah|Xygian','shop'),
   ('Food market','Carnivore|Bakery|Dairy','shop'),
   ('Bank & outfitter','Bank of New|Young Adventurer','shop'),
   ('Warehouses','Dark Corner|Dark Warehouse|empty warehouse|Courier|Shining Emerald|Quills','dark'),
   ('Auction & arms','Auction House|Damaged Goods|Solid Parry|Daring Attack|Tagerte','shop'),
   ('Clothier','Annir','shop'),('Stables','Companions and Mounts','shop'),
   ('Public park','Public Park Grounds','grove'),('Marina','Marina','shop')]
districts=[]
for name,pat,kind in D:
    ps=[p for v,p in pos.items() if R(v)['area']==AREA and p[2]==0 and re.search(pat,R(v)['name'])]
    ps=list({(p[0],p[1]) for p in ps}); seen=set(); cl=[]
    for p in ps:
        if p in seen: continue
        st=[p]; seen.add(p); c=[]
        while st:
            a_=st.pop(); c.append(a_)
            for qq in ps:
                if qq not in seen and abs(qq[0]-a_[0])<=1 and abs(qq[1]-a_[1])<=1: seen.add(qq); st.append(qq)
        cl.append(c)
    cl.sort(key=len,reverse=True)
    for k,c in enumerate(cl):
        districts.append(dict(name=name,kind=kind,x0=min(p[0] for p in c),x1=max(p[0] for p in c),y0=min(p[1] for p in c),y1=max(p[1] for p in c),n=len(c),main=k==0,total=len(ps)))
# gates
gates=[]
for v,p in pos.items():
    n=R(v)['name']
    m=re.match(r'Inside (Dark\w+), (\w+) Gate',n)
    if m: gates.append(dict(name=m.group(1),side=m.group(2),x=p[0],y=p[1]))
# levels summary
levels=Counter(p[2] for v,p in pos.items() if R(v)['area']==AREA)
# exits out of the area
outs=[]
for v,(x,y,z) in pos.items():
    if R(v)['area']!=AREA: continue
    for e in exits.get(v,[]):
        t=e['to']; ta=R(t)['area']
        if ta in (AREA,'','visual'): continue
        outs.append(dict(fx=x,fy=y,fz=z,room=R(v)['name'],vnum=v,dir=DN.get(e['dir'],'special'),cmd=e['cmd'],to=ta,toroom=R(t)['name'],hidden=bool(e['flags']&1)))
# kinds of exits
OVER={'Shadow Grove','Forest of Tears','Western Trade Route','Northern Trade Route','Eastern Trade Route','The Ashen Forest','Moria','Southern Mountain Range','Along the Forest Path'}
for o in outs:
    o['kind']='overworld' if o['to'] in OVER else ('below' if o['to']=='Sewer' else 'inner')
data=dict(edges=[list(a)+list(b)+[k] for a,b,k in edges],patches=patch,streets={k:sorted(v) for k,v in streets.items()},districts=districts,gates=gates,
          outs=outs,levels=dict(levels),square=[0,0],
          rooms=len(nd))
json.dump(data,open('nd.json','w'))
print(len(edges),'edges',{k:len(v) for k,v in patch.items()},len(districts),'districts',gates,len(outs),'exits')
print(Counter((o['kind'],o['to']) for o in outs))
