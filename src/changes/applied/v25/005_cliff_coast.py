"""Owner, Oct 20: on the east coast north of the Coral Depths, the cliff-top path should meet the sea itself: no green land between the cliff and
the water from the north (where the coast already meets the path, y ~13) down to the small bay just north of the Coral Depths marker (y ~35.3),
where the green land runs into the cliff and stops. The new coastline runs along the cliff hachures' outer ends (+ OUT); everything east of it in
that stretch becomes sea: cut from the land, added to the sea polygon, ground tints clipped, sprites in it removed."""
import math
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union

Y0, Y1 = 12.9, 35.3                                 # the stretch: from the north end of the green strip to the bay
OUT = 0.1                                           # the coast this far beyond the hachures' outer ends
SPIT = 0.4                                          # land thinner than twice this at the bay is a spit: removed
XMAX = 84.0                                         # (east of the coast, in the open sea)


def apply(town, wild, pos):
    G = wild['geo']; mk = lambda p: Polygon([q[:2] for q in p]).buffer(0)
    H = sorted([h for h in wild['hach'] if 55 < h[0] < 67 and Y0 - 0.5 < h[1] < Y1 + 0.5], key=lambda h: h[1])
    ends = [(h[2] + OUT, h[3]) for h in H]                                             # (each hachure: x1, y1 at the path, x2, y2 out over the cliff)
    # a smooth coastline through them: a running median in x, sampled every 0.25 in y (gaps, as at the path crossing at y 18-24, interpolated)
    pts = []
    y = Y0
    while y <= Y1 + 1e-9:
        near = sorted(e for e in ends if abs(e[1] - y) < 0.9)
        if near: x = sorted(e[0] for e in near)[len(near) // 2]
        else:
            a = max((e for e in ends if e[1] < y), key=lambda e: e[1]); b = min((e for e in ends if e[1] > y), key=lambda e: e[1])
            x = a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1])
        pts.append((round(x, 3), round(y, 3))); y += 0.25
    coast = LineString(pts).simplify(0.03)
    cut = Polygon(list(coast.coords) + [(XMAX, pts[-1][1]), (XMAX, pts[0][1])]).buffer(0)
    land0 = mk(G['land'][0]); R = land0.intersection(cut)
    keep = land0.difference(R)
    if keep.geom_type != 'Polygon': keep = max(keep.geoms, key=lambda g: g.area)
    zone = box(56.5, Y1 - 1.0, 64.5, Y1 + 1.5)                                         # at the bay: a thin spit of land left between the new sea and the bay goes too
    near = keep.intersection(zone); thin = near.difference(near.buffer(-SPIT).buffer(SPIT))
    thin = unary_union([g for g in getattr(thin, 'geoms', [thin]) if g.area > 0.005 and g.distance(cut) < 0.05])
    if not thin.is_empty:
        keep = keep.difference(thin.buffer(0.01))
        if keep.geom_type != 'Polygon': keep = max(keep.geoms, key=lambda g: g.area)
    R = land0.difference(keep)                                                         # (any sliver cut off from the main land goes too)
    G['land'][0] = [[round(x, 3), round(y, 3)] for x, y in list(keep.exterior.coords)[:-1]]
    assert not keep.interiors
    # the sea: the big sea polygon next to it grows into the cut
    W = [mk(p) for p in G['water']]
    i = max(range(len(W)), key=lambda k: W[k].intersection(cut.buffer(3)).area)
    add = unary_union([cut.intersection(land0.buffer(0.3)), R.difference(cut).buffer(0.01)])        # (its west edge the smooth coastline itself, so sea and land meet cleanly)
    sea = unary_union([W[i], add]).buffer(0)
    if sea.geom_type != 'Polygon': sea = max(sea.geoms, key=lambda g: g.area)
    G['water'][i] = [[round(x, 3), round(y, 3)] for x, y in list(sea.exterior.coords)[:-1]]
    # ground tints clipped, sprites removed
    clipped = {}
    for k, L in G.items():
        if k in ('land', 'water', 'seafill'): continue
        out = []
        for p in L:
            if len(p) < 3: out.append(p); continue
            g = mk(p)
            if not g.intersects(R): out.append(p); continue
            d = g.difference(R.buffer(0.01))
            clipped[k] = clipped.get(k, 0) + 1
            for h in getattr(d, 'geoms', [d]):
                if h.area > 0.02: out.append([[round(x, 3), round(y, 3)] for x, y in list(h.exterior.coords)[:-1]])
        G[k] = out
    gone = {}
    for k in ('trees', 'tufts', 'boulders', 'crags', 'hills', 'peaks', 'brush', 'wheattufts', 'reeds', 'thorns', 'talltrees'):
        L = wild.get(k) or []; kk = [q for q in L if not R.buffer(0.15).contains(Point(q[:2]))]
        if len(kk) != len(L): gone[k] = len(L) - len(kk); wild[k] = kk
    lines_in = [k for k in ('fwtracks', 'dirtroads', 'etrtracks', 'seaways', 'streams') for l in (wild.get(k) or [])
                if isinstance(l, list) and len(l) > 1 and isinstance(l[0], (list, tuple)) and LineString([q[:2] for q in l]).intersection(R.buffer(-0.05)).length > 0.05]
    rooms_in = [k for k, p in pos.items() if R.buffer(-0.05).contains(Point(p[:2]))]
    return {'land cut to sea (area, box)': (round(R.area, 1), [round(b, 2) for b in R.bounds]), 'coast points': len(coast.coords),
            'ground tints clipped': clipped, 'sprites removed': gone, 'paths in the cut (should be none)': lines_in, 'rooms in the cut (should be none)': rooms_in}
