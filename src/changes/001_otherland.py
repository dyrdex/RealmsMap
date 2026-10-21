"""Owner's Otherland save of Oct 21 (23:28Z, `legacy/ol_layout_final.json`; editor data `legacy/ol_editor_edges.json`). A basic render only (owner, Oct 21:
customised later):
  - the shown Otherland rooms placed where saved (hidden rooms left off); the 28 unlocked map rooms moved to their saved spots, and the sea lines
    through them (`seawaysfaint` straight, `seawaves` re-waved) follow them;
  - every exit of a shown Otherland room (spacers included, up/down not drawn) a plain dirt trail (`fwtracks`), straight room to room;
  - plain snow ground (`geo.snow`, template) on a new land piece round the rooms and trails, kept off the existing land and sea;
  - Winterlight Island's drawing (`snowisles`) removed for now (owner: to be re-fitted later); its marker stays."""
import json, math, os
from collections import defaultdict
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__)); LEG = os.path.join(HERE, '..', 'legacy')
SNOW_R = 1.6                                        # snow reaches this far round each room and trail
CLOSE = 3.0                                         # gaps narrower than 6 rooms between pieces filled
WAVE_AMP, WAVE_LEN = 0.12, 2.5                       # as applied/v2.3/001


def _wave(line):
    pts = [line[0]] + [q for a, q in zip(line, line[1:]) if math.dist(a, q) > 1e-6]
    out = [[round(pts[0][0], 3), round(pts[0][1], 3)]]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        L = math.hypot(bx - ax, by - ay); n = max(1, round(L / WAVE_LEN)); m = max(4, int(L / 0.06))
        nx, ny = -(by - ay) / L, (bx - ax) / L
        for i in range(1, m + 1):
            t = i / m; o = WAVE_AMP * math.sin(2 * math.pi * n * t) * min(1, L / 0.8)
            out.append([round(ax + (bx - ax) * t + nx * o, 3), round(ay + (by - ay) * t + ny * o, 3)])
    return out


def _chains(G, P):
    """lines between junctions, each inner room given twice so the template's curve runs straight from room to room (as applied/v2.3/001)"""
    chains = []; seen = set()
    for v in [v for v in G if len(G[v]) != 2] + sorted(G):
        for u in sorted(G[v]):
            k = (min(v, u), max(v, u))
            if k in seen: continue
            ch = [v, u]; seen.add(k)
            while len(G[ch[-1]]) == 2:
                nx = [q for q in G[ch[-1]] if q != ch[-2]][0]; k = (min(ch[-1], nx), max(ch[-1], nx))
                if k in seen: break
                seen.add(k); ch.append(nx)
            chains.append(ch)
    out = []
    for ch in chains:
        line = []
        for i, v in enumerate(ch):
            q = [round(P[v][0], 2), round(P[v][1], 2)]
            line += [q, list(q)] if 0 < i < len(ch) - 1 else [q]
        out.append(line)
    return out


def apply(town, wild, pos):
    S = json.load(open(os.path.join(LEG, 'ol_layout_final.json'))); E = json.load(open(os.path.join(LEG, 'ol_editor_edges.json')))
    R = {r['id']: r for r in E['rooms']}
    P = {v: (x, y) for v, x, y in zip(S['ids'], S['xs'], S['ys'])}; H = set(S['hidden'])
    OL = {v for v, r in R.items() if not r.get('fixed') and r['grp'] != 'un' and v not in H}
    UN = {v for v, r in R.items() if r.get('grp') == 'un'}
    assert all(str(v) not in pos for v in OL)
    # ---- unlocked map rooms moved, and the sea lines through them ----
    old = {v: tuple(pos[str(v)][:2]) if str(v) in pos else tuple(wild['track']['cx%d' % v][:2]) for v in UN}
    moved = {v for v in UN if math.dist(old[v], P[v]) > 0.01}
    near = lambda q: [v for v in moved if math.dist(q[:2], old[v]) < 0.003]
    nf = 0
    for l in wild['seawaysfaint']:
        for q in l:
            m = near(q)
            if m: q[0], q[1] = P[m[0]][0], P[m[0]][1]; nf += 1
    rp = {}
    for p in list(pos.values()) + list(wild['track'].values()): rp[(round(p[0], 2), round(p[1], 2))] = tuple(p[:2])
    nw = 0
    for j, l in enumerate(wild['seawaves']):
        if not any(near(q) for q in l): continue
        vs = [q for q in l if (round(q[0], 2), round(q[1], 2)) in rp and math.dist(q, rp[(round(q[0], 2), round(q[1], 2))]) < 0.003]
        assert _wave(vs) == l, j
        vs = [list(P[near(q)[0]]) if near(q) else q for q in vs]
        wild['seawaves'][j] = _wave(vs); nw += 1
    for v in moved:
        if str(v) in pos: pos[str(v)] = [P[v][0], P[v][1]]
        else: wild['track']['cx%d' % v] = [P[v][0], P[v][1]]
    for v in OL: pos[str(v)] = [P[v][0], P[v][1]]
    # ---- exits: plain trails ----
    G = defaultdict(set); ud = 0
    for a, b, k in E['edges']:
        if not ({a, b} & OL) or {a, b} & H: continue
        if k == 'ud': ud += 1; continue
        G[a].add(b); G[b].add(a)
    trails = _chains(G, P)
    wild['fwtracks'] = list(wild['fwtracks']) + trails
    # ---- snow ground ----
    geo = wild['geo']
    land0 = unary_union([Polygon(p).buffer(0) for p in geo['land'] if len(p) > 2])
    water = unary_union([Polygon(p).buffer(0) for p in geo['water'] if len(p) > 2] + [Polygon(p).buffer(0) for p in geo.get('seafill') or [] if len(p) > 2])
    snow = unary_union([Point(P[v]).buffer(SNOW_R) for v in OL] + [LineString(l).buffer(SNOW_R) for l in trails if len(l) > 1])
    snow = snow.buffer(CLOSE).buffer(-CLOSE).difference(land0.buffer(0.3)).difference(water.buffer(0.3))
    pieces = sorted([g for g in getattr(snow, 'geoms', [snow]) if g.area > 1.0], key=lambda g: -g.area)
    holes = sum(len(g.interiors) for g in pieces)
    pieces = [Polygon(g.exterior).difference(land0.buffer(0.3)).difference(water.buffer(0.3)) for g in pieces]
    pieces = [h for g in pieces for h in getattr(g, 'geoms', [g]) if h.area > 1.0]
    rd = lambda g: [[round(x, 3), round(y, 3)] for x, y in list(g.simplify(0.03).exterior.coords)[:-1]]
    geo['land'] = list(geo['land']) + [rd(g) for g in pieces]
    geo['snow'] = [rd(g) for g in pieces]
    allsnow = unary_union(pieces)
    b = wild['bounds']; xb = allsnow.bounds
    wild['bounds'] = [min(b[0], math.floor(xb[0] - 1)), b[1], max(b[2], math.ceil(xb[2] + 1)), max(b[3], math.ceil(xb[3] + 1))]
    # ---- Winterlight Island's drawing, for now ----
    isles = len(wild.get('snowisles') or []); wild['snowisles'] = []
    # ---- checks ----
    offsnow = sorted(v for v in OL if not allsnow.buffer(0.01).contains(Point(P[v])))
    inwater = sorted(v for v in offsnow if water.contains(Point(P[v])))
    return {'rooms placed (Otherland shown; hidden; unlocked moved)': (len(OL), len(H), len(moved)),
            'trails added (lines, exits; up/down not drawn)': (len(trails), sum(len(G[v]) for v in G) // 2, ud),
            'sea lines moved with their rooms (faint points, wave lines)': (nf, nw),
            'snow (pieces, area; holes filled)': (len(pieces), round(allsnow.area, 1), holes),
            'rooms not on the snow (in the sea; elsewhere)': (inwater, [v for v in offsnow if v not in inwater]),
            'Winterlight Island drawings removed': isles, 'bounds': wild['bounds']}
