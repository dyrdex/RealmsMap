# Tirebaen's Gorge (owner, Oct 22): its east wall pulled back where it met the A Tunnel in the Snow maze, so the two never touch (a gap of GAP);
# the floor keeps at least WALL of wall inside that, the hachures crossing the cut are clipped. The maze itself is unchanged.
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union

GAP, WALL = 0.35, 0.4


def apply(town, wild, pos):
    G = wild['olgorge']
    mz = next(m for m in wild['fwmazes'] if m.get('style') == 'ice' and not m['name'] and m.get('top'))
    M = Polygon(mz['poly'])
    band = unary_union([Polygon(p).buffer(0) for p in G['band'] if len(p) > 2])
    floor = unary_union([Polygon(p).buffer(0) for p in G['floor'] if len(p) > 2])
    before = (round(M.intersection(band).area, 2), round(M.distance(floor), 2))
    cut = M.buffer(GAP).buffer(0.5).buffer(-0.5)
    nb = band.difference(cut); nf = floor.difference(M.buffer(GAP + WALL).buffer(0.5).buffer(-0.5))
    ring = lambda g: [[round(x, 3), round(y, 3)] for x, y in g.coords]
    def rings(g):
        return [ring(r) for h in getattr(g, 'geoms', [g]) if h.geom_type == 'Polygon' and h.area > 0.01 for r in [h.exterior, *h.interiors]]
    G['band'] = rings(nb); G['floor'] = rings(nf)
    hk, n = [], 0
    for h in G['hach']:
        s = LineString(h)
        if not s.intersects(cut): hk.append(h); continue
        c = s.difference(cut); n += 1
        if c.geom_type == 'LineString' and c.length > 0.08: hk.append(ring(c))
    G['hach'] = hk
    return {'gorge vs the A Tunnel in the Snow maze (overlap, floor gap) before -> after; area cut from wall, floor; hachures clipped':
            (before, (round(M.intersection(nb).area, 3), round(M.distance(nb), 2), round(M.distance(nf), 2)), round(band.area - nb.area, 2), round(floor.area - nf.area, 2), n)}
