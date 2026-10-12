import json, sys
exec(open('extract.py').read().split("# exits out of the area")[0])
sys.path.insert(0,'.'); from data import AREAS
routes={l.split('|',1)[0]:l.split('|',1)[1] for l in AREAS.strip().splitlines()}
# shortest path through the city between rooms (directional exits only)
def path_to(goal):
    prev={764:None}; q=deque([764])
    while q:
        v=q.popleft()
        if v==goal: break
        for e in exits.get(v,[]):
            t=e['to']
            if t in pos and t not in prev and e['dir'] in DV and pos[t][2]==0 and R(t)['area']!='visual':
                prev[t]=v; q.append(t)
    p=[];v=goal
    while v is not None: p.append(pos[v][:2]); v=prev[v]
    return p[::-1]
import re as _re
def walk(route):
    v=764; out=[pos[v][:2]]
    for tok in [x.strip() for x in route.split(';')]:
        m=_re.match(r'^#\s*(\d+)\s*(\w+)$',tok); n,dd=(int(m.group(1)),m.group(2)) if m else (1,tok)
        if dd not in ('n','s','e','w','ne','nw','se','sw','u','d'): continue
        for _ in range(n):
            nxt=[e['to'] for e in exits.get(v,[]) if e['name']==dd or e['cmd'].split(';')[-1]==dd]
            if not nxt: return out
            v=nxt[0]
            if v not in pos or pos[v][2]!=0 or R(v)['area'] not in (AREA,''): return out
            out.append(pos[v][:2])
            guard=0
            while R(v)['flags']&8 and guard<20:
                guard+=1
                cont=[e['to'] for e in exits.get(v,[]) if e['name']==dd] or [e['to'] for e in exits.get(v,[]) if pos.get(e['to'],(None,None))[:2]!=out[-2]]
                if not cont: break
                v=cont[0]
                if v not in pos: return out
                out.append(pos[v][:2])
    return out
P=[('Darkhaven Art Gallery',797,'n',None),('Dragon Cult',802,'n',None),('Warehouse',969,'sw',None),('Halls of Knowledge',1454,'d',None),
   ('Isle of the Monkeys',1454,'d','Inside the Halls of Knowledge: go down, then follow the halls west to the portal room.'),
   ('A Moment in Nature',1454,'d','Inside the Halls of Knowledge: go down, then follow the halls west to the portal room.')]
places=[]
for name,room,d,note in P:
    pth=walk(routes[name]) or path_to(room)
    places.append(dict(name=name,route=routes[name],room=R(room)['name'],dir=d,path=pth,note=note))
def guild(G):
    gs={v for v,r in rooms.items() if r['area']==G}
    prev={764:None}; q=deque([764]); hit=None
    while q:
        v=q.popleft()
        if v in gs: hit=v; break
        for e in exits.get(v,[]):
            t_=e['to']
            if t_ in prev: continue
            if not (t_ in gs or R(t_)['area']==AREA or (R(t_)['flags']&8 and R(t_)['area']=='')): continue
            prev[t_]=(v,e); q.append(t_)
    seq=[];x=hit
    while prev[x]: p_,e=prev[x]; seq.append((p_,e)); x=p_
    seq=seq[::-1]
    cmds=[e['cmd'] for p_,e in seq if not (R(p_)['flags']&8)]
    # compress into speedwalk
    out=[];i=0
    while i<len(cmds):
        j=i
        while j<len(cmds) and cmds[j]==cmds[i]: j+=1
        out.append(cmds[i] if j-i==1 else f"#{j-i} {cmds[i]}"); i=j
    last=[p_ for p_,e in seq if not (R(p_)['flags']&8)][-1]
    d=[e for p_,e in seq if p_==last][0]['name']
    pth=[pos[p_][:2] for p_,e in seq if p_ in pos]
    return dict(name=G.replace('The ',''),route=';'.join(out),room=R(last)['name'],dir=d,path=pth,note=None,kind='guild')
def route_to(goal):
    prev={764:None}; q=deque([764])
    while q:
        v=q.popleft()
        if v==goal: break
        for e in exits.get(v,[]):
            t_=e['to']
            if t_ in prev or t_ not in pos or pos[t_][2]!=0: continue
            if not (R(t_)['area']==AREA or (R(t_)['flags']&8 and R(t_)['area']=='')): continue
            prev[t_]=(v,e); q.append(t_)
    seq=[];x=goal
    while prev[x]: p_,e=prev[x]; seq.append((p_,e)); x=p_
    seq=seq[::-1]
    cmds=[e['cmd'] for p_,e in seq if not (R(p_)['flags']&8)]
    out=[];i=0
    while i<len(cmds):
        j=i
        while j<len(cmds) and cmds[j]==cmds[i]: j+=1
        out.append(cmds[i] if j-i==1 else f"#{j-i} {cmds[i]}"); i=j
    return ';'.join(out),[pos[p_][:2] for p_,e in seq]+[pos[goal][:2]]
for name,v,kind,note in [('Castle Darkhawk',12550,'structure',None),('Notre Dame de Sioux',780,'structure',None),
                         ('Sonoria',1310,'mob','Found at the Altar to Thoric, at the far end of Notre Dame de Sioux.')]:
    r_,pth=route_to(v)
    places.append(dict(name=name,route=r_,room=R(v)['name'],dir='here',path=pth,note=note,kind=kind,vnum=v))
for G in ('The Guild of Origin','The Guild of Spirit','The Guild of Nature'):
    places.append(guild(G))
town=dict(streets={k:sorted(v) for k,v in streets.items()},gates=gates,blocks=[d for d in districts if d['kind']!='grove' or True],
          water=patch.get('Water',[]),rooms=len(nd),levels=dict(levels))
json.dump(dict(town=town,places=places),open('nd2.json','w'))
for p in places: print(p['name'],p['path'][-1],len(p['path']))
