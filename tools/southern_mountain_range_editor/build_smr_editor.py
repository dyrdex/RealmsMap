# The layout editor for the Southern Mountain Range (owner, Oct 13: set up the area layout editor first, adjust room configurations, render the map afterwards).
#   python3 build_smr_editor.py <final map state (json, from FINAL_DUMP=...)> <out html>     (run inside src, with smr_editor_template.html beside it)
# Fixed rooms (cannot move), exactly where they are on the finished map (w['track']):
#   every Darkhaven, Shadow Grove and Forgotten Woods room (w['track'] 'cx<id>', source in w['ctxsrc']), every Forest of Tears / Lake of Tich'Pyga room ('ft<id>')
#   and the Western Trade Route's drawn road ('wt<id>').
# Movable rooms (area 'SM'):
#   - every Southern Mountain Range room (597) in pieces laid out from TinTin's own exits (levels shifted by LV, as in the Forest of Tears editor); a piece that
#     touches the map is anchored to the rooms it links to (shifted, and stretched per axis when it touches in several places), the rest is parked south of them
#   - the spacer rooms that join two rooms of the range, or one of them to a fixed room, however long the chain; dead-end spacer stubs are left off
# Nothing else is filtered: sub-areas and other areas its exits lead to (Wastelands, Elemental Canyon, World Housing ...) stay off.
import sys, os, json
from collections import defaultdict, Counter, deque
import numpy as np
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import ashen_forest as AF

w = json.load(open(sys.argv[1])); out = sys.argv[2]
rooms, exits = AF._world(); DV = AF.DV
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd', 0: '?'}
isspacer = lambda v: v in rooms and bool(rooms[v]['flags'] & 8) and rooms[v]['area'] == ''
SA, LA = 'Southern Mountain Range', "Lake of Tich'Pyga"
LV = 0.55
tr = w['track']

# ---- fixed rooms ----
CTX = {}; cpos = {}
for k, src in w['ctxsrc'].items(): CTX[int(k)] = src; cpos[int(k)] = tuple(tr['cx' + k])
# The Forest of Tears, the lake's ring path and the Western Trade Route are where the owner's Forest of Tears layout put them (ft_layout_final.json, which
# ft_merge.py draws from), NOT at w['track']'s 'ft<id>' / 'wt<id>' positions: those are the forest's OLD positions (median 6.6 rooms away; found Oct 14).
FL = json.load(open(os.path.join(here, 'ft_layout_final.json'))); FE = json.load(open(os.path.join(here, 'fot_editor_edges.json')))
FPOS = dict(zip(FL['ids'], zip(FL['xs'], FL['ys']))); FHID = set(FL['hidden']) | {1891}
FINFO = {r['id']: r for r in FE['rooms']}
for v, r in FINFO.items():
    if r.get('fixed') or v in FHID or v not in FPOS or v not in rooms: continue
    CTX[v] = {'ft': 'FT', 'lk': 'LK', 'wt': 'WT', 'fw': 'FW'}[r['grp']]; cpos[v] = tuple(FPOS[v])
if 20036 not in CTX: CTX[20036] = 'FT'; cpos[20036] = tuple(tr['ft20036'][:2])         # (a dead-end spacer stub the forest editor left off: where the old map had it)
# A visual-only connection (owner, Oct 14; not in TinTin's map): room 559 --ne--> a new spacer room --n--> room 670 'Before the Ashen Forest'. Room 670 (an
# Ashen Forest room, where the Ashen save puts it) is unlocked; the Ashen room it leads north to (2864) is shown fixed so its neighbour is visible.
AF_ROOM, AF_NEXT, FICT = 670, 2864, 990001
AL = json.load(open(os.path.join(here, 'ashen_layout_final.json'))); AFPOS = dict(zip(AL['ids'], zip(AL['xs'], AL['ys']))); assert AF_ROOM in AFPOS and AF_NEXT in AFPOS and not {AF_ROOM, AF_NEXT} & set(AL['hidden'])
CTX[AF_NEXT] = 'AF'; cpos[AF_NEXT] = tuple(AFPOS[AF_NEXT])
SMR = {v for v, r in rooms.items() if r['area'] == SA}
assert not SMR & set(CTX)
# Forest of Tears rooms unlocked on request (owner, Oct 14): the whole Sparse Woodlands trail, 1514 -> 1553, i.e. the 18 rooms named 'The Sparse Woodlands'
# and the rooms with other names between them (1533-1538 Canyon Edge ... Harsh, Dry Lands, 1540, 1543, 1544, 1547, 1548), plus the spacer rooms (chains of them
# too) that join two of those rooms. Movable (grp 'ft'), starting exactly where the map has them; they do not take part in anchoring the range.
_nb = defaultdict(set)
for _v, _l in exits.items():
    for _e in _l: _nb[_v].add(_e['to']); _nb[_e['to']].add(_v)
TRAIL = sorted(v for v in CTX if CTX[v] == 'FT' and rooms[v]['name'] == 'The Sparse Woodlands') + list(range(1533, 1539)) + [1540, 1543, 1544, 1547, 1548]
assert all(CTX.get(v) == 'FT' for v in TRAIL)
UNLOCK = sorted(TRAIL); _seen = set()
for s in sorted(v for v in CTX if CTX[v] == 'FT' and isspacer(v)):                      # spacer chains whose ends touch two trail rooms
    if s in _seen: continue
    comp = {s}; st = [s]
    while st:
        x = st.pop()
        for t in _nb[x]:
            if CTX.get(t) == 'FT' and isspacer(t) and t not in comp: comp.add(t); st.append(t)
    _seen |= comp
    if len({u for x in comp for u in _nb[x] if u in set(TRAIL)}) >= 2: UNLOCK += sorted(comp)
UNLOCK += [20036, 1980, 1985]                                                          # dead-end spacer stubs off the trail, unlocked on request (owner, Oct 14)
assert all(CTX.get(v) == 'FT' for v in (20036, 1980, 1985))
UL = set(UNLOCK)
for v in UL: CTX.pop(v)                                      # (cpos keeps their map position: anchor and starting spot)

# ---- the spacer rooms that join the range to itself and to fixed rooms ----
rev = defaultdict(list)
for v, l in exits.items():
    for e in l: rev[e['to']].append(v)
raw_nb = defaultdict(set)
for v, l in exits.items():
    for e in l: raw_nb[v].add(e['to']); raw_nb[e['to']].add(v)
TA = 'The Southern Mountain Trade Route'
TR = {v for v, r in rooms.items() if r['area'] == TA}                  # added on request (owner, Oct 14): all 126 rooms, one piece, 12 exits to the range
assert TR and not TR & set(CTX) and not TR & UL
def spacer_keep(core, scope):
    """the spacer rooms hanging off `core` whose chains touch at least two rooms of `scope`; the dead-end stubs"""
    cand = set(); q = deque(core)
    while q:
        v = q.popleft()
        for t in raw_nb[v]:
            if t not in cand and t not in CTX and t not in core and isspacer(t): cand.add(t); q.append(t)
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
    return keep, stubs
keep0, stubs0 = spacer_keep(SMR, SMR | set(CTX) | UL)                    # the range alone, as in the first version of the editor (its layout must not change)
keep, stubs = spacer_keep(SMR | TR, SMR | TR | set(CTX) | UL)
S0 = SMR | keep0; S = SMR | TR | keep
assert S0 <= S
SP = {v for v in S if isspacer(v)}

def links(v):
    res = [(e['to'], DV[e['dir']]) for e in exits.get(v, []) if e['dir'] in DV and e['to'] != v]
    for u in rev[v]:
        for e in exits.get(u, []):
            if e['to'] == v and e['dir'] in DV and u != v: d = DV[e['dir']]; res.append((u, (-d[0], -d[1], -d[2])))
    return res

# ---- pieces by TinTin's own exits, with levels ----
rest = sorted(S0); inS = set(S0); loc3 = {}; piece = {}; comps = []
for s in rest:
    if s in piece: continue
    loc = {s: (0, 0, 0)}; q = deque([s]); piece[s] = len(comps)
    while q:
        x = q.popleft()
        for t, d in links(x):
            if t in inS and t not in loc: loc[t] = tuple(a + b for a, b in zip(loc[x], d)); piece[t] = len(comps); q.append(t)
    comps.append(loc)
inS = set(S)                                                           # phase 2: the Trade Route (and its spacers), laid out from the range outwards
for k, loc in enumerate(comps):
    q = deque(loc)
    while q:
        x = q.popleft()
        for t, d in links(x):
            if t in inS and t not in loc and t not in piece: loc[t] = tuple(a + b for a, b in zip(loc[x], d)); piece[t] = k; q.append(t)
for s in sorted(S - set(piece)):                                       # (anything not reached from the range: its own piece)
    if s in piece: continue
    loc = {s: (0, 0, 0)}; q = deque([s]); piece[s] = len(comps)
    while q:
        x = q.popleft()
        for t, d in links(x):
            if t in inS and t not in loc and t not in piece: loc[t] = tuple(a + b for a, b in zip(loc[x], d)); piece[t] = len(comps); q.append(t)
    comps.append(loc)
lvl = {v: loc[v][2] for loc in comps for v in loc}
pl = lambda loc: {v: (p[0] + LV * p[2], p[1] - LV * p[2]) for v, p in loc.items()}

# ---- anchor each piece to the fixed rooms it links to ----
start = {}; raw = {}; fit = []; anchored = set()
for k, loc in enumerate(comps):
    P = pl(loc); pairs = []; seenp = set()
    for v in loc:
        if v not in S0: continue                                          # (the fit uses the range's own links, so adding the Trade Route never moves it)
        for t, d in links(v):
            if t in cpos and (v, t) not in seenp:
                seenp.add((v, t)); g = (1.0, 0.0) if d[2] else (-d[0], -d[1]); pairs.append((P[v], (cpos[t][0] + g[0], cpos[t][1] + g[1])))
    if not pairs: continue
    m = [np.mean([a[i] - b[i] for a, b in pairs]) for i in (0, 1)]               # TinTin's own offset (no stretching)
    raw.update({v: [p[0] - m[0], p[1] - m[1]] for v, p in P.items()})
    sc = []
    for i in (0, 1):
        xa = np.array([a[i] for a, b in pairs]); xb = np.array([b[i] for a, b in pairs])
        if len(pairs) >= 3 and np.ptp(xa) >= 5:
            s_, t_ = np.polyfit(xa, xb, 1); s_ = float(np.clip(s_, 0.8, 1.6)); t_ = float(np.mean(xb - s_ * xa))
        else: s_ = 1.0; t_ = float(np.mean(xb - xa))
        sc.append((s_, t_))
    fit.append((k, len(loc), len(pairs), [round(s_, 3) for s_, t_ in sc]))
    start.update({v: [sc[0][0] * p[0] + sc[0][1], sc[1][0] * p[1] + sc[1][1]] for v, p in P.items()}); anchored.add(k)
# pieces that touch nothing on the map: TinTin's layout, parked in a row south of everything placed so far, biggest first
ay = [p[1] for p in start.values()] + [p[1] for p in cpos.values()]
ex = min(p[0] for p in start.values()) if start else 0; ey = max(ay) + 6; PARKED = []
for k in sorted((k for k in range(len(comps)) if k not in anchored), key=lambda k: -len(comps[k])):
    P = pl(comps[k]); x0 = min(p[0] for p in P.values()); y0 = min(p[1] for p in P.values()); wd = max(p[0] for p in P.values()) - x0; ht = max(p[1] for p in P.values()) - y0
    if len(comps[k]) == 1 and ex > 0: pass
    for v, p in P.items(): start[v] = [ex + p[0] - x0, ey + p[1] - y0]; raw[v] = list(start[v]); PARKED.append(v)
    ex += wd + 3
    if len(comps[k]) <= 3: ex += 0.4
    if ex > min(p[0] for p in start.values()) + 200: ex = min(p[0] for p in start.values()); ey += ht + 4
assert set(start) == S, S - set(start)
for v in UNLOCK: start[v] = list(cpos[v]); raw[v] = list(cpos[v]); lvl[v] = 0           # unlocked Forest of Tears rooms: where the map has them
_seen = set(); _np = len(comps)
for s in UNLOCK:                                                                      # their own pieces (flat exits among themselves)
    if s in _seen: continue
    _st = [s]; _seen.add(s)
    while _st:
        x = _st.pop(); piece[x] = _np
        for t, d in links(x):
            if t in UL and d[2] == 0 and t not in _seen: _seen.add(t); _st.append(t)
    _np += 1
S = S | UL; SP = {v for v in S if isspacer(v)}
try: _svp = dict(zip(*(lambda d: (d['ids'], zip(d['xs'], d['ys'])))(json.load(open(os.path.join(here, 'smr_layout_final.json'))))))   # the owner's save, if there is one: 559's spot
except Exception: _svp = {}
_p559 = _svp.get(559) or start[559]
start[AF_ROOM] = list(AFPOS[AF_ROOM]); start[FICT] = [(_p559[0] + AFPOS[AF_ROOM][0]) / 2, (_p559[1] + AFPOS[AF_ROOM][1]) / 2]       # (the new spacer starts half way)
for v in (AF_ROOM, FICT): raw[v] = list(start[v]); lvl[v] = 0
piece[AF_ROOM] = piece[FICT] = _np; _np += 1
S = S | {AF_ROOM, FICT}; SP = SP | {FICT}
EXTRA = {6365: 181}                                                                  # rooms added on request (owner, Oct 15): 6365 'Dry foothills' (Desert of Despair), reached from 181 through spacer 19863; unlocked, starts south-east of 181
for _v, _nb181 in EXTRA.items():
    _b = _svp.get(_nb181) or start[_nb181]; start[_v] = [round(_b[0] + 2.2, 2), round(_b[1] + 2.2, 2)]; raw[_v] = list(start[_v]); lvl[_v] = 0; piece[_v] = _np; _np += 1
    S = S | {_v}
    _sp = 19863                                                                      # the spacer between them (181 se -> 19863 se -> 6365), halfway
    start[_sp] = [round(_b[0] + 1.1, 2), round(_b[1] + 1.1, 2)]; raw[_sp] = list(start[_sp]); lvl[_sp] = 0; piece[_sp] = piece[_v]; S = S | {_sp}; SP = SP | {_sp}
xy = {v: list(p) for v, p in start.items()}
for Pz in (xy, raw):
    cells = defaultdict(list)
    for v in sorted(Pz): cells[(round(Pz[v][0] / 0.3), round(Pz[v][1] / 0.3))].append(v)
    for vs in cells.values():
        for k, v in enumerate(vs[1:], 1): Pz[v][0] += 0.42 * k; Pz[v][1] += 0.42 * k

# ---- rooms and exits ----
def exlist(v):
    res = []
    for e in exits.get(v, []):
        r = rooms.get(e['to'])
        if not r: continue
        res.append(f"{DN.get(e['dir'], '?')} → {r['name'] or 'spacer room'}" + (f" ({r['area']})" if r['area'] and r['area'] != SA else ''))
    return res
GROUP = {v: ('af' if v in (AF_ROOM, FICT) else 'ft' if v in UL else 'tr' if v in TR or (v in SP and v not in S0 and v != 19863) else 'ug' if rooms[v]['terrain'] == 'Underground' else 'sm') for v in S}
R = []
for v in sorted(CTX):
    r = rooms[v]
    R.append(dict(id=v, name=r['name'], terrain='', void=isspacer(v), lvl=0, x=round(cpos[v][0], 2), y=round(cpos[v][1], 2), x0=round(cpos[v][0], 2), y0=round(cpos[v][1], 2), fixed=True, src=CTX[v]))
for v in sorted(S):
    r = rooms.get(v) or dict(name='', terrain='', area=''); sp = v in SP
    R.append(dict(id=v, name='' if sp else r['name'], terrain='' if sp else r['terrain'], void=sp, lvl=lvl.get(v, 0), area='SM', grp=GROUP[v], piece=piece[v],
                  x=round(xy[v][0], 2), y=round(xy[v][1], 2), x0=round(raw[v][0], 2), y0=round(raw[v][1], 2), ex=exlist(v)))
for _r in R:                                                                      # the visual-only link, in the rooms' exit lists
    if _r['id'] == 559: _r['ex'] = _r['ex'] + ['ne → spacer room (visual only, not in TinTin)']
    elif _r['id'] == AF_ROOM: _r['ex'] = _r['ex'] + ['s → spacer room (visual only, not in TinTin)']
    elif _r['id'] == FICT: _r['ex'] = ['sw → Lost In The Dark Pine Forest (visual only)', 'n → Before the Ashen Forest']
V = {r['id'] for r in R}
pair = defaultdict(lambda: [False, False, False])
for v in V:
    for e in exits.get(v, []):
        t = e['to']
        if t not in V or t == v: continue
        k = (min(v, t), max(v, t)); pair[k][0 if v == k[0] else 1] = True
        if e['dir'] not in (16, 32): pair[k][2] = True
EDG = [[a, b, 'two' if (f and r and flat) else ('one' if flat else 'ud')] for (a, b), (f, r, flat) in sorted(pair.items())]
CUT = [(560, 670)]                                                                 # TinTin exits left out of the editor (owner, Oct 14): 670 joins the range only by the visual-only link
EDG = [e for e in EDG if (e[0], e[1]) not in CUT and (e[1], e[0]) not in CUT]
for _a, _b in CUT:
    for _r in R:
        if _r['id'] == _a: _r['ex'] = [x for x in _r['ex'] if f"→ {rooms[_b]['name']}" not in x]
        elif _r['id'] == _b: _r['ex'] = [x for x in _r['ex'] if f"→ {rooms[_a]['name']}" not in x]
EDG += [[559, FICT, 'two'], [FICT, AF_ROOM, 'two']]                                  # the visual-only connection
lk = sorted(k for k in pair if (k[0] in S) != (k[1] in S))
cnt = Counter(CTX.values()); tz = Counter(lvl.get(v, 0) for v in S)
audit = dict(af=1, fict=FICT, smr=len(SMR), tr=len(TR), spacers=len(SP), stubs=len(stubs), exits=sum(1 for k in pair if k[0] in S and k[1] in S), links=len(lk), pieces=_np, unlocked=len(UL),
             parked=len(PARKED), levels=', '.join(f'{z:+d}: {n}' for z, n in sorted(tz.items())),
             anchored=sum(len(comps[k]) for k in anchored), anchored_pieces=len(anchored),
             dh=cnt['DH'], grove=cnt['Grove'], fw=cnt['FW'], ft=cnt['FT'], lake=cnt['LK'], wtr=cnt['WT'])
rd = lambda poly: [[round(x, 2), round(y, 2)] for x, y in poly]
trk = list(w['fwtracks']) + list(w['swtracks']) + [w['road'], w['southpath'], w['link']] + list(w['ring']) + [t for t in w.get('etrtracks', []) if len(t) > 1] \
    + list(w.get('ntrroad', [])) + list(w.get('dirtroads', []))
ctx = dict(land=[rd(p) for p in w['geo']['land']], water=[rd(p) for p in w['geo']['water']],
           tracks=[rd(t) for t in trk if len(t) > 1], mazes=[dict(poly=rd(m['poly'])) for m in w['fwmazes']], town=[-7.4, -9.4, 7.4, 9.4],
           labels=[[0, 0.4, 'Darkhaven', 2.4], [3, -14.2, 'Shadow Grove', 1.5], [1, -47.3, 'Forgotten Woods', 2.4]] +
                  [[(a['x0'] + a['x1']) / 2, a['y'], 'Forest of Tears', 2.4] for a in [w['label']]])
D = dict(rooms=R, edges=EDG, groups=[], ctx=ctx, audit=audit, unlocked=sorted(UL) + [AF_ROOM, FICT])
t = open(os.path.join(here, 'smr_editor_template.html'), encoding='utf-8').read()
open(out, 'w', encoding='utf-8').write(t.replace('__DATA__', json.dumps(D, separators=(',', ':'))))
json.dump(dict(rooms=[{k: r[k] for k in ('id', 'terrain', 'void', 'lvl', 'fixed', 'src', 'area', 'grp', 'piece') if k in r} for r in R], edges=EDG),
          open(os.path.join(here, 'smr_editor_edges.json'), 'w'), separators=(',', ':'))

# ---- report ----
print('AUDIT', audit)
print('anchored pieces (piece, rooms, link pairs, scale x/y):', fit)
print('pieces', sorted((len(p) for p in comps), reverse=True)[:12], '...', len(comps), '| parked', len(PARKED), '| unlocked', UNLOCK)
print('fixed rooms', len(CTX), dict(cnt), '| edges', len(EDG), '| file', os.path.getsize(out) // 1024, 'KB')
