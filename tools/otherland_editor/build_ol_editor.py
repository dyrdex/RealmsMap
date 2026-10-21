# The layout editor for Otherland (owner, Oct 21): all its rooms, the unnamed rooms that lead only back into it, and the spacer rooms that join them,
# in the empty sea west and south of the Sea of Sorrows coast. It joins the map ONLY at 22534 -> 13379 and 22535 -> 13380 (owner); every other exit
# out of it (Blood Sea, Azure Sea, Sea of Sorrows, Wild Tundra, Cursed Lands, Asgard Nexus) is left off.
# Owner (Oct 21): the owner's map 'flattens' Otherland: where a room has an up/down exit to the same room as a flat exit (n/e/s/w/ne/se/nw/sw), the
# flat exit is used and the up/down one ignored (per pair of rooms, both ways). Space things out to minimise overlaps and keep sections apart.
#   python3 build_ol_editor.py <final map state (json, from FINAL_DUMP=...)> <out html>     (ol_editor_template.html beside this file)
# Movable (area 'OL', grp 'ol'): the Otherland rooms; unnamed real rooms (area '', not spacers) reached from them through unnamed rooms, unless they
# have an exit to another area or the map (22537); spacer rooms among those that join two of them (dead-end spacer stubs left off).
# Starting spots as build_dd_editor: sections = louvain communities (resolution RES, seed 1), each laid out on its own by editor_spread.spread, then
# placed as rigid blocks at the free spot with the shortest exits to what is placed, no room closer than GAP to another section or FIXGAP to the map.
import sys, os, json, math
import numpy as np, networkx as nx
from collections import defaultdict, Counter, deque
here = os.path.dirname(os.path.abspath(__file__)); SRCDIR = os.path.normpath(os.path.join(here, '..', '..', 'src', 'legacy')); sys.path[:0] = [SRCDIR, os.path.dirname(SRCDIR)]
import ashen_forest as AF, editor_spread as ES

w = json.load(open(sys.argv[1])); out = sys.argv[2]
rooms, exits = AF._world(); DV = AF.DV
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd', 0: '?'}
isspacer = lambda v: v in rooms and bool(rooms[v]['flags'] & 8) and rooms[v]['area'] == ''
LINK = {(22534, 13379), (22535, 13380)}                                                   # the only exits to the map (owner)
LINKS = LINK | {(b, a) for a, b in LINK}
K = {v for v, r in rooms.items() if r['area'] == 'Otherland'}
STEP = float(os.environ.get('STEP', 2.0))
RES, GAP, FIXGAP, CROSS, THRU, PASSES, CELL = float(os.environ.get('RES', 0.2)), float(os.environ.get('GAP', 9.0)), 5.0, float(os.environ.get('CROSS', 30.0)), 8.0, 4, 0.5
MAPW, DIRW = 4.0, 1.0
NEAR = 30
cnt0 = len(K); assert cnt0 == 503, cnt0

# ---- rooms on the finished map ----
B = json.load(open(os.path.join(SRCDIR, '..', 'base', 'map.json')))
ACODE = {'Wastelands': 'WL', 'Southern Mountain Range': 'SM', 'Desert of Despair': 'DD', 'The Mire': 'MI', 'Forest of Tears': 'FT', 'Ashen Forest': 'AF', 'Azure Sea': 'AZ'}
CODES = set(ACODE.values()) | {'DH', 'Grove', 'FW', 'LK', 'WT', 'N'}
POS = {}; SRC = {}
for k, src in w['ctxsrc'].items():
    v = int(k)
    if v in rooms: POS[v] = tuple(map(float, w['track']['cx' + k])); SRC[v] = src if src in CODES else 'N'
for k, p in B['room_pos'].items():
    v = int(k)
    if v in rooms and v not in POS: POS[v] = (float(p[0]), float(p[1])); SRC[v] = ACODE.get(rooms[v]['area'])
named = [v for v in POS if SRC[v]]
for v in POS:
    if not SRC[v]:
        p = POS[v]; u = min(named, key=lambda u: (POS[u][0] - p[0]) ** 2 + (POS[u][1] - p[1]) ** 2); SRC[v] = SRC[u] if math.dist(POS[u], p) < 6 else 'N'
assert not K & set(POS)

# ---- unnamed rooms reached from Otherland through unnamed rooms ----
raw_nb = defaultdict(set)
for v, l in exits.items():
    for e in l: raw_nb[v].add(e['to']); raw_nb[e['to']].add(v)
nbs = lambda v: raw_nb[v]
cand = set(); q = deque(K)
while q:
    v = q.popleft()
    for t in nbs(v):
        if t in rooms and t not in cand and t not in POS and t not in K and rooms[t]['area'] == '': cand.add(t); q.append(t)
leadout = {v for v in cand if not isspacer(v) and any(t not in K and t not in cand for t in nbs(v))}     # real rooms with an exit off Otherland (left off)
keep = cand - leadout
while True:                                                                              # spacers: prune dead ends; real unnamed rooms stay while joined
    leaf = {s for s in keep if len({u for u in nbs(s) if u in keep or u in K} - {s}) <= (1 if isspacer(s) else 0)}
    if not leaf: break
    keep -= leaf
stubs = cand - keep
REAL = {v for v in keep if not isspacer(v)}
S = K | keep
GRP = {v: 'ol' for v in S}
UNL = set()                                                                              # unlocked map rooms (set below)
def ok(v, t):                                                                            # exits kept
    if (v, t) in LINKS: return True
    a, b = v in UNL, t in UNL
    if a or b: return (a or v in POS) and (b or t in POS)                               # unlocked rooms: only their exits to other map rooms
    return v in S and t in S
# up/down ignored where a flat exit joins the same two rooms (either way)
FLATP = {frozenset((v, e['to'])) for v, l in exits.items() for e in l if e['dir'] in DV and e['dir'] not in (16, 32) and e['to'] != v}
nflat = sum(1 for v in S for e in exits.get(v, []) if e['dir'] in (16, 32) and ok(v, e['to']) and frozenset((v, e['to'])) in FLATP)
nud = sum(1 for v in S for e in exits.get(v, []) if e['dir'] in (16, 32) and ok(v, e['to']) and frozenset((v, e['to'])) not in FLATP)
rev = defaultdict(list)
for v, l in exits.items():
    for e in l: rev[e['to']].append(v)
def use(v, e): return e['dir'] in DV and e['to'] != v and not (e['dir'] in (16, 32) and frozenset((v, e['to'])) in FLATP)
def links(v):
    res = [(e['to'], DV[e['dir']]) for e in exits.get(v, []) if use(v, e) and ok(v, e['to'])]
    for u in rev[v]:
        if not ok(v, u): continue
        for e in exits.get(u, []):
            if e['to'] == v and use(u, e): d = DV[e['dir']]; res.append((u, (-d[0], -d[1], -d[2])))
    return res
def links2(v):                                                                           # + a link north-east/south-west for 'enter'-only pairs
    res = links(v); have = {u for u, _ in res}
    return res + [(u, (1, -1, 0) if v < u else (-1, 1, 0)) for u in sorted(nbs(v)) if u not in have and u != v and ok(v, u)]

# ---- 1. sections ----
G = nx.Graph(); G.add_nodes_from(sorted(S))
for v in sorted(S):
    for t, _ in links2(v):
        if t in S and t != v: G.add_edge(v, t)
SEC = sorted([set(c) for c in nx.community.louvain_communities(G, resolution=RES, seed=1)], key=min)
sec = {v: i for i, c in enumerate(SEC) for v in c}
ALLN = Counter(rooms[v]['name'] for v in K)
def sname(c):
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
    r0 = min(c, key=lambda v: (-sum(1 for t, _ in links2(v) if t in c), v))
    sl = lambda v, c=c: [(t, d) for t, d in links2(v) if t in c]
    p = ES.spread(c - {r0}, sl, {r0: (0.0, 0.0)}, [r0], step=STEP) if len(c) > 1 else {}
    p[r0] = [0.0, 0.0]
    local[i] = p

# ---- 2. sections as blocks ----
XL = sorted({(v, t) for v in S for t, _ in links2(v) if (t in S and sec[t] != sec[v] and v < t) or (t in POS)})
LDIR = {}
for v in S:
    for t, d in links2(v):
        if (v, t) in LDIR: continue
        LDIR[(v, t)] = _v = ES._vec(d); LDIR[(t, v)] = (-_v[0], -_v[1])
PARK = {}
for i, c in enumerate(SEC):
    if lone1(c):
        v = next(iter(c)); PARK[i] = (v, min((u for u in S if u != v and len(SEC[sec[u]]) > 1), key=lambda u: (abs(u - v), u)))
x0, x1, y0, y1 = -90.0, 110.0, 110.0, 360.0                                              # the search window: the sea west of the link rooms and south of the map
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
    pts = list(local[i].values())
    okm = np.ones((nx_, ny_), bool)
    for x, y in pts:
        a, b = int(round(x / CELL)), int(round(y / CELL))
        sh = np.ones((nx_, ny_), bool)
        ia0, ia1 = max(0, -a), min(nx_, nx_ - a); ib0, ib1 = max(0, -b), min(ny_, ny_ - b)
        sh[ia0:ia1, ib0:ib1] = F[ia0 + a:ia1 + a, ib0 + b:ib1 + b]
        okm &= ~sh
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
    cost[~okm] = np.inf
    if not mine:
        cx = np.mean([at(v)[0] for j in off for v in local[j]]) if off else 60; cy = np.mean([at(v)[1] for j in off for v in local[j]]) if off else 200
        cost = np.where(okm, np.hypot(OX - cx, OY - cy), np.inf)
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
        for u, z in others:
            pu, pz = at(u), at(z); pen += THRU * sum(1 for c in mys if segd(c, pu, pz) < 0.6)
        del off[i]
        sc = cost[a, b] + pen
        if best is None or sc < best[0]: best = (sc, o)
    assert best, f'no room for section {i}'
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
secgap = min(math.dist(start[u], start[v]) for i in range(len(SEC)) for j in range(i + 1, len(SEC)) for u in SEC[i] for v in SEC[j]) if len(SEC) > 1 else 0

# ---- added later (owner, Oct 21): Frost Mansion 22248-22250 (Asgard Nexus; grp 'an'), joined to Otherland at 22247 (n) and 21819 (s), movable,
# spread from those rooms after the layout above, so it stays as it was; their exits to Otherland are kept
ADD = [22248, 22249, 22250]
S = S | set(ADD)
for v in ADD: GRP[v] = 'an'
FIX2 = dict(POS); FIX2.update({v: tuple(p) for v, p in start.items()})
roots2 = sorted({t for v in ADD for t, _ in links2(v) if t in start})
sp2 = ES.spread(set(ADD), lambda v: [(t, d) for t, d in links2(v) if t in ADD or t in FIX2], FIX2, roots2, step=STEP)
for v in ADD: start[v] = [round(sp2[v][0], 2), round(sp2[v][1], 2)]
addnear = {v: round(min(math.dist(start[v], start[u]) for u in start if u != v and u not in {t for t, _ in links2(v)}), 2) for v in ADD}

# ---- fixed rooms near the new ones ----
pts = [start[v] for v in S]
CTX = {v: SRC[v] for v, p in POS.items() if min(math.hypot(p[0] - a[0], p[1] - a[1]) for a in pts) <= NEAR}
# ---- unlocked map rooms (owner, Oct 21; grp 'un'): movable, starting at their spots on the map; Otherland's exits to them stay off but the two links
UN = [18064, 18067, 18068, 18066, 18072, 18075, 18071, 13379, 13380, 6166, 6180, 15418, 15417, 15416, 15415, 15414, 15413, 15412, 15411, 15410,
      18052, 6174, 18047, 18059, 18058, 18062, 18063]                                     # (+ Oct 21, second set)
assert all(v in CTX for v in UN), [v for v in UN if v not in CTX]
UNL = set(UN)
LINK2 = {(18071, 22511), (18066, 22512)}                                                 # also shown (owner, Oct 21): the Ahtborne Straights south into Otherland
LINKS |= LINK2 | {(b, a) for a, b in LINK2}
for v in UN: GRP[v] = 'un'; start[v] = [round(POS[v][0], 2), round(POS[v][1], 2)]; CTX.pop(v)
S = S | UNL
# ---- rooms and exits ----
def exlist(v):
    res = []
    for e in exits.get(v, []):
        r = rooms.get(e['to'])
        if not r: continue
        why = '' if ok(v, e['to']) else ' · left off'
        if ok(v, e['to']) and not use(v, e) and e['dir'] in (16, 32): why = ' · ignored (flat exit used)'
        res.append(f"{DN.get(e['dir'], e['name'])} → {r['name'] or 'spacer room'}" + (f" ({r['area']})" if r['area'] and r['area'] != rooms[v]['area'] else '') + why)
    return res
R = []
for v in sorted(CTX):
    r = rooms[v]
    R.append(dict(id=v, name=r['name'], terrain='', void=isspacer(v), lvl=0, x=round(POS[v][0], 2), y=round(POS[v][1], 2), x0=round(POS[v][0], 2), y0=round(POS[v][1], 2), fixed=True, src=CTX[v]))
for v in sorted(S):
    r = rooms[v]
    R.append(dict(id=v, name=r['name'], terrain='' if isspacer(v) else r['terrain'], void=isspacer(v), lvl=0, area='OL', grp=GRP[v], piece=sec.get(v), ga=r['area'] or ('spacer' if isspacer(v) else 'unnamed'),
                  x=start[v][0], y=start[v][1], x0=start[v][0], y0=start[v][1], ex=exlist(v)))
V = {r['id'] for r in R}
pair = defaultdict(lambda: [False, False, False])
for v in V:
    for e in exits.get(v, []):
        t = e['to']
        if t not in V or t == v: continue
        if not ok(v, t) and (v in S or t in S): continue                                 # Otherland's exits off it: left off
        if e['dir'] in (16, 32) and frozenset((v, t)) in FLATP: continue                 # ignored up/down
        k = (min(v, t), max(v, t)); pair[k][0 if v == k[0] else 1] = True
        if e['dir'] not in (16, 32): pair[k][2] = True
for (a, b), f in pair.items():                                                           # a pair with a flat exit one way and an ignored up/down the other is still two-way
    if f[2] and not (f[0] and f[1]):
        f[0] = f[0] or any(e['to'] == b for e in exits.get(a, [])); f[1] = f[1] or any(e['to'] == a for e in exits.get(b, []))
EDG = [[a, b, 'two' if (f and r and flat) else ('one' if flat else 'ud')] for (a, b), (f, r, flat) in sorted(pair.items())]
lk = sorted(k for k in pair if (k[0] in S) != (k[1] in S))
cnt = Counter(CTX.values())
offc = Counter()
for v in S - UNL:
    for e in exits.get(v, []):
        if not ok(v, e['to']): offc[rooms.get(e['to'], {}).get('area') or 'unnamed/spacer rooms'] += 1
audit = dict(ol=cnt0, an=len(ADD), un=len(UN), oln=len(REAL), ols=len(keep) - len(REAL), flat=nflat, ud=nud, secs=len(SEC), exits=sum(1 for k in pair if k[0] in S and k[1] in S), links=len(lk), fixed=len(CTX),
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
t = open(os.path.join(here, 'ol_editor_template.html'), encoding='utf-8').read()
open(out, 'w', encoding='utf-8').write(t.replace('__DATA__', json.dumps(D, separators=(',', ':'))))
json.dump(dict(rooms=[{k: r[k] for k in ('id', 'terrain', 'void', 'lvl', 'fixed', 'src', 'area', 'grp', 'piece', 'ga', 'x0', 'y0') if k in r and not (k in ('x0', 'y0') and r.get('fixed'))} for r in R], edges=EDG, secs=secs),
          open(os.path.join(SRCDIR, 'ol_editor_edges.json'), 'w'), separators=(',', ':'))
print('AUDIT', audit)
print('unnamed real rooms kept', len(REAL), sorted(REAL), '| left off (exit off Otherland)', sorted(leadout), '| spacers kept', len(keep) - len(REAL), '| stubs left off', len(stubs))
print('added (an)', {v: start[v] for v in ADD}, '| roots', roots2, '| nearest room not joined', addnear)
print('links to the map', lk, '| no exit at all', lone)
for i, c in enumerate(SEC):
    xs = [start[v][0] for v in c]; ys = [start[v][1] for v in c]
    print(f'  section {i + 1:2d} {NAMES[i]!r:42s} {len(c):3d} rooms  box x {min(xs):6.1f}..{max(xs):6.1f} y {min(ys):6.1f}..{max(ys):6.1f}')
print('start: rooms closer than 0.8 (not neighbours)', close, '| exits stretched past 2 steps', far, '(inside sections', far_in, ') | wrong way', wrong, '| lines through another room', thru)
print('links between sections / to the map', len(XL), '| crossing each other', xcross, '| length min/median/max %.1f %.1f %.1f' % (min(seglen), sorted(seglen)[len(seglen) // 2], max(seglen)), '| closest rooms of two sections %.1f' % secgap)
xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
print('box x %.1f..%.1f y %.1f..%.1f' % (min(xs), max(xs), min(ys), max(ys)), '| fixed rooms', len(CTX), dict(cnt), '| edges', len(EDG), '| file', os.path.getsize(out) // 1024, 'KB', '| map bounds', w['bounds'])
if os.environ.get('PLOT'):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(14, 14)); ax.set_facecolor('#111')
    for v, p in POS.items():
        if -100 < p[0] < 130 and 90 < p[1] < 370: ax.plot(p[0], p[1], '.', color='#555', ms=2)
    cm = plt.get_cmap('tab20')
    for a, b, k in EDG:
        if a in S or b in S:
            p, q = (start.get(a) or POS[a]), (start.get(b) or POS[b]); xl = a in S and b in S and sec[a] == sec[b]
            ax.plot([p[0], q[0]], [p[1], q[1]], '--' if k == 'ud' else '-', color='#888' if xl else '#e44', lw=.5 if xl else 1.0)
    for v in S: ax.plot(start[v][0], start[v][1], 'o', color=cm(sec[v] % 20), ms=2.5)
    for i, c in enumerate(SEC):
        ax.text(np.mean([start[v][0] for v in c]), np.mean([start[v][1] for v in c]), f'{i + 1} {NAMES[i]}', color='w', fontsize=7)
    ax.set_aspect('equal'); ax.invert_yaxis(); fig.savefig(os.environ['PLOT'], dpi=110, bbox_inches='tight')
