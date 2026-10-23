"""Owner's Wastelands save of Oct 23 (01:00Z; 18041, 18039, 18042, 18043 placed, 19 sea rooms moved, some 5 rooms east): the Sea of Sorrows'
water is grown round its rooms (applied/v2.2/001, SEA_R), so its west edge pulled back with them, leaving 32.7 square rooms of bare background
(x 15-20, y 131.6-144) that was sea. Kept as sea: that piece (`legacy/sos_keep_water_oct23.json`) is merged into the water ring it touches, so no
shore line shows at the seam; never over land."""
import json, os
from shapely.geometry import Polygon
from shapely.ops import unary_union

LEG = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'legacy')


def apply(town, wild, pos):
    K = json.load(open(os.path.join(LEG, 'sos_keep_water_oct23.json')))
    keep = Polygon(K['poly'], K['holes'])
    geo = wild['geo']
    land = unary_union([Polygon(p).buffer(0) for p in geo['land'] if len(p) > 2])
    keep = keep.difference(land)
    touch = [i for i, p in enumerate(geo['water']) if len(p) > 2 and Polygon(p).buffer(0).buffer(0.01).intersects(keep)]
    assert len(touch) == 1, touch
    i = touch[0]; merged = unary_union([Polygon(geo['water'][i]).buffer(0), keep.buffer(0.005).difference(land)])   # (0.005: closes the seam)
    merged = max(getattr(merged, 'geoms', [merged]), key=lambda g: g.area)
    rd = lambda cs: [[round(x, 3), round(y, 3)] for x, y in list(cs)[:-1]]
    old = Polygon(geo['water'][i]).buffer(0).area
    geo['water'][i] = rd(merged.exterior.coords)
    geo['water'] += [rd(h.coords) for h in merged.interiors]                           # (evenodd: holes as their own rings)
    return {'sea kept (area added to the ring, its holes)': (round(merged.area - old, 2), len(merged.interiors))}
