"""Owner, Oct 25: Fireball Island, in the open Blood Sea due west of the Barren Peaks of Tahjliera.
  - size: its mean diameter = the full height (y) of Angel's Landing's island (measured from the land, 14.32), made irregular (an uneven,
    rounded outline); centre half way between the Barren Peaks' west coast and the map's west edge, level with the Barren Peaks' name;
  - a land piece of its own + a hole in the sea (as Irrybis, 2.13/001); a sand beach all round (uneven width), jungle inside it
    (canopy clumps + palms along the beach, own Random); a new volcano at its centre (template FIREBALL);
  - the place: marker on the south-east beach, a large name (1.4) west of it; directions = the owner's text (no walking route);
    the highlighted line runs Sailing the Seas' route (unchanged) and then a dotted, wavy boat line with large bends north to the marker (`sail`)."""
import math, random
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union

ROUTE = "Board the Bounty's Revenge in Grimdog Port Authority. Docks at the north of the Knock Dock 02:00 - 04:00."
FROM = 'Sailing the Seas'
WAY = [(-97.0, -19.6), (-108.5, -30.0), (-100.0, -44.5), (-114.5, -58.0), (-102.5, -72.5), (-117.0, -86.0), (-105.5, -99.5), (-111.0, -110.5)]
WAVE_A, WAVE_L = 0.45, 4.2                    # the boat line's small waves on top of its bends
BEACH = 0.95                                  # the beach's mean width
VOLC = (0.0, 1.6, 0.65)                       # the volcano's base centre (from the island's centre) and scale: base 7.6 wide, peak 6.2 up at 1 (owner, Oct 25: smaller, 0.65)
DOCK_A, DOCK_OUT = 45, 1.0                    # the dock: from the marker south-east (degrees from east, y down), this far past the shore (owner, Oct 25)
PIN_A = 52                                    # the marker: this many degrees round from east (y down), on the beach


def _parity(rings):
    A = Polygon()
    for p in rings:
        if len(p) > 2: A = A.symmetric_difference(Polygon(p).buffer(0))
    return A


def _radial(c, r, n=144):
    return Polygon([(c[0] + r(2 * math.pi * i / n) * math.cos(2 * math.pi * i / n), c[1] + r(2 * math.pi * i / n) * math.sin(2 * math.pi * i / n)) for i in range(n)])


def _catmull(P, n=14):
    P = [P[0]] + P + [P[-1]]; out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n; t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(tuple(P[-2])); return out


def apply(town, wild, pos):
    rng = random.Random(1155)
    G = wild['geo']; land = _parity(G['land'])
    al = [g for g in (land.geoms if hasattr(land, 'geoms') else [land]) if g.distance(Point(-66.18, -69.1)) < 1.5 and g.area < 500]
    assert len(al) == 1; H = al[0].bounds[3] - al[0].bounds[1]; R = H / 2
    lbl = next(a for a in wild['arealabels'] if a['lines'][0] == 'Barren Peaks'); cy = lbl['y']
    coast = land.intersection(LineString([(wild['bounds'][0], cy), (lbl['x'], cy)]))
    west = min(g.bounds[0] for g in (coast.geoms if hasattr(coast, 'geoms') else [coast]))
    cx = round((wild['bounds'][0] + west) / 2, 2); C = (cx, cy)
    ph = [rng.uniform(0, 2 * math.pi) for _ in range(8)]
    rf = lambda t: R * (1 + 0.10 * math.sin(2 * t + ph[0]) + 0.07 * math.sin(3 * t + ph[1]) + 0.05 * math.sin(5 * t + ph[2]) + 0.03 * math.sin(7 * t + ph[3]))
    isle = _radial(C, rf).buffer(0.4).buffer(-0.4)
    bw = lambda t: BEACH * (1 + 0.3 * math.sin(3 * t + ph[4]) + 0.15 * math.sin(5 * t + ph[5]))
    jungle = _radial(C, lambda t: rf(t) - bw(t)).buffer(0.3).buffer(-0.3).intersection(isle.buffer(-0.45))
    assert not isle.intersects(land.buffer(10)), 'too close to land'
    ring = lambda g: [[round(x, 3), round(y, 3)] for x, y in list(g.exterior.coords)[:-1]]
    poly = ring(isle)
    G['land'] = list(G['land']) + [poly]
    G['water'] = list(G['water']) + [poly]          # (evenodd: a hole in the sea; its outline is the shore line)
    wash = [ring(isle.buffer(-d)) for d in (0.2, 0.42)]
    # ---- the jungle: canopy clumps on a jittered grid, palms along the beach's inner edge ----
    canopy = []; x0, y0, x1, y1 = jungle.bounds; y = y0 + 0.2
    inner = jungle.buffer(-0.25)
    while y <= y1:
        x = x0 + rng.uniform(0, 0.55)
        while x <= x1:
            jx, jy = x + rng.uniform(-.2, .2), y + rng.uniform(-.16, .16)
            if inner.contains(Point(jx, jy)): canopy.append([round(jx, 3), round(jy, 3), round(rng.uniform(0.34, 0.56), 2), rng.randrange(3)])
            x += 0.55
        y += 0.46
    edge = jungle.exterior; palms = []; s = rng.uniform(0, 1)
    while s < edge.length:
        p = edge.interpolate(s); a = math.atan2(p.y - cy, p.x - cx)
        palms.append([round(p.x, 3), round(p.y, 3), round(rng.uniform(0.75, 1.05), 2), round(math.cos(a) * rng.uniform(.12, .25), 3)])
        s += rng.uniform(1.0, 1.6)
    vx, vy = cx + VOLC[0], cy + VOLC[1]
    # ---- the marker, on the south-east beach ----
    a = math.radians(PIN_A); r = rf(a) - bw(a) * 0.45
    pin = [round(cx + r * math.cos(a), 2), round(cy + r * math.sin(a), 2)]
    assert isle.contains(Point(pin)) and not jungle.buffer(-0.1).contains(Point(pin))
    # ---- the dock: from the marker out south-east, one room past the shore ----
    da = math.radians(DOCK_A); ux, uy = math.cos(da), math.sin(da)
    ray = LineString([pin, (pin[0] + ux * 6, pin[1] + uy * 6)]); hit = ray.intersection(isle.exterior)
    hits = list(hit.geoms) if hasattr(hit, 'geoms') else [hit]; sh = min(hits, key=lambda q: Point(pin).distance(q))
    dock = [pin[0], pin[1], round(sh.x + ux * DOCK_OUT, 2), round(sh.y + uy * DOCK_OUT, 2)]
    # ---- the boat line: from Sailing the Seas, big bends north, small waves on top ----
    src = next(p for p in wild['places'] if p['name'] == FROM)
    start = tuple(src['path'][-1])
    base = _catmull([start] + WAY + [tuple(pin)], 16)
    L = LineString(base); n = int(L.length / 0.25); sail = []
    for i in range(n + 1):
        d = L.length * i / n; p = L.interpolate(d); q = L.interpolate(min(L.length, d + 0.05)); o = L.interpolate(max(0, d - 0.05))
        tx, ty = q.x - o.x, q.y - o.y; tl = math.hypot(tx, ty) or 1
        fade = min(1, d / 2.5, (L.length - d) / 2.5)
        w = WAVE_A * fade * math.sin(2 * math.pi * d / WAVE_L)
        sail.append([round(p.x - ty / tl * w, 3), round(p.y + tx / tl * w, 3)])
    sea_line = LineString(sail[12:-12])
    near_land = round(sea_line.distance(land), 2); near_isle = round(LineString(sail[:-14]).distance(isle), 2)
    wild['places'].append({'name': 'Fireball Island', 'route': ROUTE, 'room': 'Fireball Island', 'dir': 'here', 'group': src.get('group'),
                           'where': 'in the Blood Sea', 'card': 'Island in the Blood Sea · reached by boat', 'rhead': 'Directions:', 'note': None,
                           'path': [list(q) for q in src['path']] + sail[1:], 'segs': [[list(q) for q in g] for g in (src.get('segs') or [src['path']])],
                           'sail': sail, 'at': pin, 'fs': 1.4})
    wild['fireball'] = {'isle': poly, 'jungle': ring(jungle), 'wash': wash, 'canopy': canopy, 'palms': palms, 'volcano': [round(vx, 2), round(vy, 2), VOLC[2]], 'dock': dock}
    return {"Angel's Landing island height = diameter": round(H, 2), 'centre (coast x, edge x)': (C, round(west, 2), wild['bounds'][0]),
            'island box, area': ([round(c, 2) for c in isle.bounds], round(isle.area, 1)), 'beach area': round(isle.difference(jungle).area, 1),
            'canopy clumps, palms': (len(canopy), len(palms)), 'volcano at': wild['fireball']['volcano'], 'marker': pin, 'dock (from, to; shore to its end)': (dock, round(math.dist((sh.x, sh.y), dock[2:]), 2)),
            'boat line: points, length, nearest land, nearest the island before landing': (len(sail), round(L.length, 1), near_land, near_isle)}
