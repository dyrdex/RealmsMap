"""Owner, Oct 20: Winterlight Island. Room 9842 is its north-east tip; the island fills the sea south-west of it, as large as it can be without
touching any path (CLEAR from every route's line, current and room). Snow covered, a few little shacks in the north-east, a snow-covered forest in
the south-west (template SNOWISLE). Label "Winterlight Island" (small label, gfx 'text') on the island, between the shacks and the forest."""
import math, random
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union

TIP = 9842
BOX = (15.0, 138.0, 34.0, 150.0)                   # (the space between the routes round it)
CLEAR = 0.5                                         # from any path's centre line or room (line half-widths are 0.25 at most)
N_SHACKS, TREE_STEP = 4, 0.62


def apply(town, wild, pos):
    tip = tuple(pos[str(TIP)][:2]); rng = random.Random(9842)
    lines = list(wild['seaways']) + list(wild.get('seawaysfaint') or []) + [c['pts'] for c in wild.get('seacurrents') or []] + \
        [c['head'] for c in wild.get('seacurrents') or []] + list(wild['fwtracks'])
    near = box(*BOX).buffer(3)
    L = [LineString([q[:2] for q in l]) for l in lines if len(l) > 1]
    L = [g for g in L if g.intersects(near)]
    blocked = unary_union([g.buffer(CLEAR) for g in L] + [Point(p[:2]).buffer(CLEAR) for k, p in pos.items() if int(k) != TIP and near.contains(Point(p[:2]))])
    water = unary_union([Polygon(p).buffer(0) for p in wild['geo']['water']])
    free = box(*BOX).intersection(water).difference(blocked)
    comps = list(free.geoms) if free.geom_type != 'Polygon' else [free]
    space = min(comps, key=lambda g: g.distance(Point(tip)))
    assert space.distance(Point(tip)) < CLEAR + 0.05
    isle = space.buffer(-0.35).buffer(0.35)                                          # (rounded off)
    if isle.geom_type != 'Polygon': isle = max(isle.geoms, key=lambda g: g.area)
    # the north-east tip reaches the room: a tapering point from the island to 9842 (the path from 9841 ends there)
    c = isle.exterior.interpolate(isle.exterior.project(Point(tip)))
    horn = unary_union([Point(tip).buffer(0.08), Point(c.x, c.y).buffer(0.55)]).convex_hull
    isle = unary_union([isle, horn]).buffer(0.12).buffer(-0.12)
    # an organic shore: the outline nudged in by a little noise (never out, so it stays clear of the paths)
    ring = isle.exterior; n = max(60, int(ring.length / 0.18)); ph = [rng.uniform(0, 6.3) for _ in range(3)]
    pts = []
    for i in range(n):
        q = ring.interpolate(ring.length * i / n); s = i / n * 2 * math.pi
        d = 0.12 + 0.1 * math.sin(5 * s + ph[0]) + 0.06 * math.sin(11 * s + ph[1]) + 0.04 * math.sin(19 * s + ph[2])
        if q.distance(Point(tip)) < 0.6: d = 0.0                                          # (the tip stays on the room)
        r = ring.interpolate(ring.length * ((i / n + 0.003) % 1)); dx, dy = r.x - q.x, r.y - q.y; ll = math.hypot(dx, dy) or 1
        nx_, ny_ = -dy / ll, dx / ll
        if not isle.contains(Point(q.x + nx_ * 0.05, q.y + ny_ * 0.05)): nx_, ny_ = -nx_, -ny_          # (inward)
        pts.append((q.x + nx_ * max(0, d), q.y + ny_ * max(0, d)))
    isle = Polygon(pts).buffer(0)
    if isle.geom_type != 'Polygon': isle = max(isle.geoms, key=lambda g: g.area)
    poly = [[round(x, 3), round(y, 3)] for x, y in list(isle.exterior.coords)[:-1]]
    # the NE / SW split: along the island's long axis from the tip
    far = max(isle.exterior.coords, key=lambda q: math.dist(q, tip)); ax_, ay_ = far[0] - tip[0], far[1] - tip[1]; AL = math.hypot(ax_, ay_)
    along = lambda x, y: ((x - tip[0]) * ax_ + (y - tip[1]) * ay_) / AL / AL               # 0 at the tip, 1 at the far (south-west) end
    inner = isle.buffer(-0.35)
    # shacks: a little cluster in the north-east
    shacks = []; tries = 0
    while len(shacks) < N_SHACKS and tries < 4000:
        tries += 1; x = rng.uniform(*isle.bounds[0::2]); y = rng.uniform(*isle.bounds[1::2])
        if not 0.06 < along(x, y) < 0.26 or math.dist((x, y), tip) > 3.2 or not inner.contains(Point(x, y)): continue
        if any(math.dist((x, y), s[:2]) < 0.85 for s in shacks): continue
        shacks.append([round(x, 2), round(y, 2), round(rng.uniform(0.62, 0.78), 2), rng.choice([1, -1])])
    # the label between the shacks and the forest
    lab = None
    for t in [0.42 + d for d in (0, -0.03, 0.03, -0.06, 0.06)]:
        cx, cy = tip[0] + ax_ * t, tip[1] + ay_ * t
        tb = box(cx - 1.75, cy - 0.33, cx + 1.75, cy + 0.1)
        if isle.buffer(0.3).contains(tb) or (lab is None and isle.contains(Point(cx, cy))): lab = (round(cx, 2), round(cy + 0.12, 2), tb)
        if isle.buffer(0.3).contains(tb): break
    lx0, ly0, lx1, ly1 = lab[2].bounds; keep_off = box(lx0 - 0.25, ly0 - 0.2, lx1 + 0.25, ly1 + 0.75)   # (a fir's top stands 0.4 above its foot)
    # the snow-covered forest: the south-west part, a jittered grid of firs
    trees = []
    x0, y0, x1, y1 = isle.bounds; y = y0
    while y <= y1:
        x = x0 + (rng.uniform(0, TREE_STEP) if True else 0)
        while x <= x1:
            jx, jy = x + rng.uniform(-.2, .2), y + rng.uniform(-.15, .15)
            if along(jx, jy) > 0.54 + rng.uniform(-.05, .05) and inner.contains(Point(jx, jy + 0.25)) and not keep_off.contains(Point(jx, jy)):
                trees.append([round(jx, 2), round(jy, 2), round(rng.uniform(0.42, 0.62), 2)])
            x += TREE_STEP
        y += TREE_STEP * 0.8
    trees.sort(key=lambda q: q[1])
    wild['snowisles'] = list(wild.get('snowisles') or []) + [{'poly': poly, 'trees': trees, 'shacks': shacks}]
    wild['gfx'] = list(wild['gfx']) + [{'k': 'text', 'at': 'xy', 'x': lab[0], 'y': lab[1], 'text': 'Winterlight Island'}]
    gap = min(isle.distance(g) for g in L if g.distance(Point(tip)) > 0.6 or not g.intersects(Point(tip).buffer(0.6)))
    return {'island (area, box, tip)': (round(isle.area, 1), [round(b, 2) for b in isle.bounds], tip),
            'closest path (excluding the one ending at the tip)': round(gap, 2), 'shacks': len(shacks), 'snowy firs': len(trees),
            'label': lab[:2], 'label inside the island': isle.buffer(0.3).contains(lab[2])}
