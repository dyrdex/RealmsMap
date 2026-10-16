# The layout editor for the rooms the owner calls "Coral Depths" (Oct 16): 47 listed rooms (Azure Sea, Coral Depths, and 2522 of the Asgard Nexus) that tie
# the Ashen Forest and the Southern Mountains together, plus rooms on the map unlocked so they can be moved: Southern Mountain Range 7, 8, 9, 10, 572, 6365, 19863, then 569-571, and Ashen Forest 14360 (Oct 16).
#   python3 build_cd_editor.py <final map state (json, from FINAL_DUMP=...)> <out html>     (run inside src, with cd_editor_template.html beside it)
# Movable (area 'CD'): exactly the listed rooms, grp 'cd' (game area kept in 'ga'), plus the spacer rooms that join two of them or one of them to a fixed
# room (dead-end spacer stubs left off), and grp 'un' (the unlocked rooms, starting at their spots in the Southern Mountain or Ashen save). The others start where
# TinTin's exits put them, one room apart, from rooms 10 and 572; a room on another level is offset LV diagonally (up = north-east).
# Fixed: every room already on the finished map near enough to matter (as the Pixie Forest editor).
import sys, os, json
from collections import defaultdict, Counter, deque
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import ashen_forest as AF

w = json.load(open(sys.argv[1])); out = sys.argv[2]
rooms, exits = AF._world(); DV = AF.DV
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd', 0: '?'}
isspacer = lambda v: v in rooms and bool(rooms[v]['flags'] & 8) and rooms[v]['area'] == ''
CD = [669, 6302, 6286, 6287, 6303, 6288, 6289, 6290, 6291, 6292, 6329, 12984, 12983, 12982, 12956, 12598, 12599, 12597, 1494, 1495, 2516, 2806, 2807, 2808,
      2809, 2810, 2811, 2814, 2815, 2816, 2817, 2818, 2517, 2518, 2519, 2520, 2521, 2522, 2523, 2524, 2525, 2526, 2527, 2528, 2529, 2530, 2531]
UN = [7, 8, 9, 10, 572, 6365, 19863, 14360, 569, 570, 571]
NEWLY, NEWLY_AT = [569, 570, 571], '2026-10-16T16:30:02Z'                     # (unlocked after the owner's save of 16:25Z: its lock on them is dropped)
LV = 0.55
J = lambda f: json.load(open(os.path.join(here, f)))
assert len(set(CD)) == 47 and all(v in rooms for v in CD + UN)

# ---- fixed rooms (as the Pixie Forest editor) ----
CTX = {}; cpos = {}
def fix(v, src, p):
    if v not in CTX and v in rooms: CTX[v] = src; cpos[v] = (float(p[0]), float(p[1]))
for k, src in w['ctxsrc'].items(): fix(int(k), src, w['track']['cx' + k])
SML = J('smr_layout_final.json'); SME = J('smr_editor_edges.json'); SPOS = dict(zip(SML['ids'], zip(SML['xs'], SML['ys']))); SHID = set(SML['hidden'])
SGRP = {r['id']: r.get('grp') for r in SME['rooms'] if r.get('area') == 'SM'}
FL = J('ft_layout_final.json'); FE = J('fot_editor_edges.json'); FPOS = dict(zip(FL['ids'], zip(FL['xs'], FL['ys']))); FHID = set(FL['hidden']) | {1891}
for v, g in SGRP.items():
    if g == 'ft' and v in FPOS and v in SPOS: FPOS[v] = SPOS[v]
for r in FE['rooms']:
    v = r['id']
    if r.get('fixed') or v in FHID or v not in FPOS: continue
    fix(v, {'ft': 'FT', 'lk': 'LK', 'wt': 'WT', 'fw': 'FW'}[r['grp']], FPOS[v])
AL = J('ashen_layout_final.json'); AHID = set(AL.get('hidden', []))
for v, x, y in zip(AL['ids'], AL['xs'], AL['ys']):
    if v not in AHID: fix(v, 'AF', (x, y))
for v, g in SGRP.items():
    if g in ('sm', 'ug', 'tr') and v in SPOS and v not in SHID: fix(v, 'SM', SPOS[v])
assert all(CTX.get(v) == ('AF' if v == 14360 else 'SM') for v in UN), [CTX.get(v) for v in UN]
assert not set(CD) & set(CTX), set(CD) & set(CTX)
start = {v: [cpos[v][0], cpos[v][1]] for v in UN}
for v in UN: CTX.pop(v); cpos.pop(v)
K = set(CD) | set(UN)

# ---- spacers: those joining two rooms (listed or on the map); dead-end stubs left off ----
raw_nb = defaultdict(set)
for v, l in exits.items():
    for e in l: raw_nb[v].add(e['to']); raw_nb[e['to']].add(v)
cand = set(); q = deque(K)
while q:
    v = q.popleft()
    for t in raw_nb[v]:
        if t not in cand and t not in CTX and t not in K and isspacer(t): cand.add(t); q.append(t)
keep = set(); stubs = set(); seen = set()
for s in sorted(cand):
    if s in seen: continue
    comp = {s}; st = [s]
    while st:
        x = st.pop()
        for t in raw_nb[x]:
            if t in cand and t not in comp: comp.add(t); st.append(t)
    seen |= comp
    (keep if len({u for x in comp for u in raw_nb[x] if u in K or u in CTX}) >= 2 else stubs).update(comp)
S = K | keep

# ---- starting spots: TinTin's exits, one room apart, from 10 and 572 ----
rev = defaultdict(list)
for v, l in exits.items():
    for e in l: rev[e['to']].append(v)
def links(v):
    res = [(e['to'], DV[e['dir']]) for e in exits.get(v, []) if e['dir'] in DV and e['to'] != v]
    for u in rev[v]:
        for e in exits.get(u, []):
            if e['to'] == v and e['dir'] in DV and u != v: d = DV[e['dir']]; res.append((u, (-d[0], -d[1], -d[2])))
    return res
step = lambda p, d: [p[0] + d[0] + LV * d[2], p[1] + d[1] - LV * d[2]]
q = deque([10, 572])
while q:
    x = q.popleft()
    for t, d in links(x):
        if t in S and t not in start: start[t] = step(start[x], d); q.append(t)
for v in sorted(S - set(start)):                                                         # (no compass exit from the rest: 'enter' only, or reached from the map)
    t = next((t for t in sorted(raw_nb[v]) if t in start or t in cpos), None)
    p = start.get(t) or list(cpos[t]); start[v] = [p[0] + 1, p[1] - 1]
assert set(start) == S, S - set(start)
cells = defaultdict(list)
for v in sorted(start): cells[(round(start[v][0] / 0.3), round(start[v][1] / 0.3))].append(v)
for vs in cells.values():
    for k, v in enumerate(vs[1:], 1): start[v][0] += 0.42 * k; start[v][1] += 0.42 * k
GRP = {**{v: 'cd' for v in CD}, **{v: 'cd' for v in keep}, **{v: 'un' for v in UN}}

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
    R.append(dict(id=v, name=r['name'], terrain='', void=isspacer(v), lvl=0, x=round(cpos[v][0], 2), y=round(cpos[v][1], 2), x0=round(cpos[v][0], 2), y0=round(cpos[v][1], 2), fixed=True, src=CTX[v]))
for v in sorted(S):
    r = rooms[v]
    R.append(dict(id=v, name=r['name'], terrain='' if isspacer(v) else r['terrain'], void=isspacer(v), lvl=0, area='CD', grp=GRP[v], piece=0, ga=r['area'],
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
cnt = Counter(CTX.values()); ga = Counter(rooms[v]['area'] for v in CD)
audit = dict(cd=len(CD), az=ga['Azure Sea'], cdp=ga['Coral Depths'], an=ga['Asgard Nexus'], spc=len(keep), sm=len(UN), smu=sum(v != 14360 for v in UN), afu=1,
             exits=sum(1 for k in pair if k[0] in S and k[1] in S), links=len(lk),
             dh=cnt['DH'], grove=cnt['Grove'], fwfix=cnt['FW'], ft=cnt['FT'], lake=cnt['LK'], wtr=cnt['WT'], af=cnt['AF'], smfix=cnt['SM'])
rd = lambda poly: [[round(x, 2), round(y, 2)] for x, y in poly]
trk = list(w['fwtracks']) + list(w['swtracks']) + [w['road'], w['southpath'], w['link']] + list(w['ring']) + [t for t in w.get('etrtracks', []) if len(t) > 1] \
    + list(w.get('ntrroad', [])) + list(w.get('dirtroads', []))
ctx = dict(land=[rd(p) for p in w['geo']['land']], water=[rd(p) for p in w['geo']['water']],
           tracks=[rd(t) for t in trk if len(t) > 1], mazes=[dict(poly=rd(m['poly'])) for m in w['fwmazes']], town=[-7.4, -9.4, 7.4, 9.4],
           labels=[[0, 0.4, 'Darkhaven', 2.4], [3, -14.2, 'Shadow Grove', 1.5], [1, -47.3, 'Forgotten Woods', 2.4]])
D = dict(rooms=R, edges=EDG, groups=[], ctx=ctx, audit=audit, unlocked=UN, newly=NEWLY, newlyAt=NEWLY_AT)
t = open(os.path.join(here, 'cd_editor_template.html'), encoding='utf-8').read()
open(out, 'w', encoding='utf-8').write(t.replace('__DATA__', json.dumps(D, separators=(',', ':'))))
json.dump(dict(rooms=[{k: r[k] for k in ('id', 'terrain', 'void', 'lvl', 'fixed', 'src', 'area', 'grp', 'piece', 'ga') if k in r} for r in R], edges=EDG),
          open(os.path.join(here, 'cd_editor_edges.json'), 'w'), separators=(',', ':'))
print('AUDIT', audit)
print('spacers kept', sorted(keep), '| stubs left off', sorted(stubs))
print('links to the map', [(a, b) for a, b in lk])
print('fixed rooms', len(CTX), dict(cnt), '| edges', len(EDG), '| file', os.path.getsize(out) // 1024, 'KB')
