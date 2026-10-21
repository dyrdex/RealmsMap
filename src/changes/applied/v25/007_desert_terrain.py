"""Owner, Oct 20: the Desert of Despair's ground was a plain colour. Desert terrain of its own, unlike the Wastelands' (grass tufts, crags, brush),
in the map's muted old style (template DDSAND, drawn just over the sand):
  - a texture over the whole desert sand (geo.sand 16): fine grain and faint wind ripples (two SVG patterns of unrelated sizes, so no repeat shows);
  - wind-ripple fields: patches of parallel wavy strokes in open sand;
  - crescent dunes (barchans) with a shaded lee side;
  - a few dry, cracked lake beds;
  - small loose rock clusters, sparse dry scrub, and a handful of cacti (very few: owner).
Everything keeps clear of paths, rooms, clearings, mazes, drawings, markers and names. Own random.Random, so nothing else moves."""
import json, math, os, random
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union

SAND = 16                                            # geo.sand 16: the Desert of Despair's ground
N = dict(ripples=110, dunes=26, flats=3, rocks=34, scrub=42, cacti=4)
CLEAR = dict(path=0.45, room=0.4, marker=0.9)


def apply(town, wild, pos):
    rng = random.Random(7007)
    G = wild['geo']; mk = lambda p: Polygon([q[:2] for q in p]).buffer(0)
    sand = mk(G['sand'][SAND])
    # ---- what to keep clear of ----
    lines = []
    for k in ('fwtracks', 'swtracks', 'dirtroads', 'etrtracks', 'seaways', 'seawaysfaint', 'streams', 'ntrroad', 'smrdash', 'seadash', 'mdfaint'):
        for l in wild.get(k) or []:
            l = l['pts'] if isinstance(l, dict) else l
            if isinstance(l, list) and len(l) > 1 and isinstance(l[0], (list, tuple)): lines.append(LineString([q[:2] for q in l]))
    for k in ('road', 'southpath', 'link'):
        l = wild.get(k)
        if isinstance(l, list) and len(l) > 1 and isinstance(l[0], (list, tuple)): lines.append(LineString([q[:2] for q in l]))
    near = sand.buffer(1)
    lines = [l for l in lines if l.intersects(near)]
    busy = [l.buffer(CLEAR['path']) for l in lines]
    busy += [Point(p[:2]).buffer(CLEAR['room']) for p in pos.values() if near.contains(Point(p[:2]))]
    busy += [mk(p).buffer(0.3) for p in wild.get('smrpatch') or [] if len(p) > 2]
    busy += [mk(m['poly']).buffer(0.3) for m in wild.get('fwmazes') or []]
    for g in wild['gfx']:
        if g.get('at') == 'xy' and g.get('k') != 'text': busy.append(box(g['x'] - g['w'] / 2 - .3, g['y'] - g['h'] / 2 - .3, g['x'] + g['w'] / 2 + .3, g['y'] + g['h'] / 2 + .3))
        if g.get('k') == 'text': busy.append(box(g['x'] - 0.11 * len(g['text']) - .2, g['y'] - .45, g['x'] + 0.11 * len(g['text']) + .2, g['y'] + .2))
    for p in wild['places']:                                                     # markers and their names (to the right of the marker, 0.96 tall)
        q = (p.get('at') or p['path'][-1])[:2] if p.get('path') else None
        if not q: continue
        busy.append(Point(q).buffer(CLEAR['marker']))
        if not p.get('nolabel'): busy.append(box(q[0] - 0.4, q[1] - 0.9, q[0] + 0.75 + 0.48 * len(p['name']), q[1] + 0.6))
    for a in wild.get('arealabels') or []:                                       # big area names
        hw = a.get('hw', 6); n = len(a.get('lines', [1])); lh = a.get('lh', 2.8)
        busy.append(box(a['x'] - hw - .5, a['y'] - 2.0, a['x'] + hw + .5, a['y'] + n * lh))
    blocked = unary_union(busy)
    free = sand.buffer(-0.3).difference(blocked)

    def spots(n, r, sep, others=(), tries=40000):
        """n points in free space, each with a clear disc of radius r, sep apart from each other and from others"""
        out = []; k = 0; x0, y0, x1, y1 = free.bounds
        room = free.buffer(-r)
        while len(out) < n and k < tries:
            k += 1; q = (rng.uniform(x0, x1), rng.uniform(y0, y1))
            if not room.contains(Point(q)): continue
            if any(math.dist(q, o) < sep for o in list(out) + list(others)): continue
            out.append(q)
        return out
    R = lambda v: round(v, 3)
    # ---- dry lake beds: rounded blobs with a few crack lines inside ----
    flats = []
    for (x, y) in spots(N['flats'], 1.6, 12):
        rx, ry = rng.uniform(1.1, 1.6), rng.uniform(0.7, 1.0); ph = rng.uniform(0, 6.3)
        poly = [[R(x + rx * (1 + .1 * math.sin(3 * a + ph)) * math.cos(a)), R(y + ry * (1 + .1 * math.sin(3 * a + ph)) * math.sin(a))] for a in [i * 2 * math.pi / 28 for i in range(28)]]
        P = Polygon(poly); cracks = []
        for _ in range(9):
            a = (rng.uniform(x - rx * .8, x + rx * .8), rng.uniform(y - ry * .7, y + ry * .7)); pts = [a]
            for _ in range(rng.randint(2, 4)):
                t = rng.uniform(0, 6.3); b = (pts[-1][0] + .35 * math.cos(t), pts[-1][1] + .35 * math.sin(t))
                if not P.buffer(-.1).contains(Point(b)): break
                pts.append(b)
            if len(pts) > 1: cracks.append([[R(u), R(v)] for u, v in pts])
        flats.append({'poly': poly, 'cracks': cracks})
    fl = [Point(f['poly'][0]).buffer(0) for f in flats]
    flatzone = unary_union([Polygon(f['poly']).buffer(0.4) for f in flats]) if flats else None
    if flatzone: free = free.difference(flatzone)
    # ---- crescent dunes ----
    dunes = [[R(x), R(y), round(rng.uniform(1.0, 1.7), 2), round(rng.uniform(-0.35, 0.35), 2)] for x, y in spots(N['dunes'], 1.1, 3.4)]
    dz = unary_union([Point(d[:2]).buffer(0.9 * d[2]) for d in dunes]); free = free.difference(dz)
    # ---- wind-ripple fields: 3-5 parallel wavy strokes ----
    ripples = []
    rf = spots(N['ripples'], 0.7, 1.7)
    for x, y in rf:
        ang = rng.uniform(-0.35, 0.35); L = rng.uniform(0.9, 1.6); n = rng.randint(3, 5); ph = rng.uniform(0, 6.3)
        ca, sa = math.cos(ang), math.sin(ang)
        for j in range(n):
            off = (j - (n - 1) / 2) * 0.17; l = L * (1 - abs(j - (n - 1) / 2) * 0.18)
            pts = []
            for i in range(9):
                u = -l / 2 + l * i / 8; v = off + 0.04 * math.sin(u * 5 + ph + j)
                pts.append([R(x + u * ca - v * sa), R(y + u * sa + v * ca)])
            ripples.append(pts)
    rz = unary_union([LineString(l).buffer(0.25) for l in ripples]); free = free.difference(rz)
    # ---- rocks, scrub, cacti ----
    rocks = [[R(x), R(y), round(rng.uniform(0.3, 0.42), 2), rng.randint(2, 3)] for x, y in spots(N['rocks'], 0.45, 2.2)]
    free = free.difference(unary_union([Point(q[:2]).buffer(0.5) for q in rocks]))
    scrub = [[R(x), R(y), round(rng.uniform(0.5, 0.68), 2), rng.randint(0, 2)] for x, y in spots(N['scrub'], 0.4, 1.8)]
    free = free.difference(unary_union([Point(q[:2]).buffer(0.4) for q in scrub]))
    cacti = [[R(x), R(y), round(rng.uniform(0.75, 0.9), 2), rng.choice([1, -1])] for x, y in spots(N['cacti'], 0.6, 14)]
    wild['ddsand'] = {'poly': [[R(x), R(y)] for x, y in list(sand.exterior.coords)[:-1]], 'flats': flats, 'dunes': dunes, 'ripples': ripples,
                      'rocks': rocks, 'scrub': scrub, 'cacti': cacti}
    return {'desert sand (area)': round(sand.area, 1), 'free for drawings (area)': round(sand.buffer(-0.3).difference(blocked).area, 1),
            'ripple fields (strokes)': (len(rf), len(ripples)), 'dunes': len(dunes), 'dry lake beds': len(flats), 'rock clusters': len(rocks),
            'scrub': len(scrub), 'cacti': len(cacti)}
