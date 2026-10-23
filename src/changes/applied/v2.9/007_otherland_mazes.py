"""Otherland's mazes (owner, Oct 23):
  - A Tunnel in the Snow (the icy maze over the paths, south-east Otherland) labelled "Tunnel in the Snow Maze" on top of it, at its centre,
    as Over the Cliff Maze's label (3 lines, size 0.55);
  - Over the Cliff Maze: its north, east (the coast) and south sides kept; its west side, a straight edge till now, bulges out to the
    north-west: an irregular, roughly circular arc (height BULGE at the middle, a slow wobble of WOB on it, own random.Random), off the snow."""
import math, random
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import unary_union

BULGE, WOB = 5.0, 0.7


def apply(town, wild, pos):
    mz = wild['fwmazes']
    tn = [m for m in mz if m.get('style') == 'ice' and m.get('nolabel') and m.get('top')]
    assert len(tn) == 1
    t = tn[0]; T = Polygon(t['poly'])
    c = T.centroid if T.buffer(-1.2).contains(T.centroid) else T.representative_point()
    t.update(name='Tunnel in the Snow Maze', lines=['Tunnel in', 'the Snow', 'Maze'], fs=0.55, cx=round(c.x, 2), cy=round(c.y, 2))
    del t['nolabel']
    # ---- Over the Cliff Maze's west side ----
    m = next(m for m in mz if m['name'] == 'Over the Cliff Maze')
    M = Polygon(m['poly'])
    snow = unary_union([Polygon(p).buffer(0) for p in wild['geo']['snow'] if len(p) > 2])
    a, b = pos['14428'], pos['683']                                     # its two rooms: the strip runs from one to the other
    L = math.dist(a, b); tx, ty = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    nx, ny = -ty, tx
    if snow.contains(Point(a[0] + (b[0] - a[0]) / 2 + nx * 4, a[1] + (b[1] - a[1]) / 2 + ny * 4)): nx, ny = -nx, -ny   # out to sea
    cs = list(M.exterior.coords)
    u = [(q[0] - a[0]) * tx + (q[1] - a[1]) * ty for q in cs]; v = [(q[0] - a[0]) * nx + (q[1] - a[1]) * ny for q in cs]
    u0, u1 = min(u), max(u)
    # the present west edge: for each step along the strip, how far out it reaches
    n = 80; edge = []
    for i in range(n + 1):
        uu = u0 + (u1 - u0) * i / n
        vs = [vv for q, uq, vv in zip(cs, u, v) if abs(uq - uu) <= (u1 - u0) / n]
        edge.append(max(vs) if vs else 0)
    base = max(edge[n // 5:n - n // 5])                                 # the flat side's line (its outermost reach in the middle part)
    rg = random.Random(231023); p1, p2 = rg.uniform(0, 2 * math.pi), rg.uniform(0, 2 * math.pi)
    arc = []
    for i in range(n + 1):
        s = i / n; uu = u0 + (u1 - u0) * s
        h = base + BULGE * math.sin(math.pi * s) ** 0.9 + WOB * math.sin(math.pi * s) * (0.65 * math.sin(2 * math.pi * 2.3 * s + p1) + 0.35 * math.sin(2 * math.pi * 4.1 * s + p2))
        arc.append((a[0] + tx * uu + nx * h, a[1] + ty * uu + ny * h))
    inner = [(a[0] + tx * (u0 + (u1 - u0) * i / n) + nx * (base - 3), a[1] + ty * (u0 + (u1 - u0) * i / n) + ny * (base - 3)) for i in (n, 0)]
    cap = Polygon(arc + inner).buffer(0)
    new = unary_union([M, cap]).buffer(0.8).buffer(-0.8)                # (joins rounded where the bulge meets the north and south ends)
    new = new.difference(snow)
    new = max(getattr(new, 'geoms', [new]), key=lambda g: g.area)
    old_area = M.area
    m['poly'] = [[round(x, 3), round(y, 3)] for x, y in new.exterior.coords]
    tr = [l for k in ('oltracks', 'fwtracks') for l in wild.get(k) or [] if len(l) > 1]
    newpart = new.difference(M.buffer(0.01))
    return {'Tunnel in the Snow label (spot)': (t['cx'], t['cy']),
            'Over the Cliff Maze (area was -> now, reach out from the old west side, on snow, rooms newly inside, trail length newly inside)':
            (round(old_area, 1), round(new.area, 1), round(max(Point(q).distance(M) for q in new.exterior.coords), 2),
             round(new.intersection(snow).area, 3), [r for r, q in pos.items() if newpart.contains(Point(q[:2]))],
             round(sum(LineString(l).intersection(newpart).length for l in tr), 2))}
