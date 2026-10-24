"""Owner, Oct 24:
  - the Ashen Forest beach's sea: where 2.10/001 joined its new sea to the old, two water rings overlap round the beach's south-east corner
    (and one at its north end): read even-odd they cancel, leaving small holes that are neither land nor sea, and their outlines are drawn
    as shore lines out in the open sea. The rings there are redone as one shape, the holes filled with sea (SEA_BOX);
  - the Forest of Tears' big name moved LABEL_DY south, off the Treetops and Canopy marker;
  - The Forgotten Beach (5665-5668, 5680-5683): its sand extends from the rooms west to the sea (the land between them and the coast,
    from 5668 to 5683; not the separate spit further west), joined into the beach's own sand shape; forest tints clipped, trees and tufts on it
    removed."""
import math
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union

SEA_BOX = (52.0, -34.0, 80.0, 19.0)                 # the Ashen beach and its sea
LABEL_DY = 1.0
BEACH = [5668, 5667, 5666, 5665, 5680, 5681, 5682, 5683]   # The Forgotten Beach, south to north
BEACH_E = 0.45                                      # the sand reaches this far east of the rooms (as the beach's own strip)
SPRITES = ('trees', 'tufts', 'hills', 'thorns', 'brush', 'boulders', 'crags', 'reeds', 'wheattufts', 'talltrees')


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


def apply(town, wild, pos):
    g = wild['geo']; out = {}
    # ---- the Ashen beach's sea ----
    B = box(*SEA_BOX); L = _parity(g['land'])
    W = _parity(g['water']); holes = B.difference(L).difference(W)
    holes = unary_union([q for q in getattr(holes, 'geoms', [holes]) if q.area > 0.0005])
    def outl():                                      # water outlines out at sea (not along land)
        return round(sum(LineString(r + [r[0]]).intersection(B).difference(L.buffer(0.15)).length for r in g['water'] if len(r) > 2), 2)
    o0 = outl()
    if not holes.is_empty:
        g['water'], nw = _edit(g['water'], holes.buffer(0.05), lambda T: T.union(holes.buffer(0.02)))
    W1 = _parity(g['water'])
    out['Ashen sea: holes filled (count, area), outlines at sea before/after, gaps left'] = (
        len(getattr(holes, 'geoms', [holes])), round(holes.area, 3), (o0, outl()), round(B.difference(L).difference(W1).area, 4))
    # ---- the Forest of Tears' name ----
    y0 = wild['label']['y']; wild['label']['y'] = round(y0 + LABEL_DY, 2)
    out['Forest of Tears name y (old -> new)'] = (y0, wild['label']['y'])
    # ---- The Forgotten Beach ----
    R = lambda v: tuple(pos[str(v)][:2])
    east = [(R(5668)[0] + BEACH_E, R(5668)[1] + 0.4), (R(5666)[0], R(5666)[1] + 0.5), (R(5665)[0] + BEACH_E, R(5665)[1] + 0.5),
            (R(5680)[0] + BEACH_E, R(5680)[1]), (R(5681)[0] + BEACH_E, R(5681)[1]), (R(5682)[0] + BEACH_E, R(5682)[1]), (R(5683)[0] + BEACH_E, R(5683)[1] - 0.4)]
    zone = Polygon(east + [(-80.0, east[-1][1]), (-80.0, east[0][1])]).buffer(0)
    Lnow = _parity(g['land']).difference(_parity(g['water']))
    sand = zone.intersection(Lnow)
    sand = next(q for q in getattr(sand, 'geoms', [sand]) if q.buffer(0.01).contains(Point(R(5667))))   # (the beach's own piece, not the spit)
    sand = sand.buffer(-0.15).buffer(0.15).intersection(Lnow)
    s0 = _parity(g['sand']).area
    g['sand'], ns = _edit(g['sand'], sand.buffer(0.05), lambda T: T.union(sand))
    tints = {}
    for k in ('fill', 'fill2', 'fwwood', 'deep'):
        if k in g and any(len(r) > 2 and Polygon(r).buffer(0).intersects(sand) for r in g[k]):
            a0 = _parity(g[k]).area; g[k], _ = _edit(g[k], sand.buffer(0.01), lambda T: T.difference(sand)); tints[k] = round(a0 - _parity(g[k]).area, 2)
    zone_s = sand.buffer(0.1); gone = {}
    for k in SPRITES:
        L0 = wild.get(k) or []; keep = [q for q in L0 if not zone_s.contains(Point(q[:2]))]
        if len(keep) != len(L0): gone[k] = len(L0) - len(keep); wild[k] = keep
    coast = Lnow.boundary
    out['Forgotten Beach: sand added (area; rings touched), west edge to the sea, tints clipped, sprites removed'] = (
        round(_parity(g['sand']).area - s0, 2), ns, round(coast.distance(Point(sand.bounds[0], (sand.bounds[1] + sand.bounds[3]) / 2)), 2), tints, gone)
    return out
