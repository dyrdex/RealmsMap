# The layout editor for the Wastelands (owner, Oct 16): all its 351 rooms (underwater and tunnel rooms included), off the Southern Mountain Range
# (34-36) and the Southern Mountain Trade Route (9339, 9346). Its exits into the Blood Sea, the Sea of Sorrows and the other areas it leads to are left off.
#   python3 build_wl_editor.py <final map state (json, from FINAL_DUMP=...)> <out html>     (run inside src, with wl_editor_template.html beside it)
# Movable (area 'WL', grp 'wl'): the Wastelands rooms plus the spacer rooms that join two of them or one of them to a fixed room (dead-end spacer stubs
# and spacer branches that only lead off to the seas left off). Starting spots: editor_spread.spread_clear (TinTin's exits, STEP rooms apart, spread
# so no rooms overlap, the whole area then moved next to its anchors clear of the map). Fixed: the rooms on the finished map within NEAR rooms of these.
import sys, os, json, math
from collections import defaultdict, Counter, deque
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import ashen_forest as AF, editor_spread as ES

w = json.load(open(sys.argv[1])); out = sys.argv[2]
rooms, exits = AF._world(); DV = AF.DV
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd', 0: '?'}
isspacer = lambda v: v in rooms and bool(rooms[v]['flags'] & 8) and rooms[v]['area'] == ''
AREAS = {'wl': 'Wastelands'}
GRP = {v: g for g, a in AREAS.items() for v, r in rooms.items() if r['area'] == a}
ANCHORS = [35, 34, 36, 9339, 9346]
LV, NEAR = 0.55, 30
STEP = float(os.environ.get('STEP', 2.0))                    # one exit = STEP map rooms in the starting layout (spread out to read it; editor_spread.py)
J = lambda f: json.load(open(os.path.join(here, f)))
cnt0 = Counter(GRP.values()); assert cnt0 == {'wl': 351}, cnt0

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
for f, src in (('md', 'MD'), ('pf', 'PF'), ('cd', 'CD'), ('na', 'NA')):                             # later editors' movable rooms, as saved
    L = J(f + '_layout_final.json'); E = {r['id']: r for r in J(f + '_editor_edges.json')['rooms']}; H = set(L.get('hidden', []))
    for v, x, y in zip(L['ids'], L['xs'], L['ys']):
        if v in E and not E[v].get('fixed'):
            if v in H: POS.pop(v, None); SRC.pop(v, None)
            else: fix(v, src, (x, y), True)
assert all(a in POS for a in ANCHORS) and not set(GRP) & set(POS), (set(GRP) & set(POS))
K = set(GRP)

# ---- spacers: those joining two rooms (listed or on the map); dead-end stubs and branches that only lead off (to the seas) left off ----
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
while True:                                                                                 # prune dead-end branches of kept spacer pieces
    leaf = {s for s in keep if len({u for u in nbs(s) if u in keep or u in K or u in POS}) <= 1}
    if not leaf: break
    keep -= leaf; stubs |= leaf
for s in keep: GRP[s] = 'wl'
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
    return res
def links2(v):                                                                           # + a link north-east/south-west for 'enter'-only pairs
    res = links(v); have = {u for u, _ in res}
    return res + [(u, (1, -1, 0) if v < u else (-1, 1, 0)) for u in sorted(nbs(v)) if u not in have and u != v and (u in S or u in POS)]
start = ES.spread_clear(S, links2, POS, ANCHORS, step=STEP)
assert set(start) == S, S - set(start)
lone = sorted(v for v in K if not any(u in S or u in POS for u, _ in links2(v)))                                     # rooms with no exit at all
close, far, wrong, thru = ES.report(start, POS, links2, step=STEP)
# ---- fixed rooms: those near the new rooms ----
pts = [start[v] for v in S]
CTX = {v: SRC[v] for v, p in POS.items() if min(math.hypot(p[0] - a[0], p[1] - a[1]) for a in pts) <= NEAR}

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
    R.append(dict(id=v, name=r['name'], terrain='' if isspacer(v) else r['terrain'], void=isspacer(v), lvl=0, area='WL', grp=GRP[v], piece=0, ga=r['area'],
                  x=round(start[v][0], 2), y=round(start[v][1], 2), x0=round(start[v][0], 2), y0=round(start[v][1], 2), ex=exlist(v)))
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
cnt = Counter(CTX.values()); g = Counter(GRP[v] for v in S); gs = Counter(GRP[v] for v in keep)
off = Counter()
for v in K:
    for e in exits.get(v, []):
        a = rooms.get(e['to'], {}).get('area', '')
        if e['to'] not in V and a not in ('', 'Wastelands'): off['bs' if a == 'The Blood Sea' else 'ss' if a == 'Sea of Sorrows' else 'oth'] += 1
audit = dict(wl=cnt0['wl'], wls=gs['wl'], bs=off['bs'], ss=off['ss'], oth=off['oth'],
             exits=sum(1 for k in pair if k[0] in S and k[1] in S), links=len(lk), fixed=len(CTX))
rd = lambda poly: [[round(x, 2), round(y, 2)] for x, y in poly]
trk = list(w['fwtracks']) + list(w['swtracks']) + [w['road'], w['southpath'], w['link']] + list(w['ring']) + [t for t in w.get('etrtracks', []) if len(t) > 1] \
    + list(w.get('ntrroad', [])) + list(w.get('dirtroads', [])) + [t['pts'] if isinstance(t, dict) else t for t in w.get('seaways', [])]
trk = [t for t in trk if t and isinstance(t[0], (list, tuple)) and len(t) > 1]
ctx = dict(land=[rd(p) for p in w['geo']['land']], water=[rd(p) for p in w['geo']['water']],
           tracks=[rd(t) for t in trk], mazes=[dict(poly=rd(m['poly'])) for m in w['fwmazes']], town=[-7.4, -9.4, 7.4, 9.4],
           labels=[[0, 0.4, 'Darkhaven', 2.4], [3, -14.2, 'Shadow Grove', 1.5], [1, -47.3, 'Forgotten Woods', 2.4]])
D = dict(rooms=R, edges=EDG, groups=[], ctx=ctx, audit=audit, unlocked=[])
t = open(os.path.join(here, 'wl_editor_template.html'), encoding='utf-8').read()
open(out, 'w', encoding='utf-8').write(t.replace('__DATA__', json.dumps(D, separators=(',', ':'))))
json.dump(dict(rooms=[{k: r[k] for k in ('id', 'terrain', 'void', 'lvl', 'fixed', 'src', 'area', 'grp', 'piece', 'ga') if k in r} for r in R], edges=EDG),
          open(os.path.join(here, 'wl_editor_edges.json'), 'w'), separators=(',', ':'))
print('AUDIT', audit)
print('spacers kept', sorted(keep), '| stubs left off', sorted(stubs))
print('links to the map', [(a, b) for a, b in lk], '| no exit at all', lone)
print('start: rooms closer than 0.8 (not neighbours)', close, '| exits stretched past 2 steps', far, '| exits pointing the wrong way', wrong, '| exit lines through another room', thru)
for gg in AREAS:
    xs = [start[v][0] for v in S if GRP[v] == gg]; ys = [start[v][1] for v in S if GRP[v] == gg]
    print(gg, 'start box x %.1f..%.1f y %.1f..%.1f' % (min(xs), max(xs), min(ys), max(ys)))
print('fixed rooms', len(CTX), dict(cnt), '| edges', len(EDG), '| file', os.path.getsize(out) // 1024, 'KB', '| map bounds', w['bounds'])
