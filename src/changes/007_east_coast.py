# Otherland's east coast (owner, Oct 23): the bay east of Morte's Peak filled in, the coast smooth there (snow, as the land round it); and the
# sea along the east coast, like the other coasts': up to SEA_W off the land inside EBOX, round-ended, joined to the sea already there,
# drawn as `seafill` + `seashore`. (Its ice: 008.)
import math, random
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union

BAY = box(64, 187, 82, 206)                     # the bay and the two small dents beside it
CLOSE_R = 5.0                                   # the coast closed this round there
EBOX = box(56, 180, 96, 242)                    # the east coast's sea (from the north coast's sea round to the south shore's)
SEA_W, SEA_CLOSE = 6.0, 6.0


def apply(town, wild, pos):
    geo = wild['geo']; rr = random.Random(23232)
    rd = lambda g: [[round(x, 3), round(y, 3)] for x, y in list(g.exterior.coords)[:-1]]
    snowp = [Polygon(p).buffer(0) for p in geo['snow'] if len(p) > 2]
    main = max(snowp, key=lambda g: g.area)
    key = lambda p: (round(Polygon(p).area, 1), tuple(round(c, 1) for c in Polygon(p).bounds))
    mk = key(rd(main))
    # ---- the bay: the coast closed round over it ----
    closed = main.buffer(CLOSE_R).buffer(-CLOSE_R)
    add = closed.difference(main).intersection(BAY)
    add = unary_union([g for g in getattr(add, 'geoms', [add]) if g.area > 0.05])
    nmain = unary_union([main, add.buffer(0.02)]).buffer(0)
    nmain = Polygon(nmain.exterior) if nmain.geom_type == 'Polygon' else Polygon(max(nmain.geoms, key=lambda g: g.area).exterior)
    nr = rd(nmain)
    for k in ('snow', 'land'):
        geo[k] = [nr if len(p) > 2 and key(p) == mk else p for p in geo[k]]
    o = wild['olsnow']; o['poly'] = [nr if len(p) > 2 and key(p) == mk else p for p in o['poly']]
    swapped = (sum(1 for p in geo['snow'] if p is nr), sum(1 for p in geo['land'] if p is nr), sum(1 for p in o['poly'] if p is nr))
    nd = round(len(o['drifts']) / main.area * add.area)                         # its snow drifts, as thick as the rest of the snow's
    inner = add.buffer(-0.5); x0, y0, x1, y1 = add.bounds; dr = []
    for _ in range(2000):
        if len(dr) >= nd or inner.is_empty: break
        x, y = rr.uniform(x0, x1), rr.uniform(y0, y1)
        if inner.contains(Point(x, y)) and all(math.dist((x, y), d[:2]) > 2.0 for d in o['drifts'] + dr):
            dr.append([round(x, 3), round(y, 3), round(rr.uniform(0.7, 1.0), 2), round(rr.uniform(-0.2, 0.2), 3)])
    o['drifts'] = list(o['drifts']) + dr
    # ---- the east sea ----
    land = unary_union([Polygon(p).buffer(0) for p in geo['land'] if len(p) > 2])
    W = unary_union([Polygon(p).buffer(0) for p in geo['water'] if len(p) > 2])
    SF = unary_union([Polygon(p).buffer(0) for p in geo['seafill'] if len(p) > 2])
    old = unary_union([W, SF])
    reach = unary_union([nmain.intersection(EBOX).buffer(SEA_W), old.intersection(EBOX.buffer(SEA_W))])
    region = reach.buffer(SEA_CLOSE).buffer(-SEA_CLOSE)
    fill = region.difference(land.buffer(-0.03)).difference(old)
    fill = unary_union([g for g in getattr(fill, 'geoms', [fill]) if g.area > 0.05 and g.distance(nmain) < 0.1])
    fills = [g for g in getattr(fill, 'geoms', [fill]) if g.area > 0.05]
    geo['seafill'] = list(geo['seafill']) + [rd(g) for g in fills] + [[[round(x, 3), round(y, 3)] for x, y in list(h.coords)[:-1]] for g in fills for h in g.interiors]
    total = unary_union([old] + fills)
    shore = total.boundary.difference(W.boundary.buffer(0.03)).difference(SF.boundary.buffer(0.03)).intersection(nmain.buffer(0.1))
    shore = [l for l in getattr(shore, 'geoms', [shore]) if l.geom_type == 'LineString' and l.length > 0.2]
    wild['seashore'] = list(wild['seashore']) + [[[round(x, 3), round(y, 3)] for x, y in l.simplify(0.02).coords] for l in shore]
    b = wild['bounds']; fb = unary_union(fills).bounds
    wild['bounds'] = [min(b[0], math.floor(fb[0] - 0.5)), b[1], max(b[2], math.ceil(fb[2] + 0.5)), max(b[3], math.ceil(fb[3] + 0.5))]
    sea_now = total.difference(nmain)
    east = nmain.exterior.intersection(EBOX)
    bare = east.difference(sea_now.buffer(0.3))
    return {'east coast (bay + dents filled: pieces, area; rooms in it; snow/land/texture rings swapped; drifts added) ; east sea (pieces, area, its width, '
            'on land, east coast without sea, map bounds)':
            ((len(getattr(add, 'geoms', [add])), round(add.area, 1), [k for k, q in pos.items() if add.contains(Point(q))], swapped, len(dr)),
             (len(fills), round(fill.area, 1), round(fill.bounds[2] - nmain.bounds[2], 1), round(fill.intersection(land.buffer(-0.05)).area, 3), round(bare.length, 2), wild['bounds']))}
