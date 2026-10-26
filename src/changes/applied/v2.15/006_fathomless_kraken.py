"""Owner, Oct 25:
  - 'Blood Sea - Fathomless Depths': the owner's directions (53 w, se, 13 d, n; condensed by build.py); its marker west of Hurricane Island
    (4 past its west shore, level with its centre); its line: The Blood Sea's (the drawn part of #53 w), on to The Blood Sea's marker and
    straight west to this marker (owner: the final se;#13 d;n not drawn); its name west of its marker.
  - a giant sea creature in the Blood Sea, due west of the Forgotten Woods (level with the middle of its ground, geo.fwwood's bounds; half
    way from that coast to the map's west edge): tentacles barely breaking the surface, a dark shape under the water (template KRAKEN)."""
import math
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union

ROUTE = 'w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;w;se;#13 d;n'
GAP = 4.0
KR_SCALE = 1.6                                     # the creature: about 14 rooms across (owner, Oct 25: bigger; was 1.0, 9 across)


def _parity(rings):
    A = Polygon()
    for p in rings:
        if len(p) > 2: A = A.symmetric_difference(Polygon(p).buffer(0))
    return A


def apply(town, wild, pos):
    out = {}; land = _parity(wild['geo']['land'])
    bs = next(p for p in wild['places'] if p['name'] == 'The Blood Sea'); H = wild['hurricane']; hi = Polygon(H['isle'])
    pin = [round(hi.bounds[0] - GAP, 2), round(H['c'][1], 2)]
    line = [list(q) for q in bs['path']] + [list(bs['at']), pin]
    wild['places'].append({'name': 'Blood Sea - Fathomless Depths', 'route': ROUTE, 'room': 'Fathomless Depths', 'dir': 'here', 'group': 'af',
                           'where': 'in the Blood Sea', 'note': None, 'path': line, 'segs': [line], 'at': pin, 'lbl': [-.55, .06, 'end']})
    out['Fathomless Depths marker; from Hurricane Island; line from the Blood Sea marker (length, over the island)'] = (
        pin, round(Point(pin).distance(hi), 2), (round(math.dist(bs['at'], pin), 2), round(LineString([bs['at'], pin]).intersection(hi).length, 2)))
    # ---- the sea creature ----
    U = unary_union([Polygon(p).buffer(0) for p in wild['geo']['fwwood'] if len(p) > 2]); cy = round((U.bounds[1] + U.bounds[3]) / 2, 2)
    cut = land.intersection(LineString([(wild['bounds'][0], cy), (U.bounds[2], cy)])); gs = list(cut.geoms) if hasattr(cut, 'geoms') else [cut]
    coast = min(g.bounds[0] for g in gs); cx = round((coast + wild['bounds'][0]) / 2, 2)
    wild['kraken'] = [cx, cy, KR_SCALE]
    body = Point(cx, cy).buffer(5.5 * KR_SCALE)
    sail = LineString(next(p for p in wild['places'] if p['name'] == 'Fireball Island')['sail'])
    out['creature at; coast x; clear of land, of Fireball Island\'s boat line'] = ([cx, cy], round(coast, 2), round(body.distance(land), 1), round(body.distance(sail), 1))
    return out
