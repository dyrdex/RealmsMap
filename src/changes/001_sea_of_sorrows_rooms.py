"""Owner's Wastelands save of Oct 20 (20:39Z, editor v3): the new Sea of Sorrows / Blood Sea rooms (grp 'ss': the owner's 47 rooms + 45 spacers)
placed where saved, and the 7 beach rooms the save moved (the beach water route follows them). Owner: all the new rooms are joined by blue water
routes ('seaways'): every flat exit between two new rooms, or between a new room and a beach room (up/down exits not drawn). Lines run through
the rooms' spots, exactly through every real room, rounding off only at spacer rooms; a line from a beach room on the coast route
ends on the coast route's line. The bay's sea is extended under the new rooms (inside BOX, never over land) and the map grows south to fit."""
import json, math, os
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__)); LEG = os.path.join(HERE, '..', 'legacy')
BOX = (4.0, 117.0, 53.0, 161.0)                     # (x0, y0, x1, y1): the sea added only inside this box
COAST = 16                                          # wild['seaways'][16]: the beach coast route (9928 ... 9934)
COAST_PTS = {15: 18070, 16: 9929, 17: 18073, 19: 9931, 20: 9932, 21: 9933, 22: 9934}   # its points that sit at a room the save moved
SEA_R = 2.6                                         # sea reaches this far round each new room and water route


def _chains(G, P, real):
    """lines between junctions; points at the rooms. The template draws a line as a curve through the midpoints of its points, so each real
    (non-spacer) room inside a line is given twice: the line passes it exactly; it rounds off only at spacer rooms."""
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
            line += [q, list(q)] if 0 < i < len(ch) - 1 and v in real else [q]
        out.append((ch, line))
    return out


def apply(town, wild, pos):
    S = json.load(open(os.path.join(LEG, 'wl3_layout_final.json'))); E = json.load(open(os.path.join(LEG, 'wl3_editor_edges.json')))
    R = {r['id']: r for r in E['rooms']}
    P = {v: (x, y) for v, x, y in zip(S['ids'], S['xs'], S['ys'])}
    assert not S['hidden']
    SS = {v for v, r in R.items() if r.get('grp') == 'ss'}; WL = {v for v, r in R.items() if r.get('grp') == 'wl'}
    assert all(str(v) not in pos for v in SS)
    # ---- rooms ----
    moved = {}
    for v in WL:
        if math.dist(P[v], pos[str(v)][:2]) > 0.01: moved[v] = (tuple(pos[str(v)][:2]), P[v])
    assert set(moved) == set(COAST_PTS.values()), sorted(moved)
    for v in SS | set(moved): pos[str(v)] = [P[v][0], P[v][1]]
    # ---- the coast route follows the moved beach rooms ----
    L = wild['seaways'][COAST]
    assert math.dist(L[0], (19, 120.5)) < .01 and math.dist(L[-1], (42.5, 124.5)) < .01
    for j, v in COAST_PTS.items():
        (ox, oy), (nx_, ny_) = moved[v]; L[j] = [round(L[j][0] + nx_ - ox, 2), round(L[j][1] + ny_ - oy, 2)]
    coast = LineString(L)
    # ---- the new water routes ----
    G = defaultdict(set); ud = 0
    for a, b, k in E['edges']:
        if not (a in SS or b in SS) or not ({a, b} <= SS | WL): continue
        if k == 'ud': ud += 1; continue
        G[a].add(b); G[b].add(a)
    new = []
    for ch, line in _chains(G, P, {v for v in SS | WL if not R[v]['void']}):
        for end, nxt in ((0, 1), (-1, -2)):                                             # a line from a beach room on the coast route ends on it
            v = ch[end]
            if v in WL and coast.distance(Point(P[v])) < 1.5:
                q = coast.interpolate(coast.project(Point(line[nxt]))) if len(line) > 2 else coast.interpolate(coast.project(Point(P[v])))
                line[end] = [round(q.x, 2), round(q.y, 2)]
        new.append(line)
    wild['seaways'] = list(wild['seaways']) + new
    # ---- the sea under them ----
    geo = wild['geo']; W = [Polygon(p) for p in geo['water']]
    bay = [i for i, g in enumerate(W) if g.bounds[0] > -5 and g.bounds[1] > 118][0]
    solid = unary_union([Polygon(p).buffer(0) for k in ('land',) for p in geo[k] if len(p) > 2])
    reach = unary_union([Point(P[v]).buffer(SEA_R) for v in SS] + [LineString(l).buffer(SEA_R) for l in new if len(l) > 1])
    add = reach.buffer(1.2).buffer(-1.2).intersection(box(*BOX)).difference(solid.buffer(0.15))
    sea = unary_union([W[bay].buffer(0), add]).buffer(0.4).buffer(-0.4).difference(solid.buffer(0.05))
    if sea.geom_type != 'Polygon': sea = max(sea.geoms, key=lambda g: g.area)
    holes = [round(Polygon(h).area, 2) for h in sea.interiors]
    sea = Polygon(sea.exterior).difference(solid.buffer(0.05)) if not any(Polygon(h).intersects(solid) for h in sea.interiors) else sea
    sea = sea.simplify(0.04)
    old_area = W[bay].area
    geo['water'][bay] = [[round(x, 3), round(y, 3)] for x, y in list(sea.exterior.coords)[:-1]]
    b = wild['bounds']; y1 = max(b[3], math.ceil(sea.bounds[3] + 0.5)); wild['bounds'] = [b[0], b[1], b[2], y1]
    # ---- checks ----
    wet = sea.buffer(0.01)
    dry = [v for v in SS if not wet.contains(Point(P[v]))]
    overland = sum(1 for l in new for a, c in zip(l, l[1:]) if LineString([a, c]).intersects(solid))
    spr = {k: sum(1 for q in wild.get(k) or [] if add.contains(Point(q[:2]))) for k in ('trees', 'tufts', 'boulders', 'crags', 'hills', 'peaks', 'brush', 'reeds', 'wheattufts', 'thorns')}
    return {'rooms placed (new; beach rooms moved)': (len(SS), {v: (moved[v][0], moved[v][1]) for v in sorted(moved)}),
            'water routes added (lines, exits; up/down not drawn)': (len(new), sum(len(G[v]) for v in G) // 2, ud),
            'bay sea area (was, now)': (round(old_area, 1), round(sea.area, 1)), 'sea box': BOX, 'bounds': wild['bounds'],
            'new rooms not in the sea': dry, 'route segments over land': overland, 'sprites inside the added sea': {k: n for k, n in spr.items() if n},
            'holes in the sea (filled: areas)': (holes, len(sea.interiors))}
