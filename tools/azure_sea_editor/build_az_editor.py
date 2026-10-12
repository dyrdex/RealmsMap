# The layout editor for the Azure Sea rooms that join the map (owner, Oct 12: only the Azure Sea rooms linked to rooms already
# mapped, plus the rooms that join those to each other).
#   python3 build_az_editor.py <final map state (json, from FINAL_DUMP=...)> <out html>     (run inside src, with az_editor_template.html beside it)
# Fixed rooms: every shown room on the finished map, where it is: the Northern Plains save (Darkhaven, Grove, Woods, NTR, Barren Peaks,
#   Plains, road) and the Ashen Forest save (forest, Eastern Trade Route, Ocean Keep / Azure beach rooms).
# Movable rooms (area 'AZ'), found from the TinTin map:
#   - Northern Plains: 4317 'Rocky Coastline' (spacers 14314, 22557 lead to Plains room 4316)
#   - the coast north from the cliffs to 4317 (owner, Oct 12): the shortest walk 14282/14283 -> 14287, 14286, 14323, 14322, 14321, 14319, 14318, 14313, spacer 14315 -> 4317; plus 14284, 14285 (14283 -> 14284 -> 14285 -> 14286, owner asked)
#   - the spacer path 4317 -> 14314 -> 22557 -> Plains room 4316: both spacers are on the map (Plains save) but unlocked here, starting where they are (owner, Oct 12)
#   - the path from 4317 north to the Village of Edo (owner, Oct 12): 5749, 5966, 5967, 5968, spacer 15604, 5969, 5970, 7746 (nw -> Edo 7747 'Bridging the Maelstrom')
#   - Barren Peaks: 14271, 14272, 14278, 14279, 14282, 14283 (each has an up exit to a Peaks room) and the cliff-foot rooms between them (14273-14277, 14280, 14281)
#   - Forgotten Woods: no Azure Sea room has an exit to a Woods room. The 'Forgotten Woods Coastline' rooms (14262-14269) are the shore walk that joins
#     the Peaks cliffs (14270 -> 14271) to Azure room 14254, already on the map by the Ashen beach: 14257, spacer 14293, 14259, spacer 14295, 14261..14270.
import sys, os, json
from collections import defaultdict, Counter, deque
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import ashen_forest as AF

w = json.load(open(sys.argv[1])); out = sys.argv[2]
rooms, exits = AF._world(); DV = AF.DV
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd', 0: '?'}
isspacer = lambda v: v in rooms and bool(rooms[v]['flags'] & 8) and rooms[v]['area'] == ''
A = 'Azure Sea'

# ---- fixed rooms ----
NL = json.load(open(os.path.join(here, 'np_layout_final.json'))); NE = json.load(open(os.path.join(here, 'np_editor_edges.json')))
AL = json.load(open(os.path.join(here, 'ashen_layout_final.json'))); AE = json.load(open(os.path.join(here, 'ashen_editor_edges.json')))
CTX = {}; cpos = {}
nr = {r['id']: r for r in NE['rooms']}; nhid = set(NL['hidden'])
for v, x, y in zip(NL['ids'], NL['xs'], NL['ys']):
    if v in nhid: continue
    r = nr[v]; CTX[v] = r['src'] if r.get('fixed') else {'NP': 'NP', 'RD': 'NTR', 'PK': 'BP'}[r['area']]; cpos[v] = (x, y)
ar = {r['id']: r for r in AE['rooms']}; ahid = set(AL['hidden'])
for v, x, y in zip(AL['ids'], AL['xs'], AL['ys']):
    if v in ahid or v in CTX: continue
    CTX[v] = 'AF'; cpos[v] = (x, y)

# ---- movable Azure Sea rooms ----
PLAINS = [4317]
NORTH = [14287, 14284, 14285, 14286, 14323, 14322, 14321, 14319, 14318, 14313, 14315]   # from the cliffs (14282/14283) north to 4317
PEAKS = list(range(14271, 14284))
COAST = [14257, 14293, 14259, 14295, 14261] + list(range(14262, 14271))
EDO = [5749, 5966, 5967, 5968, 15604, 5969, 5970, 7746]   # from 4317 north to the Village of Edo
UNLOCK = [14314, 22557]                                       # the spacers between 4317 and Plains room 4316
for v in UNLOCK: CTX.pop(v)                                   # (cpos keeps their map position: anchor and starting spot)
S = set(PLAINS + NORTH + PEAKS + COAST + EDO + UNLOCK)
assert not S & set(CTX)
assert all(rooms[v]['area'] == A or isspacer(v) for v in S)
SP = {v for v in S if isspacer(v)}
GROUP = {**{v: 'ed' for v in EDO}, **{v: 'np' for v in PLAINS + NORTH + UNLOCK}, **{v: 'pk' for v in PEAKS}, **{v: 'cw' for v in COAST}}

rev = defaultdict(list)
for v, l in exits.items():
    for e in l: rev[e['to']].append(v)
def links(v):
    res = [(e['to'], DV[e['dir']]) for e in exits.get(v, []) if e['dir'] in DV and e['to'] != v]
    for u in rev[v]:
        for e in exits.get(u, []):
            if e['to'] == v and e['dir'] in DV and u != v: d = DV[e['dir']]; res.append((u, (-d[0], -d[1], -d[2])))
    return res

# ---- pieces (flat exits) and where TinTin's exits put them, anchored to the fixed rooms they link to ----
fpos = {}; piece = {}; pieces = []
for s in sorted(S):
    if s in fpos: continue
    k = len(pieces); fpos[s] = (0, 0); piece[s] = k; mem = [s]; q = deque([s])
    while q:
        x = q.popleft()
        for t, d in links(x):
            if t in S and d[2] == 0 and t not in fpos:
                fpos[t] = (fpos[x][0] + d[0], fpos[x][1] + d[1]); piece[t] = k; mem.append(t); q.append(t)
    pieces.append(mem)
LV = 0.55; vec = lambda d: (d[0] + LV * d[2], d[1] - LV * d[2])
est = defaultdict(list); anchor = {}
for v in S:
    for t, d in links(v):
        if t in cpos:
            g = vec(d); est[piece[v]].append((cpos[t][0] - g[0] - fpos[v][0], cpos[t][1] - g[1] - fpos[v][1]))
            anchor.setdefault(v, (t, d))
off = {k: (sum(a for a, b in l) / len(l), sum(b for a, b in l) / len(l)) for k, l in est.items()}
raw = {v: [fpos[v][0] + off[piece[v]][0], fpos[v][1] + off[piece[v]][1]] for v in S}

# ---- starting spot: each room linked to the map starts one room from the room it links to (east of it for an up/down link,
#      else the way the exit points); the rooms between two such rooms are spread evenly along the shore walk between them ----
xy = {}
for v, (t, d) in anchor.items():
    g = (1.0, 0.0) if d[2] else (-d[0], -d[1])
    xy[v] = [cpos[t][0] + g[0], cpos[t][1] + g[1]]
WALK = COAST + [14271, 14272, 14273, 14274, 14275, 14276, 14277, 14278, 14279, 14281, 14282, 14283]
ai = [i for i, v in enumerate(WALK) if v in xy]
for a, b in zip(ai, ai[1:]):
    for i in range(a + 1, b):
        f = (i - a) / (b - a); xy[WALK[i]] = [xy[WALK[a]][0] + f * (xy[WALK[b]][0] - xy[WALK[a]][0]) + 0.6, xy[WALK[a]][1] + f * (xy[WALK[b]][1] - xy[WALK[a]][1])]
for i, v in enumerate(NORTH, 1):
    f = i / (len(NORTH) + 1); xy[v] = [xy[14282][0] + f * (xy[4317][0] - xy[14282][0]) + 0.6, xy[14282][1] + f * (xy[4317][1] - xy[14282][1])]
for v in EDO: xy[v] = [xy[4317][0] + fpos[v][0] - fpos[4317][0], xy[4317][1] + fpos[v][1] - fpos[4317][1]]   # north of 4317 as TinTin's exits lay them out
xy[14280] = [(xy[14278][0] + xy[14281][0]) / 2 + 0.8, (xy[14278][1] + xy[14281][1]) / 2]
for v in UNLOCK: xy[v] = list(cpos[v])
assert set(xy) == S
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
        res.append(f"{DN.get(e['dir'], '?')} → {r['name'] or 'spacer room'}" + (f" ({r['area']})" if r['area'] and r['area'] != A else ''))
    return res
R = []
for v in sorted(CTX):
    r = rooms[v]
    R.append(dict(id=v, name=r['name'], terrain='', void=isspacer(v), lvl=0, x=round(cpos[v][0], 2), y=round(cpos[v][1], 2), x0=round(cpos[v][0], 2), y0=round(cpos[v][1], 2), fixed=True, src=CTX[v]))
for v in sorted(S):
    r = rooms[v]; sp = v in SP
    R.append(dict(id=v, name='' if sp else r['name'], terrain='' if sp else r['terrain'], void=sp, lvl=0, area='AZ', grp=GROUP[v], piece=piece[v],
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
cnt = Counter(CTX.values())
audit = dict(edo=len(EDO), unlocked=len(UNLOCK), plains=len(PLAINS + NORTH), peaks=len(PEAKS), coast=len(COAST), spacers=len(SP & set(COAST)), exits=sum(1 for k in pair if k[0] in S and k[1] in S), links=len(lk),
             linked=', '.join(f'{a}→{b}' if a in S else f'{b}→{a}' for a, b in lk), pieces=len(pieces),
             dh=cnt['DH'], grove=cnt['Grove'], fw=cnt['FW'], ntr=cnt['NTR'], bp=cnt['BP'], np=cnt['NP'], af=cnt['AF'])
rd = lambda poly: [[round(x, 2), round(y, 2)] for x, y in poly]
trk = list(w['fwtracks']) + list(w['swtracks']) + [w['road'], w['southpath'], w['link']] + list(w['ring']) + [t for t in w.get('etrtracks', []) if len(t) > 1] \
    + list(w.get('ntrroad', [])) + list(w.get('dirtroads', []))
ctx = dict(land=[rd(p) for p in w['geo']['land']], water=[rd(p) for p in w['geo']['water']],
           tracks=[rd(t) for t in trk if len(t) > 1], mazes=[dict(poly=rd(m['poly'])) for m in w['fwmazes']], town=[-7.4, -9.4, 7.4, 9.4],
           labels=[[0, 0.4, 'Darkhaven', 2.4], [3, -14.2, 'Shadow Grove', 1.5], [1, -47.3, 'Forgotten Woods', 2.4], [-0.03, -120.14, 'Barren Peaks', 2.4],
                   [-26.5, -164.0, 'Northern Plains', 2.4], [40.25, -24.0, 'Ashen Forest', 2.0]])
D = dict(rooms=R, edges=EDG, groups=[], ctx=ctx, audit=audit, unlocked=UNLOCK)
t = open(os.path.join(here, 'az_editor_template.html'), encoding='utf-8').read()
open(out, 'w', encoding='utf-8').write(t.replace('__DATA__', json.dumps(D, separators=(',', ':'))))
json.dump(dict(rooms=[{k: r[k] for k in ('id', 'terrain', 'void', 'lvl', 'fixed', 'src', 'area', 'grp', 'piece') if k in r} for r in R], edges=EDG),
          open(os.path.join(here, 'az_editor_edges.json'), 'w'), separators=(',', ':'))

# ---- report ----
print('AUDIT', audit)
print('pieces', [len(p) for p in pieces])
print('fixed rooms', len(CTX), dict(cnt), '| edges', len(EDG), '| file', os.path.getsize(out) // 1024, 'KB')
fixedpts = [cpos[v] for v in CTX]
for v in sorted(S):
    dmin = min(((xy[v][0] - c[0]) ** 2 + (xy[v][1] - c[1]) ** 2) ** .5 for c in fixedpts)
    print(v, GROUP[v], (rooms[v]['name'] or 'spacer')[:28].ljust(28), 'start', [round(a, 2) for a in xy[v]], 'nearest fixed %.2f' % dmin, 'anchor', anchor.get(v, ('', ''))[0])
