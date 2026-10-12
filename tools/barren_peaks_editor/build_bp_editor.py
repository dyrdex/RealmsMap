# The layout editor for the Barren Peaks of Tahjliera.
#   python3 build_bp_editor.py <final map state (json, from FINAL_DUMP=...)> <out html>     (run inside src, with bp_editor_template.html beside it)
# Fixed (locked) rooms: every room already on the finished map in Darkhaven, the Shadow Grove and the Forgotten Woods, and the
#   Northern Trade Route up to the long bridge (from ntr_layout_final.json), where they are.
# Left out: REMOVE (owner's request).
# Movable rooms: the three rooms of the long bridge (4133-4135, starting where they are), every Barren Peaks room, the Northern Trade Route past the bridge, and the spacer rooms joined to them,
#   in "pieces" (rooms joined by flat exits; up/down exits do not join pieces).
import sys, os, json
from collections import defaultdict, Counter, deque
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here)
import ashen_forest as AF

w = json.load(open(sys.argv[1])); out = sys.argv[2]
fot = json.load(open(os.path.join(here, 'fot.json')))
NL = json.load(open(os.path.join(here, 'ntr_layout_final.json')))
rooms, exits = AF._world(); DV = AF.DV
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd', 0: '?'}
tr = w['track']; LV = 0.55
isspacer = lambda v: v in rooms and bool(rooms[v]['flags'] & 8) and rooms[v]['area'] == ''
vec = lambda d: (d[0] + LV * d[2], d[1] - LV * d[2])

# ---- fixed rooms: tracked Darkhaven / Grove / Woods rooms, plus the placed Northern Trade Route ----
CTX = {int(k): s for k, s in fot['ctxsrc'].items() if 'cx' + k in tr}
cpos = {v: tuple(tr['cx' + str(v)][:2]) for v in CTX}
nlk = set(NL['locked']); nhid = set(NL['hidden'])
for v, x, y in zip(NL['ids'], NL['xs'], NL['ys']):
    if v not in nlk and v not in nhid: CTX[v] = 'NTR'; cpos[v] = (x, y)
onmap_ntr = set(NL['ids'])

# ---- movable rooms ----
A = 'Barren Peaks of Tahjliera'
BP = {v for v, r in rooms.items() if r['area'] == A}
ROAD = {v for v, r in rooms.items() if r['area'] == 'Northern Trade Route'} - onmap_ntr
rev = defaultdict(list)
for v, l in exits.items():
    for e in l: rev[e['to']].append(v)
S = BP | ROAD; dq = deque(sorted(S))
while dq:
    v = dq.popleft()
    for t in [e['to'] for e in exits.get(v, [])] + rev[v]:
        if t not in S and t not in onmap_ntr and t not in CTX and isspacer(t): S.add(t); dq.append(t)
REMOVE = {7058}                                                 # "The Barrier": owner asked (Oct 9) to unlink it and leave it off the map
S -= REMOVE
SP = S - BP - ROAD

def links(v):                                   # (other room, (dx,dy,dz)) both ways, file order
    res = [(e['to'], DV[e['dir']]) for e in exits.get(v, []) if e['dir'] in DV and e['to'] != v]
    for u in rev[v]:
        for e in exits.get(u, []):
            if e['to'] == v and e['dir'] in DV and u != v: d = DV[e['dir']]; res.append((u, (-d[0], -d[1], -d[2])))
    return res

# ---- pieces: flat exits only ----
ENTRY = 5090                                                    # "A Disturbing Cry", where the road enters the Peaks
fpos = {}; piece = {}; raw_pieces = []
for s in [ENTRY] + sorted(S):
    if s in fpos: continue
    k = len(raw_pieces); fpos[s] = (0, 0); piece[s] = k; mem = [s]; q = deque([s])
    while q:
        x = q.popleft()
        for t, d in links(x):
            if t in S and d[2] == 0 and t not in fpos:
                fpos[t] = (fpos[x][0] + d[0], fpos[x][1] + d[1]); piece[t] = k; mem.append(t); q.append(t)
    raw_pieces.append(mem)
order = sorted(range(len(raw_pieces)), key=lambda k: (-len(raw_pieces[k]), min(raw_pieces[k])))
ren = {k: i for i, k in enumerate(order)}; piece = {v: ren[k] for v, k in piece.items()}
pieces = [raw_pieces[k] for k in order]

# ---- level above/below the entrance (all exits) ----
lvl = {ENTRY: 0}; q = deque([ENTRY])
while q:
    x = q.popleft()
    for t, d in links(x):
        if t in S and t not in lvl: lvl[t] = lvl[x] + d[2]; q.append(t)
for v in S: lvl.setdefault(v, 0)

# ---- where TinTin's exits put each piece: anchored to the fixed rooms, then to pieces already anchored ----
off = {}
est = defaultdict(list)
for v in S:
    for t, d in links(v):
        if t in CTX:
            g = vec(d); est[piece[v]].append((cpos[t][0] - g[0] - fpos[v][0], cpos[t][1] - g[1] - fpos[v][1]))
for k, l in est.items(): off[k] = (sum(a for a, b in l) / len(l), sum(b for a, b in l) / len(l))
anchored_by_fixed = sorted(off)
for _ in range(len(pieces)):
    est = defaultdict(list)
    for v in S:
        if piece[v] in off: continue
        for t, d in links(v):
            if t in S and piece[t] in off:
                g = vec(d); p = (fpos[t][0] + off[piece[t]][0], fpos[t][1] + off[piece[t]][1])
                est[piece[v]].append((p[0] - g[0] - fpos[v][0], p[1] - g[1] - fpos[v][1]))
    if not est: break
    for k, l in est.items(): off[k] = (sum(a for a, b in l) / len(l), sum(b for a, b in l) / len(l))
assert len(off) == len(pieces), 'a piece with no link to anything placed'
raw = {v: [fpos[v][0] + off[piece[v]][0], fpos[v][1] + off[piece[v]][1]] for v in S}

# ---- starting spot: north of everything; the big piece keeps TinTin's shape, the small pieces in a column to its east ----
fy0 = min(p[1] for p in cpos.values())
main = pieces[0]
dy = (fy0 - 8) - max(raw[v][1] for v in main)
xy = {v: [raw[v][0], raw[v][1] + dy] for v in main}
colx = max(xy[v][0] for v in main) + 6; coly = min(xy[v][1] for v in main)
for k in range(1, len(pieces)):
    vs = pieces[k]; x0 = min(fpos[v][0] for v in vs); y0 = min(fpos[v][1] for v in vs)
    for v in vs: xy[v] = [colx + fpos[v][0] - x0, coly + fpos[v][1] - y0]
    coly += max(fpos[v][1] for v in vs) - y0 + 4
for P in (xy, raw):                                             # rooms that land on the same spot are fanned out
    cells = defaultdict(list)
    for v in sorted(P): cells[(round(P[v][0] / 0.3), round(P[v][1] / 0.3))].append(v)
    for vs in cells.values():
        for k, v in enumerate(vs[1:], 1): P[v][0] += 0.42 * k; P[v][1] += 0.42 * k

# ---- rooms and exits for the editor ----
def exlist(v):
    res = []
    for e in exits.get(v, []):
        r = rooms.get(e['to'])
        if not r: continue
        res.append(f"{DN.get(e['dir'], '?')} \u2192 {r['name'] or 'spacer room'}" + (f" ({r['area']})" if r['area'] and r['area'] != A else ''))
    return res
UNLOCK = [4133, 4134, 4135]                                     # the long bridge: owner can move these (Oct 9); they start where they are on the map
R = []
for v in sorted(CTX):
    r = rooms[v]
    if v in UNLOCK:
        R.append(dict(id=v, name=r['name'], terrain=r['terrain'], void=False, lvl=0, area='RD', x=round(cpos[v][0], 2), y=round(cpos[v][1], 2), x0=round(cpos[v][0], 2), y0=round(cpos[v][1], 2), ex=exlist(v)))
        continue
    R.append(dict(id=v, name=r['name'], terrain='', void=isspacer(v), lvl=0, x=round(cpos[v][0], 2), y=round(cpos[v][1], 2), x0=round(cpos[v][0], 2), y0=round(cpos[v][1], 2), fixed=True, src=CTX[v]))
for v in sorted(S):
    r = rooms[v]; sp = v in SP
    assert v not in REMOVE
    R.append(dict(id=v, name='' if sp else r['name'], terrain='' if sp else r['terrain'], void=sp, lvl=lvl[v], area='RD' if v in ROAD else 'BP', piece=piece[v],
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
inner = sum(1 for k in pair if k[0] in S and k[1] in S)
sizes = ', '.join(str(len(p)) for p in pieces[:3]) + (f' and {len(pieces) - 3} single rooms' if all(len(p) == 1 for p in pieces[3:]) else ' …')
audit = dict(bp=len(BP - REMOVE), removed=', '.join(map(str, sorted(REMOVE))), road=len(ROAD), spacers=len(SP), pieces=len(pieces), sizes=sizes, exits=inner, links=len(lk),
             dh=sum(1 for s in CTX.values() if s == 'DH'), grove=sum(1 for s in CTX.values() if s == 'Grove'), fw=sum(1 for s in CTX.values() if s == 'FW'), ntr=sum(1 for v, s in CTX.items() if s == 'NTR' and v not in UNLOCK), unlocked=len(UNLOCK))
rd = lambda poly: [[round(x, 2), round(y, 2)] for x, y in poly]
trk = list(w['fwtracks']) + list(w['swtracks']) + list(w.get('etrtracks', [])) + [w['road'], w['southpath'], w['link']] + list(w['ring'])
ctx = dict(land=[rd(p) for p in w['geo']['land']], water=[rd(p) for p in w['geo']['water']],
           tracks=[rd(t) for t in trk if len(t) > 1], mazes=[dict(poly=rd(m['poly'])) for m in w['fwmazes']], town=[-7.4, -9.4, 7.4, 9.4],
           labels=[[0, 0.4, 'Darkhaven', 2.4], [3, -14.2, 'Shadow Grove', 1.5], [1, -47.3, 'Forgotten Woods', 2.4]])
D = dict(rooms=R, edges=EDG, groups=[], ctx=ctx, audit=audit, unlocked=UNLOCK)
t = open(os.path.join(here, 'bp_editor_template.html'), encoding='utf-8').read()
open(out, 'w', encoding='utf-8').write(t.replace('__DATA__', json.dumps(D, separators=(',', ':'))))

# ---- report ----
mv = [r for r in R if not r.get('fixed')]
print('AUDIT', audit)
print('start: x %.0f..%.0f, y %.0f..%.0f | fixed rooms reach up to y %.1f' % (min(r['x'] for r in mv), max(r['x'] for r in mv), min(r['y'] for r in mv), max(r['y'] for r in mv), fy0))
print('pieces anchored by links to the map:', [k + 1 for k in sorted(ren[k] for k in anchored_by_fixed)] if False else sorted({piece[v] + 1 for v in S for t, d in links(v) if t in CTX}))
print('by terrain:', dict(Counter(r['terrain'] for r in mv if r['terrain'])))
print('levels:', dict(sorted(Counter(lvl[v] for v in S).items())))
near = sum(1 for v in S for p in [raw[v]] if any(abs(p[0] - c[0]) < .6 and abs(p[1] - c[1]) < .6 for c in cpos.values()))
print('suggested spot: rooms within 0.6 of a fixed room:', near, '| edges', len(EDG), '| file', os.path.getsize(out) // 1024, 'KB')
print('links to the map:', [(a, b) for a, b in lk])
