# The layout editor for the Northern Plains.
#   python3 build_np_editor.py <final map state (json, from FINAL_DUMP=...)> <out html>     (run inside src/legacy, with np_editor_template.html beside it)
# Fixed (locked) rooms: every room already on the finished map: Darkhaven, the Shadow Grove, the Forgotten Woods, the Northern Trade Route
#   up to and including the long bridge, and the shown Barren Peaks rooms (from bp_layout_final.json), where they are.
# Movable rooms:
#   - the Northern Trade Route past the bridge (area 'RD', placed by the Barren Peaks layout) and the spacer rooms that lie only on that road:
#     they start where they are on the map (the Plains overlap them; owner asked for them to be movable, Oct 10)
#   - every Northern Plains room and the spacer rooms joined to them (area 'NP'), in pieces (flat exits), starting where TinTin's exits put them.
import sys, os, json
from collections import defaultdict, Counter, deque
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, here); sys.path.insert(1, os.path.abspath('..'))   # (src/legacy is the working folder; src for editor_spread, maplib)
import ashen_forest as AF

w = json.load(open(sys.argv[1])); out = sys.argv[2]
fot = json.load(open(os.path.join(here, 'fot.json')))
NL = json.load(open(os.path.join(here, 'ntr_layout_final.json')))
BL = json.load(open(os.path.join(here, 'bp_layout_final.json')))
BE = json.load(open(os.path.join(here, 'bp_editor_edges.json')))
rooms, exits = AF._world(); DV = AF.DV
DN = {1: 'n', 2: 'e', 4: 's', 8: 'w', 3: 'ne', 9: 'nw', 6: 'se', 12: 'sw', 16: 'u', 32: 'd', 0: '?'}
tr = w['track']; LV = 0.55
isspacer = lambda v: v in rooms and bool(rooms[v]['flags'] & 8) and rooms[v]['area'] == ''
vec = lambda d: (d[0] + LV * d[2], d[1] - LV * d[2])
A = 'Northern Plains'

# ---- fixed rooms ----
CTX = {int(k): s for k, s in fot['ctxsrc'].items() if 'cx' + k in tr}
cpos = {v: tuple(tr['cx' + str(v)][:2]) for v in CTX}
nlk = set(NL['locked']); nhid = set(NL['hidden'])
for v, x, y in zip(NL['ids'], NL['xs'], NL['ys']):
    if v not in nlk and v not in nhid: CTX[v] = 'NTR'; cpos[v] = (x, y)
bpos = {v: (x, y) for v, x, y in zip(BL['ids'], BL['xs'], BL['ys'])}
bhid = set(BL['hidden']); BR = {r['id']: r for r in BE['rooms']}
BRIDGE = [4133, 4134, 4135]
for v in BRIDGE: CTX[v] = 'NTR'; cpos[v] = bpos[v]
badj = defaultdict(set)
for a, b, k in BE['edges']: badj[a].add(b); badj[b].add(a)
RD = {v for v, r in BR.items() if r.get('area') == 'RD' and v not in bhid} - set(BRIDGE)
RD |= {v for v, r in BR.items() if r.get('void') and r.get('area') == 'BP' and v not in bhid and badj[v] and all(BR.get(t, {}).get('area') == 'RD' for t in badj[v])}
for v, r in BR.items():
    if r.get('area') == 'BP' and v not in bhid and v not in RD: CTX[v] = 'BP'; cpos[v] = bpos[v]
UNLOCK = [4216, 4219, 4382]                                     # spacer chain between road rooms 4213 and 4214: owner asked (Oct 10) to move them with the road
for v in UNLOCK: CTX.pop(v); RD.add(v)
PEAKS_ROAD = set(range(4136, 4152))   # 4152-4155 unlocked again (owner, Oct 11)                             # the road inside the Barren Peaks (4136 'Entering the Barren Peaks' .. 4155 'The Roadway Rises From the Canyon'): owner asked (Oct 10) to lock it; from 4156 'A Dirt Road Through the Foothills' on, the road is in the Plains and stays movable
for v in PEAKS_ROAD: RD.discard(v); CTX[v] = 'NTR'; cpos[v] = bpos[v]
UNLOCK_PK = [v for v in list(range(7188, 7200)) + list(range(7208, 7221)) if CTX.get(v) == 'BP']   # Barren Peaks rooms by the Plains: owner asked (Oct 11) to move them; area 'PK', start where they are
UNLOCK_RD = [4152, 4153, 4154, 4155]                                                            # road rooms in the canyon: owner asked (Oct 11)
for v in UNLOCK_PK: CTX.pop(v)
for v in UNLOCK_RD: CTX.pop(v, None); RD.add(v)
onmap = set(CTX) | RD | set(BR)                                 # anything the Peaks editor knew (hidden rooms included) stays out of the Plains

# ---- movable Plains rooms ----
NP = {v for v, r in rooms.items() if r['area'] == A}
rev = defaultdict(list)
for v, l in exits.items():
    for e in l: rev[e['to']].append(v)
S = set(NP); dq = deque(sorted(S))
while dq:
    v = dq.popleft()
    for t in [e['to'] for e in exits.get(v, [])] + rev[v]:
        if t not in S and t not in onmap and isspacer(t): S.add(t); dq.append(t)
REMOVE = {4363, 4417, 4515} | {4384, 4524, 4764, 4801, 4802}   # owner asked (Oct 10): these three Plains rooms and the spacer rooms next to them are left off
S -= REMOVE
SP = S - NP
M = S | RD                                                      # every movable room

def links(v):
    res = [(e['to'], DV[e['dir']]) for e in exits.get(v, []) if e['dir'] in DV and e['to'] != v]
    for u in rev[v]:
        for e in exits.get(u, []):
            if e['to'] == v and e['dir'] in DV and u != v: d = DV[e['dir']]; res.append((u, (-d[0], -d[1], -d[2])))
    return res

# ---- pieces (Plains only; flat exits) ----
fpos = {}; piece = {}; raw_pieces = []
for s in sorted(S):
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
NPC = len(pieces)
rdpiece = {}                                                    # the road's own pieces, numbered after the Plains'
for s in sorted(RD):
    if s in rdpiece: continue
    k = NPC + len(set(rdpiece.values())); rdpiece[s] = k; q = deque([s])
    while q:
        x = q.popleft()
        for t in badj[x]:
            if t in RD and t not in rdpiece: rdpiece[t] = k; q.append(t)

# ---- levels (from the room with most links to the road / Peaks) ----
ENTRY = max(sorted(NP), key=lambda v: sum(1 for t, d in links(v) if t in CTX or t in RD))
lvl = {ENTRY: 0}; q = deque([ENTRY])
while q:
    x = q.popleft()
    for t, d in links(x):
        if t in S and t not in lvl: lvl[t] = lvl[x] + d[2]; q.append(t)
for v in S: lvl.setdefault(v, 0)

# ---- where TinTin's exits put each piece: anchored to the fixed rooms and the road, then to pieces already anchored ----
known = dict(cpos); known.update({v: bpos[v] for v in RD}); known.update({v: bpos[v] for v in UNLOCK_PK})
off = {}; est = defaultdict(list)
for v in S:
    for t, d in links(v):
        if t in known:
            g = vec(d); est[piece[v]].append((known[t][0] - g[0] - fpos[v][0], known[t][1] - g[1] - fpos[v][1]))
for k, l in est.items(): off[k] = (sum(a for a, b in l) / len(l), sum(b for a, b in l) / len(l))
anchored = sorted(off)
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
loose = [k for k in range(len(pieces)) if k not in off]
raw = {v: [fpos[v][0] + off[piece[v]][0], fpos[v][1] + off[piece[v]][1]] for v in S if piece[v] in off}

# ---- starting spot: pieces linked to the map start where TinTin's exits put them (overlapping the road past the bridge, which is movable);
#      pieces with no link to anything placed go in a column east of the big piece ----
fy0 = min(p[1] for p in known.values())
xy = {v: list(raw[v]) for v in raw}
colx = max(xy[v][0] for v in xy) + 6; coly = min(xy[v][1] for v in xy)
for k in loose:
    vs = pieces[k]; x0 = min(fpos[v][0] for v in vs); y0 = min(fpos[v][1] for v in vs)
    for v in vs: xy[v] = [colx + fpos[v][0] - x0, coly + fpos[v][1] - y0]
    coly += max(fpos[v][1] for v in vs) - y0 + 3
for v in S: raw.setdefault(v, list(xy[v]))
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
        res.append(f"{DN.get(e['dir'], '?')} \u2192 {r['name'] or 'spacer room'}" + (f" ({r['area']})" if r['area'] and r['area'] != A else ''))
    return res
SRC = {'DH', 'Grove', 'FW', 'NTR', 'BP'}
R = []
for v in sorted(CTX):
    r = rooms[v]
    R.append(dict(id=v, name=r['name'], terrain='', void=isspacer(v), lvl=0, x=round(cpos[v][0], 2), y=round(cpos[v][1], 2), x0=round(cpos[v][0], 2), y0=round(cpos[v][1], 2), fixed=True, src=CTX[v]))
for v in sorted(S):
    r = rooms[v]; sp = v in SP
    R.append(dict(id=v, name='' if sp else r['name'], terrain='' if sp else r['terrain'], void=sp, lvl=lvl[v], area='NP', piece=piece[v],
                  x=round(xy[v][0], 2), y=round(xy[v][1], 2), x0=round(raw[v][0], 2), y0=round(raw[v][1], 2), ex=exlist(v)))
# (the road comes after the Plains so it is drawn on top of them)
for v in sorted(UNLOCK_PK):
    r = rooms[v]; sp = isspacer(v)
    R.append(dict(id=v, name='' if sp else r['name'], terrain='' if sp else r['terrain'], void=sp, lvl=0, area='PK',
                  x=round(bpos[v][0], 2), y=round(bpos[v][1], 2), x0=round(bpos[v][0], 2), y0=round(bpos[v][1], 2), ex=exlist(v)))
for v in sorted(RD):
    r = rooms[v]; sp = isspacer(v)
    R.append(dict(id=v, name='' if sp else r['name'], terrain='' if sp else r['terrain'], void=sp, lvl=0, area='RD', piece=rdpiece[v],
                  x=round(bpos[v][0], 2), y=round(bpos[v][1], 2), x0=round(bpos[v][0], 2), y0=round(bpos[v][1], 2), ex=exlist(v)))
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
lk_rd = [k for k in lk if k[0] in RD or k[1] in RD]
inner = sum(1 for k in pair if k[0] in S and k[1] in S)
sizes = ', '.join(str(len(p)) for p in pieces[:4]) + (f' and {sum(1 for p in pieces[4:] if len(p) == 1)} single rooms' if len(pieces) > 4 and all(len(p) <= 1 for p in pieces[4:]) else (f' and {len(pieces) - 4} smaller' if len(pieces) > 4 else ''))
audit = dict(np=len(NP - REMOVE), removed=', '.join(map(str, sorted(REMOVE))), road=len(RD), spacers=len(SP), pieces=len(pieces), sizes=sizes, exits=inner, links=len(lk), linksrd=len(lk_rd),
             dh=sum(1 for s in CTX.values() if s == 'DH'), grove=sum(1 for s in CTX.values() if s == 'Grove'), fw=sum(1 for s in CTX.values() if s == 'FW'),
             ntr=sum(1 for v, s in CTX.items() if s == 'NTR' and v not in PEAKS_ROAD), ntrpk=len(PEAKS_ROAD), bp=sum(1 for s in CTX.values() if s == 'BP'))
rd = lambda poly: [[round(x, 2), round(y, 2)] for x, y in poly]
trk = list(w['fwtracks']) + list(w['swtracks']) + [w['road'], w['southpath'], w['link']] + list(w['ring'])
# road lines: leave out the stretch past the bridge (it is drawn live from the movable road rooms instead)
rdpts = [bpos[v] for v in RD]
def on_rd(t): return sum(1 for p in t if min((p[0] - a) ** 2 + (p[1] - b) ** 2 for a, b in rdpts) < 2.0) > len(t) / 2
etr = [t for t in w.get('etrtracks', []) if len(t) > 1]
trk += [t for t in etr if not on_rd(t)]
ctx = dict(land=[rd(p) for p in w['geo']['land']], water=[rd(p) for p in w['geo']['water']],
           tracks=[rd(t) for t in trk if len(t) > 1], mazes=[dict(poly=rd(m['poly'])) for m in w['fwmazes']], town=[-7.4, -9.4, 7.4, 9.4],
           labels=[[0, 0.4, 'Darkhaven', 2.4], [3, -14.2, 'Shadow Grove', 1.5], [1, -47.3, 'Forgotten Woods', 2.4], [-0.03, -120.14, 'Barren Peaks', 2.4]])
D = dict(rooms=R, edges=EDG, groups=[], ctx=ctx, audit=audit, unlocked=UNLOCK + UNLOCK_PK + UNLOCK_RD)
t = open(os.path.join(here, 'np_editor_template.html'), encoding='utf-8').read()
open(out, 'w', encoding='utf-8').write(t.replace('__DATA__', json.dumps(D, separators=(',', ':'))))
json.dump(dict(rooms=[{k: r[k] for k in ('id', 'terrain', 'void', 'lvl', 'fixed', 'src', 'area', 'piece') if k in r} for r in R], edges=EDG),
          open(os.path.join(here, 'np_editor_edges.json'), 'w'), separators=(',', ':'))

# ---- report ----
print('AUDIT', audit)
print('road tracks left out of the background:', sum(1 for t in etr if on_rd(t)), 'of', len(etr))
mv = [r for r in R if r.get('area') == 'NP']
print('start: x %.0f..%.0f, y %.0f..%.0f | fixed rooms reach up to y %.1f' % (min(r['x'] for r in mv), max(r['x'] for r in mv), min(r['y'] for r in mv), max(r['y'] for r in mv), fy0))
print('TinTin spot: x %.0f..%.0f, y %.0f..%.0f' % (min(r['x0'] for r in mv), max(r['x0'] for r in mv), min(r['y0'] for r in mv), max(r['y0'] for r in mv)))
print('pieces anchored:', len(anchored), 'loose (no link to anything placed):', len(loose))
print('levels:', dict(sorted(Counter(lvl[v] for v in S).items())), 'entry', ENTRY, rooms[ENTRY]['name'])
print('by terrain:', dict(Counter(r['terrain'] for r in mv if r['terrain'])))
fixedpts = list(cpos.values())
near = sum(1 for v in S if v in raw and any(abs(raw[v][0] - c[0]) < .6 and abs(raw[v][1] - c[1]) < .6 for c in fixedpts))
nrd = sum(1 for v in S if any(abs(raw[v][0] - c[0]) < .6 and abs(raw[v][1] - c[1]) < .6 for c in rdpts))
print('TinTin spot overlaps: with fixed rooms', near, '| with the road', nrd, '| edges', len(EDG), '| file', os.path.getsize(out) // 1024, 'KB')
print('links: to fixed', len(lk) - len(lk_rd), 'to road', len(lk_rd))
print('areas linked:', dict(Counter(rooms[t]['area'] or 'spacer' for v in NP for t, d in links(v) if t not in S)))
