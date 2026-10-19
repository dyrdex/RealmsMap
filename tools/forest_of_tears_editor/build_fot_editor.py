# The layout editor for the Forest of Tears and the Lake of Tich'Pyga (owner, Oct 12: configure both areas together; the whole section is redrawn afterwards).
#   python3 build_fot_editor.py <final map state (json, from FINAL_DUMP=...)> <out html>     (run inside src/legacy, with fot_editor_template.html beside it)
# Fixed rooms (cannot move): every Darkhaven, Shadow Grove and Forgotten Woods room (w['track'] 'cx<id>', source in w['ctxsrc']), exactly where it is on the finished map.
# Movable too (grp 'wt', unlocked on request Oct 12): the Western Trade Route's drawn road (w['track'] 'wt<id>', fot_extract.py's _WTCHAIN), starting where it is on the map.
# Movable rooms (area 'FT'):
#   - every Forest of Tears room (683), starting where the finished map has it (w['track'] 'ft<id>'; levels other than ground are shifted by LV, as in the Ashen editor)
#   - every Lake of Tich'Pyga room (276), laid out fresh from TinTin's exits (it is a single drawn lake on the map today, with no rooms), then stretched
#     per axis so that the rooms that touch Darkhaven, the Forest of Tears and the Forgotten Woods land by the rooms they link to
#   - the spacer rooms that join two of those rooms (or one of them to a fixed room), however long the chain; dead-end spacer stubs are left off
# Nothing else is filtered: the sub-areas (Bartok Grove, Major Oak ...) and other areas beside these two stay off, as they are markers on the map.
import sys, os, json
from collections import defaultdict, Counter, deque
import numpy as np
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here); sys.path.insert(1, os.path.abspath('..'))   # (src/legacy is the working folder; src for editor_spread, maplib)
import ashen_forest as AF

w = json.load(open(sys.argv[1])); out = sys.argv[2]
rooms, exits = AF._world(); DV = AF.DV
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd', 0: '?'}
isspacer = lambda v: v in rooms and bool(rooms[v]['flags'] & 8) and rooms[v]['area'] == ''
FA, LA = 'Forest of Tears', "Lake of Tich'Pyga"
LV = 0.55
tr = w['track']

# ---- fixed rooms ----
CTX = {}; cpos = {}
for k, src in w['ctxsrc'].items(): CTX[int(k)] = src; cpos[int(k)] = tuple(tr['cx' + k])
FOT = {v for v, r in rooms.items() if r['area'] == FA}
LAKE = {v for v, r in rooms.items() if r['area'] == LA}
WT = set()                                                   # the Western Trade Route's drawn road: movable (owner, Oct 12), starting where it is on the finished map
for k in tr:
    if k.startswith('wt'):
        v = int(k[2:])
        if v not in CTX and v not in FOT: WT.add(v)
UNLOCK_FW = [5634, 5635, 5636, 5637, 5638]                   # Forgotten Woods rooms unlocked on request (owner, Oct 13): movable, starting where the map has them
assert all(CTX[v] == 'FW' for v in UNLOCK_FW)
FWU = set(UNLOCK_FW)
for v in UNLOCK_FW: CTX.pop(v)                               # (cpos keeps their map position: the starting spot)
assert not (FOT | LAKE | WT) & set(CTX)

# ---- the spacer rooms that join the two areas to each other and to fixed rooms ----
rev = defaultdict(list)
for v, l in exits.items():
    for e in l: rev[e['to']].append(v)
raw_nb = defaultdict(set)
for v, l in exits.items():
    for e in l: raw_nb[v].add(e['to']); raw_nb[e['to']].add(v)
core = FOT | LAKE | WT | FWU
cand = set(); q = deque(core)
while q:
    v = q.popleft()
    for t in raw_nb[v]:
        if t not in cand and t not in CTX and t not in core and isspacer(t): cand.add(t); q.append(t)
scope = core | set(CTX)
keep = set(); stubs = set(); seen = set()
for s in sorted(cand):
    if s in seen: continue
    comp = {s}; st = [s]
    while st:
        x = st.pop()
        for t in raw_nb[x]:
            if t in cand and t not in comp: comp.add(t); st.append(t)
    seen |= comp
    real = {u for x in comp for u in raw_nb[x] if u in scope}
    (keep if len(real) >= 2 else stubs).update(comp)
S = core | keep
SP = {v for v in S if isspacer(v)}
assert not S & set(CTX)

def links(v):
    res = [(e['to'], DV[e['dir']]) for e in exits.get(v, []) if e['dir'] in DV and e['to'] != v]
    for u in rev[v]:
        for e in exits.get(u, []):
            if e['to'] == v and e['dir'] in DV and u != v: d = DV[e['dir']]; res.append((u, (-d[0], -d[1], -d[2])))
    return res

# ---- the Forest of Tears' levels, as fot_extract.py lays them out (820 at the entrance) ----
zf = {820: 0}; q = deque([820])
while q:
    v = q.popleft()
    for e in exits.get(v, []):
        t = e['to']
        if not (r_ := rooms.get(t)) or t in zf or e['dir'] not in DV: continue
        if not (r_['area'] == FA or (r_['flags'] & 8 and r_['area'] == '')): continue
        zf[t] = zf[v] + DV[e['dir']][2]; q.append(t)

# ---- positions ----
start = {}; lvl = {}
for v in S:
    if f'ft{v}' in tr:
        z = zf.get(v, 0); lvl[v] = z; start[v] = [tr[f'ft{v}'][0] + LV * z, tr[f'ft{v}'][1] - LV * z]
    elif v in WT: lvl[v] = 0; start[v] = list(tr[f'wt{v}'])
    elif v in FWU: lvl[v] = 0; start[v] = list(cpos[v])
known = dict(cpos)
for v, p in start.items(): known[v] = tuple(p)
# the rest (the lake, and any Forest of Tears room the map does not hold) in pieces by TinTin's own exits, with levels
rest = sorted(S - set(start)); piece3 = {}; comps = []
for s in rest:
    if s in piece3: continue
    loc = {s: (0, 0, 0)}; q = deque([s]); piece3[s] = len(comps)
    while q:
        x = q.popleft()
        for t, d in links(x):
            if t in rest and t not in loc: loc[t] = tuple(a + b for a, b in zip(loc[x], d)); piece3[t] = len(comps); q.append(t)
    comps.append(loc)
fit = []; placed = {}; raw0 = {}
for k, loc in enumerate(comps):
    pl = {v: (p[0] + LV * p[2], p[1] - LV * p[2]) for v, p in loc.items()}
    pairs = []; seenp = set()
    for v in loc:
        for t, d in links(v):
            if t in known and t not in loc and (v, t) not in seenp:
                seenp.add((v, t)); g = (1.0, 0.0) if d[2] else (-d[0], -d[1]); pairs.append((pl[v], (known[t][0] + g[0], known[t][1] + g[1])))
    if pairs:
        m = [np.mean([a[i] - b[i] for a, b in pairs]) for i in (0, 1)]           # TinTin's own offset (no stretching)
        raw0.update({v: [p[0] - m[0], p[1] - m[1]] for v, p in pl.items()})
        sc = []
        for i in (0, 1):
            xa = np.array([a[i] for a, b in pairs]); xb = np.array([b[i] for a, b in pairs])
            if len(pairs) >= 3 and np.ptp(xa) >= 5:
                s_, t_ = np.polyfit(xa, xb, 1); s_ = float(np.clip(s_, 0.8, 1.6)); t_ = float(np.mean(xb - s_ * xa))
            else: s_ = 1.0; t_ = float(np.mean(xb - xa))
            sc.append((s_, t_))
        fit.append((k, len(loc), len(pairs), [round(s_, 3) for s_, t_ in sc]))
        placed.update({v: [sc[0][0] * p[0] + sc[0][1], sc[1][0] * p[1] + sc[1][1]] for v, p in pl.items()})
for v, p in placed.items(): start[v] = p; lvl[v] = round(comps[piece3[v]][v][2])
orph = [k for k in range(len(comps)) if not any(v in placed for v in comps[k])]
if orph:                                                                   # (no exit to anything on the map: parked in a column east of the lake)
    lp = [p for v, p in start.items() if v in LAKE]
    ex = max(p[0] for p in lp) + 3; ey = min(p[1] for p in lp); PARKED = []
    for k in orph:
        for v, p in comps[k].items(): start[v] = [ex + p[0] + LV * p[2], ey + p[1] - LV * p[2]]; lvl[v] = p[2]; raw0[v] = list(start[v]); PARKED.append(v)
        ey += 1.4
assert set(start) == S, S - set(start)

# ---- TinTin's own layout per piece, anchored to the starting spots (the "where TinTin's exits suggest" button) ----
fpos = {}; piece = {}; pieces = []
for s in sorted(S):
    if s in fpos: continue
    k = len(pieces); fpos[s] = (0, 0); piece[s] = k; mem = [s]; q = deque([s])
    while q:
        x = q.popleft()
        for t, d in links(x):
            if t in S and d[2] == 0 and t not in fpos: fpos[t] = (fpos[x][0] + d[0], fpos[x][1] + d[1]); piece[t] = k; mem.append(t); q.append(t)
    pieces.append(mem)
raw = {}
for k, mem in enumerate(pieces):
    own = [v for v in mem if v in raw0]
    if own: raw.update({v: raw0[v] for v in mem if v in raw0})
    ref = [v for v in mem if v not in raw0]
    if ref:
        off = (np.mean([start[v][0] - LV * lvl.get(v, 0) - fpos[v][0] for v in ref]), np.mean([start[v][1] + LV * lvl.get(v, 0) - fpos[v][1] for v in ref]))
        for v in ref: raw[v] = [fpos[v][0] + off[0] + LV * lvl.get(v, 0), fpos[v][1] + off[1] - LV * lvl.get(v, 0)]
xy = {v: list(p) for v, p in start.items()}
for P in (xy, raw):
    cells = defaultdict(list)
    for v in sorted(P): cells[(round(P[v][0] / 0.3), round(P[v][1] / 0.3))].append(v)
    for vs in cells.values():
        for k, v in enumerate(vs[1:], 1): P[v][0] += 0.42 * k; P[v][1] += 0.42 * k

# ---- rooms and exits ----
def exlist(v):
    res = []
    for e in exits.get(v, []):
        r = rooms.get(e['to'])
        if not r: continue
        res.append(f"{DN.get(e['dir'], '?')} → {r['name'] or 'spacer room'}" + (f" ({r['area']})" if r['area'] and r['area'] not in (FA, LA) else ''))
    return res
GROUP = {v: ('lk' if v in LAKE else 'wt' if v in WT else 'fw' if v in FWU else 'ft') for v in S}
for v in sorted(SP):                                                       # a spacer room takes the group of the real room it hangs off
    nb = [u for u in raw_nb[v] if u in FOT | LAKE]
    if nb and v not in WT and v not in FWU: GROUP[v] = 'lk' if nb[0] in LAKE and not any(u in FOT for u in nb) else 'ft'
R = []
for v in sorted(CTX):
    r = rooms[v]
    R.append(dict(id=v, name=r['name'], terrain='', void=isspacer(v), lvl=0, x=round(cpos[v][0], 2), y=round(cpos[v][1], 2), x0=round(cpos[v][0], 2), y0=round(cpos[v][1], 2), fixed=True, src=CTX[v]))
for v in sorted(S):
    r = rooms[v]; sp = v in SP
    R.append(dict(id=v, name='' if sp else r['name'], terrain='' if sp else r['terrain'], void=sp, lvl=lvl.get(v, 0), area='FT', grp=GROUP[v], piece=piece[v],
                  x=round(xy[v][0], 2), y=round(xy[v][1], 2), x0=round(raw[v][0], 2), y0=round(raw[v][1], 2), ex=exlist(v)))
V = {r['id'] for r in R}
pair = defaultdict(lambda: [False, False, False])
for v in V:
    for e in exits.get(v, []):
        t = e['to']
        if t not in V or t == v: continue
        k = (min(v, t), max(v, t)); pair[k][0 if v == k[0] else 1] = True
        if e['dir'] not in (16, 32): pair[k][2] = True
EDG = [[a, b, 'two' if (f and r and flat) else ('one' if flat else 'ud')] for (a, b), (f, r, flat) in sorted(pair.items())]
lk = sorted(k for k in pair if (k[0] in S) != (k[1] in S))
cnt = Counter(CTX.values()); tz = Counter(lvl.get(v, 0) for v in S)
audit = dict(fot=len(FOT), lake=len(LAKE), spacers=len(SP), fot_sp=sum(1 for v in SP if GROUP[v] == 'ft'), lake_sp=sum(1 for v in SP if GROUP[v] == 'lk'), stubs=len(stubs),
             exits=sum(1 for k in pair if k[0] in S and k[1] in S), links=len(lk), pieces=len(pieces),
             dh=cnt['DH'], grove=cnt['Grove'], fw=cnt['FW'], wtr=len(WT), fwu=len(FWU), levels=', '.join(f'{z:+d}: {n}' for z, n in sorted(tz.items())),
             parked=len(PARKED) if orph else 0, lake_in_map=sum(1 for v in LAKE if f'ft{v}' in tr), fot_untracked=sum(1 for v in FOT if f'ft{v}' not in tr))
rd = lambda poly: [[round(x, 2), round(y, 2)] for x, y in poly]
trk = list(w['fwtracks']) + list(w['swtracks']) + [w['road'], w['southpath'], w['link']] + list(w['ring']) + [t for t in w.get('etrtracks', []) if len(t) > 1] \
    + list(w.get('ntrroad', [])) + list(w.get('dirtroads', []))
ctx = dict(land=[rd(p) for p in w['geo']['land']], water=[rd(p) for p in w['geo']['water']],
           tracks=[rd(t) for t in trk if len(t) > 1], mazes=[dict(poly=rd(m['poly'])) for m in w['fwmazes']], town=[-7.4, -9.4, 7.4, 9.4],
           labels=[[0, 0.4, 'Darkhaven', 2.4], [3, -14.2, 'Shadow Grove', 1.5], [1, -47.3, 'Forgotten Woods', 2.4]] +
                  [[(a['x0'] + a['x1']) / 2, a['y'], 'Forest of Tears', 2.4] for a in [w['label']]])
D = dict(rooms=R, edges=EDG, groups=[], ctx=ctx, audit=audit, unlocked=sorted(WT | FWU))
t = open(os.path.join(here, 'fot_editor_template.html'), encoding='utf-8').read()
open(out, 'w', encoding='utf-8').write(t.replace('__DATA__', json.dumps(D, separators=(',', ':'))))
json.dump(dict(rooms=[{k: r[k] for k in ('id', 'terrain', 'void', 'lvl', 'fixed', 'src', 'area', 'grp', 'piece') if k in r} for r in R], edges=EDG),
          open(os.path.join(here, 'fot_editor_edges.json'), 'w'), separators=(',', ':'))

# ---- report ----
print('AUDIT', audit)
print('parked (no exits to anything here):', [(v, rooms[v]['name'][:22]) for v in (PARKED if orph else [])])
print('lake/other pieces placed (comp, rooms, link pairs, scale+shift x/y):', fit, '| unanchored pieces', len(orph))
print('pieces', sorted((len(p) for p in pieces), reverse=True)[:12], '...', len(pieces))
print('fixed rooms', len(CTX), dict(cnt), '| edges', len(EDG), '| file', os.path.getsize(out) // 1024, 'KB')
