# Over the Cliff Maze (owner, Oct 22): off the land and its east-side trail, it only abuts the coast; its west edge is one smooth
# curve that takes in both maze rooms (14428, 683) and their entry paths with no juts.
import math
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union, substring, polylabel

ROOMS = ('14428', '683')
R_ROOM, R_PATH, MARGIN = 1.4, 0.9, 0.5        # room / path clearance inside the blob, plus a little sea beyond the farthest of them


def apply(town, wild, pos):
    mz = next(m for m in wild['fwmazes'] if m['name'] == 'Over the Cliff Maze')
    snow = unary_union([Polygon(p) for p in wild['geo']['snow'] if len(p) > 2])
    main = max(getattr(snow, 'geoms', [snow]), key=lambda g: g.area); ring = LineString(main.exterior.coords)
    pr = [ring.project(Point(pos[v])) for v in ROOMS]
    d1, d2 = sorted(pr)
    arc = substring(ring, d1, d2)
    if arc.length > ring.length / 2: arc = unary_union([substring(ring, d2, ring.length), substring(ring, 0, d1)])
    # a smoothed coast line from the 14428 end to the 683 end, and its sea-side normal
    pts = list(arc.coords)
    if math.dist(pts[0], pos[ROOMS[0]]) > math.dist(pts[-1], pos[ROOMS[0]]): pts = pts[::-1]
    a = LineString(pts); n = 60
    base = [a.interpolate(i / n, normalized=True).coords[0] for i in range(n + 1)]
    sm = []
    for i in range(n + 1):
        ws = [(j, math.exp(-((j - i) / 6) ** 2)) for j in range(max(0, i - 15), min(n, i + 15) + 1)]
        W = sum(x for _, x in ws); sm.append((sum(base[j][0] * x for j, x in ws) / W, sum(base[j][1] * x for j, x in ws) / W))
    sm[0], sm[-1] = base[0], base[-1]
    chord = (sm[-1][0] - sm[0][0], sm[-1][1] - sm[0][1]); L = math.hypot(*chord); t = (chord[0] / L, chord[1] / L)
    nrm = (-t[1], t[0])
    if main.contains(Point(sm[n // 2][0] + nrm[0], sm[n // 2][1] + nrm[1])): nrm = (-nrm[0], -nrm[1])       # pointing out to sea
    # what must be inside: the two rooms and the sea part of every path ending at them
    paths = [l for k in ('seawaysfaint', 'oltracks') for l in wild[k] if len(l) > 1 and any(math.dist(q, pos[v]) < 0.05 for v in ROOMS for q in (l[0], l[-1]))]
    core = unary_union([Point(pos[v]).buffer(R_ROOM) for v in ROOMS] + [LineString(l).buffer(R_PATH) for l in paths]).difference(main)
    cc = [c for g in getattr(core, 'geoms', [core]) for c in g.exterior.coords]
    proj = lambda q: ((q[0] - sm[0][0]) * t[0] + (q[1] - sm[0][1]) * t[1], (q[0] - sm[0][0]) * nrm[0] + (q[1] - sm[0][1]) * nrm[1])
    # the coast's own offset at each step, then the needed width there: one concave curve over all of it (no dents, no juts)
    us = [proj(q)[0] for q in sm]
    req = []
    for i in range(n + 1):
        lo, hi = (us[i - 1] if i else -1e9), (us[i + 1] if i < n else 1e9)
        vs = [proj(c)[1] for c in cc if (lo + us[i]) / 2 <= proj(c)[0] <= (us[i] + hi) / 2]
        req.append(max(vs) - proj(sm[i])[1] + MARGIN if vs else 0.0)
    hull = []                                                                   # upper concave envelope of (i, req)
    for p in enumerate(req):
        while len(hull) > 1 and (hull[-1][0] - hull[-2][0]) * (p[1] - hull[-2][1]) - (hull[-1][1] - hull[-2][1]) * (p[0] - hull[-2][0]) >= 0: hull.pop()
        hull.append(p)
    env = []
    for (i0, r0), (i1, r1) in zip(hull, hull[1:]):
        env += [r0 + (r1 - r0) * (i - i0) / (i1 - i0) for i in range(i0, i1)]
    env.append(hull[-1][1])
    env = [sum(env[min(n, max(0, i + k))] * math.exp(-(k / 4) ** 2) for k in range(-8, 9)) / sum(math.exp(-(k / 4) ** 2) for k in range(-8, 9)) for i in range(n + 1)]
    env = [max(e, r) for e, r in zip(env, req)]
    west = [(sm[i][0] + nrm[0] * env[i], sm[i][1] + nrm[1] * env[i]) for i in range(n + 1)]
    inland = [(q[0] - nrm[0] * 3, q[1] - nrm[1] * 3) for q in sm]
    r_cap = 1.6
    ext = lambda q, s: (q[0] + t[0] * s, q[1] + t[1] * s)                       # carry the ends past the outer rooms by the room clearance
    rib = Polygon([ext(inland[0], -R_ROOM - MARGIN), ext(west[0], -R_ROOM - MARGIN)] + west + [ext(west[-1], R_ROOM + MARGIN), ext(inland[-1], R_ROOM + MARGIN)] + inland[::-1])
    rib = unary_union([rib.buffer(-r_cap).buffer(r_cap), core]).buffer(0.6).buffer(-0.6)
    blob = rib.difference(snow)
    pieces = sorted(getattr(blob, 'geoms', [blob]), key=lambda g: -g.area)
    blob = pieces[0]
    lab = blob.centroid if blob.buffer(-1.2).contains(blob.centroid) else polylabel(blob, 0.05)
    old = Polygon(mz['poly'])
    mz['poly'] = [[round(x, 3), round(y, 3)] for x, y in blob.exterior.coords]
    mz['cx'], mz['cy'] = round(lab.x, 2), round(lab.y, 2)
    jut = blob.difference(blob.buffer(-1.2).buffer(1.2)).difference(snow.buffer(0.3))     # west-side corners sharper than 1.2 rooms
    tr = [LineString(l) for l in wild['oltracks'] if len(l) > 1]
    rooms_in = [v for v, q in pos.items() if blob.contains(Point(q))]
    return {'Over the Cliff Maze (area was -> now, on land, sea pieces dropped, its rooms inside, paths fully inside, other rooms inside, track length inside, west juts, label)':
            (round(old.area, 1), round(blob.area, 1), round(blob.intersection(snow).area, 3), [round(p.area, 2) for p in pieces[1:]],
             [v for v in ROOMS if blob.buffer(-R_ROOM + 0.01).contains(Point(pos[v]))], f'{sum(1 for l in paths if blob.buffer(0.01).contains(LineString(l).difference(main)))}/{len(paths)}',
             [v for v in rooms_in if v not in ROOMS], round(sum(l.intersection(blob).length for l in tr), 2), round(jut.area, 2), (mz['cx'], mz['cy']))}
