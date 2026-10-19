# The layout editor for three areas the owner added on Oct 16: Angel's Landing (22 rooms + Blood Sea room 16226, shown only with its links ne to 5667 and
# nw to 21135), The Village of Edo (77 rooms, off 7746 on the Azure Sea Coast) and The Grimdog Port Authority (29 rooms + Western Trade Route room 21076,
# the only way in, off road room 2356).
#   python3 build_na_editor.py <final map state (json, from FINAL_DUMP=...)> <out html>     (run inside src/legacy, with na_editor_template.html beside it)
# Movable (area 'NA'): grp 'al' / 'edo' / 'gp' (game area kept in 'ga'), plus the spacer rooms that join two of their rooms or one of them to a fixed room
# (dead-end spacer stubs left off). They start where TinTin's exits put them, one room apart, from 5667, 7746 and 2356; a room on another level is offset LV
# diagonally (up = north-east). Fixed: the rooms on the finished map within NEAR rooms of these starts.
import sys, os, json, math
from collections import defaultdict, Counter, deque
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here); sys.path.insert(1, os.path.abspath('..'))   # (src/legacy is the working folder; src for editor_spread, maplib)
import ashen_forest as AF

w = json.load(open(sys.argv[1])); out = sys.argv[2]
rooms, exits = AF._world(); DV = AF.DV
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd', 0: '?'}
isspacer = lambda v: v in rooms and bool(rooms[v]['flags'] & 8) and rooms[v]['area'] == ''
AREAS = {'al': "Angel's Landing", 'edo': 'Village of Edo', 'gp': 'The Grimdog Port Authority'}
GRP = {v: g for g, a in AREAS.items() for v, r in rooms.items() if r['area'] == a}
BS, BS_LINKS = 16226, {5667, 21184}                       # Blood Sea room: only ne -> 5667 and nw -> spacer 21184 -> 21135 shown
WT = 21076                                                # Western Trade Route room between road room 2356 and the port (not on the map)
GRP[BS] = 'al'; GRP[WT] = 'gp'
ANCHORS = [5667, 7746, 2356]
LV, NEAR = 0.55, 30
J = lambda f: json.load(open(os.path.join(here, f)))
cnt0 = Counter(GRP.values()); assert cnt0 == {'al': 23, 'edo': 77, 'gp': 30}, cnt0

# ---- rooms on the finished map, at their final positions ----
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
for v, x, y in zip(AZ['ids'], AZ['xs'], AZ['ys']):                                     # the north (Plains, Peaks, NTR, Azure Sea Coast): the Azure save
    if v in AZH or v in south: continue
    fix(v, 'AZ' if AZE.get(v, {}).get('area') == 'AZ' else 'N', (x, y))
for f, src in (('md', 'MD'), ('pf', 'PF'), ('cd', 'CD')):                             # later editors' movable rooms, as saved
    L = J(f + '_layout_final.json'); E = {r['id']: r for r in J(f + '_editor_edges.json')['rooms']}; H = set(L.get('hidden', []))
    for v, x, y in zip(L['ids'], L['xs'], L['ys']):
        if v in E and not E[v].get('fixed'):
            if v in H: POS.pop(v, None); SRC.pop(v, None)
            else: fix(v, src, (x, y), True)
assert all(a in POS for a in ANCHORS) and not set(GRP) & set(POS), (set(GRP) & set(POS))
K = set(GRP)

# ---- spacers: those joining two rooms (listed or on the map); dead-end stubs left off ----
raw_nb = defaultdict(set)
for v, l in exits.items():
    for e in l: raw_nb[v].add(e['to']); raw_nb[e['to']].add(v)
def nbs(v):
    return raw_nb[v] & BS_LINKS if v == BS else {t for t in raw_nb[v] if t != BS or v in BS_LINKS}
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
for s in keep: GRP[s] = next(GRP[u] for x in [s] for u in sorted(nbs(x)) if u in GRP) if any(u in GRP for u in nbs(s)) else None
while any(g is None for g in GRP.values()):
    for s in [s for s, g in GRP.items() if g is None]:
        GRP[s] = next((GRP[u] for u in sorted(nbs(s)) if GRP.get(u)), None)
S = K | keep

# ---- starting spots: TinTin's exits, one room apart, from the anchors on the map ----
rev = defaultdict(list)
for v, l in exits.items():
    for e in l: rev[e['to']].append(v)
def links(v):
    res = [(e['to'], DV[e['dir']]) for e in exits.get(v, []) if e['dir'] in DV and e['to'] != v]
    for u in rev[v]:
        for e in exits.get(u, []):
            if e['to'] == v and e['dir'] in DV and u != v: d = DV[e['dir']]; res.append((u, (-d[0], -d[1], -d[2])))
    return [(t, d) for t, d in res if (v != BS or t in BS_LINKS) and (t != BS or v in BS_LINKS)]
step = lambda p, d: [p[0] + d[0] + LV * d[2], p[1] + d[1] - LV * d[2]]
start = {}
for a in ANCHORS:
    q = deque([a]); P = {a: list(POS[a])}
    while q:
        x = q.popleft()
        for t, d in links(x):
            if t in S and t not in start: start[t] = step(P[x], d); P[t] = start[t]; q.append(t)
parked = []
while S - set(start):                                                                    # (no compass exit: 'enter' only and the like)
    for v in sorted(S - set(start)):
        t = next((t for t in sorted(nbs(v)) if t in start or t in POS), None)
        if t is not None: p = start.get(t) or list(POS[t]); start[v] = [p[0] + 1, p[1] - 1]
    rest = sorted(S - set(start))
    if rest and all(next((t for t in nbs(v) if t in start or t in POS), None) is None for v in rest):
        v = rest[0]; mine = [start[u] for u in start if GRP[u] == GRP[v]]                # a piece with no exit to the rest: parked just east of its area
        start[v] = [max(p[0] for p in mine) + 2, min(p[1] for p in mine) + 1.5 * len(parked)]; parked.append(v)
assert set(start) == S, S - set(start)
cells = defaultdict(list)
for v in sorted(start): cells[(round(start[v][0] / 0.3), round(start[v][1] / 0.3))].append(v)
for vs in cells.values():
    for k, v in enumerate(vs[1:], 1): start[v][0] += 0.42 * k; start[v][1] += 0.42 * k

# ---- fixed rooms: those near the new rooms ----
pts = [start[v] for v in S]
CTX = {v: SRC[v] for v, p in POS.items() if min(math.hypot(p[0] - a[0], p[1] - a[1]) for a in pts) <= NEAR}

# ---- rooms and exits ----
def exlist(v):
    res = []
    for e in exits.get(v, []):
        r = rooms.get(e['to'])
        if not r or (v == BS and e['to'] not in BS_LINKS): continue
        res.append(f"{DN.get(e['dir'], e['name'])} → {r['name'] or 'spacer room'}" + (f" ({r['area']})" if r['area'] and r['area'] != rooms[v]['area'] else ''))
    return res
R = []
for v in sorted(CTX):
    r = rooms[v]
    R.append(dict(id=v, name=r['name'], terrain='', void=isspacer(v), lvl=0, x=round(POS[v][0], 2), y=round(POS[v][1], 2), x0=round(POS[v][0], 2), y0=round(POS[v][1], 2), fixed=True, src=CTX[v]))
for v in sorted(S):
    r = rooms[v]
    R.append(dict(id=v, name=r['name'], terrain='' if isspacer(v) else r['terrain'], void=isspacer(v), lvl=0, area='NA', grp=GRP[v], piece=0, ga=r['area'],
                  x=round(start[v][0], 2), y=round(start[v][1], 2), x0=round(start[v][0], 2), y0=round(start[v][1], 2), ex=exlist(v)))
V = {r['id'] for r in R}
pair = defaultdict(lambda: [False, False, False])
for v in V:
    for e in exits.get(v, []):
        t = e['to']
        if t not in V or t == v or (BS in (v, t) and ({v, t} - {BS}).pop() not in BS_LINKS): continue
        k = (min(v, t), max(v, t)); pair[k][0 if v == k[0] else 1] = True
        if e['dir'] not in (16, 32): pair[k][2] = True
EDG = [[a, b, 'two' if (f and r and flat) else ('one' if flat else 'ud')] for (a, b), (f, r, flat) in sorted(pair.items())]
lk = sorted(k for k in pair if (k[0] in S) != (k[1] in S))
cnt = Counter(CTX.values()); g = Counter(GRP[v] for v in S); gs = Counter(GRP[v] for v in keep)
audit = dict(al=cnt0['al'] - 1, edo=cnt0['edo'], gp=cnt0['gp'] - 1, als=gs['al'], edos=gs['edo'], gps=gs['gp'],
             exits=sum(1 for k in pair if k[0] in S and k[1] in S), links=len(lk), fixed=len(CTX))
rd = lambda poly: [[round(x, 2), round(y, 2)] for x, y in poly]
trk = list(w['fwtracks']) + list(w['swtracks']) + [w['road'], w['southpath'], w['link']] + list(w['ring']) + [t for t in w.get('etrtracks', []) if len(t) > 1] \
    + list(w.get('ntrroad', [])) + list(w.get('dirtroads', [])) + [t['pts'] if isinstance(t, dict) else t for t in w.get('seaways', [])]
trk = [t for t in trk if t and isinstance(t[0], (list, tuple)) and len(t) > 1]
ctx = dict(land=[rd(p) for p in w['geo']['land']], water=[rd(p) for p in w['geo']['water']],
           tracks=[rd(t) for t in trk], mazes=[dict(poly=rd(m['poly'])) for m in w['fwmazes']], town=[-7.4, -9.4, 7.4, 9.4],
           labels=[[0, 0.4, 'Darkhaven', 2.4], [3, -14.2, 'Shadow Grove', 1.5], [1, -47.3, 'Forgotten Woods', 2.4]])
D = dict(rooms=R, edges=EDG, groups=[], ctx=ctx, audit=audit, unlocked=[])
t = open(os.path.join(here, 'na_editor_template.html'), encoding='utf-8').read()
open(out, 'w', encoding='utf-8').write(t.replace('__DATA__', json.dumps(D, separators=(',', ':'))))
json.dump(dict(rooms=[{k: r[k] for k in ('id', 'terrain', 'void', 'lvl', 'fixed', 'src', 'area', 'grp', 'piece', 'ga') if k in r} for r in R], edges=EDG),
          open(os.path.join(here, 'na_editor_edges.json'), 'w'), separators=(',', ':'))
print('AUDIT', audit)
print('spacers kept', sorted(keep), '| stubs left off', sorted(stubs))
print('links to the map', [(a, b) for a, b in lk], '| parked', parked)
for gg in AREAS:
    xs = [start[v][0] for v in S if GRP[v] == gg]; ys = [start[v][1] for v in S if GRP[v] == gg]
    print(gg, 'start box x %.1f..%.1f y %.1f..%.1f' % (min(xs), max(xs), min(ys), max(ys)))
print('fixed rooms', len(CTX), dict(cnt), '| edges', len(EDG), '| file', os.path.getsize(out) // 1024, 'KB', '| map bounds', w['bounds'])
