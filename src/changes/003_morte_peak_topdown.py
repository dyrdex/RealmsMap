# Morte's Peak seen from above (owner, Oct 23): a drawn mountain set into the snow over every room that mentions it, in the map's old-map ink:
# crisp flat-toned ridge faces lit from the west-north-west, inked crests, fall-line hachures (template OLPEAK, drawn under the trails).
# Shaped by the room names: the foothills / approaches are its foot (it only begins there); twin summits either side of Nestled Between
# the Peaks (Upon the Roof on the western one); An Icy Pass, A Snow Clogged Pass and Dead Man's Pass are notches in its ridges; The Drop-Off
# and The Sudden Stop a steep west scarp; Cradled in the Shadow a hollow on its east flank; the Heart rooms lie under its south-west spur.
import math, random, sys
import numpy as np
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union
from maplib import world

MP_NAMES = {'Nestled Between the Peaks', 'Upon the Roof', 'Platforms of Sacrifice', 'An Icy Pass', 'A Snow Clogged Pass', "Dead Man's Pass", 'The Drop-Off',
            'The Sudden Stop', 'Entombed in Ice', 'A Cavern of Ice', 'An Icy Burrow', 'The Cave', 'Home of the Jarl', 'A Crisp Path', 'Scratching the Surface',
            'Lost in the Darkness', 'The Last of the Foothills'}
FOOT = {"Embracing the Fear of Morte's Peak", "The View of Morte's Peak", "The Foothills along Morte's Peak", 'The Last of the Foothills'}   # where it begins
R_IN, R_FOOT, FADE = 2.2, 0.9, 2.2          # outline this far round its rooms / its foot rooms; it fades in over this much from its edge
K = 0.105                                   # height lost per room away from a ridge
# the ridges: (x, y, height) points; k = steepness factor (the Drop-Off's scarp is steep)
A, B, S = (62.7, 192.4, 1.0), (65.6, 192.3, 0.94), (64.0, 192.05, 0.80)
RIDGES = [([A, S, B], 1.0),                                                                          # the summit crest, the saddle between
          ([B, (65.2, 189.6, 0.70), (64.7, 187.4, 0.44), (64.4, 185.6, 0.42), (64.0, 183.0, 0.14)], 1.0),   # north ridge, An Icy Pass notch
          ([A, (61.5, 190.0, 0.62), (60.6, 187.6, 0.34), (60.1, 185.6, 0.12)], 1.0),                  # north-west spur
          ([A, (61.4, 192.9, 0.70), (60.5, 193.2, 0.52), (59.3, 193.6, 0.52), (58.5, 194.2, 0.46)], 1.0),   # west ridge, A Snow Clogged Pass notch
          ([(58.6, 192.6, 0.44), (58.5, 195.5, 0.47), (58.6, 198.5, 0.42), (58.7, 200.2, 0.30)], 1.9),    # the Drop-Off's scarp
          ([A, (61.6, 195.4, 0.72), (60.2, 198.4, 0.56), (58.9, 201.5, 0.40), (57.4, 204.8, 0.24), (56.3, 207.4, 0.08)], 1.0),   # south-west spur over the Heart
          ([(60.2, 198.4, 0.56), (59.0, 197.6, 0.40)], 1.0),
          ([S, (64.3, 195.0, 0.70), (63.9, 198.4, 0.50), (63.6, 201.0, 0.26), (63.7, 203.5, 0.22), (64.3, 206.0, 0.05)], 1.0),   # south-east ridge, Dead Man's Pass
          ([(63.9, 198.4, 0.50), (65.9, 200.0, 0.24), (67.2, 201.0, 0.06)], 1.0),
          ([B, (67.3, 193.9, 0.60), (68.9, 195.6, 0.28), (70.0, 197.2, 0.06)], 1.0),                  # east spur (Cradled in the Shadow north of it)
          ([(65.2, 189.6, 0.70), (67.2, 188.7, 0.30), (68.6, 188.4, 0.10)], 1.0)]
LIGHT = (-0.80, -0.45, 0.55)                # from the west-north-west, high
Z = 7.0
RES = 0.1
TONES = [(-9, -0.42, '#4F585D', .85), (-0.42, -0.16, '#69737A', .75), (0.16, 0.40, '#A8B1B6', .70), (0.40, 9, '#C3CBCF', .85)]   # (no fill in between)


def _contour_polys(V, gx, gy, lo, hi):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig = plt.figure(); cs = plt.contourf(gx, gy, V, levels=[lo, hi]); out = []
    for path in cs.get_paths():
        for ring in path.to_polygons():
            if len(ring) > 3: out.append(Polygon(ring))
    plt.close(fig)
    acc = Polygon()                                     # even-odd: a path's rings are shells and holes
    for p in out: acc = acc.symmetric_difference(p.buffer(0))
    return acc


def apply(town, wild, pos):
    rooms, exits = world()
    P = {int(k): v for k, v in pos.items()}
    MPR = [v for v, r in rooms.items() if v in P and r['area'] == 'Otherland' and P[v][0] > 50 and 180 <= P[v][1] <= 212
           and (r['name'] in MP_NAMES or "Morte's Peak" in r['name'])]
    foot = [v for v in MPR if rooms[v]['name'] in FOOT]
    snow = unary_union([Polygon(p) for p in wild['geo']['snow'] if len(p) > 2])
    F = unary_union([Point(P[v]).buffer(R_FOOT if v in foot else R_IN) for v in MPR]).buffer(2.0).buffer(-2.0).buffer(0.8).buffer(-0.8)
    F = Polygon(F.exterior) if F.geom_type == 'Polygon' else Polygon(max(F.geoms, key=lambda g: g.area).exterior)
    F = F.intersection(snow.buffer(-0.4)).simplify(0.02)
    bx0, by0, bx1, by1 = F.bounds
    gx = np.arange(bx0 - 0.5, bx1 + 0.5, RES); gy = np.arange(by0 - 0.5, by1 + 0.5, RES); X, Y = np.meshgrid(gx, gy)
    H = np.zeros_like(X)
    for pts, kf in RIDGES:
        for (ax, ay, ah), (bx, by, bh) in zip(pts, pts[1:]):
            vx, vy = bx - ax, by - ay; L2 = vx * vx + vy * vy
            u = np.clip(((X - ax) * vx + (Y - ay) * vy) / L2, 0, 1)
            d = np.hypot(X - ax - u * vx, Y - ay - u * vy)
            H = np.maximum(H, ah + (bh - ah) * u - K * kf * d)
    for v in foot:                                      # the foothills: the mountain only begins there
        H *= 1 - 0.8 * np.exp(-((X - P[v][0]) ** 2 + (Y - P[v][1]) ** 2) / 1.6 ** 2)
    rr = random.Random(23101); ph = [rr.uniform(0, 6.3) for _ in range(2)]
    H += 0.02 * np.sin(X * 0.9 + ph[0]) * np.sin(Y * 0.7 + ph[1])         # only a slow sway, no speckle
    from scipy.ndimage import gaussian_filter, distance_transform_edt
    H = gaussian_filter(np.maximum(H, 0), 1.6)
    # inside F, and how far in (the fade at its foot)
    from matplotlib.path import Path as MPath
    inside = MPath(np.array(F.exterior.coords)).contains_points(np.c_[X.ravel(), Y.ravel()]).reshape(X.shape)
    din = distance_transform_edt(inside) * RES
    env = np.clip(din / FADE, 0, 1) ** 1.3
    dy_, dx_ = np.gradient(H, RES)
    nx_, ny_ = -dx_ * Z, -dy_ * Z; nn = np.sqrt(nx_ ** 2 + ny_ ** 2 + 1)
    lx, ly, lz = LIGHT; ln = math.sqrt(lx * lx + ly * ly + lz * lz)
    V = ((nx_ * lx + ny_ * ly + lz) / nn - lz) / ln * env
    V = gaussian_filter(V, 1.2)
    layers = []
    for lo, hi, col, op in TONES:
        g = _contour_polys(V, gx, gy, lo, hi).intersection(F)
        gs = [h for h in getattr(g, 'geoms', [g]) if h.geom_type == 'Polygon' and h.area > 0.25]
        if gs: layers.append({'fill': col, 'op': op, 'rings': [[[round(x, 3), round(y, 3)] for x, y in r.coords] for h in gs for r in [h.exterior, *h.interiors]]})
    # crests: the ridge lines themselves (above a third of the height), inked pale on their lit edge
    crests = []
    for pts, kf in RIDGES:
        cur = []
        for (ax, ay, ah), (bx, by, bh) in zip(pts, pts[1:]):
            n = max(2, int(math.dist((ax, ay), (bx, by)) / 0.25))
            for i in range(n + 1):
                t = i / n; x, y, h = ax + (bx - ax) * t, ay + (by - ay) * t, ah + (bh - ah) * t
                if h >= 0.3 and F.buffer(-1.0).contains(Point(x, y)): cur.append([round(x, 3), round(y, 3), round(min(1, (h - 0.3) / 0.5), 2)])
                elif len(cur) > 1: crests.append(cur); cur = []
                else: cur = []
        if len(cur) > 1: crests.append(cur)
    # hachures (old-map style): rows of short strokes down the fall line, set along the height contours, only on the shaded faces, longer where steep
    hach = []; sl = np.hypot(dx_, dy_); smax = float(np.percentile(sl[inside], 97))
    tl = unary_union([LineString(l) for l in wild['oltracks'] if len(l) > 1]).buffer(0.2)
    from skimage.measure import find_contours
    He = gaussian_filter(H * env, 1.0)
    for lev in np.arange(0.06, 1.0, 0.08):
        for c in find_contours(He, lev):
            line = LineString([(gx[0] + q[1] * RES, gy[0] + q[0] * RES) for q in c])
            if line.length < 0.5: continue
            for k in range(int(line.length / 0.24)):
                q = line.interpolate(k * 0.24 + 0.12); j, i = int(round((q.x - gx[0]) / RES)), int(round((q.y - gy[0]) / RES))
                if not (0 <= i < H.shape[0] and 0 <= j < H.shape[1]) or not inside[i, j]: continue
                sv = sl[i, j] / smax; v = V[i, j]
                if v > -0.14 or sv < 0.4: continue
                L = 0.12 + 0.2 * min(1, sv); ux, uy = -dx_[i, j] / sl[i, j], -dy_[i, j] / sl[i, j]
                seg = LineString([(q.x, q.y), (q.x + ux * L, q.y + uy * L)])
                if F.buffer(-0.2).contains(seg) and not tl.intersects(seg):
                    hach.append([[round(q.x, 3), round(q.y, 3)], [round(q.x + ux * L, 3), round(q.y + uy * L, 3)], round(min(.8, 0.3 + 0.5 * min(1, -v)), 2)])
    wild['olpeak'] = {'layers': layers, 'crests': crests, 'hach': hach}
    # the snow's drifts / ice flecks where the mountain is drawn (above its faded foot) are dropped
    body = F.buffer(-FADE * 0.5); o = wild['olsnow']; n0 = (len(o['drifts']), len(o['ice']))
    o['drifts'] = [d for d in o['drifts'] if not body.contains(Point(d[:2]))]; o['ice'] = [q for q in o['ice'] if not body.intersects(Polygon(q))]
    gorge = unary_union([Polygon(p) for p in wild['olgorge']['band'] if len(p) > 2])
    return {"Morte's Peak from above (rooms, of them its foot, all inside, outline area, tone pieces per level, crest lines, hachures, drifts/ice dropped, gap to the gorge, foot rooms' depth inside)":
            (len(MPR), len(foot), all(F.contains(Point(P[v])) for v in MPR), round(F.area, 1), [len(l['rings']) for l in layers], len(crests), len(hach),
             (n0[0] - len(o['drifts']), n0[1] - len(o['ice'])), round(F.distance(gorge), 2),
             {rooms[v]['name'][:22] + ' ' + str(v): round(F.exterior.distance(Point(P[v])), 2) for v in foot})}
