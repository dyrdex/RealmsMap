"""Owner, Oct 19: the Northern Plains' groves over the 'Tall Trees' and 'The Fringe of Trees' rooms (4 little groups of round trees running
28 rooms north to south) replaced by one grove of tall green trees in a circle round the central Tall Trees room (4575), reaching south
to the Valley of the Elves marker and as far north: semi-dense in the middle, sparser outward. The trade road through it stays clear
(no tree drawn over it), as do the Valley of the Elves marker and its name; the brush inside the circle is cleared."""
import math, random

LABEL = (-9.28, -.62, -.68, .68)                                 # the Valley of the Elves name's box beside its marker on the site (anchor end, west of it)


def apply(town, wild, pos):
    # the grove follows its rooms: centred on 4575 wherever it is, reaching to the Valley of the Elves marker wherever that is
    C = tuple(pos['4575'])
    VALLEY = tuple(next(p for p in wild['places'] if p['name'] == 'Valley of the Elves')['path'][-1][:2])
    LB = (VALLEY[0] + LABEL[0], VALLEY[1] + LABEL[1], VALLEY[0] + LABEL[2], VALLEY[1] + LABEL[3])
    R = math.dist(C, VALLEY)
    n0 = len(wild['gfx']); wild['gfx'] = [g for g in wild['gfx'] if g['k'] != 'grove']; groves = n0 - len(wild['gfx'])
    road = [q[:2] for L in wild['etrtracks'] for a, b in zip(L, L[1:]) for t in (0, .25, .5, .75) for q in [(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)]
            if math.dist(q, C) < R + 3]
    def clear(x, y, h):                                          # the tree's drawing (and a margin) off the road, the marker and its name
        w = h * .36 / 2 + .15
        box = (x - w, y - h - .1, x + w, y + .3)
        if any(box[0] <= q[0] <= box[2] and box[1] <= q[1] <= box[3] for q in road): return False
        if math.dist((x, y), VALLEY) < .9 or (box[0] <= VALLEY[0] + .5 and box[2] >= VALLEY[0] - .5 and box[1] <= VALLEY[1] + .5 and box[3] >= VALLEY[1] - .5): return False
        return not (box[0] <= LB[2] and box[2] >= LB[0] and box[1] <= LB[3] and box[3] >= LB[1])
    rng = random.Random(4575); spots = []
    for _ in range(8000):                                        # an even spread of spots at least .7 apart over the circle...
        a = rng.uniform(0, 2 * math.pi); r = R * math.sqrt(rng.random()); x, y = C[0] + r * math.cos(a), C[1] + r * math.sin(a)
        if all(math.dist((x, y), s_) >= .7 for s_ in spots): spots.append((x, y))
    trees = []
    for x, y in sorted(spots, key=lambda q: (q[1], q[0])):       # ...thinned outward: most kept in the middle, a few at the edge
        f = math.dist((x, y), C) / R; keep = .8 * (1 - f ** 1.3) + .04
        h = rng.uniform(1.55, 2.25) - .3 * f; v = rng.randrange(3)
        if rng.random() > keep or not clear(x, y, h): continue
        trees.append([round(x, 3), round(y, 3), round(h, 2), v])
    wild['talltrees'] = list(wild.get('talltrees') or []) + trees
    nb = len(wild['brush']); wild['brush'] = [q for q in wild['brush'] if math.dist(q[:2], C) > R]
    rings = [sum(1 for t in trees if lo <= math.dist(t[:2], C) < hi) for lo, hi in ((0, R / 3), (R / 3, 2 * R / 3), (2 * R / 3, R + .01))]
    return dict(centre=[round(C[0], 2), round(C[1], 2)], radius=round(R, 2), old_groves_removed=groves, tall_trees=len(trees), by_ring_inner_middle_outer=rings, brush_cleared=nb - len(wild['brush']))
