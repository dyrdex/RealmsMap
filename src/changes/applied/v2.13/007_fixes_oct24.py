"""Owner, Oct 24:
  - the Ashen Forest beach's sea: where 2.10/001 joined its new sea to the old, two water rings overlap round the beach's south-east corner
    (and one at its north end): read even-odd they cancel, leaving small holes that are neither land nor sea, and their outlines are drawn
    as shore lines out in the open sea. The rings there are redone as one shape, the holes filled with sea (SEA_BOX);
  - the Forest of Tears' big name moved LABEL_DY south, off the Treetops and Canopy marker;
  - The Forgotten Beach (5665-5668, 5680-5683): its sand extends from the rooms west to the sea (the land between them and the coast,
    from 5668 to 5683; not the separate spit further west), joined into the beach's own sand shape; forest tints clipped, trees and tufts on it
    removed. Its north edge (owner, Oct 24): wavy, and along the shore the sand thins out northwards (TAIL) with flecks of sand past it, no
    straight east-west line; the whole beach has a sand texture (`fwbeach`, template FWBEACH: fine grain, a few pebbles, wash lines along the
    shore)."""
import math, random
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union

SEA_BOX = (52.0, -34.0, 80.0, 19.0)                 # the Ashen beach and its sea
LABEL_DY = 1.0
BEACH = [5668, 5667, 5666, 5665, 5680, 5681, 5682, 5683]   # The Forgotten Beach, south to north
TAIL, N_FLECKS = 2.4, 140                           # the beach thins out along the shore over TAIL rooms north of its rooms; sand flecks past its edge
BEACH_BOX = (-66.0, -76.0, -48.0, -62.0)
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
    Lnow = _parity(g['land']).difference(_parity(g['water']))
    rng = random.Random(5683); y0 = east[-1][1]
    ph = [rng.uniform(0, 2 * math.pi) for _ in range(4)]
    wav = lambda x: 0.3 * math.sin(1.7 * x + ph[0]) + 0.18 * math.sin(3.9 * x + ph[1]) + 0.1 * math.sin(7.3 * x + ph[2])
    xe = east[-1][0]; edge = [(xe - k * 0.25, y0 + wav(xe - k * 0.25) - 0.2) for k in range(int((xe + 80) / 0.25) + 1)]   # (a wavy north edge, owner Oct 24: not a straight line)
    zone = Polygon(east[:-1] + [(xe, y0)] + edge + [(-80.0, east[0][1])]).buffer(0)
    coast_ln = Lnow.boundary; tail = []
    for k in range(int(coast_ln.length / 0.15)):                          # (and along the shore it thins out northwards over TAIL)
        q = coast_ln.interpolate(k * 0.15)
        if y0 - TAIL < q.y < y0 + 0.5 and q.x < xe and q.x > -66:
            t = (q.y - (y0 - TAIL)) / TAIL; r = 1.5 * max(0.0, min(1.0, t)) ** 1.3 * (1 + 0.25 * math.sin(5.1 * q.y + ph[3]))
            if r > 0.08: tail.append(q.buffer(r, 12))
    zone = unary_union([zone] + tail)
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
    # ---- its texture (template FWBEACH): the whole beach's sand, grain and wash lines along the shore; sand flecks thinning out past its north edge
    Sall = _parity(g['sand']).intersection(box(*BEACH_BOX)); Sall = unary_union([q for q in getattr(Sall, 'geoms', [Sall]) if q.intersects(sand)])
    sea = box(*BEACH_BOX).difference(Lnow)
    wash = []
    for d in (0.22, 0.48):
        ln = sea.buffer(d).boundary.intersection(Sall.buffer(-0.05))
        for q in getattr(ln, 'geoms', [ln]):
            if q.geom_type == 'LineString' and q.length > 0.4: wash.append([[round(x, 3), round(y, 3)] for x, y in q.simplify(0.02).coords])
    trails = unary_union([LineString([q[:2] for q in l]).buffer(0.25) for l in wild['fwtracks'] if len(l) > 1 and LineString([q[:2] for q in l]).intersects(box(*BEACH_BOX))])
    spots = []; tries = 0
    while len(spots) < N_FLECKS and tries < 20000:
        tries += 1; x = rng.uniform(-62, xe + 0.6); y = rng.uniform(y0 - TAIL - 0.6, y0 + 0.4)
        p = Point(x, y)
        if Sall.contains(p) or not Lnow.contains(p) or trails.contains(p): continue
        dd = Sall.distance(p)
        if dd > 0.9 or rng.random() > (1 - dd / 0.9) ** 1.5: continue
        spots.append([round(x, 3), round(y, 3), round(rng.uniform(0.05, 0.16) * (1 - dd / 1.1), 3)])
    wild['fwbeach'] = {'poly': _rings(Sall.simplify(0.01)), 'wash': wash, 'spots': spots}
    coast = Lnow.boundary
    out['Forgotten Beach texture (sand area, wash lines, flecks past the edge)'] = (round(Sall.area, 1), len(wash), len(spots))
    out['Forgotten Beach: sand added (area; rings touched), west edge to the sea, tints clipped, sprites removed'] = (
        round(_parity(g['sand']).area - s0, 2), ns, round(coast.distance(Point(sand.bounds[0], (sand.bounds[1] + sand.bounds[3]) / 2)), 2), tints, gone)
    return out
