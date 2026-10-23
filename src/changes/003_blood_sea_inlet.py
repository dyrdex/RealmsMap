"""Owner, Oct 23: the sea brought in as far as it can go under the Woods' coast cliff:
  - just south of Between a Rock and a Hard Place 11745, Path to the Tower 13642, Driftwood Swamp 13641, Sand, Rocks and Seaweed 13640 (FOOT off
    their spots), and of Skirting the Coast 5644 / Unearthly Views 5645 (DROP: the cliff falls straight into the sea there);
  - then a narrow inlet up along 5646 and 5495 (DROP off their south-east side), tapering near Sand and Rocks 5494 into a sandy beach
    (geo.sand, a patch round the inlet's end) and nothing;
  - coming back south, the coast runs parallel to the long forest path 5491 - 1669 (fwtracks[384]) at PATH_OFF from it, round 1669, and
    parallel to the path 1669 - 1668 (fwtracks[375]'s last leg) at PATH_OFF, until short of the Grimdog Port Authority (21077 stays on land),
    where it turns up into the old west coast.
  - the new coast: a Catmull-Rom curve through CP (its first two and last two points on the old coast), as 2.12/002; the land between it and the
    old coast (only inside BOX) becomes sea; tints clipped, trees and other sprites in the new water (and SPRITE_M inside its shore) removed."""
import math
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union

BOX = (-87.0, -48.5, -36.5, -14.0)                  # (x0, y0, x1, y1): land turned to sea only inside this box
FOOT, DROP, PATH_OFF = 0.66, 0.95, 1.0
FOOT_ROOMS = [11745, 13642, 13641, 13640]             # at the cliff's foot (west to east)
TOP_ROOMS = [5644, 5645, 5646, 5495, 5494]           # on the clifftop, the sea right below (then the inlet)              # sea this far from: the rooms at the cliff's foot, the clifftop rooms, the two forest paths
SPRITE_M = 0.15
SPRITES = ('trees', 'tufts', 'hills', 'thorns', 'brush', 'boulders', 'crags', 'reeds', 'wheattufts', 'peaks', 'talltrees')
SAND_R = 1.1                                        # the beach: land within this of the inlet's last INLET_END of shore
INLET_END = 1.6
CLOSE = [(-86.0, -26.0), (-70.0, -40.0), (-62.0, -47.0)]   # (back round through the open sea, to close the shape)
KEEP_DRY = [11745, 13642, 13641, 13640, 5644, 5645, 5646, 5495, 5494, 5491, 1669, 21077, 11744, 11743]


def _parity(rings):
    A = Polygon()
    for p in rings:
        if len(p) > 2: A = A.symmetric_difference(Polygon(p).buffer(0))
    return A


def _rings(S):
    out = []
    for P in getattr(S, 'geoms', [S]):
        if P.is_empty or P.geom_type != 'Polygon': continue
        out.append([[round(x, 3), round(y, 3)] for x, y in list(P.exterior.coords)[:-1]])
        out += [[[round(x, 3), round(y, 3)] for x, y in list(h.coords)[:-1]] for h in P.interiors]
    return out


def _edit(rings, band, fn):
    touch = [i for i, r in enumerate(rings) if len(r) > 2 and Polygon(r).buffer(0).intersects(band)]
    T = _parity([rings[i] for i in touch])
    return [r for i, r in enumerate(rings) if i not in touch] + _rings(fn(T).buffer(0)), len(touch)


def _catmull(P, n=12):
    P = [P[0]] + P + [P[-1]]; out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n; t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    return out + [P[-2]]


def apply(town, wild, pos):
    R = lambda v: tuple(pos[str(v)][:2])
    S = lambda v, dx, dy: (R(v)[0] + dx, R(v)[1] + dy)
    A, B = R(5491), R(1669); C0 = tuple(wild['fwtracks'][375][-2][:2])
    def off(a, b, t, d):                            # a point t of the way a -> b, d off it on the line's north-west side
        ux, uy = (b[0] - a[0]) / math.dist(a, b), (b[1] - a[1]) / math.dist(a, b); nx, ny = uy, -ux
        if nx + ny > 0: nx, ny = -nx, -ny
        return (a[0] + (b[0] - a[0]) * t + nx * d, a[1] + (b[1] - a[1]) * t + ny * d)
    def shore(vs, d, step, cut_end=0.0):          # points d off the line through rooms vs, on its south side (shapely's left in this y-down map)
        g = LineString([R(v) for v in vs]).offset_curve(d, join_style=1)
        n = max(2, int(g.length / step)); L = g.length * (1 - cut_end / max(g.length, 1e-9))
        return [tuple(g.interpolate(L * i / n).coords[0]) for i in range(n + 1)]
    def se(a, b, v, d):                             # room v pushed d to the south-east of the line a -> b
        ux, uy = (b[0] - a[0]) / math.dist(a, b), (b[1] - a[1]) / math.dist(a, b); nx, ny = -uy, ux
        if nx + ny < 0: nx, ny = -nx, -ny
        return (R(v)[0] + nx * d, R(v)[1] + ny * d)
    CP = [(-59.25, -45.95), (-57.3, -44.9),         # the old coast (the Knights bay's north-east shore)
          (-55.2, -44.3)] + shore(FOOT_ROOMS, FOOT, 0.7) + shore(TOP_ROOMS, DROP, 0.7, cut_end=0.25) + [
          off(A, B, 0.15, PATH_OFF), off(A, B, 0.3, PATH_OFF), off(A, B, 0.5, PATH_OFF), off(A, B, 0.7, PATH_OFF), off(A, B, 0.88, PATH_OFF),
          (B[0] - 0.55, B[1] - 1.05),               # round 1669
          off(B, C0, 0.1, PATH_OFF), off(B, C0, 0.3, PATH_OFF), off(B, C0, 0.5, PATH_OFF), off(B, C0, 0.7, PATH_OFF), off(B, C0, 0.8, PATH_OFF),
          (-83.41, -20.1), (-84.93, -19.5)]         # the old coast, short of the Grimdog Port Authority
    g = wild['geo']; Lold = _parity(g['land']); W0 = _parity(g['water'])
    Cv = _catmull([list(p) for p in CP]); coast = LineString(Cv)
    shape = Polygon(Cv + CLOSE).buffer(0)
    closing = LineString([Cv[-1]] + CLOSE + [Cv[0]])
    assert closing.intersection(Lold).length < 0.05, ('the closing path crosses land', closing.intersection(Lold).length)
    add = shape.intersection(Lold).intersection(box(*BOX))
    add = unary_union([q for q in getattr(add, 'geoms', [add]) if q.area > 0.02])
    band = add.buffer(0.01)
    pieces0 = len(getattr(Lold, 'geoms', [Lold]))
    g['land'], nl = _edit(g['land'], band, lambda T: T.difference(add))
    sea = shape.intersection(box(*BOX)).difference(_parity(g['land']))
    g['water'], nw = _edit(g['water'], band, lambda T: T.union(sea))
    tints = {}
    for k, rs in g.items():
        if k in ('land', 'water') or not isinstance(rs, list) or not rs or not isinstance(rs[0], list): continue
        if any(len(r) > 2 and Polygon(r).buffer(0).intersects(add) for r in rs):
            before = _parity(rs).area; g[k], _ = _edit(rs, band, lambda T: T.difference(add)); tints[k] = round(before - _parity(g[k]).area, 2)
    wet = add.buffer(SPRITE_M); gone = {}
    for k in SPRITES:
        if k in wild:
            n0 = len(wild[k]); wild[k] = [q for q in wild[k] if not wet.contains(Point(q[0], q[1]))]
            if n0 - len(wild[k]): gone[k] = n0 - len(wild[k])
    # ---- the beach at the inlet's end: land within SAND_R of the shore's last INLET_END, off the trails ----
    Lnew = _parity(g['land'])
    i_tip = min(range(len(Cv)), key=lambda i: math.dist(Cv[i], se(R(5495), R(5494), 5494, DROP * 0.95)))
    k = i_tip; s = 0.0
    while k > 0 and s < INLET_END: s += math.dist(Cv[k], Cv[k - 1]); k -= 1
    j = i_tip; s = 0.0
    while j < len(Cv) - 1 and s < INLET_END * 0.6: s += math.dist(Cv[j], Cv[j + 1]); j += 1
    end = LineString(Cv[k:j + 1])
    trails = unary_union([LineString([q[:2] for q in l]).buffer(0.26) for l in wild['fwtracks'] if len(l) > 1 and LineString([q[:2] for q in l]).distance(end) < 3])
    sand = end.buffer(SAND_R).intersection(Lnew).difference(trails).buffer(-0.08).buffer(0.08)
    sand = unary_union([q for q in getattr(sand, 'geoms', [sand]) if q.area > 0.05])
    if not sand.is_empty:
        g['sand'] = list(g['sand']) + _rings(sand.simplify(0.02))
        n0 = len(wild['tufts']); wild['tufts'] = [q for q in wild['tufts'] if not sand.contains(Point(q[:2]))]
        n1 = len(wild['trees']); wild['trees'] = [q for q in wild['trees'] if not sand.buffer(0.1).contains(Point(q[:2]))]
        gone['tufts on the beach'] = n0 - len(wild['tufts']); gone['trees on the beach'] = n1 - len(wild['trees'])
    # ---- checks ----
    W = _parity(g['water'])
    p384 = LineString([q[:2] for q in wild['fwtracks'][384]]); p375 = LineString([q[:2] for q in wild['fwtracks'][375][-2:]])
    wetp = lambda l: round(LineString([q[:2] for q in l]).intersection(add).length, 2)
    trails_wet = [(i, wetp(l)) for i, l in enumerate(wild['fwtracks']) if len(l) > 1 and LineString([q[:2] for q in l]).intersects(add)]
    dry = {v: (Lnew.contains(Point(R(v))), round(coast.distance(Point(R(v))), 2)) for v in KEEP_DRY if str(v) in pos}
    near = sorted((round(coast.distance(Point(q[:2])), 2), int(v)) for v, q in pos.items() if coast.distance(Point(q[:2])) < 1.0)
    bx = box(*BOX)
    return {'land turned to sea (area; rings touched land/water)': (round(add.area, 1), (nl, nw)), 'land pieces before/after': (pieces0, len(getattr(Lnew, 'geoms', [Lnew]))),
            'land/sea overlap inside BOX after': round(Lnew.intersection(W).intersection(bx).area, 3),
            'gaps (neither land nor sea) inside BOX before/after': (round(bx.difference(Lold).difference(W0).area, 3), round(bx.difference(Lnew).difference(W).area, 3)),
            'tints clipped (area)': tints, 'sprites removed': gone, 'beach (area)': round(sand.area, 2),
            'coast to the 5491-1669 path, the 1669-1668 path (closest)': (round(coast.distance(p384), 2), round(coast.distance(p375), 2)),
            'rooms kept dry (on land, from the coast)': dry, 'rooms within 1.0 of the new coast': near, 'trails crossing the new sea (length)': trails_wet}
