# The layout editor for Miden'nir (owner, Oct 15: put Miden'nir's rooms in a layout editor so some of them can be displayed on the map; the painting stays).
#   python3 build_md_editor.py <final map state (json, from FINAL_DUMP=...)> <out html>     (run inside src, with md_editor_template.html beside it)
# Movable rooms (area 'MD'): Miden'nir's rooms except the tunnels under Mount Doom (owner: not needed), starting where fot_extract.py's painting puts them
# (its layout from TinTin's exits, `mpos`; the arranger never moved Miden'nir), plus the spacer rooms that join two of them or one of them to a fixed room.
# Fixed rooms: every room already on the finished map near enough to matter: Darkhaven, Shadow Grove, Forgotten Woods ('cx'), the Forest of Tears, lake ring
# and Western Trade Route (ft_layout_final.json, with the Sparse Woodlands trail where the Southern Mountain save moved it), the Ashen Forest (its save) and
# the Southern Mountain Range + its trade route (their save). Hidden rooms in those saves are left off.
import sys, os, io, re, json, contextlib
from collections import defaultdict, Counter, deque
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import ashen_forest as AF

w = json.load(open(sys.argv[1])); out = sys.argv[2]
rooms, exits = AF._world(); DV = AF.DV
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd', 0: '?'}
isspacer = lambda v: v in rooms and bool(rooms[v]['flags'] & 8) and rooms[v]['area'] == ''
MA = "Miden'nir"; LV = 0.55
J = lambda f: json.load(open(os.path.join(here, f)))

# ---- fixed rooms ----
CTX = {}; cpos = {}
def fix(v, src, p):
    if v not in CTX and v in rooms: CTX[v] = src; cpos[v] = (float(p[0]), float(p[1]))
for k, src in w['ctxsrc'].items(): fix(int(k), src, w['track']['cx' + k])
SML = J('smr_layout_final.json'); SME = J('smr_editor_edges.json'); SPOS = dict(zip(SML['ids'], zip(SML['xs'], SML['ys']))); SHID = set(SML['hidden'])
SGRP = {r['id']: r.get('grp') for r in SME['rooms'] if r.get('area') == 'SM'}
FL = J('ft_layout_final.json'); FE = J('fot_editor_edges.json'); FPOS = dict(zip(FL['ids'], zip(FL['xs'], FL['ys']))); FHID = set(FL['hidden']) | {1891}
for v, g in SGRP.items():                                                                 # (the Sparse Woodlands trail: where the Southern Mountain save moved it, as build.py does)
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

# ---- Miden'nir: the painting's own layout (fot_extract.py) ----
g = {}
with contextlib.redirect_stdout(io.StringIO()): exec(open(os.path.join(here, 'fot_extract.py')).read(), g)
mpos, MD = g['mpos'], g['MD']
TUNNEL = re.compile(r'Tunnel|Slop|Doom|Ladder|Passage|Alcove|Skull|Landing|Goblin')            # the painting's own 'doom' rooms (fot_extract.mtheme)
TUN = {v for v in MD if TUNNEL.search(rooms[v]['name']) and 'Gazing' not in rooms[v]['name']}    # ('Gazing Upon Mount Doom' is the forest room outside it)
K = MD - TUN
assert not K & set(CTX)

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
S = K | keep; SP = keep

rev = defaultdict(list)
for v, l in exits.items():
    for e in l: rev[e['to']].append(v)
def links(v):
    res = [(e['to'], DV[e['dir']]) for e in exits.get(v, []) if e['dir'] in DV and e['to'] != v]
    for u in rev[v]:
        for e in exits.get(u, []):
            if e['to'] == v and e['dir'] in DV and u != v: d = DV[e['dir']]; res.append((u, (-d[0], -d[1], -d[2])))
    return res

loc = {v: mpos[v] for v in S if v in mpos}                                               # start: the painting's spots; spacers it never placed follow their neighbours
q = deque(sorted(loc))
while q:
    x = q.popleft()
    for t, d in links(x):
        if t in S and t not in loc: loc[t] = tuple(a + b for a, b in zip(loc[x], d)); q.append(t)
for v in sorted(S - set(loc)):                                                           # (a spacer reached only from a fixed room)
    t = next((t for t, d in links(v) if t in cpos), None)
    loc[v] = (cpos[t][0], cpos[t][1], 0) if t else (0, 14, 0)
assert set(loc) >= S
lvl = {v: loc[v][2] for v in S}
xy = {v: [round(loc[v][0] + LV * loc[v][2], 3), round(loc[v][1] - LV * loc[v][2], 3)] for v in S}
cells = defaultdict(list)
for v in sorted(xy): cells[(round(xy[v][0] / 0.3), round(xy[v][1] / 0.3))].append(v)
for vs in cells.values():
    for k, v in enumerate(vs[1:], 1): xy[v][0] += 0.42 * k; xy[v][1] += 0.42 * k
piece = {}; npc = 0
for s in sorted(S):
    if s in piece: continue
    st = [s]; piece[s] = npc
    while st:
        x = st.pop()
        for t, d in links(x):
            if t in S and t not in piece: piece[t] = npc; st.append(t)
    npc += 1

# ---- rooms and exits ----
def exlist(v):
    res = []
    for e in exits.get(v, []):
        r = rooms.get(e['to'])
        if not r: continue
        res.append(f"{DN.get(e['dir'], '?')} → {r['name'] or 'spacer room'}" + (f" ({r['area']})" if r['area'] and r['area'] != MA else ''))
    return res
R = []
for v in sorted(CTX):
    r = rooms[v]
    R.append(dict(id=v, name=r['name'], terrain='', void=isspacer(v), lvl=0, x=round(cpos[v][0], 2), y=round(cpos[v][1], 2), x0=round(cpos[v][0], 2), y0=round(cpos[v][1], 2), fixed=True, src=CTX[v]))
for v in sorted(S):
    r = rooms[v]; sp = v in SP
    R.append(dict(id=v, name='' if sp else r['name'], terrain='' if sp else r['terrain'], void=sp, lvl=lvl[v], area='MD', grp='md', piece=piece[v],
                  x=round(xy[v][0], 2), y=round(xy[v][1], 2), x0=round(xy[v][0], 2), y0=round(xy[v][1], 2), ex=exlist(v)))
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
cnt = Counter(CTX.values()); tz = Counter(lvl[v] for v in S)
audit = dict(md=len(K), all=len(MD), tunnels=len(TUN), spacers=len(SP), stubs=len(stubs), exits=sum(1 for k in pair if k[0] in S and k[1] in S), links=len(lk), pieces=npc,
             levels=', '.join(f'{z:+d}: {n}' for z, n in sorted(tz.items())),
             dh=cnt['DH'], grove=cnt['Grove'], fw=cnt['FW'], ft=cnt['FT'], lake=cnt['LK'], wtr=cnt['WT'], af=cnt['AF'], sm=cnt['SM'])
rd = lambda poly: [[round(x, 2), round(y, 2)] for x, y in poly]
trk = list(w['fwtracks']) + list(w['swtracks']) + [w['road'], w['southpath'], w['link']] + list(w['ring']) + [t for t in w.get('etrtracks', []) if len(t) > 1] \
    + list(w.get('ntrroad', [])) + list(w.get('dirtroads', []))
ctx = dict(land=[rd(p) for p in w['geo']['land']], water=[rd(p) for p in w['geo']['water']],
           tracks=[rd(t) for t in trk if len(t) > 1], mazes=[dict(poly=rd(m['poly'])) for m in w['fwmazes']], town=[-7.4, -9.4, 7.4, 9.4],
           labels=[[0, 0.4, 'Darkhaven', 2.4], [3, -14.2, 'Shadow Grove', 1.5], [1, -47.3, 'Forgotten Woods', 2.4], [(w['midlabel']['x0'] + w['midlabel']['x1']) / 2, w['midlabel']['y'], "Miden'nir", 1.5]])
D = dict(rooms=R, edges=EDG, groups=[], ctx=ctx, audit=audit, unlocked=[])
t = open(os.path.join(here, 'md_editor_template.html'), encoding='utf-8').read()
open(out, 'w', encoding='utf-8').write(t.replace('__DATA__', json.dumps(D, separators=(',', ':'))))
json.dump(dict(rooms=[{k: r[k] for k in ('id', 'terrain', 'void', 'lvl', 'fixed', 'src', 'area', 'grp', 'piece') if k in r} for r in R], edges=EDG),
          open(os.path.join(here, 'md_editor_edges.json'), 'w'), separators=(',', ':'))

# ---- report ----
print('AUDIT', audit)
print('tunnel rooms left out:', sorted(Counter(rooms[v]['name'] for v in TUN).items()))
print('kept:', sorted(Counter(rooms[v]['name'] for v in K).items()))
print('fixed rooms', len(CTX), dict(cnt), '| edges', len(EDG), '| file', os.path.getsize(out) // 1024, 'KB')
