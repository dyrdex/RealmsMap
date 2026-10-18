# The layout editor for The Mire (owner, Oct 17): all its 488 rooms and the spacer rooms that join them, in the empty ground south-west of the map
# between the Forest of Tears (1610, 1612, 1613), the Southern Mountain Range (116) and the Wastelands (8591, 8633, 8638). Its exits into the Blood
# Sea, Dragon Tower, Old Marsh and the other areas it leads to are left off.
#   python3 build_mi_editor.py <final map state (json, from FINAL_DUMP=...)> <out html>     (mi_editor_template.html beside this file)
# Owner (Oct 17): the area is very large and confusingly joined, so keep its major sections apart, stretching exits between them as needed.
# Movable (area 'MI', grp 'mi'): the Mire rooms plus the spacer rooms that join two of them or one of them to a fixed room (as build_wl_editor).
# Starting spots, in two steps:
#   1. sections: communities of the exit graph (networkx louvain, resolution RES, seed 1: few exits between them), plus the hand splits in SPLIT;
#      each section is laid out ON ITS OWN by editor_spread.spread (TinTin's exits, STEP rooms apart, no overlaps);
#   2. the sections are placed as rigid blocks (directions kept, no turning), one after another (most exits to what is placed first), each at the
#      free spot with the shortest exits to what is placed (exits to the map MAPW times, + DIRW x how far an exit runs backwards, + CROSS per crossing of another section link, + THRU per room a link passes), no room
#      closer than GAP to another section's rooms or FIXGAP to the map's; then each block is re-placed against all the others, PASSES times.
import sys, os, json, math
import numpy as np, networkx as nx
from collections import defaultdict, Counter, deque
here = os.path.dirname(os.path.abspath(__file__)); SRCDIR = os.path.normpath(os.path.join(here, '..', '..', 'src')); sys.path.insert(0, SRCDIR)
import ashen_forest as AF, editor_spread as ES

w = json.load(open(sys.argv[1])); out = sys.argv[2]
rooms, exits = AF._world(); DV = AF.DV
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd', 0: '?'}
isspacer = lambda v: v in rooms and bool(rooms[v]['flags'] & 8) and rooms[v]['area'] == ''
GRP = {v: 'mi' for v, r in rooms.items() if r['area'] == 'The Mire'}
STEP = float(os.environ.get('STEP', 2.0))
RES, GAP, FIXGAP, CROSS, THRU, PASSES, CELL = 0.3, 6.0, 4.0, 30.0, 8.0, 4, 0.5
MAPW, DIRW = 4.0, 1.0      # exits to the map count MAPW times; DIRW per room an exit between sections runs against its direction
NEAR = 30
J = lambda f: json.load(open(os.path.join(SRCDIR, f)))
cnt0 = len(GRP); assert cnt0 == 488, cnt0

# ---- rooms on the finished map, at their final positions (as build_wl_editor, + the Wastelands save) ----
POS = {}; SRC = {}
def fix(v, src, p, over=False):
    if v in rooms and (over or v not in POS): POS[v] = (float(p[0]), float(p[1])); SRC[v] = src
for k, src in w['ctxsrc'].items(): fix(int(k), src, w['track']['cx' + k])
SML = J('smr_layout_final.json'); SME = J('smr_editor_edges.json'); SPOS = dict(zip(SML['ids'], zip(SML['xs'], SML['ys']))); SHID = set(SML['hidden'])
SGRP = {r['id']: r.get('grp') for r in SME['rooms'] if r.get('area') == 'SM'}
FL = J('ft_layout_final.json'); FE = J('fot_editor_edges.json'); FPOS = dict(zip(FL['ids'], zip(FL['xs'], FL['ys']))); FHID = set(FL['hidden']) | {1891}
for v, g in SGRP.items():
    if g == 'ft' and v in FPOS and v in SPOS: FPOS[v] = SPOS[v]
for r in FE['rooms']:
    v = r['id']
    if r.get('fixed') or v in FHID or v not in FPOS: continue
    fix(v, {'ft': 'FT', 'lk': 'LK', 'wt': 'WT', 'fw': 'FW'}[r['grp']], FPOS[v], True)
AL = J('ashen_layout_final.json'); AHID = set(AL.get('hidden', []))
for v, x, y in zip(AL['ids'], AL['xs'], AL['ys']):
    if v not in AHID: fix(v, 'AF', (x, y))
for v, g in SGRP.items():
    if g in ('sm', 'ug', 'tr') and v in SPOS and v not in SHID: fix(v, 'SM', SPOS[v], True)
south = set(FL['ids']) | set(AL['ids']) | set(SML['ids'])
AZ = J('az_layout_final.json'); AZH = set(AZ['hidden']); AZE = {r['id']: r for r in J('az_editor_edges.json')['rooms']}
for v, x, y in zip(AZ['ids'], AZ['xs'], AZ['ys']):
    if v in AZH or v in south: continue
    fix(v, 'AZ' if AZE.get(v, {}).get('area') == 'AZ' else 'N', (x, y))
for f, src in (('md', 'MD'), ('pf', 'PF'), ('cd', 'CD'), ('na', 'NA'), ('wl', 'WL')):                # later editors' movable rooms, as saved
    L = J(f + '_layout_final.json'); E = {r['id']: r for r in J(f + '_editor_edges.json')['rooms']}; H = set(L.get('hidden', []))
    for v, x, y in zip(L['ids'], L['xs'], L['ys']):
        if v in E and not E[v].get('fixed'):
            if v in H: POS.pop(v, None); SRC.pop(v, None)
            else: fix(v, src, (x, y), True)
K = set(GRP); assert not K & set(POS)

# ---- spacers: those joining two rooms (listed or on the map); dead-end stubs and branches that only lead off left off ----
raw_nb = defaultdict(set)
for v, l in exits.items():
    for e in l: raw_nb[v].add(e['to']); raw_nb[e['to']].add(v)
nbs = lambda v: raw_nb[v]
cand = set(); q = deque(K)
while q:
    v = q.popleft()
    for t in nbs(v):
        if t not in cand and t not in POS and t not in K and isspacer(t): cand.add(t); q.append(t)
keep = set(); stubs = set(); seen = set()
for s in sorted(cand):
    if s in seen: continue
    comp = {s}; st = [s]
    while st:
        x = st.pop()
        for t in nbs(x):
            if t in cand and t not in comp: comp.add(t); st.append(t)
    seen |= comp
    (keep if len({u for x in comp for u in nbs(x) if u in K or u in POS}) >= 2 else stubs).update(comp)
while True:
    leaf = {s for s in keep if len({u for u in nbs(s) if u in keep or u in K or u in POS}) <= 1}
    if not leaf: break
    keep -= leaf; stubs |= leaf
for s in keep: GRP[s] = 'mi'
S = K | keep
rev = defaultdict(list)
for v, l in exits.items():
    for e in l: rev[e['to']].append(v)
def links(v):
    res = [(e['to'], DV[e['dir']]) for e in exits.get(v, []) if e['dir'] in DV and e['to'] != v]
    for u in rev[v]:
        for e in exits.get(u, []):
            if e['to'] == v and e['dir'] in DV and u != v: d = DV[e['dir']]; res.append((u, (-d[0], -d[1], -d[2])))
    return res
def links2(v):                                                                           # + a link north-east/south-west for 'enter'-only pairs
    res = links(v); have = {u for u, _ in res}
    return res + [(u, (1, -1, 0) if v < u else (-1, 1, 0)) for u in sorted(nbs(v)) if u not in have and u != v and (u in S or u in POS)]

# ---- 1. sections ----
G = nx.Graph(); G.add_nodes_from(sorted(S))
for v in sorted(S):
    for t, _ in links2(v):
        if t in S and t != v: G.add_edge(v, t)
SEC = [set(c) for c in sorted(nx.community.louvain_communities(G, resolution=RES, seed=1), key=min)]
SPLIT = [{667, 7868, 7869, 7870, 7871, 7872, 22204}]      # the valley trail from the Southern Mountains (116) is ~120 rooms from the Grassy Trail by the
for part in SPLIT:                                        # Forest of Tears (1610-1613) on the map: its own section, so neither end is stretched
    for c in SEC:
        if part <= c and part != c: c -= part; SEC.append(set(part)); break
SEC = sorted(SEC, key=min)
sec = {v: i for i, c in enumerate(SEC) for v in c}
ALLN = Counter(rooms[v]['name'] for v in K)
def sname(c):                                                     # its most common room name that is (mostly) its own, else the most common one
    n = Counter(rooms[v]['name'] for v in c if rooms[v]['name'] and not isspacer(v)).most_common()
    own = [m for m, k in n if k >= 0.8 * ALLN[m]]
    return own[0] if own else n[0][0] if n else 'spacer rooms'
lone1 = lambda c: len(c) == 1 and not any(t in S or t in POS for t, _ in links2(next(iter(c))))
NAMES = [f'lone room {next(iter(c))} ({sname(c)})' if lone1(c) else sname(c) for c in SEC]
for m, k in Counter(NAMES).items():
    if k > 1:
        for j, i in enumerate(i for i in range(len(SEC)) if NAMES[i] == m): NAMES[i] = f'{m} ({j + 1})'

# ---- 1b. each section on its own ----
local = {}
for i, c in enumerate(SEC):
    r0 = min(c, key=lambda v: (-sum(1 for t, _ in links2(v) if t in c), v))     # the best-joined room as its root
    sl = lambda v, c=c: [(t, d) for t, d in links2(v) if t in c]
    p = ES.spread(c - {r0}, sl, {r0: (0.0, 0.0)}, [r0], step=STEP) if len(c) > 1 else {}
    p[r0] = [0.0, 0.0]
    local[i] = p

# ---- 2. sections as blocks ----
XL = [(v, t) for v in S for t, _ in links2(v) if (t in S and sec[t] != sec[v] and v < t) or (t in POS)]     # exits leaving a section
XL = sorted(set(XL))
LDIR = {}
for v in S:
    for t, d in links2(v):
        if (v, t) in LDIR: continue
        LDIR[(v, t)] = _v = ES._vec(d); LDIR[(t, v)] = (-_v[0], -_v[1])
PARK = {}                                                                                 # rooms with no exit at all: beside the room with the nearest number
for i, c in enumerate(SEC):
    if lone1(c):
        v = next(iter(c)); PARK[i] = (v, min((u for u in S if u != v and len(SEC[sec[u]]) > 1), key=lambda u: (abs(u - v), u)))
x0, x1, y0, y1 = -140.0, 40.0, -10.0, 190.0                                              # the search window (the map may grow round it)
nx_, ny_ = int((x1 - x0) / CELL) + 1, int((y1 - y0) / CELL) + 1
cell = lambda x, y: (int(round((x - x0) / CELL)), int(round((y - y0) / CELL)))
def disk(r):
    k = int(math.ceil(r / CELL)); a = np.arange(-k, k + 1)
    return [(i, j) for i in a for j in a if math.hypot(i, j) * CELL < r]
def stamp(M, pts, r):
    for (i, j) in disk(r):
        for x, y in pts:
            a, b = cell(x, y); a += i; b += j
            if 0 <= a < nx_ and 0 <= b < ny_: M[a, b] = True
MAPF = np.zeros((nx_, ny_), bool); stamp(MAPF, POS.values(), FIXGAP)
def segx(p, q, r, s):
    d = lambda a, b, c: (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return d(p, q, r) * d(p, q, s) < 0 and d(r, s, p) * d(r, s, q) < 0
def segd(c, p, q):
    L2 = (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2
    if L2 < 1e-9: return 9
    u = ((c[0] - p[0]) * (q[0] - p[0]) + (c[1] - p[1]) * (q[1] - p[1])) / L2
    if not 0.02 < u < 0.98: return 9
    return math.hypot(p[0] + u * (q[0] - p[0]) - c[0], p[1] + u * (q[1] - p[1]) - c[1])
off = {}
def at(v):
    if v in POS: return POS[v]
    i = sec[v]; o = off[i]; p = local[i][v]; return (p[0] + o[0], p[1] + o[1])
def place(i):
    """the best free spot for block i against the blocks in off (i not in it) and the map"""
    F = MAPF.copy()
    for j, o in off.items():
        if j != i: stamp(F, [(p[0] + o[0], p[1] + o[1]) for p in local[j].values()], GAP)
    pts = list(local[i].values()); mnx = min(p[0] for p in pts); mny = min(p[1] for p in pts)
    ok = np.ones((nx_, ny_), bool)                                                       # ok[a, b]: block offset = (x0 + a*CELL, y0 + b*CELL)
    for x, y in pts:
        a, b = int(round(x / CELL)), int(round(y / CELL))
        sh = np.ones((nx_, ny_), bool)                                                   # F[a + i, b + j] for offset cell (i, j); out of window = blocked
        ia0, ia1 = max(0, -a), min(nx_, nx_ - a); ib0, ib1 = max(0, -b), min(ny_, ny_ - b)
        sh[ia0:ia1, ib0:ib1] = F[ia0 + a:ia1 + a, ib0 + b:ib1 + b]
        ok &= ~sh
    mine = [(v, t) for v, t in XL if (v in local[i]) != (t in local[i]) and (v in POS or t in POS or sec.get(v if t in local[i] else t) in off)]
    if i in PARK and sec[PARK[i][1]] in off: mine = [PARK[i]]
    OX = x0 + np.arange(nx_)[:, None] * CELL; OY = y0 + np.arange(ny_)[None, :] * CELL
    cost = np.zeros((nx_, ny_))
    for v, t in mine:
        a, b = (v, t) if v in local[i] else (t, v)
        p = local[i][a]; q = at(b); dx = q[0] - OX - p[0]; dy = q[1] - OY - p[1]
        cost += np.hypot(dx, dy) * (MAPW if b in POS else 1.0)
        if (a, b) in LDIR:
            vx, vy = LDIR[(a, b)]; n = math.hypot(vx, vy); cost += DIRW * np.maximum(0, -(dx * vx + dy * vy) / n)
    cost[~ok] = np.inf
    if not mine:                                                                          # nothing placed yet that it joins: next to the rest
        cx = np.mean([at(v)[0] for j in off for v in local[j]]) if off else -70; cy = np.mean([at(v)[1] for j in off for v in local[j]]) if off else 60
        cost = np.where(ok, np.hypot(OX - cx, OY - cy), np.inf)
    order = np.argsort(cost, axis=None)[:400]
    best = None
    others = [(a, b) for a, b in XL if a not in local[i] and b not in local[i] and all(x in POS or sec[x] in off for x in (a, b))]
    orooms = [at(v) for j in off if j != i for v in local[j]]
    for k in order:
        a, b = np.unravel_index(k, cost.shape)
        if not np.isfinite(cost[a, b]): break
        o = (x0 + a * CELL, y0 + b * CELL); pen = 0.0
        off[i] = o
        segs = [(at(v), at(t)) for v, t in mine if (v, t) != PARK.get(i)]
        for p, q in segs:
            pen += CROSS * sum(1 for u, z in others if segx(p, q, at(u), at(z)))
            pen += THRU * sum(1 for c in orooms if segd(c, p, q) < 0.6)
        mys = [(p[0] + o[0], p[1] + o[1]) for p in local[i].values()]
        for u, z in others:                                                               # others' links through this block
            pu, pz = at(u), at(z); pen += THRU * sum(1 for c in mys if segd(c, pu, pz) < 0.6)
        del off[i]
        sc = cost[a, b] + pen
        if best is None or sc < best[0]: best = (sc, o)
    off[i] = best[1]
todo = set(range(len(SEC)))
seq = []
while todo:
    i = max(todo, key=lambda i: (sum((MAPW if v in POS or t in POS else 1) for v, t in XL if (sec.get(v) == i and (t in POS or sec.get(t) in off)) or (sec.get(t) == i and (v in POS or sec.get(v) in off))), len(SEC[i])))
    place(i); todo.discard(i); seq.append(i)
for _ in range(PASSES):
    for i in seq: place(i)
start = {v: [round(at(v)[0], 2), round(at(v)[1], 2)] for v in S}
lone = sorted(v for v in K if not any(u in S or u in POS for u, _ in links2(v)))
close, far, wrong, thru = ES.report(start, POS, links2, step=STEP)
def within(f):
    n = 0
    for v in S:
        for t, _ in links2(v):
            if t in S and sec[t] == sec[v] and v < t: n += f(start[v], start[t])
    return n
far_in = within(lambda p, q: math.hypot(q[0] - p[0], q[1] - p[1]) > 2 * STEP)
seglen = [math.hypot(at(v)[0] - at(t)[0], at(v)[1] - at(t)[1]) for v, t in XL]
xcross = sum(1 for a in range(len(XL)) for b in range(a + 1, len(XL)) if segx(at(XL[a][0]), at(XL[a][1]), at(XL[b][0]), at(XL[b][1])))

# ---- fixed rooms near the new ones ----
pts = [start[v] for v in S]
CTX = {v: SRC[v] for v, p in POS.items() if min(math.hypot(p[0] - a[0], p[1] - a[1]) for a in pts) <= NEAR}
UN = list(range(110, 117)) + [8606, 8608, 10049, 8610, 8611, 8614, 10045]   # unlocked map rooms (owner, Oct 18): Southern Mountain Range 110-116; Wastelands east-bank rooms; movable, starting at their spots on the map
assert all(v in POS for v in UN), [(v, rooms[v]['area'], v in POS) for v in UN]
for v in UN: start[v] = [round(POS[v][0], 2), round(POS[v][1], 2)]; GRP[v] = 'un'; CTX.pop(v, None)
S = S | set(UN)
# ---- added later (owner, Oct 18): the Old Marsh's rooms and Dragon Tower's 7940, movable (grp 'om'), starting next to the rooms they join in the
# owner's saved layout (spread from there, clear of it and of the map), with the spacers that join them
SAVED = {v: (x, y) for v, x, y in zip(*(J('mi_layout_final.json')[k] for k in ('ids', 'xs', 'ys'))) if v in S}
ADD = {v for v, r in rooms.items() if r['area'] == 'Old Marsh'} | {7940}
ends_ = lambda c: {u for x in c for u in nbs(x) if u in ADD or u in S or u in POS}
cand2 = set(); q = deque(ADD)
while q:
    v = q.popleft()
    for t in nbs(v):
        if t not in cand2 and t not in POS and t not in S and t not in ADD and isspacer(t): cand2.add(t); q.append(t)
keep2 = set(); seen2 = set()
for s0 in sorted(cand2):
    if s0 in seen2: continue
    comp = {s0}; st = [s0]
    while st:
        x = st.pop()
        for t in nbs(x):
            if t in cand2 and t not in comp: comp.add(t); st.append(t)
    seen2 |= comp
    if len(ends_(comp)) >= 2: keep2 |= comp
while True:
    leaf = {s0 for s0 in keep2 if len({u for u in nbs(s0) if u in keep2 or u in ADD or u in S or u in POS}) <= 1}
    if not leaf: break
    keep2 -= leaf
ADDS = ADD | keep2
FIX2 = dict(POS); FIX2.update(SAVED)
roots2 = sorted({t for v in ADDS for t, _ in links2(v) if t in SAVED})
sp2 = ES.spread(ADDS, lambda v: [(t, d) for t, d in links2(v) if t in ADDS or t in FIX2], FIX2, roots2, step=STEP)
for v in ADDS: start[v] = sp2[v]; GRP[v] = 'om'; CTX.pop(v, None)
S = S | ADDS

# ---- rooms and exits ----
def exlist(v):
    res = []
    for e in exits.get(v, []):
        r = rooms.get(e['to'])
        if not r: continue
        res.append(f"{DN.get(e['dir'], e['name'])} → {r['name'] or 'spacer room'}" + (f" ({r['area']})" if r['area'] and r['area'] != rooms[v]['area'] else ''))
    return res
R = []
for v in sorted(CTX):
    r = rooms[v]
    R.append(dict(id=v, name=r['name'], terrain='', void=isspacer(v), lvl=0, x=round(POS[v][0], 2), y=round(POS[v][1], 2), x0=round(POS[v][0], 2), y0=round(POS[v][1], 2), fixed=True, src=CTX[v]))
for v in sorted(S):
    r = rooms[v]
    R.append(dict(id=v, name=r['name'], terrain='' if isspacer(v) else r['terrain'], void=isspacer(v), lvl=0, area='MI', grp=GRP[v], piece=sec.get(v), ga=r['area'] or 'spacer',
                  x=start[v][0], y=start[v][1], x0=start[v][0], y0=start[v][1], ex=exlist(v)))
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
cnt = Counter(CTX.values())
offc = Counter()
for v in K:
    for e in exits.get(v, []):
        a = rooms.get(e['to'], {}).get('area', '')
        if e['to'] not in V and a not in ('', 'The Mire'): offc[a] += 1
audit = dict(mi=cnt0, mis=len(keep), secs=len(SEC), exits=sum(1 for k in pair if k[0] in S and k[1] in S), links=len(lk), fixed=len(CTX),
             off=', '.join(f'{a} {n}' for a, n in sorted(offc.items())))
rd = lambda poly: [[round(x, 2), round(y, 2)] for x, y in poly]
trk = list(w['fwtracks']) + list(w['swtracks']) + [w['road'], w['southpath'], w['link']] + list(w['ring']) + [t for t in w.get('etrtracks', []) if len(t) > 1] \
    + list(w.get('ntrroad', [])) + list(w.get('dirtroads', [])) + [t['pts'] if isinstance(t, dict) else t for t in w.get('seaways', [])]
trk = [t for t in trk if t and isinstance(t[0], (list, tuple)) and len(t) > 1]
ctx = dict(land=[rd(p) for p in w['geo']['land']], water=[rd(p) for p in w['geo']['water']],
           tracks=[rd(t) for t in trk], mazes=[dict(poly=rd(m['poly'])) for m in w['fwmazes']], town=[-7.4, -9.4, 7.4, 9.4],
           labels=[[0, 0.4, 'Darkhaven', 2.4], [3, -14.2, 'Shadow Grove', 1.5], [1, -47.3, 'Forgotten Woods', 2.4]])
secs = [dict(i=i, name=NAMES[i], n=len(c)) for i, c in enumerate(SEC)]
D = dict(rooms=R, edges=EDG, groups=[], ctx=ctx, audit=audit, secs=secs)
t = open(os.path.join(here, 'mi_editor_template.html'), encoding='utf-8').read()
open(out, 'w', encoding='utf-8').write(t.replace('__DATA__', json.dumps(D, separators=(',', ':'))))
json.dump(dict(rooms=[{k: r[k] for k in ('id', 'terrain', 'void', 'lvl', 'fixed', 'src', 'area', 'grp', 'piece', 'ga', 'x0', 'y0') if k in r and not (k in ('x0', 'y0') and r.get('fixed'))} for r in R], edges=EDG, secs=secs),
          open(os.path.join(SRCDIR, 'mi_editor_edges.json'), 'w'), separators=(',', ':'))
print('AUDIT', audit)
print('spacers kept', len(keep), '| stubs left off', len(stubs))
print('links to the map', lk, '| no exit at all', lone)
for i, c in enumerate(SEC):
    xs = [start[v][0] for v in c]; ys = [start[v][1] for v in c]
    print(f'  section {i + 1:2d} {NAMES[i]!r:42s} {len(c):3d} rooms  box x {min(xs):6.1f}..{max(xs):6.1f} y {min(ys):6.1f}..{max(ys):6.1f}')
print('start: rooms closer than 0.8 (not neighbours)', close, '| exits stretched past 2 steps', far, '(inside sections', far_in, ') | wrong way', wrong, '| lines through another room', thru)
print('links between sections / to the map', len(XL), '| crossing each other', xcross, '| length min/median/max %.1f %.1f %.1f' % (min(seglen), sorted(seglen)[len(seglen) // 2], max(seglen)))
xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
print('box x %.1f..%.1f y %.1f..%.1f' % (min(xs), max(xs), min(ys), max(ys)), '| fixed rooms', len(CTX), dict(cnt), '| edges', len(EDG), '| file', os.path.getsize(out) // 1024, 'KB', '| map bounds', w['bounds'])
if os.environ.get('PLOT'):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(14, 14)); ax.set_facecolor('#111')
    for v, p in POS.items():
        if -180 < p[0] < 40 and -20 < p[1] < 200: ax.plot(p[0], p[1], '.', color='#555', ms=2)
    cm = plt.get_cmap('tab20')
    for a, b, k in EDG:
        if a in S or b in S:
            p, q = (start.get(a) or POS[a]), (start.get(b) or POS[b]); xl = a in S and b in S and sec[a] == sec[b]
            ax.plot([p[0], q[0]], [p[1], q[1]], '-', color='#888' if xl else '#e44', lw=.5 if xl else 1.0)
    for v in S: ax.plot(start[v][0], start[v][1], 'o', color=cm(sec[v] % 20), ms=2.5)
    for i, c in enumerate(SEC):
        ax.text(np.mean([start[v][0] for v in c]), np.mean([start[v][1] for v in c]), f'{i + 1} {NAMES[i]}', color='w', fontsize=7)
    ax.set_aspect('equal'); ax.invert_yaxis(); fig.savefig(os.environ['PLOT'], dpi=110, bbox_inches='tight')
