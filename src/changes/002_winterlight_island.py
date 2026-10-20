"""Owner, Oct 20: Winterlight Island. Room 9842 is its north-east tip: the island starts narrow there and widens back to the south-west into the
open sea between the paths, with an irregular, natural shore (owner: not a perfect oval, not following the paths). As large as it can be while
keeping CLEAR from every path. Snow covered, a few little shacks in the north-east, a snow-covered forest in the south-west, drawn in the map's
old style (muted snow, ink-line shacks, flat dark firs with a touch of snow; template SNOWISLE). No label (owner, Oct 20)."""
import math, random
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union

TIP = 9842
BOX = (15.0, 138.0, 34.0, 150.0)                   # (the space between the routes round it)
CLEAR = 0.9                                         # from any path's centre line or room (owner: not so close to the paths)
N_SHACKS, TREE_STEP = 3, 0.6


def apply(town, wild, pos):
    tip = tuple(pos[str(TIP)][:2]); rng = random.Random(9842)
    lines = list(wild['seaways']) + list(wild.get('seawaysfaint') or []) + [c['pts'] for c in wild.get('seacurrents') or []] + \
        [c['head'] for c in wild.get('seacurrents') or []] + list(wild['fwtracks'])
    near = box(*BOX).buffer(3)
    L = [LineString([q[:2] for q in l]) for l in lines if len(l) > 1]
    L = [g for g in L if g.intersects(near)]
    into_tip = [g for g in L if g.distance(Point(tip)) < 0.05]                          # (the path from 9841 ends at the tip)
    others = [g for g in L if g not in into_tip]
    blocked = unary_union([g.buffer(CLEAR) for g in others] + [g.difference(Point(tip).buffer(1.2)).buffer(CLEAR) for g in into_tip] +
                          [Point(p[:2]).buffer(CLEAR) for k, p in pos.items() if int(k) != TIP and near.contains(Point(p[:2]))])
    water = unary_union([Polygon(p).buffer(0) for p in wild['geo']['water']])
    allowed = box(*BOX).intersection(water).difference(blocked).union(Point(tip).buffer(0.3)).buffer(0)

    # ---- the shape: a teardrop from the tip, narrow there, widest three-quarters of the way back, a rounded south-west end; each shore wobbles on its
    # own and the long axis bends a little, so it looks natural. Fitted (direction, length, width) as the largest that stays inside `allowed`.
    ph = [rng.uniform(0, 2 * math.pi) for _ in range(8)]
    def wob(t, s):
        o = 4 * s
        return 1 + 0.2 * math.sin(2 * math.pi * 1.6 * t + ph[o]) + 0.12 * math.sin(2 * math.pi * 3.7 * t + ph[o + 1]) + 0.07 * math.sin(2 * math.pi * 7.3 * t + ph[o + 2])
    def shape(phi, Ln, k):
        ux, uy = -math.cos(phi), -math.sin(phi); nx_, ny_ = -uy, ux                      # (u: from the tip towards the south-west end)
        W = Ln * k; n = 70; left = []; right = []
        for i in range(n + 1):
            t = i / n
            f = (t ** 1.3) * ((1 - t) ** 0.45) / (0.743 ** 1.3 * 0.257 ** 0.45)          # 0 at both ends, a narrow neck at the tip, 1 at t = 0.743
            bend = 0.07 * Ln * math.sin(math.pi * t) * math.sin(ph[3] + 1.3)
            cx, cy = tip[0] + ux * Ln * t + nx_ * bend, tip[1] + uy * Ln * t + ny_ * bend
            left.append((cx + nx_ * W * f * wob(t, 0), cy + ny_ * W * f * wob(t, 0)))
            right.append((cx - nx_ * W * f * wob(t, 1), cy - ny_ * W * f * wob(t, 1)))
        g = Polygon(left + right[::-1]).buffer(0)
        return g.buffer(0.18).buffer(-0.18)                                              # (rounded off a little)
    best = None
    for phi_d in range(-80, -9, 4):
        for k in (0.26, 0.3, 0.34, 0.38, 0.42):
            lo, hi = 1.0, 14.0
            for _ in range(16):
                m = (lo + hi) / 2
                if allowed.contains(shape(math.radians(phi_d), m, k)): lo = m
                else: hi = m
            a = shape(math.radians(phi_d), lo, k).area
            if best is None or a > best[0]: best = (a, phi_d, lo, k)
    _, phi_d, Ln, K = best
    isle = shape(math.radians(phi_d), Ln, K)
    if isle.geom_type != 'Polygon': isle = max(isle.geoms, key=lambda g: g.area)
    poly = [[round(x, 3), round(y, 3)] for x, y in list(isle.exterior.coords)[:-1]]
    ux, uy = -math.cos(math.radians(phi_d)), -math.sin(math.radians(phi_d))
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
    return {'island (area, box)': (round(isle.area, 1), [round(b, 2) for b in isle.bounds]),
            'shape (long axis direction, length, widest / length)': (phi_d, round(Ln, 2), K),
            'width at 0.15 / 0.4 / 0.65 / 0.9 of the way from the tip': [round(isle.intersection(cut(t)).length, 2) for t in (0.15, 0.4, 0.65, 0.9)],
            'closest path (centre lines; the path into the tip left out)': gaps[0][0], 'shacks': len(shacks), 'snowy firs': len(trees)}
