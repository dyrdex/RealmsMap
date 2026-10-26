"""Owner, Oct 25: room 8727 (A dark bend in the forest, Thalos; 8724 n 8727) added to the map, its path from 8724 drawn.
  - placed one room north of A Wind Torn Beach 8724 (its spacing to 8813 west of it); a straight Woods-style trail 8724 - 8727 (fwtracks);
    sprites under the trail and the room cleared (0.3, as 5796 in 2.13)."""
import math
from shapely.geometry import LineString, Point
from shapely.ops import unary_union

ROOM, FROM = 8727, 8724
AT = (0.0, -1.0)                                     # one room north
CLEAR = 0.3
SPRITES = ('trees', 'tufts', 'hills', 'thorns', 'brush', 'boulders', 'crags', 'reeds', 'wheattufts')


def apply(town, wild, pos):
    R = lambda v: tuple(pos[str(v)][:2]); out = {}
    assert str(ROOM) not in pos
    fw = wild['fwtracks']
    a = R(FROM); p = [round(a[0] + AT[0], 2), round(a[1] + AT[1], 2)]; pos[str(ROOM)] = list(p)
    others = unary_union([LineString([q[:2] for q in l]) for l in fw if len(l) > 1])
    fw.append([[round(a[0], 3), round(a[1], 3)], p])
    band = unary_union([LineString([a, p]).buffer(CLEAR), Point(p).buffer(0.35)]); gone = {}
    for k in SPRITES:
        Lk = wild.get(k) or []; keep = [q for q in Lk if not band.contains(Point(q[:2]))]
        if len(keep) != len(Lk): gone[k] = len(Lk) - len(keep); wild[k] = keep
    near = min(math.dist(p, q) for v, q in pos.items() if v != str(ROOM) and len(q) >= 2)
    out['8727 at; from the nearest other trail; nearest room; sprites cleared'] = (p, round(others.distance(Point(p)), 2), round(near, 2), gone)
    return out
