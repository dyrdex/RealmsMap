# Tirebaen's Gorge and the Fissure (owner, Oct 23): rocks, debris and texture on the gorge floor, so it reads as the bottom of a rocky gorge:
# snow-dusted boulders (more of them at the foot of the walls), loose scree and gravel, a few cracks; all kept clear of the trail on it
# (template OLGORGE, under the trails).
import math, random
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union

ROCKS_PER, GRAVEL_PER, CRACKS_PER = 0.8, 2.2, 0.12          # per square room of floor
CLEAR_ROCK, CLEAR_GRAVEL = 0.34, 0.24                          # kept this far from the trail's centre line


def apply(town, wild, pos):
    G = wild['olgorge']; rr = random.Random(23230)
    floor = unary_union([Polygon(p).buffer(0) for p in G['floor'] if len(p) > 2])
    inner = floor.buffer(-0.08)
    tl = unary_union([LineString(l) for l in wild['oltracks'] + wild.get('oltunnels', []) if len(l) > 1 and LineString(l).intersects(floor.buffer(0.5))])
    x0, y0, x1, y1 = floor.bounds
    def spot(clear):
        for _ in range(200):
            p = Point(rr.uniform(x0, x1), rr.uniform(y0, y1))
            if inner.contains(p) and tl.distance(p) >= clear: return p
    wall = floor.boundary
    rocks = []
    for _ in range(int(floor.area * ROCKS_PER) * 3):
        if len(rocks) >= floor.area * ROCKS_PER: break
        p = spot(CLEAR_ROCK)
        if p is None: continue
        d = wall.distance(p)
        if d > 0.7 and rr.random() < 0.55: continue                 # (fewer in the middle: they gather at the foot of the walls)
        s = rr.uniform(0.1, 0.22) if d > 0.5 else (rr.uniform(0.3, 0.4) if rr.random() < 0.12 else rr.uniform(0.12, 0.28))   # (a few big boulders by the walls)
        if tl.distance(p) < CLEAR_ROCK + s or any(math.dist((p.x, p.y), r[:2]) < 0.06 + r[2] + s for r in rocks): continue
        n = rr.randint(5, 7); a0 = rr.uniform(0, 6.3)
        poly = [[round(p.x + s * rr.uniform(.7, 1.1) * math.cos(a0 + 2 * math.pi * i / n), 3), round(p.y + s * .8 * rr.uniform(.7, 1.1) * math.sin(a0 + 2 * math.pi * i / n), 3)] for i in range(n)]
        if not inner.contains(Polygon(poly)): continue
        rocks.append([round(p.x, 3), round(p.y, 3), round(s, 3), poly])
    gravel = []
    for _ in range(int(floor.area * GRAVEL_PER)):
        p = spot(CLEAR_GRAVEL)
        if p is not None: gravel.append([round(p.x, 3), round(p.y, 3), round(rr.uniform(0.018, 0.045), 3), rr.randint(0, 1)])
    cracks = []
    for _ in range(int(floor.area * CRACKS_PER)):
        p = spot(CLEAR_GRAVEL)
        if p is None: continue
        a = rr.uniform(0, math.pi); L = rr.uniform(0.25, 0.6); pts = [(p.x, p.y)]
        for k in range(3):
            a += rr.uniform(-.5, .5); pts.append((pts[-1][0] + L / 3 * math.cos(a), pts[-1][1] + L / 3 * math.sin(a)))
        c = LineString(pts)
        if inner.contains(c) and tl.distance(c) >= CLEAR_GRAVEL: cracks.append([[round(x, 3), round(y, 3)] for x, y in pts])
    G['rocks'] = [r[3] for r in rocks]; G['gravel'] = gravel; G['cracks'] = cracks
    return {'gorge floor (area; rocks, gravel, cracks; nearest rock / gravel to the trail)':
            (round(floor.area, 1), len(rocks), len(gravel), len(cracks),
             round(min((tl.distance(Polygon(r[3])) for r in rocks), default=0), 2), round(min((tl.distance(Point(g[:2])) for g in gravel), default=0), 2))}
