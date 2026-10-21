# The Wastelands layout editor, v3 (owner, Oct 20): new rooms from the Sea of Sorrows and the Blood Sea (the owner's list, Winterlight Island 9841,
# 9842 included) and the spacer rooms that join them to each other or to the map, laid out south of the beaches.
# Unlocked (start at their map spots): grp 'wl' the Beaches of Sorrow and The Wasted Shores of Ahtborne rooms and the placed spacer rooms joined to them.
# Everything else fixed at today's map spots (base/map.json's room_pos + the track rooms). Save format 'wl-layout-3', so the Oct 17 save isn't reloaded.
#   python3 build_wl3_editor.py <final map state (json, from FINAL_DUMP=...)> <out html>     (wl3_editor_template.html beside this file)
import sys, os, json, math
from collections import defaultdict, Counter, deque
here = os.path.dirname(os.path.abspath(__file__)); SRCDIR = os.path.normpath(os.path.join(here, '..', '..', 'src', 'legacy')); sys.path[:0] = [SRCDIR, os.path.dirname(SRCDIR)]
import ashen_forest as AF, editor_spread as ES

w = json.load(open(sys.argv[1])); out = sys.argv[2]
rooms, exits = AF._world(); DV = AF.DV
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd', 0: '?'}
isspacer = lambda v: v in rooms and bool(rooms[v]['flags'] & 8) and rooms[v]['area'] == ''
LIST = [17980, 17991, 17768, 12272, 12271, 15686, 12270, 12269, 12268, 12267, 12266, 12265, 9840, 9841, 9842, 9839, 12277, 12278, 12279, 18052, 12282,
        12283, 12284, 12285, 12286, 12287, 12288, 12289, 12290, 12291, 18057, 12292, 18060, 12293, 12294, 12295, 12296, 12297, 18058, 18062, 18063, 18064,
        18067, 18068, 18066, 18071, 18044, 18040]                                    # the owner's list, Oct 20
SKIP = [17768]       # 'A Cemetery Path' in Machine Dreams, no exit to any of the others: left off (asked the owner)
K = set(LIST) - set(SKIP)
BEACH = sorted(v for v, r in rooms.items() if r['area'] == 'Wastelands' and r['name'] in ('Beaches of Sorrow', 'The Wasted Shores of Ahtborne'))
STEP = float(os.environ.get('STEP', 2.0)); NEAR = 30

# ---- rooms on the map, at today's spots ----
B = json.load(open(os.path.join(SRCDIR, '..', 'base', 'map.json')))
ACODE = {'Wastelands': 'WL', 'Southern Mountain Range': 'SM', 'Desert of Despair': 'DD', 'The Mire': 'MI', 'Forest of Tears': 'FT', 'Ashen Forest': 'AF'}
POS = {}; SRC = {}
for k, src in w['ctxsrc'].items():
    v = int(k)
    if v in rooms: POS[v] = tuple(map(float, w['track']['cx' + k])); SRC[v] = src
for k, p in B['room_pos'].items():
    v = int(k)
    if v in rooms and v not in POS: POS[v] = (float(p[0]), float(p[1])); SRC[v] = ACODE.get(rooms[v]['area'])
named = [v for v in POS if SRC[v]]
for v in POS:
    if not SRC[v]:
        p = POS[v]; u = min(named, key=lambda u: (POS[u][0] - p[0]) ** 2 + (POS[u][1] - p[1]) ** 2); SRC[v] = SRC[u] if math.dist(POS[u], p) < 6 else 'N'
assert not K & set(POS) and all(v in POS for v in BEACH)

raw_nb = defaultdict(set)
for v, l in exits.items():
    for e in l: raw_nb[v].add(e['to']); raw_nb[e['to']].add(v)
nbs = lambda v: raw_nb[v]
# ---- unlocked: the beach rooms + the placed spacer rooms joined to them (through other placed spacers) ----
WLS = set(); q = deque(BEACH)
while q:
    v = q.popleft()
    for t in nbs(v):
        if t in POS and isspacer(t) and t not in WLS: WLS.add(t); q.append(t)
UNL = set(BEACH) | WLS
# ---- spacers joining the new rooms (to each other or to the map); dead-end stubs and branches left off ----
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
GRP = {v: 'ss' for v in K | keep}
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
def links2(v):
    res = links(v); have = {u for u, _ in res}
    return res + [(u, (1, -1, 0) if v < u else (-1, 1, 0)) for u in sorted(nbs(v)) if u not in have and u != v and (u in S or u in POS)]
ROOTS = [9837] + [v for v in BEACH if v != 9837]                                   # grown from Beaches of Sorrow 9837 (s -> 12266)
start = ES.spread_clear(S, links2, POS, ROOTS, step=STEP)
close, far, wrong, thru = ES.report(start, POS, links2, step=STEP)
lone = sorted(v for v in K if not any(u in S or u in POS for u, _ in links2(v)))
# ---- fixed rooms near; unlocked rooms at their map spots ----
pts = [start[v] for v in S] + [POS[v] for v in UNL]
CTX = {v: SRC[v] for v, p in POS.items() if v not in UNL and min(math.hypot(p[0] - a[0], p[1] - a[1]) for a in pts) <= NEAR}
for v in UNL: start[v] = [round(POS[v][0], 2), round(POS[v][1], 2)]; GRP[v] = 'wl'
S = S | UNL

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
    R.append(dict(id=v, name=r['name'], terrain='' if isspacer(v) else r['terrain'], void=isspacer(v), lvl=0, area='WL', grp=GRP[v], ga=r['area'] or 'spacer',
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
        if e['to'] not in V: offc[rooms.get(e['to'], {}).get('area') or 'spacer rooms'] += 1
audit = dict(ss=len(K), sss=len(keep), wl=len(BEACH), wls=len(WLS), exits=sum(1 for k in pair if k[0] in S and k[1] in S), links=len(lk), fixed=len(CTX),
             off=', '.join(f'{a} {n}' for a, n in sorted(offc.items())))
rd = lambda poly: [[round(x, 2), round(y, 2)] for x, y in poly]
trk = list(w['fwtracks']) + list(w['swtracks']) + [w['road'], w['southpath'], w['link']] + list(w['ring']) + [t for t in w.get('etrtracks', []) if len(t) > 1] \
    + list(w.get('ntrroad', [])) + list(w.get('dirtroads', [])) + [t['pts'] if isinstance(t, dict) else t for t in w.get('seaways', [])]
trk = [t for t in trk if t and isinstance(t[0], (list, tuple)) and len(t) > 1]
ctx = dict(land=[rd(p) for p in w['geo']['land']], water=[rd(p) for p in w['geo']['water']],
           tracks=[rd(t) for t in trk], mazes=[dict(poly=rd(m['poly'])) for m in w['fwmazes']], town=[-7.4, -9.4, 7.4, 9.4],
           labels=[[0, 0.4, 'Darkhaven', 2.4], [3, -14.2, 'Shadow Grove', 1.5], [1, -47.3, 'Forgotten Woods', 2.4]])
D = dict(rooms=R, edges=EDG, groups=[], ctx=ctx, audit=audit)
t = open(os.path.join(here, 'wl3_editor_template.html'), encoding='utf-8').read()
open(out, 'w', encoding='utf-8').write(t.replace('__DATA__', json.dumps(D, separators=(',', ':'))))
json.dump(dict(rooms=[{k: r[k] for k in ('id', 'terrain', 'void', 'lvl', 'fixed', 'src', 'area', 'grp', 'ga', 'x0', 'y0') if k in r and not (k in ('x0', 'y0') and r.get('fixed'))} for r in R], edges=EDG),
          open(os.path.join(SRCDIR, 'wl3_editor_edges.json'), 'w'), separators=(',', ':'))
print('AUDIT', audit)
print('left off from the list', SKIP, '| spacers kept', len(keep), sorted(keep), '| stubs left off', sorted(stubs))
print('unlocked beach rooms', len(BEACH), '| their spacers', len(WLS), sorted(WLS))
print('links to the map', lk, '| no exit at all', lone)
print('start: rooms closer than 0.8 (not neighbours)', close, '| exits stretched past 2 steps', far, '| wrong way', wrong, '| lines through another room', thru)
xs = [start[v][0] for v in K | keep]; ys = [start[v][1] for v in K | keep]
print('new rooms box x %.1f..%.1f y %.1f..%.1f' % (min(xs), max(xs), min(ys), max(ys)), '| fixed rooms', len(CTX), dict(cnt), '| edges', len(EDG), '| file', os.path.getsize(out) // 1024, 'KB')
