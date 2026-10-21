"""Owner's Desert of Despair save of Oct 21 (14:20Z, `legacy/dd_layout_az.json`; editor data `legacy/dd_editor_edges_az.json`): the Azure Sea coast
south of the Docks (grp 'az': 38 rooms + 78 spacers) placed where saved, and the 3 shown desert rooms the save moved (6294, 6332, 6334; their trail
follows them; 20290, hidden, only moved). Drawn as the Sea of Sorrows was (applied/v2.2/001):
  - exits between land rooms (the sandy coastline rooms and the desert rooms), through their spacers: desert trails (`fwtracks`), straight room to room;
  - every other exit of a new room (into the water rooms): fainter, wavy water routes (`seawaves`, template SEAWAVE; owner, Oct 21: even fainter than the Sea of Sorrows' and wavy, being in the ocean):
    each stretch from room to room a gentle wave that is flat at both rooms; up/down exits not drawn;
  - land (desert sand) added round the coastline rooms and trails that lie off the land; the sea (the north-east sea, water 9) carried on south under
    the water rooms and routes, inside BOX, never over land; the map grows east and south to fit."""
import json, math, os
from collections import defaultdict
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__)); LEG = os.path.join(HERE, '..', 'legacy')
BOX = (74.0, 55.0, 118.0, 190.0)                    # (x0, y0, x1, y1): land and sea added only inside this box
SEA = 9                                             # geo.water[9]: the sea north-east of the desert (ends at y 65)
SAND = 16                                           # geo.sand[16] (= ddsand.poly): the desert's ground
TRACK = 625                                         # fwtracks[625]: 6293 - 6328 - 6294 - 6334 - 6332 - 6333 - 6310 (6294, 6332, 6334 moved)
TRACK_ROOMS = [6293, 6328, 6294, 6334, 6332, 6333, 6310]
WET = {'Swimming', 'WideSwim', 'Water'}
WAVE_AMP, WAVE_LEN = 0.12, 1.0                       # the water routes' wave: amplitude, wavelength (about; a whole number of waves per stretch)
SEA_R = 2.6                                         # sea reaches this far round each water room and water route
CLOSE = 4.0                                         # the sea's outline smoothed: pockets between routes, or between routes and the coast, narrower than 8 rooms filled
LAND_R = 1.1                                        # land reaches this far round a coastline room or trail that lies off the land


def _chains(G, P):
    """lines between junctions; each room inside a line given twice, so the template's curve runs straight from room to room"""
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
        out.append((ch, line))
    return out


def _wave(line):
    """the line through its rooms (each point once), each stretch between two rooms a sine wave with a whole number of waves: flat at the rooms"""
    pts = [line[0]] + [q for a, q in zip(line, line[1:]) if math.dist(a, q) > 1e-6]
    out = [[round(pts[0][0], 3), round(pts[0][1], 3)]]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        L = math.hypot(bx - ax, by - ay); n = max(1, round(L / WAVE_LEN)); m = max(4, int(L / 0.06))
        nx, ny = -(by - ay) / L, (bx - ax) / L
        for i in range(1, m + 1):
            t = i / m; o = WAVE_AMP * math.sin(2 * math.pi * n * t) * min(1, L / 0.8)
            out.append([round(ax + (bx - ax) * t + nx * o, 3), round(ay + (by - ay) * t + ny * o, 3)])
    return out


def apply(town, wild, pos):
    S = json.load(open(os.path.join(LEG, 'dd_layout_az.json'))); E = json.load(open(os.path.join(LEG, 'dd_editor_edges_az.json')))
    O = json.load(open(os.path.join(LEG, 'dd_layout_final.json'))); OP = {v: (x, y) for v, x, y in zip(O['ids'], O['xs'], O['ys'])}
    R = {r['id']: r for r in E['rooms']}
    P = {v: (x, y) for v, x, y in zip(S['ids'], S['xs'], S['ys'])}; H = set(S['hidden'])
    AZ = {v for v, r in R.items() if r['grp'] == 'az'}
    assert not AZ & H and all(str(v) not in pos for v in AZ)
    # ---- rooms ----
    moved = {v: (OP[v], P[v]) for v in OP if v in P and R[v]['grp'] != 'az' and math.dist(OP[v], P[v]) > 0.01}
    assert set(moved) == {6294, 6332, 6334, 20290}, sorted(moved)
    for v in AZ | set(moved): pos[str(v)] = [P[v][0], P[v][1]]
    t = wild['fwtracks'][TRACK]
    assert math.dist(t[0], P[6293]) < .01 and math.dist(t[-1], P[6310]) < .01 and len(t) == 14
    wild['fwtracks'][TRACK] = [list(P[6293]), list(P[6293])] + [q for v in TRACK_ROOMS[:-1] for q in ([list(P[v]), list(P[v])])][2:] + [list(P[6310])]
    # ---- exits: land trails and water routes ----
    wet = lambda v: R[v]['terrain'] in WET
    G = defaultdict(set); ud = 0
    for a, b, k in E['edges']:
        if not ({a, b} & AZ) or {a, b} & H: continue
        if k == 'ud': ud += 1; continue
        G[a].add(b); G[b].add(a)
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
            if not R[v]['void'] and wet(v): return True
            if R[v]['void'] and any(wet(x) for x in ends(v, o)): return True
        return False
    GL, GW = defaultdict(set), defaultdict(set)
    for a in G:
        for b in G[a]:
            (GW if wetedge(a, b) else GL)[a].add(b)
    trails = [l for _, l in _chains(GL, P)]; water = [l for _, l in _chains(GW, P)]
    wild['fwtracks'] = list(wild['fwtracks']) + trails
    wild['seawaves'] = list(wild.get('seawaves') or []) + [_wave(l) for l in water]
    # ---- land under the coastline rooms and trails that lie off it ----
    geo = wild['geo']; Bx = box(*BOX)
    L0 = Polygon(geo['land'][0]).buffer(0); land_all = unary_union([Polygon(p).buffer(0) for p in geo['land'] if len(p) > 2])
    dryrooms = [v for v in AZ if not R[v]['void'] and not wet(v)]
    off = [v for v in dryrooms if not land_all.buffer(-0.3).contains(Point(P[v]))]
    addl = unary_union([Point(P[v]).buffer(LAND_R) for v in dryrooms] + [LineString(l).buffer(LAND_R) for l in trails if len(l) > 1])
    addl = addl.difference(land_all.buffer(-0.01)).intersection(Bx)
    addl = unary_union([g for g in getattr(addl, 'geoms', [addl]) if g.area > 0.02 and g.distance(land_all) < 0.05])
    land1 = unary_union([L0, addl]).buffer(0.5).buffer(-0.5)
    land1 = unary_union([L0, land1.intersection(Bx)])
    if land1.geom_type != 'Polygon': land1 = max(land1.geoms, key=lambda g: g.area)
    land_added = land1.area - L0.area
    geo['land'][0] = [[round(x, 3), round(y, 3)] for x, y in list(land1.exterior.coords)[:-1]]
    # (the land polygon's holes, if any, are other entries of geo.land: left as they are)
    S0 = Polygon(geo['sand'][SAND]).buffer(0)
    sand = unary_union([S0, land1.difference(L0).buffer(0.02)]).buffer(0.3).buffer(-0.3).intersection(land1)
    sand = unary_union([S0, sand])
    if sand.geom_type != 'Polygon': sand = max(sand.geoms, key=lambda g: g.area)
    sp = [[round(x, 3), round(y, 3)] for x, y in list(sand.exterior.coords)[:-1]]
    same = geo['sand'][SAND] == wild['ddsand']['poly']
    geo['sand'][SAND] = sp
    if same: wild['ddsand']['poly'] = [list(q) for q in sp]
    # ---- the sea ----
    solid = unary_union([land_all, land1])
    W = Polygon(geo['water'][SEA]).buffer(0)
    wetrooms = [v for v in AZ if not R[v]['void'] and wet(v)]
    reach = unary_union([Point(P[v]).buffer(SEA_R) for v in wetrooms] + [LineString(l).buffer(SEA_R) for l in water if len(l) > 1])
    add = unary_union([reach, solid.intersection(Bx)]).buffer(CLOSE).buffer(-CLOSE).intersection(Bx).difference(solid.buffer(0.15))
    sea = unary_union([W, add]).buffer(0.4).buffer(-0.4).difference(solid.buffer(0.05))
    if sea.geom_type != 'Polygon': sea = max(sea.geoms, key=lambda g: g.area)
    holes = [round(Polygon(h).area, 2) for h in sea.interiors]
    sea = Polygon(sea.exterior).difference(solid.buffer(0.05))
    if sea.geom_type != 'Polygon': sea = max(sea.geoms, key=lambda g: g.area)
    sea = sea.simplify(0.04)
    old_area = W.area
    geo['water'][SEA] = [[round(x, 3), round(y, 3)] for x, y in list(sea.exterior.coords)[:-1]]
    b = wild['bounds']
    wild['bounds'] = [b[0], b[1], max(b[2], math.ceil(sea.bounds[2] + 0.5)), max(b[3], math.ceil(sea.bounds[3] + 0.5))]
    # ---- checks ----
    wetg = sea.buffer(0.01)
    dry = [v for v in wetrooms if not wetg.contains(Point(P[v]))]
    notland = [v for v in dryrooms if not land1.buffer(0.01).contains(Point(P[v]))]
    trail_wet = round(sum(LineString(l).intersection(sea).length for l in trails if len(l) > 1), 2)
    water_land = round(sum(LineString(l).intersection(solid.buffer(-0.05)).length for l in water if len(l) > 1), 2)
    near = sorted((round(math.dist(P[a], P[b]), 2), a, b) for a in AZ for b in P if b != a and b not in H and b not in G[a] and math.dist(P[a], P[b]) < 0.8)
    spr = {k: sum(1 for q in wild.get(k) or [] if add.contains(Point(q[:2]))) for k in ('trees', 'tufts', 'boulders', 'crags', 'hills', 'peaks', 'brush', 'reeds', 'wheattufts', 'thorns')}
    return {'rooms placed (new; moved)': (len(AZ), {v: (moved[v][0], moved[v][1]) for v in sorted(moved)}),
            'trails added (lines, exits)': (len(trails), sum(len(GL[v]) for v in GL) // 2),
            'water routes added (lines, exits; up/down not drawn)': (len(water), sum(len(GW[v]) for v in GW) // 2, ud),
            'coastline rooms off the land before': sorted(off), 'land added': round(land_added, 1),
            'sea area (was, now)': (round(old_area, 1), round(sea.area, 1)), 'box': BOX, 'bounds': wild['bounds'],
            'water rooms not in the sea': dry, 'coastline rooms not on land': notland,
            'trail length in the sea': trail_wet, 'water route length over land': water_land,
            'rooms closer than 0.8 (not joined)': near[:10], 'sprites inside the added sea': {k: n for k, n in spr.items() if n},
            'holes in the sea (filled: areas)': holes}
