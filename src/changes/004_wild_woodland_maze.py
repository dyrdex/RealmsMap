"""The Wild Woodland (Knights of the Round: 14072-14076, a maze; owner, Oct 23): a Forgotten Woods maze blob (`fwmazes`, the Woods' own style,
under the trails) over its rooms, reaching a little east of them for its small label (two lines, size FS; widths measured in the browser
with the map's Alegreya 600 italic: 'The Wild' 3.375, 'Woodland' 3.943 per unit size)."""
import math
from shapely.geometry import Point, LineString, Polygon, box
from shapely.ops import unary_union

ROOMS = [14072, 14073, 14074, 14075, 14076]
FS = 0.34
LX, LY = -54.6, -46.75                              # the label's centre: just east of the rooms
TEXT_W = 3.943 * FS                                 # its wider line
PAD_ROOM, PAD_TEXT = 0.42, 0.22


def _parity(rings):
    S = Polygon()
    for p in rings:
        if len(p) > 2: S = S.symmetric_difference(Polygon(p).buffer(0))
    return S


def apply(town, wild, pos):
    pts = [tuple(pos[str(v)][:2]) for v in ROOMS]
    th = 2 * FS * 1.1
    lab = box(LX - TEXT_W / 2, LY - th / 2, LX + TEXT_W / 2, LY + th / 2)
    blob = unary_union([Point(q).buffer(PAD_ROOM, 12) for q in pts] + [lab.buffer(PAD_TEXT, 6)]).buffer(0.35, 8).buffer(-0.35, 8).simplify(0.03)
    ring = list(blob.exterior.coords)[:-1]
    cx, cy = blob.centroid.x, blob.centroid.y
    ring = [[round(cx + (x - cx) * (1 + 0.035 * math.sin(4 * math.atan2(y - cy, x - cx) + 0.7)), 3),
             round(cy + (y - cy) * (1 + 0.05 * math.sin(3 * math.atan2(y - cy, x - cx) + 2.1)), 3)] for x, y in ring]
    P = Polygon(ring)
    wild['fwmazes'] = list(wild['fwmazes']) + [{'name': 'The Wild Woodland', 'cx': round(cx, 3), 'cy': round(cy, 3), 'poly': ring,
                                                'lx': LX, 'ly': LY, 'fs': FS, 'lines': ['The Wild', 'Woodland']}]
    land = _parity(wild['geo']['land'])
    entry = P.contains(Point(pos['14071'][:2]))
    others = sorted((round(P.exterior.distance(Point(q[:2])), 2), int(v)) for v, q in pos.items()
                    if int(v) not in ROOMS and P.buffer(0.3).contains(Point(q[:2])))
    return {'blob (x range, y range, area)': ((round(P.bounds[0], 2), round(P.bounds[2], 2)), (round(P.bounds[1], 2), round(P.bounds[3], 2)), round(P.area, 2)),
            'its rooms inside': sum(P.contains(Point(q)) for q in pts), 'label inside (margin)': (P.contains(lab), round(P.exterior.distance(lab), 2)),
            'blob over the sea': round(P.difference(land).area, 3), 'other rooms within 0.3 of it': others, '14071 (the way in) inside': entry,
            'trail 11744-11745/11743 (x -53) from it': round(P.distance(LineString([(-53, -51), (-53, -42)])), 2)}
