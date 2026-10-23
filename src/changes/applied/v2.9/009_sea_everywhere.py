"""The sea all round (owner, Oct 23): every bit of undrawn background inside the map's frame (`bounds`) that is open to the frame becomes sea:
round the main continent, the whole gap between the Mire and Otherland, round Otherland. It is merged with the sea already drawn into one
water shape (`geo.water` rewritten as its rings, even-odd; `seafill` taken in too and kept as is over it), so no shore line shows where old
and new sea meet; the shore line runs only where the water meets land. Small background pockets shut in by land (gaps between land shapes,
not open to the frame) stay as they are. Never over land: the background is the frame minus everything in `geo`.
The drawn shore lines (`seashore`) that marked the old sea's outer edge (off Otherland's west coast) are cut away wherever they lie out in
the sea (farther than SHORE_D from land): only shore along the land is left (owner, Oct 23)."""
from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union

SHORE_D = 0.4
PAD = 0.5                                            # the sea runs this far past the frame, so its edge (stroked) never shows


def _parity(rings):
    A = Polygon()
    for p in rings:
        if len(p) > 2: A = A.symmetric_difference(Polygon(p).buffer(0))
    return A


def apply(town, wild, pos):
    g = wild['geo']; x0, y0, x1, y1 = wild['bounds']
    cover = []
    for k, rs in g.items():
        if not isinstance(rs, list) or not rs or not isinstance(rs[0], list): continue
        cover.append(_parity(rs) if k in ('land', 'water', 'seafill') else unary_union([Polygon(p).buffer(0) for p in rs if len(p) > 2]))
    B = box(x0, y0, x1, y1)
    bg = B.difference(unary_union(cover))
    edge = B.exterior.buffer(0.01)
    parts = list(getattr(bg, 'geoms', [bg]))
    open_ = [p for p in parts if p.intersects(edge)]; shut = [p for p in parts if not p.intersects(edge)]
    new = unary_union(open_)
    pad = box(x0 - PAD, y0 - PAD, x1 + PAD, y1 + PAD).difference(B)
    land = _parity(g['land'])
    water0 = _parity(g['water'])
    W = unary_union([water0, _parity(g.get('seafill') or []), new, pad.difference(land)]).buffer(0)
    rings = []
    for P in getattr(W, 'geoms', [W]):
        rings.append([[round(x, 3), round(y, 3)] for x, y in list(P.exterior.coords)[:-1]])
        rings += [[[round(x, 3), round(y, 3)] for x, y in list(h.coords)[:-1]] for h in P.interiors]
    ground = unary_union([land] + [Polygon(p).buffer(0) for k in ('snow', 'iceisle') for p in g.get(k) or [] if len(p) > 2]).buffer(SHORE_D)
    shore, cut = [], 0.0
    for l in wild.get('seashore') or []:
        if len(l) < 2: shore.append(l); continue
        L = LineString(l); keep = L.intersection(ground); cut += L.length - keep.length
        for piece in getattr(keep, 'geoms', [keep]):
            if piece.geom_type == 'LineString' and piece.length > 0.05: shore.append([[round(x, 3), round(y, 3)] for x, y in piece.coords])
    wild['seashore'] = shore
    old_n = len(g['water'])
    g['water'] = rings
    chk = _parity(rings)
    return {'sea added (area; pieces open to the frame; shut-in pockets left, their area)': (round(new.area, 1), len(open_), len(shut), round(sum(p.area for p in shut), 1)),
            'water rings was -> now; sea over land added; even-odd check (lost, gained vs intended)': (old_n, len(rings), round(new.intersection(land).area, 3),
             round(W.difference(chk).area, 3), round(chk.difference(W).area, 3)), 'shore lines: length cut away out at sea, lines now': (round(cut, 1), len(shore))}
