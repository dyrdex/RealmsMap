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
NBOX = unary_union([box(-22, 144, 82, 177), box(-22, 177, -6, 189), box(60, 177, 82, 187)])     # the north coast (with 'Over the Cliff' 683 on the
                                                    # west coast; east, down to the Azure Sea strip's south end)
WET = {'Swimming', 'Underwater', 'Water', 'Seafloor'}
CLIFF = 'Over the Cliff'
ICEBERG = [22531, 22532, 22533, 22534, 22535, 6166, 13379, 13380, 6180]   # owner (Oct 22): The Iceberg, its own little white island; 22530 on the mainland
ZONE_R, TIGHT_R, TIGHT_TR = 5.0, 0.75, 0.55          # near the iceberg the mainland hugs its rooms (this far) and trails (this far)
FILL1 = unary_union([box(68.5, 174.6, 70.5, 183.0), box(65.5, 176.0, 70.5, 183.0),
                     Polygon([(70.5, 174.6), (72.3, 174.6), (72.75, 176.4), (72.35, 178.2), (72.9, 180.0), (72.5, 181.7), (72.8, 183.0), (70.5, 183.0)])])   # (an uneven east shore)   # owner (Oct 22): land west and south of 13287, its sea inlets gone
FAINT_CHAIN = [6180, 15418, 15417, 15416, 15415, 15414, 15413, 15412, 15411, 15410, 6650, 15128]   # owner (Oct 22): drawn as the Sea of Sorrows' routes
TRACK_A, TRACK_L = 0.16, 7.0                        # Otherland's trails: a gentle long wave (owner, Oct 22): a smooth warp this strong, this long
CLEAR_SEEDS = {13492: 'The Tundra Fields', 13322: 'A Tunnel in the Snow / A Cold Lair'}   # owner (Oct 22): these two clumps only
CLEAR_D, CLEAR_R, CLEAR_TR = 1.5, 0.62, 0.45        # a clump: rooms this close joined by an exit; its clearing this far round its rooms and exits
CLEAR_FILL, CLEAR_EDGE = '#97A1A6', '#6B767C'       # packed snow, a little lighter than the snow
SHACKS = {'The Desolate Outpost': ([13087, 13089, 13090, 13091, 13092, 13093], 0.5, 0.55),    # owner (Oct 22): a log shack over its main section (rooms;
           "The Hunter's Outpost": ([14419], 0.55, 0.6)}                                       #  margin round them across, down), its back door trail west/south clear
WATER_LINKS = [(22530, 22531)]                      # owner (Oct 22): a water path (as the Sea of Sorrows routes), though one-way in TinTin
NW_X = 50.0                                         # water routes wholly west of this: drawn as the Sea of Sorrows' routes (`seawaysfaint`)
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
    nw = 0; icesegs = []; extra = []; faintsegs = []
    isice = lambda q: any(math.dist(q[:2], P[v]) < 0.003 for v in ICEBERG)
    FP = [tuple(P[v]) if v in P else tuple(pos[str(v)][:2]) for v in FAINT_CHAIN]
    isfaint = lambda q: any(math.dist(q[:2], f) < 0.003 for f in FP)
    for j, l in enumerate(wild['seawaves']):
        if not any(near(q) for q in l): continue
        vs = [q for q in l if (round(q[0], 2), round(q[1], 2)) in rp and math.dist(q, rp[(round(q[0], 2), round(q[1], 2))]) < 0.003]
        assert _wave(vs) == l, j
        vs = [list(P[near(q)[0]]) if near(q) else q for q in vs]
        runs = [[vs[0]]]                                # stretches between two iceberg rooms: trails on the iceberg (owner, Oct 22)
        for a, b in zip(vs, vs[1:]):
            if isice(a) and isice(b):
                if math.dist(a, b) > 1e-6: icesegs.append([list(a), list(b)])
                runs.append([b])
            elif isfaint(a) and isfaint(b):
                if math.dist(a, b) > 1e-6: faintsegs.append([list(a), list(b)])
                runs.append([b])
            else: runs[-1].append(b)
        runs = [r for r in runs if len(r) > 1]
        wild['seawaves'][j] = _wave(runs[0]) if runs else []; extra += [_wave(r) for r in runs[1:]]; nw += 1
    wild['seawaves'] = [l for l in wild['seawaves'] if l] + extra
    wild['seawaysfaint'] = list(wild['seawaysfaint']) + faintsegs
    wild['oltracks'] = list(wild.get('oltracks') or []) + icesegs     # Otherland's own trails (owner, Oct 22: tracks in the snow; template OLTRACK)
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
    wet = lambda v: inb(v) and v not in ICEBERG and ((v in OL and not R[v]['void'] and (R[v]['terrain'] in WET or rooms_name(v) == CLIFF)) or v in UN)   # (the unlocked rooms: sea, but the iceberg's)
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
    wild['oltracks'] = list(wild['oltracks']) + ltrails
    nwr = [l for l in wroutes if all(q[0] < NW_X for q in l)]
    wild['seawaysfaint'] = list(wild['seawaysfaint']) + nwr
    wild['seawaves'] = list(wild['seawaves']) + [_wave(l) for l in wroutes if not all(q[0] < NW_X for q in l)]
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
    ice_r = [v for v in ICEBERG if v in OL or v in UN]
    landr = [v for v in OL if inb(v) and not R[v]['void'] and v not in WR and v not in ice_r]
    core = unary_union([Point(P[v]).buffer(LAND_R) for v in landr] + [LineString(l).buffer(LTRAIL_R) for l in ltrails if len(l) > 1 and NBOX.intersects(LineString(l))])
    wetreach = unary_union([Point(P[v]).buffer(WET_R) for v in WR] + [LineString(l).buffer(WTRAIL_R) for l in wroutes if len(l) > 1]
                           + [Point(P[v]).buffer(WET_R) for v in moved if v not in ICEBERG])
    icetr = [l for l in ltrails + icesegs if len(l) > 1 and all(any(math.dist(q, P[v]) < 0.01 for v in ice_r) for q in (l[0], l[-1]))]
    iceberg = unary_union([Point(P[v]).buffer(ICE_R) for v in ice_r] + [LineString(l).buffer(ICE_R * 0.8) for l in icetr]).buffer(0.4).buffer(-0.4)
    land_all = unary_union([Polygon(p).buffer(0) for p in geo['land'][:-len(pieces)] if len(p) > 2])
    W = unary_union([Polygon(p).buffer(0) for p in geo['water'] if len(p) > 2])
    SF = unary_union([Polygon(p).buffer(0) for p in geo.get('seafill') or [] if len(p) > 2])
    protect = unary_union([Point(P[v]).buffer(0.55) for v in landr] + [LineString(l).buffer(0.3) for l in ltrails if len(l) > 1 and NBOX.intersects(LineString(l))
                                                                           and not any(math.dist(q, P[v]) < 0.01 for v in ice_r for q in (l[0], l[-1]))])
    ZONE = iceberg.buffer(ZONE_R)                       # near the iceberg: the mainland hugs its rooms and trails (owner, Oct 22)
    tight = unary_union([Point(P[v]).buffer(TIGHT_R) for v in landr] + [LineString(l).buffer(TIGHT_TR) for l in ltrails if len(l) > 1 and ZONE.intersects(LineString(l))]).intersection(ZONE)
    closed = unary_union([core.buffer(CLOSE_N).buffer(-CLOSE_N).difference(ZONE), tight])
    mainland = unary_union([closed.difference(wetreach), protect.difference(iceberg.buffer(0.01))]).difference(iceberg.buffer(SLIVER).difference(protect))
    mainland = mainland.intersection(allsnow.buffer(0.01))   # (where the old snow kept off the old sea, sea now: no gap)
    fill1 = FILL1.difference(W.buffer(0.3)).difference(iceberg.buffer(SLIVER))
    fill1 = unary_union([fill1, mainland.intersection(FILL1.buffer(1.0))]).buffer(0.3).buffer(-0.3).intersection(FILL1.buffer(0.5)).difference(W.buffer(0.3)).difference(iceberg.buffer(SLIVER))
    mainland = unary_union([mainland, fill1])
    solid = unary_union([land_all, mainland, iceberg])
    reach = unary_union([allsnow.buffer(SEA_W), W.buffer(SEA_W), wetreach]).intersection(NBOX)
    region = unary_union([reach, wetreach]).buffer(SEA_CLOSE).buffer(-SEA_CLOSE).intersection(NBOX)
    sea = region.difference(solid)                      # (exactly up to the land: no hairline gaps)
    sea = unary_union([g for g in getattr(sea, 'geoms', [sea]) if g.distance(W) < 0.05 or g.distance(wetreach) < 0.05 and g.area > 1.0])
    # the snow: the old snow minus the new sea (the mainland's north edge), plus the iceberg
    newsnow = unary_union([allsnow.difference(ZONE), allsnow.intersection(tight), fill1]).difference(sea).difference(iceberg.buffer(SLIVER).difference(protect))
    snowp = [g for g in getattr(newsnow, 'geoms', [newsnow]) if g.area > 0.5 and any(g.contains(Point(P[v])) for v in OL)]
    stray = round(sum(g.area for g in getattr(newsnow, 'geoms', [newsnow]) if g.area > 0.5) - sum(g.area for g in snowp), 2)
    pock = round(sum(Polygon(h).area for g in snowp for h in g.interiors if not Polygon(h).intersects(sea)), 2)
    snowp = [Polygon(g.exterior, [h for h in g.interiors if Polygon(h).intersects(sea)]) for g in snowp]   # pockets inside the snow that aren't sea: snow   # (bits of the old snow with no room: sea now)
    sea = unary_union([sea] + [g for g in getattr(newsnow, 'geoms', [newsnow]) if g.area > 0.5 and g not in snowp and NBOX.contains(g)])
    dropped = round(sum(g.area for g in getattr(newsnow, 'geoms', [newsnow]) if g.area <= 0.5), 2)
    ice_p = iceberg.difference(land_all.buffer(0.3)).difference(W.buffer(0.05))
    ice_p = [g for g in getattr(ice_p, 'geoms', [ice_p]) if g.area > 0.3]
    newp = snowp + ice_p
    rings = lambda gs: [r for g in gs for r in [rd(g)] + [[[round(x, 3), round(y, 3)] for x, y in list(h.coords)[:-1]] for h in g.simplify(0.03).interiors]]   # (holes: rings of their own, the paths are evenodd)
    geo['land'] = list(geo['land'][:-len(pieces)]) + rings(newp)
    geo['snow'] = rings(snowp + ice_p)                  # (the iceberg in the mainland's snow: owner, Oct 22)
    geo['iceisle'] = []
    allsnow2 = unary_union(newp)
    # the sea drawn: seafill (over the old sea's edge where they meet, hiding its shore line there), its own shore lines
    fill = sea.difference(W)
    fill = unary_union([fill, W.intersection(fill.buffer(0.3))]).difference(SF).difference(land_all.buffer(0.05)).difference(allsnow2.buffer(-0.03))   # (just over the snow's edge: no gap)
    fills = [g for g in getattr(fill, 'geoms', [fill]) if g.area > 0.05]
    geo['seafill'] = list(geo.get('seafill') or []) + rings(fills)
    total = unary_union([W, SF] + fills)
    shore = total.boundary.difference(W.boundary.buffer(0.03)).difference(SF.boundary.buffer(0.03)).intersection(sea.buffer(0.1))
    shore = [l for l in getattr(shore, 'geoms', [shore]) if l.geom_type == 'LineString' and l.length > 0.2]
    wild['seashore'] = list(wild.get('seashore') or []) + [[[round(x, 3), round(y, 3)] for x, y in l.simplify(0.02).coords] for l in shore]
    keep = unary_union(snowp).buffer(-0.3)
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
             'snow (pieces, area; slivers dropped, bits with no room made sea, pockets filled)': ([round(g.area, 1) for g in snowp], round(unary_union(snowp).area, 1), dropped, stray, pock),
             'texture kept (drifts, ice)': ((len(wild['olsnow']['drifts']), nd), (len(wild['olsnow']['ice']), ni)),
             'trail length over the sea': trail_sea, 'Azure stretches 6180-15128 as Sea of Sorrows routes': len(faintsegs), 'NW water routes as the Sea of Sorrows routes (of)': (len(nwr), len(wroutes)),
             'iceberg trails from the old sea lines': len(icesegs),
             'mainland near the iceberg (rooms, nearest land room to the iceberg)': (sum(1 for v in landr if ZONE.contains(Point(P[v]))),
                 round(min(Point(P[v]).distance(unary_union(ice_p)) for v in landr), 2) if ice_p else None)}
    # ---- Winterlight Island's drawing, for now ----
    # ---- Otherland's trails: a gentle long wave, one smooth warp for all, so they still meet at the rooms they share ----
    ph = random.Random(13287); a1, a2, a3, a4 = (ph.uniform(0, 2 * math.pi) for _ in range(4))
    def warp(x, y):
        return (x + TRACK_A * (0.7 * math.sin(2 * math.pi * y / TRACK_L + a1) + 0.3 * math.sin(2 * math.pi * (x + y) / (TRACK_L * 1.6) + a3)),
                y + TRACK_A * (0.7 * math.sin(2 * math.pi * x / TRACK_L + a2) + 0.3 * math.sin(2 * math.pi * (x - y) / (TRACK_L * 1.6) + a4)))
    npts = 0; wav = []
    for l in wild['oltracks']:
        pts = [l[0]] + [q for a, q in zip(l, l[1:]) if math.dist(a, q) > 1e-6]
        out = []
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            n = max(2, int(math.dist((ax, ay), (bx, by)) / 0.2))
            out += [[round(c, 3) for c in warp(ax + (bx - ax) * i / n, ay + (by - ay) * i / n)] for i in range(0 if not out else 1, n + 1)]
        if len(out) > 1: wav.append(out); npts += len(out)
    wild['oltracks'] = wav
    # ---- clearings (owner, Oct 22): the two clumps of rooms side by side, packed snow (template CLEAR) ----
    ex = {(a, b) for a, b, k in E['edges'] if k != 'ud'}; ex |= {(b, a) for a, b in ex}
    solo = [v for v in OL if not R[v]['void']]
    nb = defaultdict(set)
    for i, a in enumerate(solo):
        for b in solo[i + 1:]:
            if (a, b) in ex and math.dist(P[a], P[b]) <= CLEAR_D: nb[a].add(b); nb[b].add(a)
    onsnow = unary_union(snowp).buffer(-0.15); clr = {}
    for seed, name in CLEAR_SEEDS.items():
        c, st = {seed}, [seed]
        while st:
            for u in nb[st.pop()] - c: c.add(u); st.append(u)
        g = unary_union([Point(P[v]).buffer(CLEAR_R) for v in c] + [LineString([P[a], P[b]]).buffer(CLEAR_TR) for a in c for b in nb[a] if a < b])
        g = g.buffer(0.25).buffer(-0.25).intersection(onsnow)
        gs = [Polygon(h.exterior) for h in getattr(g, 'geoms', [g]) if h.area > 0.2]
        wild['clearings'] = list(wild.get('clearings') or []) + [{'polys': [rd(h) for h in gs], 'fill': CLEAR_FILL, 'edge': CLEAR_EDGE}]
        clr[name] = (len(c), round(sum(h.area for h in gs), 1), len(gs), sorted(v for v in c if not onsnow.contains(Point(P[v]))))
    cl_all = unary_union([Polygon(h) for c in wild['clearings'][-len(CLEAR_SEEDS):] for h in c['polys']]).buffer(0.5)
    o = wild['olsnow']; n0 = (len(o['drifts']), len(o['ice']))
    o['drifts'] = [d for d in o['drifts'] if not cl_all.contains(Point(d[:2]))]; o['ice'] = [q for q in o['ice'] if not cl_all.intersects(Polygon(q))]
    clr['texture under them dropped (drifts, ice)'] = (n0[0] - len(o['drifts']), n0[1] - len(o['ice']))
    # ---- water paths and shacks (owner, Oct 22) ----
    wild['seawaysfaint'] = list(wild['seawaysfaint']) + [[list(P[a]), list(P[b])] for a, b in WATER_LINKS]
    shk = {}; tl = [LineString(l) for l in wild['oltracks']]
    for name, (vs, mx, my) in SHACKS.items():
        xs = [P[v][0] for v in vs]; ys = [P[v][1] for v in vs]
        x0, x1, y0, y1 = min(xs) - mx, max(xs) + mx, min(ys) - my - 0.35, max(ys) + my     # (the roof rises a little above the top rooms)
        wild['olshacks'] = list(wild.get('olshacks') or []) + [[round((x0 + x1) / 2, 3), round((y0 + y1) / 2, 3), round(x1 - x0, 3), round(y1 - y0, 3)]]
        r = box(x0, y0, x1, y1); inside = set(vs)
        outside = [l for l in tl if not any(math.dist(l.coords[0], P[v]) < 0.25 or math.dist(l.coords[-1], P[v]) < 0.25 for v in inside)]
        shk[name] = {'box': [round(c, 2) for c in (x0, y0, x1, y1)], 'nearest trail not its own': round(min(r.distance(l) for l in outside), 2),
                     'drifts/ice under it': sum(1 for d in wild['olsnow']['drifts'] if r.buffer(0.4).contains(Point(d[:2]))) + sum(1 for q in wild['olsnow']['ice'] if r.buffer(0.4).intersects(Polygon(q)))}
        o = wild['olsnow']; o['drifts'] = [d for d in o['drifts'] if not r.buffer(0.4).contains(Point(d[:2]))]; o['ice'] = [q for q in o['ice'] if not r.buffer(0.4).intersects(Polygon(q))]
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
            'north coast': north, 'shacks': shk, 'clearings (rooms, area, pieces, rooms not on the snow)': clr, 'Winterlight Island drawings removed': isles, 'bounds': wild['bounds']}
