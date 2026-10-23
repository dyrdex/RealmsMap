"""Owner, Oct 20: Winterlight Island. Room 9842 is its north-east tip: the island starts narrower there (a rounded end, not a point: owner, Oct 20) and widens back to the south-west into the
open sea between the paths, with an irregular, natural shore (owner: not a perfect oval, not following the paths). As large as it can be while
keeping CLEAR from every path. Snow covered, a few little shacks in the north-east, a snow-covered forest in the south-west, drawn in the map's
old style (muted snow, ink-line shacks, flat dark firs with a touch of snow; template SNOWISLE). No label (owner, Oct 20).
Owner, Oct 22: put back (removed with Otherland, applied/v2.4/001), fitted the same way between the paths round it; irregular, smooth and rounded, winter themed.
Also kept clear of the line kinds added since (sea waves, Otherland's trails and harbor ways); the sea filler counts as water."""
import math, os, random
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union

TIP = 9842
BOX = (15.0, 138.0, 34.0, 150.0)                   # (the space between the routes round it)
CLEAR = 0.9                                         # from any path's centre line or room (owner: not so close to the paths)
N_SHACKS, TREE_STEP = 3, 0.6
OPEN, CAP = 0.75, 0.7                               # rounding radius of the outline; radius of the rounded end at 9842
FIT = (132, 1.3, 28.0, 143.5, 3.1036376953125)                                       # (direction, stretch, centre x, centre y, size) found by the fit; REFIT=1 searches again


def apply(town, wild, pos):
    tip = tuple(pos[str(TIP)][:2]); rng = random.Random(9842)
    lines = list(wild['seaways']) + list(wild.get('seawaysfaint') or []) + [c['pts'] for c in wild.get('seacurrents') or []] + \
        [c['head'] for c in wild.get('seacurrents') or []] + list(wild['fwtracks']) + \
        [l for k in ('seawaves', 'olharborways', 'oltracks', 'oltunnels') for g in wild.get(k) or [] for l in (g if g and isinstance(g[0][0], (list, tuple)) else [g])]
    near = box(*BOX).buffer(3)
    L = [LineString([q[:2] for q in l]) for l in lines if len(l) > 1]
    L = [g for g in L if g.intersects(near)]
    into_tip = [g for g in L if g.distance(Point(tip)) < 0.05]                          # (the path from 9841 ends at the tip)
    others = [g for g in L if g not in into_tip]
    blocked = unary_union([g.buffer(CLEAR) for g in others] + [g.difference(Point(tip).buffer(1.2)).buffer(CLEAR) for g in into_tip] +
                          [Point(p[:2]).buffer(CLEAR) for k, p in pos.items() if int(k) != TIP and near.contains(Point(p[:2]))])
    water = unary_union([Polygon(p).buffer(0) for p in wild['geo']['water'] + (wild['geo'].get('seafill') or [])])
    allowed = box(*BOX).intersection(water).difference(blocked).union(Point(tip).buffer(0.3)).buffer(0)

    # ---- the shape (owner, Oct 22): a smooth, irregular blob, a few gentle bulges round an oval (low harmonics only, so the shore stays round),
    # joined to a rounded end at the tip. Fitted (direction, stretch, centre, size) as the largest that stays inside the open water round the tip.
    piece = [g for g in (allowed.geoms if allowed.geom_type != 'Polygon' else [allowed]) if g.distance(Point(tip)) < 0.01][0]
    hm = [(k, a, rng.uniform(0, 2 * math.pi)) for k, a in ((2, 0.1), (3, 0.09), (4, 0.05), (5, 0.03))]
    ctip = None
    def shape(phi, e, cx, cy, sc):
        cp, sp = math.cos(phi), math.sin(phi); pts = []
        for i in range(120):
            t = 2 * math.pi * i / 120; r = sc * (1 + sum(a * math.sin(k * t + p) for k, a, p in hm))
            x, y = r * math.cos(t) * e, r * math.sin(t)
            pts.append((cx + x * cp - y * sp, cy + x * sp + y * cp))
        g = Polygon(pts).buffer(0)
        d = (cx - tip[0], cy - tip[1]); n = math.hypot(*d) or 1; c = (tip[0] + d[0] / n * CAP, tip[1] + d[1] / n * CAP)
        neck = unary_union([Point(c).buffer(CAP), g.intersection(Point(c).buffer(1.8))]).convex_hull     # a rounded end at the room
        g = unary_union([g, neck]).buffer(OPEN).buffer(-OPEN)                                            # the joint rounded off
        return g if g.geom_type == 'Polygon' else max(g.geoms, key=lambda h: h.area)
    def size(phi, e, cx, cy):
        lo, hi = 0.5, 6.0
        for _ in range(13):
            m = (lo + hi) / 2
            if allowed.contains(shape(phi, e, cx, cy, m)): lo = m
            else: hi = m
        return lo
    if FIT is None or os.environ.get('REFIT'):                                                           # (slow: ~1 min; the result is kept in FIT)
        best = None; core = piece.buffer(-1.6)
        for phi_d in range(0, 180, 12):
            for e in (1.0, 1.3, 1.6, 2.0):
                for gx in range(int(piece.bounds[0] * 2), int(piece.bounds[2] * 2) + 1):
                    for gy in range(int(piece.bounds[1] * 2), int(piece.bounds[3] * 2) + 1):
                        cx, cy = gx / 2, gy / 2
                        if not core.contains(Point(cx, cy)): continue
                        sc = size(math.radians(phi_d), e, cx, cy)
                        g = shape(math.radians(phi_d), e, cx, cy, sc)
                        if (best is None or g.area > best[0]) and g.distance(Point(tip)) < 0.05: best = (g.area, phi_d, e, cx, cy, sc)
        print('Winterlight Island fit:', best)
        fit = best[1:]
    else: fit = FIT
    phi_d, e, cx, cy, sc = fit
    isle = shape(math.radians(phi_d), e, cx, cy, sc)
    far = max(isle.exterior.coords, key=lambda q: math.dist(q, tip)); Ln = math.dist(far, tip)
    ux, uy = (far[0] - tip[0]) / Ln, (far[1] - tip[1]) / Ln
    poly = [[round(x, 3), round(y, 3)] for x, y in list(isle.exterior.coords)[:-1]]
    along = lambda x, y: ((x - tip[0]) * ux + (y - tip[1]) * uy) / Ln               # 0 at the tip, 1 at the south-west end
    inner = isle.buffer(-0.3)
    # ---- shacks: a few, where the island first widens (north-east)
    shacks = []; tries = 0
    while len(shacks) < N_SHACKS and tries < 6000:
        tries += 1; x = rng.uniform(*isle.bounds[0::2]); y = rng.uniform(*isle.bounds[1::2])
        if not 0.2 < along(x, y) < 0.45 or not inner.contains(box(x - 0.3, y - 0.35, x + 0.3, y + 0.3)): continue
        if any(math.dist((x, y), s[:2]) < 0.8 for s in shacks): continue
        shacks.append([round(x, 2), round(y, 2), round(rng.uniform(0.55, 0.68), 2), rng.choice([1, -1])])
    # ---- the snowy forest: the south-west part, a loose jittered grid of firs
    trees = []
    x0, y0, x1, y1 = isle.bounds; y = y0
    while y <= y1:
        x = x0 + rng.uniform(0, TREE_STEP)
        while x <= x1:
            jx, jy = x + rng.uniform(-.2, .2), y + rng.uniform(-.15, .15)
            if along(jx, jy) > 0.55 + rng.uniform(-.05, .05) and inner.contains(Point(jx, jy + 0.2)) and inner.contains(Point(jx, jy - 0.3)) and rng.random() < 0.85:
                trees.append([round(jx, 2), round(jy, 2), round(rng.uniform(0.4, 0.56), 2)])
            x += TREE_STEP
        y += TREE_STEP * 0.8
    trees.sort(key=lambda q: q[1])
    rip = [[[round(x, 3), round(y, 3)] for x, y in list(isle.buffer(d, join_style=1).exterior.coords)[:-1]] for d in (0.2, 0.42)]   # old-map ripple lines round the shore
    wild['snowisles'] = list(wild.get('snowisles') or []) + [{'poly': poly, 'rip': rip, 'trees': trees, 'shacks': shacks}]
    gaps = sorted((round(isle.distance(g), 2), i) for i, g in enumerate(others))
    cut = lambda t: LineString([(tip[0] + ux * Ln * t - uy * 9, tip[1] + uy * Ln * t + ux * 9), (tip[0] + ux * Ln * t + uy * 9, tip[1] + uy * Ln * t - ux * 9)])
    return {'open water between the paths (area)': round(allowed.area, 1), 'island (area, box)': (round(isle.area, 1), [round(b, 2) for b in isle.bounds]),
            'shape (direction, stretch, centre, size; tip to far end)': (phi_d, e, (cx, cy), round(sc, 3), round(Ln, 2)),
            'width at 0.15 / 0.4 / 0.65 / 0.9 of the way from the tip': [round(isle.intersection(cut(t)).length, 2) for t in (0.15, 0.4, 0.65, 0.9)],
            'closest path (centre lines; the path into the tip left out)': gaps[0][0], 'shacks': len(shacks), 'snowy firs': len(trees)}
