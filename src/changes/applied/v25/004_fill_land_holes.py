"""Owner, Oct 20: two holes in the map where no terrain was drawn. Cause: land is drawn as one path with fill-rule evenodd, and three small land
polygons (geo.land 1, 2, 4) lie inside the big one (0), so they cancel it and show the bare background. They're removed (the big polygon already
covers them):
  - land 1, by the trail from Miden'nir to the Ashen Forest (x 12.5-17.7, y 9-18.1): now the plain dark-green land of Miden'nir round it;
  - land 2, north of the Wastelands where the Southern Mountains, the Wastelands and the Desert of Despair meet (x 14.9-53, y 61-89): the owner's
    split: the Wastelands' own ground (its wheat polygon, extended north: no separate piece) in the south part, the Southern Mountains' ground (plain land) in the north part, divided where the Wastelands'
    wheat edge meets the hole on its west and the desert's sand on its east;
  - land 4 (x -2.9 to -1.4, y 75-78.5), under the Wastelands' wheat: the same fault, small (land under it again).
Each new piece of ground gets the sprites of the ground beside it, at the same density (own random.Random)."""
import math, random
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union

DROP = [1, 2, 4]
_K = [(14.0, 67.9), (22.0, 68.4), (30.0, 69.3), (38.0, 68.8), (46.2, 69.6), (54.0, 70.0)]        # the Wastelands / Southern Mountains line across hole 2
_ky = lambda x: next(a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0]) for a, b in zip(_K, _K[1:]) if a[0] <= x <= b[0])
SPLIT = [(x, round(_ky(x) + 0.7 * math.sin(x * 0.55 + 1) + 0.35 * math.sin(x * 1.3 + 2), 3)) for x in [14.0 + 0.5 * i for i in range(81)]]   # (a natural, wavy edge)
BAND = 6.0                                                                                       # the ground beside a new piece, for its sprite density
SPRITES = ('trees', 'tufts', 'boulders', 'crags', 'hills', 'peaks', 'brush', 'wheattufts', 'reeds', 'thorns')
CLEAR = 0.45                                                                                     # sprites keep this far from paths and rooms


def apply(town, wild, pos):
    G = wild['geo']; mk = lambda p: Polygon([q[:2] for q in p]).buffer(0)
    big = mk(G['land'][0]); holes = {i: mk(G['land'][i]) for i in DROP}
    assert all(big.contains(h.buffer(-0.01)) for h in holes.values()), 'a dropped land piece is not inside the big one'
    rng = random.Random(4004)
    # ---- hole 2: Wastelands wheat in the south part ----
    h2 = holes[2]; sl = LineString(SPLIT)
    south = Polygon(SPLIT + [(SPLIT[-1][0], 95), (SPLIT[0][0], 95)])
    wl = h2.intersection(south).buffer(0)
    old_wheat = unary_union([mk(p) for p in G['wheat'] if len(p) > 2])
    wl_new = wl.difference(old_wheat)
    G['land'] = [p for i, p in enumerate(G['land']) if i not in DROP]
    ring = lambda g: [[round(x, 3), round(y, 3)] for x, y in list(g.exterior.coords)[:-1]]
    # the Wastelands' own ground raised north over it (owner, Oct 20: extend the native terrain, not a separate piece, so there's no seam):
    # merged into the wheat polygon it borders most
    j = max(range(len(G['wheat'])), key=lambda k: mk(G['wheat'][k]).buffer(0.2).intersection(wl_new).area)
    merged = unary_union([mk(G['wheat'][j]), wl.buffer(0.02)]).buffer(0.05).buffer(-0.05)
    assert merged.geom_type == 'Polygon', merged.geom_type
    gaps = [round(Polygon(h).area, 3) for h in merged.interiors]                    # (slivers between the old edge and the hole's: closed)
    assert all(a < 0.5 for a in gaps), gaps
    merged = Polygon(merged.exterior)
    added = [round(merged.area - mk(G['wheat'][j]).area, 1), 'into wheat %d' % j, 'slivers closed: %s' % gaps]
    G['wheat'][j] = ring(merged)
    # ---- sprites, as on the ground beside each new piece ----
    lines = [LineString([q[:2] for q in l]) for k in ('fwtracks', 'swtracks', 'dirtroads', 'etrtracks', 'seaways', 'streams') for l in (wild.get(k) or [])
             if isinstance(l, list) and len(l) > 1 and isinstance(l[0], (list, tuple))]
    sm = h2.difference(south)
    pieces = [('Miden\'nir (hole 1)', holes[1], None), ('Southern Mountains (hole 2 north)', sm, 'land'), ('Wastelands (hole 2 south)', wl, 'wheat')]
    wheat_all = unary_union([mk(p) for p in G['wheat'] if len(p) > 2])
    rep = {}
    for name, area, kind in pieces:
        if area.is_empty: continue
        ring_ = area.buffer(BAND).difference(unary_union([h for h in holes.values()]))
        if kind == 'wheat': ring_ = ring_.intersection(wheat_all)
        elif kind == 'land': ring_ = ring_.difference(wheat_all)
        near_lines = [l for l in lines if l.distance(area) < 1]
        busy = unary_union([l.buffer(CLEAR) for l in near_lines] + [Point(p[:2]).buffer(CLEAR) for p in pos.values() if area.buffer(1).contains(Point(p[:2]))])
        room = area.difference(busy)
        got = {}
        for k in SPRITES:
            L = wild.get(k) or []
            src = [q for q in L if ring_.contains(Point(q[:2]))]
            if not src: continue
            n = round(len(src) / ring_.area * room.area)
            new = []; tries = 0
            x0, y0, x1, y1 = room.bounds
            while len(new) < n and tries < n * 60:
                tries += 1; x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
                if not room.contains(Point(x, y)): continue
                t = list(rng.choice(src)); t[0], t[1] = round(x, 2), round(y, 2); new.append(t)
            wild[k] = list(L) + new; got[k] = len(new)
        rep[name] = dict(area=round(area.area, 1), sprites=got)
    return {'land pieces removed (bare holes)': {i: [round(b, 1) for b in holes[i].bounds] for i in DROP}, 'wheat extended (area, polygon)': added, 'filled': rep}
