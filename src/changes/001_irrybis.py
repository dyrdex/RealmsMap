"""Owner, Oct 23: room 16240 'Before the Swan-ship' (The Island of Irrybis) and the Island of Irrybis.
  - 16240 squeezed in west-south-west of 4400 'Dark Cliffs' on the very edge of the Northern Plains' coast; the terrain is not changed.
    4400 d 16240 down a big cliff: a stairway (`descents`, as 5639 d 11745), sprites cleared along it;
  - just west of 16240, off the coast, a small forested island (a land piece of its own + a hole in the sea, Woods trees, own Random);
  - the place's marker moved from 4400 to 16240 (its route's last step, d; owner, Oct 23); its label pinned west of the marker, under
    the island (template LBL/PINNED)."""
import math, random
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union

TOP, BOTTOM = 4400, 16240
SPOT = (-52.2, -197.8)                          # 16240: 0.39 inside the coast line, 2.95 from 4400 (west-south-west)
CLEAR = 0.3                                     # sprites cleared this close to the stairway (as 001 of 2.12)
STEP0, STEP1 = 0.34, 0.2                        # steps apart: at the top, at the bottom (as 001 of 2.12)
HALF0, HALF1 = 0.24, 0.13                       # steps' half width: at the top, at the bottom
SPRITES = ('trees', 'tufts', 'hills', 'thorns', 'brush', 'boulders', 'crags', 'reeds', 'wheattufts')
ISLE_C, ISLE_R = (-55.5, -198.1), (1.55, 1.05)  # the island's centre and half sizes (x, y) before the wobble
TREE_STEP = 0.48


def _steps(a, b):
    L = math.dist(a, b); ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L; nx, ny = -uy, ux
    out = []; s = 0.6
    while s < L - 0.45:
        t = s / L; h = HALF0 + (HALF1 - HALF0) * t; x, y = a[0] + ux * s, a[1] + uy * s
        out.append([[round(x - nx * h, 3), round(y - ny * h, 3)], [round(x + nx * h, 3), round(y + ny * h, 3)]])
        s += STEP0 + (STEP1 - STEP0) * t
    return out


def apply(town, wild, pos):
    rng = random.Random(16240)
    a = [round(c, 2) for c in pos[str(TOP)][:2]]; b = [round(c, 2) for c in SPOT]
    pos[str(BOTTOM)] = list(b)
    G = wild['geo']
    land = unary_union([Polygon(p).buffer(0) for p in G['land']])
    coast = land.boundary
    # ---- the way down ----
    wild['descents'] = list(wild.get('descents') or []) + [{'pts': [a, b], 'steps': _steps(a, b)}]
    band = LineString([a, b]).buffer(CLEAR)
    gone = {}
    for k in SPRITES:
        L = wild.get(k) or []; keep = [q for q in L if not band.contains(Point(q[:2]))]
        if len(keep) != len(L): gone[k] = len(L) - len(keep); wild[k] = keep
    # ---- the marker: the route's last step (d) ends on 16240 ----
    pl = next(p for p in wild['places'] if p['name'] == 'The Island of Irrybis')
    assert pl['path'][-1] == a and pl['route'].endswith(';d'), pl['path'][-1]
    pl['path'] = list(pl['path']) + [list(b)]
    if pl.get('segs'): pl['segs'] = [list(g) for g in pl['segs'][:-1]] + [list(pl['segs'][-1]) + [list(b)]]
    # ---- the island: an irregular oval, rounded ----
    ph = [rng.uniform(0, 2 * math.pi) for _ in range(3)]
    pts = []
    for i in range(72):
        t = 2 * math.pi * i / 72
        w = 1 + 0.12 * math.sin(2 * t + ph[0]) + 0.08 * math.sin(3 * t + ph[1]) + 0.05 * math.sin(5 * t + ph[2])
        pts.append((ISLE_C[0] + ISLE_R[0] * w * math.cos(t), ISLE_C[1] + ISLE_R[1] * w * math.sin(t)))
    isle = Polygon(pts).buffer(0.3).buffer(-0.3)
    assert not isle.intersects(land.buffer(0.8)), 'island too close to the coast'
    poly = [[round(x, 3), round(y, 3)] for x, y in list(isle.exterior.coords)[:-1]]
    G['land'] = list(G['land']) + [poly]
    G['water'] = list(G['water']) + [poly]          # (evenodd: a hole in the sea, so the land shows; its outline is the shore line)
    # ---- its forest: a loose jittered grid of Woods trees ----
    inner = isle.buffer(-0.22); trees = []
    x0, y0, x1, y1 = isle.bounds; y = y0
    while y <= y1:
        x = x0 + rng.uniform(0, TREE_STEP)
        while x <= x1:
            jx, jy = x + rng.uniform(-.18, .18), y + rng.uniform(-.14, .14)
            if inner.contains(Point(jx, jy)) and inner.contains(Point(jx, jy - 0.3)) and rng.random() < 0.9:
                trees.append([round(jx, 3), round(jy, 3), round(rng.uniform(0.8, 1.0), 2), 'w', rng.randrange(3)])
            x += TREE_STEP
        y += TREE_STEP * 0.8
    wild['trees'] = list(wild['trees']) + trees
    return {'16240 at': b, 'from 4400': round(math.dist(a, b), 2), 'inside the coast by': round(coast.distance(Point(b)), 2),
            'steps': len(wild['descents'][-1]['steps']), 'sprites cleared': gone,
            'island (area, box)': (round(isle.area, 2), [round(c, 2) for c in isle.bounds]),
            'island to coast / to 16240': (round(isle.distance(land), 2), round(isle.distance(Point(b)), 2)), 'island trees': len(trees)}
