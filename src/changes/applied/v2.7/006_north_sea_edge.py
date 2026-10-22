# The sea north of 6173 (owner, Oct 22: "a weird break in the terrain ... the edge of the sea in the north going straight down"): the Northern
# Plains' sea (geo.water, drawn with a shore line on every edge) came down as a strip to x 83.1 and stopped there in a straight cut, a shore line
# out at sea, with bare background east of it between it and the Azure Sea. Inside BOX only: the sea's outer edge rounded off across that notch
# (closing by CLOSE_R, never onto land) and the water's straight cuts (x 83.1; y 153.6) with their shore lines covered (seafill is drawn over them).
import math
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

BOX = box(76, 146, 106, 192)                         # (gotcha 1: never fill open water without a bounding box)
CLOSE_R = 14.0                                       # the notch is ~18 wide: rounded right across it


def _eo(rings):
    u = Polygon()
    for r in rings:
        if len(r) > 2: u = u.symmetric_difference(Polygon(r).buffer(0))
    return u


def apply(town, wild, pos):
    g = wild['geo']
    land = _eo(g['land']); water = _eo(g['water'])
    near = [i for i, r in enumerate(g['seafill']) if len(r) > 2 and Polygon(r).buffer(0).intersects(BOX.buffer(1))]
    sf = _eo([g['seafill'][i] for i in near])
    sea = unary_union([water, sf]).intersection(BOX)
    closed = sea.buffer(CLOSE_R, 32).buffer(-CLOSE_R, 32).intersection(BOX)
    shore = water.boundary.intersection(closed.buffer(-0.2)).buffer(0.09).difference(land.buffer(0.15))   # the water's shore lines now out at sea: covered
    add = unary_union([closed.difference(sea), shore]).difference(land.buffer(0.05)).intersection(BOX)
    new = unary_union([sf, add]).buffer(0)
    polys = [q for q in getattr(new, 'geoms', [new]) if q.geom_type == 'Polygon' and q.area > 0.01]
    rd = lambda c: [[round(x, 3), round(y, 3)] for x, y in list(c.coords)[:-1]]
    rings = [rd(q.exterior) for q in polys] + [rd(h) for q in polys for h in q.interiors]
    g['seafill'] = [r for i, r in enumerate(g['seafill']) if i not in near] + rings
    # nothing else drawn in the new sea: drifts/plants/ice there would be on water
    gone = [q for q in getattr(add, 'geoms', [add]) if q.area > 0]
    A = unary_union(gone)
    o = wild['olsnow']; nd = len(o['drifts']); o['drifts'] = [d for d in o['drifts'] if not A.buffer(0.3).contains(Polygon([(d[0], d[1]), (d[0] + 1e-3, d[1]), (d[0], d[1] + 1e-3)]))]
    return {'north sea edge (sea added, its pieces; seafill rings replaced, now; on land after)': (round(A.area, 1), len(gone), len(near), len(rings),
            round(unary_union([_eo(g['seafill']), water]).intersection(land.buffer(-0.08)).intersection(BOX).area, 3)),
            'drifts dropped in the new sea': nd - len(o['drifts'])}
