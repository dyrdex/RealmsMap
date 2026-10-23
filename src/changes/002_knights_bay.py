"""A bay in the west coast by the Knights of the Round (owner, Oct 23): the sea rounds in from the north, passes just south-east of the Royal Jetty
of Camelot 21075 (the jetty stands in the water), comes in close to Between a Rock and a Hard Place 11745 (a coastal room, on land), turns south a
little and goes gently back out west to the old coast. Kept small enough to stay clear of the long Woods trail from the Forest of Tears
(fwtracks[384]: not touched, stays on land).
  - the new coast: a Catmull-Rom curve through CP (its first two and last two points on the old coast, so it leaves and rejoins it smoothly);
  - land inside it (only inside BOX) becomes sea: geo.land and the ground tints lose it, geo.water gains it (rings redone, even-odd);
  - trees, tufts and other sprites in the new water (and SPRITE_M inside its shore) removed."""
import math
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union

BOX = (-75.0, -56.0, -50.0, -32.0)                  # (x0, y0, x1, y1): land turned to sea only inside this box
CP = [(-63.36, -54), (-64.06, -52),                 # the old coast
      (-64.3, -50.6), (-63.2, -48.6), (-61.0, -46.9), (-59.25, -45.95),     # in from the north, just south-east of 21075
      (-57.3, -44.9), (-55.3, -43.6), (-53.75, -42.35), (-53.45, -41.55),   # close by 11745
      (-53.7, -40.6), (-54.8, -39.8), (-57.5, -39.0), (-61, -38.2), (-65, -37.3), (-68.6, -36.4),   # south a little, then gently back west
      (-70.37, -36), (-71.28, -34)]                 # the old coast
JETTY, COASTAL, PATHWAY = 21075, 11745, 384
SPRITE_M = 0.15
SPRITES = ('trees', 'tufts', 'hills', 'thorns', 'brush', 'boulders', 'crags', 'reeds', 'wheattufts', 'peaks', 'talltrees')


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
    """the rings touching band, read even-odd, changed by fn, written back; the other rings untouched (applied/v2.10/001)"""
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
    g = wild['geo']; Lold = _parity(g['land'])
    C = _catmull(CP); coast = LineString(C)
    west = Polygon([(BOX[0] - 7, C[0][1])] + C + [(BOX[0] - 7, C[-1][1])]).buffer(0)
    add = west.intersection(Lold).intersection(box(*BOX))
    add = unary_union([q for q in getattr(add, 'geoms', [add]) if q.area > 0.02])
    band = add.buffer(0.01)
    pieces0 = len(getattr(Lold, 'geoms', [Lold]))
    g['land'], nl = _edit(g['land'], band, lambda T: T.difference(add))
    g['water'], nw = _edit(g['water'], band, lambda T: T.union(add))
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
    # ---- checks ----
    Lnew = _parity(g['land']); W = _parity(g['water'])
    near = sorted((round(coast.distance(Point(q[:2])), 2), int(v)) for v, q in pos.items() if coast.distance(Point(q[:2])) < 1.2)
    path = LineString(wild['fwtracks'][PATHWAY])
    trails_wet = [(i, round(LineString(l).intersection(add).length, 2)) for i, l in enumerate(wild['fwtracks']) if len(l) > 1 and LineString(l).intersects(add)]
    rooms_wet = [int(v) for v, q in pos.items() if add.contains(Point(q[:2]))]
    return {'land turned to sea (area; rings touched land/water)': (round(add.area, 1), (nl, nw)), 'land pieces before/after': (pieces0, len(getattr(Lnew, 'geoms', [Lnew]))),
            'land/sea overlap inside BOX after': round(Lnew.intersection(W).intersection(box(*BOX)).area, 3), 'tints clipped (area)': tints, 'sprites removed': gone,
            'jetty 21075 (in the sea, from the coast)': (W.contains(Point(pos[str(JETTY)][:2])), round(coast.distance(Point(pos[str(JETTY)][:2])), 2)),
            '11745 (on land, from the coast)': (Lnew.contains(Point(pos[str(COASTAL)][:2])), round(coast.distance(Point(pos[str(COASTAL)][:2])), 2)),
            'rooms within 1.2 of the new coast': near, 'rooms now in the sea': rooms_wet, 'trails crossing the new sea (length)': trails_wet,
            'the Forest of Tears trail: from the coast, wet length': (round(path.distance(coast), 2), round(path.intersection(add).length, 2))}
