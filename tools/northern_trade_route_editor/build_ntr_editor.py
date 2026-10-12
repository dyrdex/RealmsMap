# The layout editor for the Northern Trade Route.
#   python3 build_ntr_editor.py <final map state (json, from FINAL_DUMP=...)> <out html>
# Fixed (locked) rooms: every room already on the finished map in Darkhaven, the Shadow Grove and the Forgotten Woods, where it is.
# Movable rooms: the Northern Trade Route from its entrance, past the Shadow Grove, through the Woods, to the long bridge.
import sys, os, json, math
from collections import defaultdict, Counter, deque
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ashen_forest as AF

w = json.load(open(sys.argv[1])); out = sys.argv[2]
fot = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fot.json')))
rooms, exits = AF._world(); DV = AF.DV
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd', 0: '?'}
tr = w['track']
isspacer = lambda v: bool(rooms[v]['flags'] & 8) and rooms[v]['area'] == ''

# ---- the road: every room of the area, every spacer room joined to it, taken from its entrance up to the bridge ----
NTR = {v for v, r in rooms.items() if r['area'] == 'Northern Trade Route'}
rev = defaultdict(list)
for v, l in exits.items():
    for e in l: rev[e['to']].append(v)
S = set(NTR); dq = deque(NTR)
while dq:
    v = dq.popleft()
    for t in [e['to'] for e in exits.get(v, [])] + rev[v]:
        if t not in S and isspacer(t): S.add(t); dq.append(t)
nb = defaultdict(set)
for v in S:
    for e in exits.get(v, []):
        if e['to'] in S: nb[v].add(e['to']); nb[e['to']].add(v)
ENTRANCE = 1334                                                  # "Entrance to the Northern Trade Route", beside Darkhaven's north gate
dist = {ENTRANCE: 0}; dq = deque([ENTRANCE])
while dq:
    v = dq.popleft()
    for u in nb[v]:
        if u not in dist: dist[u] = dist[v] + 1; dq.append(u)
assert len(dist) == len(S), 'the road is not one piece'
LIMIT = 47                                                       # the long bridge (rooms 4133-4135); the next room, 4136, is "Entering the Barren Peaks"
INC = {v for v, d in dist.items() if d <= LIMIT}
beyond = [v for v in S if v not in INC and v in NTR]

# ---- the rooms already on the map, tracked to where they ended up ----
CTX = {int(k): s for k, s in fot['ctxsrc'].items() if 'cx' + k in tr}
cpos = {v: tuple(tr['cx' + str(v)][:2]) for v in CTX}
maxx = max(p[0] for p in cpos.values())

# ---- TinTin's own layout of the road (north is up), anchored to the room it joins in Darkhaven ----
nbE = defaultdict(list)
for v in INC:
    for e in exits.get(v, []):
        t = e['to']
        if t in INC and e['dir'] in DV:
            d = DV[e['dir']]; nbE[v].append((t, d)); nbE[t].append((v, (-d[0], -d[1], -d[2])))
comp = {ENTRANCE: (0, 0, 0)}; q = deque([ENTRANCE])
while q:
    x = q.popleft()
    for t, d in nbE[x]:
        if t not in comp: comp[t] = (comp[x][0] + d[0], comp[x][1] + d[1], comp[x][2] + d[2]); q.append(t)
assert all(v in comp for v in INC), [v for v in INC if v not in comp]
anchors = []
for e in exits.get(ENTRANCE, []):
    if e['to'] in CTX and e['dir'] in DV: d = DV[e['dir']]; anchors.append((cpos[e['to']][0] - d[0], cpos[e['to']][1] - d[1]))
ax = sum(a[0] for a in anchors) / len(anchors); ay = sum(a[1] for a in anchors) / len(anchors)
LV = 0.55
raw = {v: (ax + p[0] + LV * p[2], ay + p[1] - LV * p[2]) for v, p in comp.items()}          # where TinTin's exits put them
sx = max(maxx, 76) + 8 - min(p[0] for p in raw.values())                                    # the road starts off to the east of everything
xy = {v: [p[0] + sx, p[1]] for v, p in raw.items()}
cells = defaultdict(list)
for v in sorted(xy): cells[(round(xy[v][0] / 0.3), round(xy[v][1] / 0.3))].append(v)
for vs in cells.values():
    for k, v in enumerate(vs[1:], 1): xy[v][0] += 0.42 * k; xy[v][1] += 0.42 * k; raw[v] = (raw[v][0] + 0.42 * k, raw[v][1] + 0.42 * k)

# ---- rooms and exits for the editor ----
def exlist(v):
    res = []
    for e in exits.get(v, []):
        r = rooms[e['to']]; res.append(f"{DN.get(e['dir'], '?')} \u2192 {r['name'] or 'spacer room'}" + (f" ({r['area']})" if r['area'] and r['area'] != 'Northern Trade Route' else ''))
    return res
R = []
for v in sorted(CTX):
    r = rooms[v]
    R.append(dict(id=v, name=r['name'], terrain='', void=isspacer(v), lvl=0, x=round(cpos[v][0], 2), y=round(cpos[v][1], 2), x0=round(cpos[v][0], 2), y0=round(cpos[v][1], 2), fixed=True, src=CTX[v]))
for v in sorted(INC):
    r = rooms[v]
    R.append(dict(id=v, name=r['name'] if v in NTR else '', terrain=r['terrain'] if v in NTR else '', void=(v not in NTR), lvl=comp[v][2], area='NTR',
                  x=round(xy[v][0], 2), y=round(xy[v][1], 2), x0=round(raw[v][0], 2), y0=round(raw[v][1], 2), ex=exlist(v)))
V = {r['id'] for r in R}
pair = defaultdict(lambda: [False, False, False])
for v in V:
    for e in exits.get(v, []):
        t = e['to']
        if t not in V or t == v: continue
        k = (min(v, t), max(v, t)); pair[k][0 if v == k[0] else 1] = True
        if e['dir'] not in (16, 32): pair[k][2] = True
EDG = [[a, b, 'two' if (f and r and flat) else ('one' if flat else 'ud')] for (a, b), (f, r, flat) in pair.items()]
ntr_pairs = [k for k in pair if k[0] in INC and k[1] in INC]
exits_total = sum(1 for v in INC for e in exits.get(v, []) if e['to'] in INC and e['to'] != v)
links = {k for k in pair if (k[0] in INC) != (k[1] in INC)}
audit = dict(ntr=len([v for v in INC if v in NTR]), spacers=len([v for v in INC if v not in NTR]), exits=exits_total, exits_total=exits_total, links=len(links),
             dh=sum(1 for s in CTX.values() if s == 'DH'), grove=sum(1 for s in CTX.values() if s == 'Grove'), fw=sum(1 for s in CTX.values() if s == 'FW'), beyond=len(beyond))
rd = lambda poly: [[round(x, 2), round(y, 2)] for x, y in poly]
ctx = dict(land=[rd(p) for p in w['geo']['land']], water=[rd(p) for p in w['geo']['water']],
           tracks=[rd(t) for t in list(w['fwtracks']) + list(w['swtracks']) + [w['road'], w['southpath'], w['link']] + list(w['ring']) if len(t) > 1],
           mazes=[dict(poly=rd(m['poly'])) for m in w['fwmazes']], town=[-7.4, -9.4, 7.4, 9.4],
           labels=[[0, 0.4, 'Darkhaven', 2.4], [3, -14.2, 'Shadow Grove', 1.5], [1, -47.3, 'Forgotten Woods', 2.4]])
D = dict(rooms=R, edges=EDG, groups=[], ctx=ctx, audit=audit)
json.dump(D, open('ntr_editor_data.json', 'w'), separators=(',', ':'))
t = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ntr_editor_template.html'), encoding='utf-8').read()
open(out, 'w', encoding='utf-8').write(t.replace('__DATA__', json.dumps(D, separators=(',', ':'))))
xs = [r['x'] for r in R if r.get('area') == 'NTR']; ys = [r['y'] for r in R if r.get('area') == 'NTR']
print('AUDIT', audit)
print('road rooms start at x %.0f..%.0f, y %.0f..%.0f' % (min(xs), max(xs), min(ys), max(ys)), '| edges', len(EDG), '| file', os.path.getsize(out) // 1024, 'KB')
print('road rooms by terrain:', dict(Counter(r['terrain'] for r in R if r.get('area') == 'NTR')))
print('links between the road and rooms already on the map:', sorted(links)[:20])
