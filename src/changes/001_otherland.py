"""Owner's Otherland save of Oct 21 (23:28Z, `legacy/ol_layout_final.json`; editor data `legacy/ol_editor_edges.json`). A basic render only (owner, Oct 21:
customised later):
  - the shown Otherland rooms placed where saved (hidden rooms left off); the 28 unlocked map rooms moved to their saved spots, and the sea lines
    through them (`seawaysfaint` straight, `seawaves` re-waved) follow them;
  - every exit of a shown Otherland room (spacers included) a plain dirt trail (`fwtracks`), straight room to room; not drawn (owner, Oct 21): up/down
    exits and one-way exits (both dashed in the editor), then spacer rooms left as dead ends by that, repeatedly;
  - snow ground (`geo.snow`, template --snow) on a new land piece round the rooms and trails, kept off the existing land and sea; on it (owner, Oct 21:
    a soft white snow texture with little drifts and icy spots; `wild.olsnow`, template OLSNOW): sparkle grain and faint wind wisps, snow drifts,
    icy patches, all clear of the trails and rooms (their own random.Random);
  - the north coast (owner, Oct 22), inside NBOX only: the water rooms there (swimming, underwater, water; 'Over the Cliff', a maze for later, as
    water) and their exits are sea: the sea carried from the Sea of Sorrows and the Azure Sea strip south to the island's north coast (the land
    rooms' edge, inlets to the 3 'The Sea of Sorrows' rooms in the Tundra Fields), at most SEA_W off the land, drawn as `seafill` + `seashore`;
    their exits faint wavy water routes (`seawaves`) instead of trails. The iceberg 22531-22535 its own little snow island, a sliver of sea
    (SLIVER) between it and 22530 on the mainland; the snow texture outside the new land dropped (none moved);
  - Winterlight Island's drawing (`snowisles`) removed for now (owner: to be re-fitted later); its marker stays."""
import json, math, os, random
from collections import defaultdict
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__)); LEG = os.path.join(HERE, '..', 'legacy')
SNOW_R = 1.6                                        # snow reaches this far round each room and trail
CLOSE = 3.0                                         # gaps narrower than 6 rooms between pieces filled
WAVE_AMP, WAVE_LEN = 0.12, 2.5                       # as applied/v2.3/001
DRIFT_AREA, DRIFT_GAP, DRIFT_CLEAR = 14.0, 1.6, 0.7  # one drift per this many square rooms; apart; from trails and rooms
ICE_N, ICE_GAP, ICE_CLEAR = 30, 4.0, 1.0            # icy patches: how many; apart; from trails and rooms
NBOX = unary_union([box(-22, 144, 82, 177), box(-22, 177, -6, 189)])     # the north coast (with 'Over the Cliff' 683 on the west coast)
WET = {'Swimming', 'Underwater', 'Water', 'Seafloor'}
CLIFF = 'Over the Cliff'
ICEBERG = [22531, 22532, 22533, 22534, 22535]       # owner: an iceberg, a little island; 22530 is on the mainland
LAND_R, LTRAIL_R, CLOSE_N = 1.3, 0.9, 3.0           # the mainland's north edge: this far round its rooms and trails, gaps narrower than 6 closed
WET_R, WTRAIL_R = 1.2, 0.8                          # sea at least this far round the water rooms and their routes
ICE_R, SLIVER = 0.9, 0.45                           # the iceberg: this far round its rooms; the sea between it and the mainland
SEA_W, SEA_CLOSE = 6.0, 6.0                         # the sea reaches this far off the land and the old sea; gaps narrower than 12 filled


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
    from maplib import world
    _rooms = world()[0]
    rooms_name = lambda v: _rooms[v]['name']
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
    G = defaultdict(set); ud = one = 0
    for a, b, k in E['edges']:
        if not ({a, b} & OL) or {a, b} & H: continue
        if k == 'ud': ud += 1; continue
        if k == 'one': one += 1; continue
        G[a].add(b); G[b].add(a)
    stub = 0
    while True:                                         # spacer rooms left as dead ends
        dead = [v for v in G if R[v]['void'] and v in OL and len(G[v]) <= 1]
        if not dead: break
        for v in dead:
            for u in G.pop(v): G[u].discard(v)
            stub += 1
    G = defaultdict(set, {v: n for v, n in G.items() if n})
    trails = _chains(G, P)                              # (all of them shape the snow, so its texture stays put)
    inb = lambda v: NBOX.contains(Point(P[v]))
    wet = lambda v: inb(v) and ((v in OL and not R[v]['void'] and (R[v]['terrain'] in WET or rooms_name(v) == CLIFF)) or v in UN)   # (the unlocked rooms: all sea)
    def ends(v, came):                                  # the real rooms a spacer leads to, through other spacers
        out, seen, st = set(), {came, v}, [v]
        while st:
            u = st.pop()
            for x in G[u]:
                if x in seen: continue
                seen.add(x)
                if R[x]['void']: st.append(x)
                else: out.add(x)
        return out
    def wetedge(a, b):
        for v, o in ((a, b), (b, a)):
            if wet(v): return True
            if R[v]['void'] and inb(v) and any(wet(x) for x in ends(v, o)): return True
        return False
    GL, GW = defaultdict(set), defaultdict(set)
    for a in G:
        for b in G[a]:
            (GW if wetedge(a, b) else GL)[a].add(b)
    ltrails = _chains(GL, P); wroutes = _chains(GW, P)
    wild['fwtracks'] = list(wild['fwtracks']) + ltrails
    wild['seawaves'] = list(wild['seawaves']) + [_wave(l) for l in wroutes]
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
    # ---- the snow's texture ----
    rng = random.Random(22534)
    lines = unary_union([LineString(l) for l in trails if len(l) > 1] + [Point(P[v]) for v in OL])
    inner = allsnow.buffer(-0.5)
    x0, y0, x1, y1 = inner.bounds
    def spots(n, gap, clear, tries):
        out = []
        for _ in range(tries):
            if len(out) >= n: break
            q = (rng.uniform(x0, x1), rng.uniform(y0, y1))
            if not inner.contains(Point(q)) or lines.distance(Point(q)) < clear or any(math.dist(q, o) < gap for o in out): continue
            out.append(q)
        return out
    ice = []
    for x, y in spots(ICE_N, ICE_GAP, ICE_CLEAR, 20000):
        rx, ry, r = rng.uniform(0.35, 0.8), rng.uniform(0.2, 0.45), rng.uniform(0, math.pi)
        poly = []
        for i in range(10):
            a = 2 * math.pi * i / 10; k = rng.uniform(0.8, 1.15)
            px, py = rx * k * math.cos(a), ry * k * math.sin(a)
            poly.append([round(x + px * math.cos(r) - py * math.sin(r), 3), round(y + px * math.sin(r) + py * math.cos(r), 3)])
        if lines.distance(Polygon(poly)) >= 0.4 and inner.contains(Polygon(poly)): ice.append(poly)
    icy = unary_union([Polygon(p).buffer(0.6) for p in ice]) if ice else Point(-9e9, -9e9)
    drifts = [[round(x, 3), round(y, 3), round(rng.uniform(0.7, 1.25), 2), round(rng.uniform(-0.35, 0.35), 3)]
              for x, y in spots(int(allsnow.area / DRIFT_AREA), DRIFT_GAP, DRIFT_CLEAR, 60000) if not icy.contains(Point(x, y))]
    wild['olsnow'] = {'poly': [list(map(list, p)) for p in geo['snow']], 'drifts': drifts, 'ice': ice}
    # ---- the north coast ----
    WR = {v for v in OL if wet(v)}
    ice_r = [v for v in ICEBERG if v in OL]
    landr = [v for v in OL if inb(v) and not R[v]['void'] and v not in WR and v not in ice_r]
    core = unary_union([Point(P[v]).buffer(LAND_R) for v in landr] + [LineString(l).buffer(LTRAIL_R) for l in ltrails if len(l) > 1 and NBOX.intersects(LineString(l))])
    wetreach = unary_union([Point(P[v]).buffer(WET_R) for v in WR] + [LineString(l).buffer(WTRAIL_R) for l in wroutes if len(l) > 1]
                           + [Point(P[v]).buffer(WET_R) for v in moved])
    icetr = [l for l in ltrails if len(l) > 1 and all(any(math.dist(q, P[v]) < 0.01 for v in ice_r) for q in (l[0], l[-1]))]
    iceberg = unary_union([Point(P[v]).buffer(ICE_R) for v in ice_r] + [LineString(l).buffer(ICE_R * 0.8) for l in icetr]).buffer(0.4).buffer(-0.4)
    land_all = unary_union([Polygon(p).buffer(0) for p in geo['land'][:-len(pieces)] if len(p) > 2])
    W = unary_union([Polygon(p).buffer(0) for p in geo['water'] if len(p) > 2])
    SF = unary_union([Polygon(p).buffer(0) for p in geo.get('seafill') or [] if len(p) > 2])
    protect = unary_union([Point(P[v]).buffer(0.55) for v in landr] + [LineString(l).buffer(0.3) for l in ltrails if len(l) > 1 and NBOX.intersects(LineString(l))
                                                                           and not any(math.dist(q, P[v]) < 0.01 for v in ice_r for q in (l[0], l[-1]))])
    mainland = unary_union([core.buffer(CLOSE_N).buffer(-CLOSE_N).difference(wetreach), protect.difference(iceberg.buffer(0.01))]).difference(iceberg.buffer(SLIVER).difference(protect))
    solid = unary_union([land_all, mainland, iceberg])
    reach = unary_union([allsnow.buffer(SEA_W), W.buffer(SEA_W), wetreach]).intersection(NBOX)
    region = unary_union([reach, wetreach]).buffer(SEA_CLOSE).buffer(-SEA_CLOSE).intersection(NBOX)
    sea = region.difference(solid.buffer(0.02))
    sea = unary_union([g for g in getattr(sea, 'geoms', [sea]) if g.distance(W) < 0.05 or g.distance(wetreach) < 0.05 and g.area > 1.0])
    # the snow: the old snow minus the new sea (the mainland's north edge), plus the iceberg
    newsnow = allsnow.difference(sea).difference(iceberg.buffer(SLIVER).difference(protect))
    snowp = [g for g in getattr(newsnow, 'geoms', [newsnow]) if g.area > 0.5 and any(g.contains(Point(P[v])) for v in OL)]   # (bits of the old snow with no room: sea now)
    stray = round(sum(g.area for g in getattr(newsnow, 'geoms', [newsnow]) if g.area > 0.5) - sum(g.area for g in snowp), 2)
    sea = unary_union([sea] + [g for g in getattr(newsnow, 'geoms', [newsnow]) if g.area > 0.5 and g not in snowp and NBOX.contains(g)])
    dropped = round(sum(g.area for g in getattr(newsnow, 'geoms', [newsnow]) if g.area <= 0.5), 2)
    ice_p = iceberg.difference(land_all.buffer(0.3)).difference(W.buffer(0.05))
    ice_p = [g for g in getattr(ice_p, 'geoms', [ice_p]) if g.area > 0.3]
    newp = snowp + ice_p
    geo['land'] = list(geo['land'][:-len(pieces)]) + [rd(g) for g in newp]
    geo['snow'] = [rd(g) for g in newp]
    allsnow2 = unary_union(newp)
    # the sea drawn: seafill (over the old sea's edge where they meet, hiding its shore line there), its own shore lines
    fill = sea.difference(W)
    fill = unary_union([fill, W.intersection(fill.buffer(0.3))]).difference(SF).difference(land_all.buffer(0.05)).difference(allsnow2.buffer(0.02))
    fills = [g for g in getattr(fill, 'geoms', [fill]) if g.area > 0.05]
    geo['seafill'] = list(geo.get('seafill') or []) + [rd(g) for g in fills]
    total = unary_union([W, SF] + fills)
    shore = total.boundary.difference(W.boundary.buffer(0.03)).difference(SF.boundary.buffer(0.03)).intersection(sea.buffer(0.1))
    shore = [l for l in getattr(shore, 'geoms', [shore]) if l.geom_type == 'LineString' and l.length > 0.2]
    wild['seashore'] = list(wild.get('seashore') or []) + [[[round(x, 3), round(y, 3)] for x, y in l.simplify(0.02).coords] for l in shore]
    keep = allsnow2.buffer(-0.3)
    nd, ni = len(drifts), len(ice)
    wild['olsnow'] = {'poly': [list(map(list, p)) for p in geo['snow']], 'drifts': [d for d in drifts if keep.contains(Point(d[:2]))],
                      'ice': [p for p in ice if keep.contains(Polygon(p))]}
    seawet = [v for v in WR if not total.buffer(0.01).contains(Point(P[v]))]
    landwet = [v for v in landr if total.buffer(-0.01).contains(Point(P[v]))]
    icepos = {v: round(Point(P[v]).distance(unary_union(ice_p).exterior if ice_p else Point(0, 0)), 2) for v in ice_r}
    gap = round(unary_union(ice_p).distance(unary_union(snowp)), 2) if ice_p else None
    trail_sea = [(round(LineString(l).intersection(sea.buffer(-0.05)).length, 2), l[0], l[-1]) for l in ltrails if len(l) > 1 and LineString(l).intersection(sea.buffer(-0.05)).length > 0.01]
    north = {'water rooms in the box (sea; not in it)': (len(WR), seawet), 'land rooms in the sea': landwet,
             'water routes (lines, exits); land trails (lines)': (len(wroutes), sum(len(GW[v]) for v in GW) // 2, len(ltrails)),
             'sea added (area, pieces, shore lines)': (round(sea.difference(W).area, 1), len(fills), len(shore)),
             'iceberg (pieces, area, its rooms to its shore, sea to the mainland)': (len(ice_p), round(sum(g.area for g in ice_p), 2), icepos, gap),
             'snow (pieces, area; slivers dropped, bits with no room made sea)': ([round(g.area, 1) for g in snowp], round(unary_union(snowp).area, 1), dropped, stray),
             'texture kept (drifts, ice)': ((len(wild['olsnow']['drifts']), nd), (len(wild['olsnow']['ice']), ni)),
             'trail length over the sea': trail_sea}
    # ---- Winterlight Island's drawing, for now ----
    isles = len(wild.get('snowisles') or []); wild['snowisles'] = []
    # ---- checks ----
    offsnow = sorted(v for v in OL if not allsnow.buffer(0.01).contains(Point(P[v])))
    inwater = sorted(v for v in offsnow if water.contains(Point(P[v])))
    return {'rooms placed (Otherland shown; hidden; unlocked moved)': (len(OL), len(H), len(moved)),
            'trails added (lines, exits; not drawn: up/down, one-way, dead-end spacer rooms)': (len(trails), sum(len(G[v]) for v in G) // 2, ud, one, stub),
            'snow texture (drifts, icy patches)': (len(drifts), len(ice)),
            'sea lines moved with their rooms (faint points, wave lines)': (nf, nw),
            'snow (pieces, area; holes filled)': (len(pieces), round(allsnow.area, 1), holes),
            'rooms not on the snow (in the sea; elsewhere)': (inwater, [v for v in offsnow if v not in inwater]),
            'north coast': north, 'Winterlight Island drawings removed': isles, 'bounds': wild['bounds']}
