"""Owner, Oct 20: the large boulders on 6403 and 6395 nudged south so each sits centred in the clearing (smrpatch) its room is part of."""
from shapely.geometry import Polygon, Point

ROOMS = [6403, 6395]


def apply(town, wild, pos):
    rep = {}
    for v in ROOMS:
        q = tuple(pos[str(v)][:2])
        g = next(g for g in wild['gfx'] if g.get('k') == 'bigboulder' and abs(g['x'] - q[0]) < 0.01 and abs(g['y'] - q[1]) < 0.01)
        P = min((Polygon([a[:2] for a in p]).buffer(0) for p in wild['smrpatch'] if len(p) > 2), key=lambda P: P.distance(Point(q[0], q[1] + 1)))
        c = P.centroid; old = (g['x'], g['y'])
        g['x'], g['y'] = round(c.x, 2), round(c.y, 2)
        rep[v] = dict(was=old, now=(g['x'], g['y']), moved_south=round(g['y'] - old[1], 2), clearing=[round(b, 2) for b in P.bounds])
    return rep
