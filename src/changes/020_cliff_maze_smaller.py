"""Over the Cliff Maze much smaller (owner, Oct 23). It was so big because the two water paths into it ran far out to its rooms (14474 ->
14428, The Icy Cliffs 15162 -> 683). Each is cut CUT rooms after it leaves the coast (no editor change; the two maze rooms are no longer
reached by a drawn line). The maze is redrawn as a band along the same stretch of coast, about WIDTH rooms out to sea, its sea side uneven
(a slow wobble WOB, own random.Random), rounded at both ends, off the snow; the cut path ends inside it. Its label smaller to fit (FS)."""
import math, random
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union, substring, polylabel

CUT, WIDTH, WOB, FS = 1.0, 2.0, 0.45, 0.45
PATHS = [('14428', '14474'), ('683', '15162')]        # (maze room, the land room the path comes from)


def apply(town, wild, pos):
    m = next(m for m in wild['fwmazes'] if m['name'] == 'Over the Cliff Maze'); M = Polygon(m['poly'])
    snow = unary_union([Polygon(p).buffer(0) for p in wild['geo']['snow'] if len(p) > 2])
    near = lambda q, r: math.dist(q[:2], pos[r][:2]) < 0.3
    F = wild['seawaysfaint']; ends = []; cut = []
    for mr, lr in PATHS:
        i = next(i for i, l in enumerate(F) if len(l) > 1 and ((near(l[0], mr) and near(l[-1], lr)) or (near(l[0], lr) and near(l[-1], mr))))
        l = F[i] if near(F[i][0], lr) else F[i][::-1]
        L = LineString([q[:2] for q in l])
        d0 = next(L.project(Point(q[:2])) for q in l if not snow.contains(Point(q[:2])))     # where it leaves the coast
        keep = substring(L, 0, min(L.length, d0 + CUT))
        F[i] = [[round(x, 3), round(y, 3)] for x, y in keep.coords]
        ends.append(Point(F[i][-1])); cut.append((lr, mr, round(L.length, 2), round(keep.length, 2)))
    # the coast it covers: the snow's edge inside the old maze
    main = max(getattr(snow, 'geoms', [snow]), key=lambda g: g.area)
    arc = LineString(main.exterior.coords).intersection(M.buffer(0.3))
    arc = max(getattr(arc, 'geoms', [arc]), key=lambda g: g.length)
    n = max(8, int(arc.length / 0.25)); P = [arc.interpolate(i / n, normalized=True) for i in range(n + 1)]
    rg = random.Random(231024); ph = [rg.uniform(0, 2 * math.pi) for _ in range(3)]
    out = []
    for i, p in enumerate(P):
        a, b = P[max(0, i - 2)], P[min(n, i + 2)]; tx, ty = b.x - a.x, b.y - a.y; L = math.hypot(tx, ty) or 1
        nx, ny = -ty / L, tx / L
        if snow.contains(Point(p.x + nx * 0.5, p.y + ny * 0.5)): nx, ny = -nx, -ny               # out to sea
        s = i / n * arc.length
        w = WIDTH + WOB * (0.6 * math.sin(s / 2.3 + ph[0]) + 0.4 * math.sin(s / 1.1 + ph[1]))
        cap = min(1.0, s / 1.2, (arc.length - s) / 1.2); w *= math.sqrt(max(cap, 0.05))         # rounded ends
        out.append((p.x + nx * w, p.y + ny * w))
    inland = [(p.x, p.y) for p in P]
    band = Polygon(inland + out[::-1]).buffer(0)
    band = unary_union([band] + [e.buffer(0.6) for e in ends]).buffer(0.5).buffer(-0.5).difference(snow)
    band = max(getattr(band, 'geoms', [band]), key=lambda g: g.area)
    m['poly'] = [[round(x, 3), round(y, 3)] for x, y in band.exterior.coords]
    c = polylabel(band, 0.02); m.update(cx=round(c.x, 2), cy=round(c.y, 2), fs=FS)
    widths = [round(Point(out[i]).distance(P[i]), 2) for i in range(0, n + 1, max(1, n // 20))]
    return {'paths cut (from, to, length was -> now)': cut, 'cut ends inside the maze by': [round(band.exterior.distance(e), 2) for e in ends],
            'maze area was -> now; coast length; on snow': (round(M.area, 1), round(band.area, 1), round(arc.length, 1), round(band.intersection(snow).area, 3)),
            'width along the coast (sampled)': widths, 'label (x, y, size)': (m['cx'], m['cy'], FS), 'label room (distance to edge)': round(band.exterior.distance(c), 2)}
