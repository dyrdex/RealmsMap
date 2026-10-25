"""Owner, Oct 24 (third batch):
  - the links between the Forgotten Woods and the Lake of Tich'Pyga at the lake's north-east corner (LAKE_LINKS: 1154 - 977, 1205 - 5478,
    1208 - 5476, 1210 - 847) drawn as thin dashed lines (`smrdash`, as the Knights of the Round's) instead of dirt trails;
  - more deadly drops (down exits to The Coast's Jagged Teeth): the High-Cliff Trail 5671 - 5677 and Overlooking the Blood Sea 5631: the cliff's
    rim there in the red warning dash (as 5640 - 5495), one skull on the High-Cliff Trail's face (below Ocean View 5674, midway); Overlooking the
    Blood Sea, a single room, its rim only. The Deceptive Shoreline 5689 and Blood Sea Cliffs 5692, where no cliff is drawn: a small skull
    beside each, on its sea side;
  - A Dark Hole 5796 (owner: a deathtrap, southwest of 5795; it wasn't in the layout editor): placed one room south-west of Burrowing into
    the Hills 5795, its trail drawn, the deathtrap emblem on it (added to the Barren Peaks + Forgotten Woods editor there too)."""
import math
from shapely.geometry import LineString, Point
from shapely.ops import unary_union, nearest_points, substring

LAKE_LINKS = [(1154, 977), (1205, 5478), (1208, 5476), (1210, 847)]
DEADLY_S1, DEADLY_ONE = (5671, 5677), [5631]
SKULL_ROOM, SKULL, SKULL_OFF = 5674, 0.42, 0.72
SMALL = [(5689, 0.34), (5692, 0.34)]
HOLE, FROM = 5796, 5795
HOLE_AT = (-0.71, 0.71)                              # one room south-west
CLEAR = 0.3
SPRITES = ('trees', 'tufts', 'hills', 'thorns', 'brush', 'boulders', 'crags', 'reeds', 'wheattufts')


def _parity(rings):
    from shapely.geometry import Polygon
    A = Polygon()
    for p in rings:
        if len(p) > 2: A = A.symmetric_difference(Polygon(p).buffer(0))
    return A


def apply(town, wild, pos):
    R = lambda v: tuple(pos[str(v)][:2]); out = {}
    fw = wild['fwtracks']
    # ---- the lake links: dashed ----
    moved = []
    for a, b in LAKE_LINKS:
        k = min((i for i, l in enumerate(fw) if len(l) > 1),
                key=lambda i: min(math.dist(fw[i][0][:2], R(a)) + math.dist(fw[i][-1][:2], R(b)), math.dist(fw[i][0][:2], R(b)) + math.dist(fw[i][-1][:2], R(a))))
        l = fw[k]; d = min(math.dist(l[0][:2], R(a)) + math.dist(l[-1][:2], R(b)), math.dist(l[0][:2], R(b)) + math.dist(l[-1][:2], R(a)))
        assert d < 1.0, (a, b, d)
        moved.append((k, a, b, round(d, 2)))
    for k, *_ in sorted(moved, reverse=True):
        l = fw.pop(k); wild['smrdash'] = list(wild.get('smrdash') or []) + [[[round(q[0], 3), round(q[1], 3)] for q in l]]
    out['lake links made dashed (trail, rooms, ends off)'] = moved
    # ---- the warning rims ----
    C = wild['fwcliff'][0]
    t30 = min((LineString([q[:2] for q in l]) for l in fw if len(l) > 1),           # (the High-Cliff Trail: the trail through both ends of the stretch;
              key=lambda g: g.distance(Point(R(DEADLY_S1[0]))) + g.distance(Point(R(DEADLY_S1[1]))))   #  trails are renumbered by 009)
    assert t30.distance(Point(R(DEADLY_S1[0]))) < 0.4 and t30.distance(Point(R(DEADLY_S1[1]))) < 0.4
    s0, s1 = sorted(t30.project(Point(R(v))) for v in DEADLY_S1)
    zone = unary_union([substring(t30, s0, s1).buffer(0.7)] + [Point(R(v)).buffer(0.75) for v in DEADLY_ONE])
    rims, danger = [], list(C.get('danger') or [])
    added = 0.0
    for r in C['rim']:
        g = LineString(r)
        inn, outp = g.intersection(zone), g.difference(zone)
        for q in getattr(inn, 'geoms', [inn]):
            if q.geom_type == 'LineString' and q.length > 0.1: danger.append([[round(x, 3), round(y, 3)] for x, y in q.coords]); added += q.length
        for q in getattr(outp, 'geoms', [outp]):
            if q.geom_type == 'LineString' and q.length > 0.1: rims.append([[round(x, 3), round(y, 3)] for x, y in q.coords])
    C['rim'], C['danger'] = rims, danger
    out['warning rim added (length)'] = round(added, 2)
    # ---- skulls ----
    rimall = unary_union([LineString(r) for r in danger])
    p = Point(R(SKULL_ROOM)); q = nearest_points(t30, p)[0]; rq = nearest_points(rimall, q)[0]
    dx, dy = rq.x - q.x, rq.y - q.y; L = math.hypot(dx, dy) or 1
    skull = [round(q.x + dx / L * SKULL_OFF, 3), round(q.y + dy / L * SKULL_OFF, 3), SKULL]
    sea = _parity(wild['geo']['water']).difference(_parity(wild['geo']['land']))
    small = []
    for v, sz in SMALL:
        p = Point(R(v)); s = nearest_points(sea, p)[0]; dx, dy = s.x - p.x, s.y - p.y; L = math.hypot(dx, dy) or 1
        small.append([round(p.x + dx / L * 0.55, 3), round(p.y + dy / L * 0.55, 3), sz])
    # ---- A Dark Hole 5796 ----
    a = R(FROM); h = [round(a[0] + HOLE_AT[0], 2), round(a[1] + HOLE_AT[1], 2)]; pos[str(HOLE)] = list(h)
    fw.append([[round(a[0], 3), round(a[1], 3)], h])
    hole = [h[0], h[1], SKULL]
    wild['deathtraps'] = list(wild.get('deathtraps') or []) + [skull] + small + [hole]
    band = unary_union([LineString([a, h]).buffer(CLEAR)] + [Point(x[:2]).buffer(0.35) for x in [skull] + small + [hole]]); gone = {}
    for k in SPRITES:
        Lk = wild.get(k) or []; keep = [q for q in Lk if not band.contains(Point(q[:2]))]
        if len(keep) != len(Lk): gone[k] = len(Lk) - len(keep); wild[k] = keep
    others = unary_union([LineString([q[:2] for q in l]) for l in fw[:-1] if len(l) > 1])
    out['skulls (High-Cliff Trail face, 5689, 5692, 5796)'] = (skull, small, hole)
    out['5796 at; from the nearest other trail; sprites cleared'] = (h, round(others.distance(Point(h)), 2), gone)
    return out
