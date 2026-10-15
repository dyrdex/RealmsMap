# The layout editor for the Pixie Forest rooms the owner listed (Oct 15: the rooms the paths to A'enari and Reomyr Village run through, so they can be laid
# out and the routes shown in full), plus Forgotten Woods rooms 4017-4019 unlocked so they can be moved.
#   python3 build_pf_editor.py <final map state (json, from FINAL_DUMP=...)> <out html>     (run inside src, with pf_editor_template.html beside it)
# Movable (area 'PF'): exactly the listed rooms (no others, no spacers: none are needed, they join directly), grp 'pf' (Pixie Forest), 'an' (Asgard Nexus),
# 'fw' (4017-4019, starting where the map has them). The others start where TinTin's exits put them, one room apart, from 4019's spot on the map; the
# Asgard Nexus is entered with 'enter' (no direction), so 5019 starts one step north-east of 5018.
# Fixed: every room already on the finished map near enough to matter (as the Miden'nir editor).
import sys, os, json
from collections import defaultdict, Counter, deque
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import ashen_forest as AF

w = json.load(open(sys.argv[1])); out = sys.argv[2]
rooms, exits = AF._world(); DV = AF.DV
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd', 0: '?'}
isspacer = lambda v: v in rooms and bool(rooms[v]['flags'] & 8) and rooms[v]['area'] == ''
PF = [5001, 5000, 4999, 4998, 4995, 4994, 4993, 5005, 5004, 5015]
AN = [5018, 5019, 5021, 12232]
FW = [4017, 4018, 4019]
J = lambda f: json.load(open(os.path.join(here, f)))

# ---- fixed rooms (as the Miden'nir editor) ----
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
assert all(CTX.get(v) == 'FW' for v in FW), [CTX.get(v) for v in FW]
assert not (set(PF) | set(AN)) & set(CTX)
start = {v: list(cpos.pop(v)) for v in FW}
for v in FW: CTX.pop(v)
S = set(PF) | set(AN) | set(FW)

# ---- starting spots: TinTin's exits, one room apart, from 4019 ----
rev = defaultdict(list)
for v, l in exits.items():
    for e in l: rev[e['to']].append(v)
def links(v):
    res = [(e['to'], DV[e['dir']]) for e in exits.get(v, []) if e['dir'] in DV and e['to'] != v]
    for u in rev[v]:
        for e in exits.get(u, []):
            if e['to'] == v and e['dir'] in DV and u != v: d = DV[e['dir']]; res.append((u, (-d[0], -d[1], -d[2])))
    if v == 5018: res.append((5019, (1, -1, 0)))                                         # 'enter': no compass direction
    if v == 5019: res.append((5018, (-1, 1, 0)))
    return res
q = deque([4019])
while q:
    x = q.popleft()
    for t, d in links(x):
        if t in S and t not in start: start[t] = [start[x][0] + d[0], start[x][1] + d[1]]; q.append(t)
assert set(start) == S, S - set(start)
cells = defaultdict(list)
for v in sorted(start): cells[(round(start[v][0] / 0.3), round(start[v][1] / 0.3))].append(v)
for vs in cells.values():
    for k, v in enumerate(vs[1:], 1): start[v][0] += 0.42 * k; start[v][1] += 0.42 * k
GRP = {**{v: 'pf' for v in PF}, **{v: 'an' for v in AN}, **{v: 'fw' for v in FW}}

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
    R.append(dict(id=v, name=r['name'], terrain=r['terrain'], void=False, lvl=0, area='PF', grp=GRP[v], piece=0,
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
cnt = Counter(CTX.values())
audit = dict(pf=len(PF), an=len(AN), fw=len(FW), exits=sum(1 for k in pair if k[0] in S and k[1] in S), links=len(lk),
             dh=cnt['DH'], grove=cnt['Grove'], fwfix=cnt['FW'], ft=cnt['FT'], lake=cnt['LK'], wtr=cnt['WT'], af=cnt['AF'], sm=cnt['SM'])
rd = lambda poly: [[round(x, 2), round(y, 2)] for x, y in poly]
trk = list(w['fwtracks']) + list(w['swtracks']) + [w['road'], w['southpath'], w['link']] + list(w['ring']) + [t for t in w.get('etrtracks', []) if len(t) > 1] \
    + list(w.get('ntrroad', [])) + list(w.get('dirtroads', []))
ctx = dict(land=[rd(p) for p in w['geo']['land']], water=[rd(p) for p in w['geo']['water']],
           tracks=[rd(t) for t in trk if len(t) > 1], mazes=[dict(poly=rd(m['poly'])) for m in w['fwmazes']], town=[-7.4, -9.4, 7.4, 9.4],
           labels=[[0, 0.4, 'Darkhaven', 2.4], [3, -14.2, 'Shadow Grove', 1.5], [1, -47.3, 'Forgotten Woods', 2.4]])
D = dict(rooms=R, edges=EDG, groups=[], ctx=ctx, audit=audit, unlocked=FW)
t = open(os.path.join(here, 'pf_editor_template.html'), encoding='utf-8').read()
open(out, 'w', encoding='utf-8').write(t.replace('__DATA__', json.dumps(D, separators=(',', ':'))))
json.dump(dict(rooms=[{k: r[k] for k in ('id', 'terrain', 'void', 'lvl', 'fixed', 'src', 'area', 'grp', 'piece') if k in r} for r in R], edges=EDG),
          open(os.path.join(here, 'pf_editor_edges.json'), 'w'), separators=(',', ':'))
print('AUDIT', audit)
print('links to the map', [(a, b) for a, b in lk])
print('starts', {v: start[v] for v in sorted(S)})
print('fixed rooms', len(CTX), dict(cnt), '| edges', len(EDG), '| file', os.path.getsize(out) // 1024, 'KB')
