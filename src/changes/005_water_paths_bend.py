"""The standard water path (owner, Oct 23): every water path but type C (`olharborways`) gets the slight imperfect bend first drawn on the Desert
of Despair east coast's primary path (Otherland's trail warp, maplib.warpline): all type B routes (`seawaysfaint`, changes/002's path included,
straight till now) and the Sea of Sorrows' one-way currents (`seacurrents`: their wave and arrowhead bent alike). One field for the whole map,
so routes meeting at a room still meet. Not water paths, untouched: `seadash` (the small dashed links), rivers and streams. New water paths
that are not type C: draw them with maplib.warpline.
Paths meeting a type B route end exactly on its line (owner, Oct 19): the ends of land trails, type C routes and dashed links that met one
are moved onto the bent line, the shift fading out over the last BLEND rooms (no kink)."""
import math
from shapely.geometry import LineString, Point
from shapely.ops import unary_union, nearest_points
from maplib import warp, warpline

BLEND = 0.6


def apply(town, wild, pos):
    F = wild['seawaysfaint']
    n0 = sum(len(l) for l in F)
    wild['seawaysfaint'] = [warpline(l) if len(l) > 1 else l for l in F]
    for c in wild.get('seacurrents') or []:
        c['pts'] = [[round(v, 3) for v in warp(*q[:2])] for q in c['pts']]
        c['head'] = [[round(v, 3) for v in warp(*q[:2])] for q in c['head']]
    Bo = unary_union([LineString([q[:2] for q in l]) for l in F if len(l) > 1])
    Bn = unary_union([LineString([q[:2] for q in l]) for l in wild['seawaysfaint'] if len(l) > 1])
    moved = {}
    for k in ('fwtracks', 'olharborways', 'seadash'):
        for l in wild.get(k) or []:
            if len(l) < 2: continue
            for end in (0, -1):
                q = Point(l[end][:2])
                if Bo.distance(q) > 0.01 or Bn.distance(q) < 1e-3: continue
                t = nearest_points(Bn, q)[0]; dx, dy = t.x - q.x, t.y - q.y
                idx = range(len(l)) if end == 0 else range(len(l) - 1, -1, -1)
                run = 0.0; prev = None
                for i in idx:
                    if prev is not None: run += math.dist(l[i][:2], l[prev][:2])
                    if run >= BLEND: break
                    f = 1 - run / BLEND; l[i] = [round(l[i][0] + dx * f, 3), round(l[i][1] + dy * f, 3)] + list(l[i][2:]); prev = i
                moved[k] = moved.get(k, 0) + 1
    d = max(math.dist(q[:2], warp(*q[:2])) for l in F for q in l)
    return {'type B routes bent (lines, points before, after); currents bent; largest shift': (len(F), n0, sum(len(l) for l in wild['seawaysfaint']),
            len(wild.get('seacurrents') or []), round(d, 3)), 'ends moved onto the bent routes': moved}
