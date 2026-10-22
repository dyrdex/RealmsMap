# The Azure Sea routes along Otherland's east coast, redrawn (owner, Oct 22). They are rebuilt from the rooms' exits as applied/v2.6/001_azure_east
# drew them (its lines removed exactly, matched to 0.005), then:
#  - the coastal path (`seawaysfaint`) leaves 6187 south-east to The Iceberg 15154 and goes on south from it to 15171 (was 6187 east to 15149, round
#    15152 and back to 15171): spine cut at 6187 / 15171, the iceberg's links (15161-15154, 15172-15171) are sea-land exits;
#  - every exit between land and sea is the primary water route (`seawaysfaint`) over the water (was the faint wavy style from rooms off the path),
#    and so is a run of sea rooms from the path to a room going ashore (owner, Oct 22: 5999-15748-15747 was half and half); The Iceberg 15154
#    is not land for this: its links other than the path and its climb up to 15738 are outer routes;
#  - the other (outer) routes: the Harbor of Icebergs' display (`olharborways`, its slight wave HWAVE_A/HWAVE_L), not `seawaves`.
import json, math, os, random, sys, heapq, importlib.util
from collections import defaultdict
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union
import maplib

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('az26', os.path.join(HERE, 'applied', 'v2.6', '001_azure_east.py')); AZM = importlib.util.module_from_spec(spec); spec.loader.exec_module(AZM)
CUT = (6187, 15171)                                 # owner (Oct 22): the coastal path leaves the old one here and rejoins it here, by The Iceberg 15154
HWAVE_A, HWAVE_L = 0.05, 1.6                        # applied/v2.4/001's harbour routes
ICE_ROOMS = {15154, 15172}                          # The Iceberg 15154 (+ 15172 on it): only its path links and its climb are primary (owner, Oct 22)


def setup(wild, pos):
    rooms, exits = maplib.world()
    S = json.load(open(os.path.join(AZM.LEG, 'ol_layout_final.json'))); E = json.load(open(os.path.join(AZM.LEG, 'ol_editor_edges.json')))
    P = {v: (x, y) for v, x, y in zip(S['ids'], S['xs'], S['ys'])}; H = set(S['hidden']); R = {r['id'] for r in E['rooms']}
    AZ = {v for v in P if v not in R and v not in H}
    at = lambda v: tuple(pos[str(v)])
    ph = random.Random(13287); a1, a2, a3, a4 = (ph.uniform(0, 2 * math.pi) for _ in range(4))
    TA, TL = AZM.TRACK_A, AZM.TRACK_L
    warp = lambda x, y: (x + TA * (0.7 * math.sin(2 * math.pi * y / TL + a1) + 0.3 * math.sin(2 * math.pi * (x + y) / (TL * 1.6) + a3)),
                         y + TA * (0.7 * math.sin(2 * math.pi * x / TL + a2) + 0.3 * math.sin(2 * math.pi * (x - y) / (TL * 1.6) + a4)))
    FLATP = {frozenset((v, e['to'])) for v, l in exits.items() for e in l if e['dir'] not in (0, 16, 32) and e['to'] != v}
    olroom = {int(k) for k in pos if int(k) not in AZ and rooms.get(int(k), {}).get('area') == 'Otherland'}
    island = set(AZM.ICEBERG); pair = {}
    for v in AZ | olroom | island:
        for e in exits.get(v, []):
            t = e['to']; k = (min(v, t), max(v, t))
            if t == v or not (v in AZ or t in AZ) or t not in AZ | olroom | island or k in AZM.NOT_DRAWN: continue
            if e['dir'] in (16, 32) and frozenset(k) in FLATP: continue
            pair[k] = pair.get(k, False) or e['dir'] in (16, 32)
    edges = sorted(pair)
    landr = {v for v in olroom | island if (rooms[v]['terrain'] not in AZM.WET or v in AZM.AS_LAND) and v != AZM.ICE1}
    wetr = {v for v in olroom if v not in landr and v != AZM.ICE1}
    onland = {v for v in AZ if min(math.dist(at(v), at(u)) for u in landr | {AZM.ICE1}) <= 0.3}
    seaside = (AZ | wetr) - onland
    land = Polygon()
    for r in wild['geo']['land']:
        if len(r) > 2: land = land.symmetric_difference(Polygon(r).buffer(0))
    endp = lambda v: warp(*at(v)) if v in landr else at(v)
    return dict(AZ=AZ, at=at, edges=edges, landr=landr, seaside=seaside, land=land, endp=endp, warp=warp)

def old_spine(C):
    at, edges, seaside = C['at'], C['edges'], C['seaside']
    cl = unary_union([q.exterior for q in AZM._polys(C['land'])])
    G = defaultdict(list)
    for a, b in edges:
        if a in seaside and b in seaside:
            L = math.dist(at(a), at(b)); m = Point((at(a)[0] + at(b)[0]) / 2, (at(a)[1] + at(b)[1]) / 2)
            w = L * (1 + cl.distance(m)) ** 2; G[a].append((b, w)); G[b].append((a, w))
    E0, E1 = AZM.COAST_END
    dist = {E0: 0}; prev = {}; hq = [(0, E0)]
    while hq:
        d, v = heapq.heappop(hq)
        if d > dist.get(v, 1e18): continue
        for t, w in G[v]:
            if d + w < dist.get(t, 1e18): dist[t] = d + w; prev[t] = v; heapq.heappush(hq, (d + w, t))
    spine = [E1]
    while spine[-1] != E0: spine.append(prev[spine[-1]])
    return spine[::-1]

def build(C, spine, wave=None, land_style=None):
    """001's step 4 for a given spine (room ids). wave: how a non-spine sea route is drawn (default 001's seawaves wave);
    land_style: None = as 001 (faint only from a spine room), 'faint' = every sea-land exit faint over the water"""
    at, edges, seaside, endp = C['at'], C['edges'], C['seaside'], C['endp']
    wave = wave or AZM._wave
    parts = spine if spine and isinstance(spine[0], list) else [spine]           # (a path in pieces)
    onsp = {v for p in parts for v in p}; coastal = {(min(a, b), max(a, b)) for p in parts for a, b in zip(p, p[1:])}
    adj = defaultdict(set)
    for a, b in edges:
        if a in seaside and b in seaside: adj[a].add(b); adj[b].add(a)
    used = set(coastal); chains = []
    def walk(a, b):
        line = [a, b]; used.add((min(a, b), max(a, b)))
        while len(adj[line[-1]]) == 2 and line[-1] not in onsp:
            nx = [t for t in adj[line[-1]] if (min(t, line[-1]), max(t, line[-1])) not in used]
            if not nx: break
            used.add((min(nx[0], line[-1]), max(nx[0], line[-1]))); line.append(nx[0])
        return line
    for a, b in edges:
        if (a, b) in used or not (a in seaside and b in seaside): continue
        s = a if (len(adj[a]) != 2 or a in onsp) else b if (len(adj[b]) != 2 or b in onsp) else a
        t = b if s == a else a
        line = walk(s, t)
        if len(adj[s]) == 2 and s not in onsp:
            back = [x for x in adj[s] if (min(x, s), max(x, s)) not in used]
            if back: line = walk(s, back[0])[::-1][:-1] + line
        chains.append(line)
    rp = lambda q: [round(q[0], 3), round(q[1], 3)]
    faint = [[rp(at(a)), rp(at(b))] for p in parts for a, b in zip(p, p[1:])]
    spos = {at(v) for v in onsp}
    ice_ = lambda l: l in ICE_ROOMS
    _, exits_ = maplib.world()
    ashore = {v for v in seaside for e in exits_.get(v, []) if e['to'] in C['landr'] and not ice_(e['to'])}    # (any exit up onto land, e.g. 15747 up to 5972)
    conn = lambda ch: land_style == 'faint' and ((ch[0] in onsp and ch[-1] in ashore) or (ch[-1] in onsp and ch[0] in ashore))   # (path -> a room going ashore)
    faint += [[rp(at(a)), rp(at(b))] for ch in chains if conn(ch) for a, b in zip(ch, ch[1:]) if at(a) != at(b)]
    nconn = sum(1 for ch in chains if conn(ch))
    waves = [wave([list(at(v)) for v in ch]) for ch in chains if not conn(ch) and LineString([at(v) for v in ch]).length > 1e-6]
    trails = []; lg = C['land'].buffer(0)
    def split(p0, p1, style):
        line = LineString([p0, p1]); hit = line.intersection(lg.boundary)
        ds = sorted({0.0, line.length} | {line.project(q) for q in getattr(hit, 'geoms', [hit]) if q.geom_type == 'Point'})
        for d0, d1 in zip(ds, ds[1:]):
            if d1 - d0 < 1e-6: continue
            a_, b_ = line.interpolate(d0).coords[0], line.interpolate(d1).coords[0]
            if lg.contains(line.interpolate((d0 + d1) / 2)):
                n = max(2, int(math.dist(a_, b_) / 0.2)); trails.append([rp((a_[0] + (b_[0] - a_[0]) * i / n, a_[1] + (b_[1] - a_[1]) * i / n)) for i in range(n + 1)])
            elif style == 'faint': faint.append([rp(a_), rp(b_)])
            else: waves.append(wave([list(a_), list(b_)]))
    landing = set()
    for a, b in edges:
        if (a in seaside) == (b in seaside): continue
        s, l = (a, b) if a in seaside else (b, a)
        if land_style == 'faint': st = 'waves' if ice_(l) and at(s) not in spos else 'faint'      # (the iceberg's other links: outer routes)
        else: st = 'faint' if s in onsp else 'waves'
        split(at(s), endp(l), st); landing.add((s, l))
    for lo, hi in sorted(AZM.CLIMBS):
        drawn = any(min(math.dist(l[0], endp(lo)), math.dist(l[-1], endp(lo))) < 0.05 and min(math.dist(l[0], endp(hi)), math.dist(l[-1], endp(hi))) < 0.05
                    for l in C['oltracks0'] if len(l) > 1)
        if (lo, hi) in landing or drawn: continue
        split(endp(lo), endp(hi), 'faint' if land_style == 'faint' else 'waves')
    return faint, waves, trails, nconn


def _take(lst, gone, tol=0.005):
    """remove from lst each line in gone (same point count, ends within tol); returns how many were not found"""
    idx = defaultdict(list)
    for i, l in enumerate(lst):
        if len(l) > 1: idx[(len(l), round(l[0][0]), round(l[0][1]))].append(i)
    drop, miss = set(), 0
    for g in gone:
        c = [i for i in idx.get((len(g), round(g[0][0]), round(g[0][1])), []) if i not in drop and math.dist(lst[i][0], g[0]) < tol and math.dist(lst[i][-1], g[-1]) < tol]
        if c: drop.add(c[0])
        else: miss += 1
    lst[:] = [l for i, l in enumerate(lst) if i not in drop]
    return miss


def apply(town, wild, pos):
    C = setup(wild, pos); C['oltracks0'] = wild['oltracks']
    sp = old_spine(C)
    f0, w0, _, _ = build(C, sp)
    mf, mw = _take(wild['seawaysfaint'], f0), _take(wild['seawaves'], w0)
    assert mf == 0 and mw == 0, (mf, mw)
    i, j = sp.index(CUT[0]), sp.index(CUT[1])
    parts = [sp[:i + 1], sp[j:]]
    f1, w1, _, nconn = build(C, parts, wave=lambda l: AZM._wave(l, HWAVE_A, HWAVE_L), land_style='faint')
    wild['seawaysfaint'] += f1; wild['olharborways'] = list(wild['olharborways']) + w1
    L = lambda ls: round(sum(LineString(l).length for l in ls if len(l) > 1), 1)
    return {'east coast routes redrawn (old primary, old wavy -> primary, harbour style; lengths)': ((len(f0), L(f0)), (len(w0), L(w0)), (len(f1), L(f1)), (len(w1), L(w1))),
            'coastal path rooms (was, now)': (len(sp), len(parts[0]) + len(parts[1])), 'left the path': sp[i + 1:j], 'connectors from the path to a room going ashore (primary)': nconn}
