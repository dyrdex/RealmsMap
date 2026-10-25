"""Owner, Oct 25: three more islands, each a little smaller than Hurricane Island (4.8 across), each with a small dock (template DOCK),
shapes and looks varied (template ISLES):
  - Bilwen: the central Azure Sea, due east of the Ashen Forest; green meadow island, a cove, wildflowers, a few round trees, boulders;
  - Eurion: the central Azure Sea, due east of the Forgotten Woods; long, jagged rock island, cliffs all round, dark pines, scree;
  - Deathvein Island: the Blood Sea, due west of the Mire's centre; three-lobed, black blighted ground, red veins, dead trees, mist.
  'Due east/west of' an area: level with the centre of its ground (Ashen: geo.ash, Woods: geo.fwwood, Mire: geo.mimud + bog2, by their bounds);
  'central': half way between the coast at that height and the map's edge, then moved out to sea until 2 clear of any land.
  Markers on the dock side (Bilwen, Eurion: west, towards Darkhaven Marina; Deathvein: east), docks from the marker out 1 past the shore;
  names large (1.4), centred above each island (p.lbl); the owner's directions, no route drawn (hidepath)."""
import math, random
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union

MERIDIA = 'Board the great ship Meridia (Darkhaven Marina 5-6pm).'
ISLES = [  # name, area tint(s), side, diameter, kind, dock/marker direction (deg, y down), directions, sea
    ('Bilwen', ('ash',), 'east', 4.3, 'meadow', 180, MERIDIA, 'Azure Sea'),
    ('Eurion', ('fwwood',), 'east', 4.1, 'rock', 185, MERIDIA, 'Azure Sea'),
    ('Deathvein Island', ('mimud', 'bog2'), 'west', 4.2, 'blight', 0, 'Captain the Fair Lady (Docks at random docks).', 'Blood Sea'),
]
CLEAR = 2.0


def _parity(rings):
    A = Polygon()
    for p in rings:
        if len(p) > 2: A = A.symmetric_difference(Polygon(p).buffer(0))
    return A


def _radial(c, r, n=160):
    return Polygon([(c[0] + r(2 * math.pi * i / n) * math.cos(2 * math.pi * i / n), c[1] + r(2 * math.pi * i / n) * math.sin(2 * math.pi * i / n)) for i in range(n)])


def _shape(kind, R, rng):
    ph = [rng.uniform(0, 2 * math.pi) for _ in range(8)]
    if kind == 'meadow':                                   # rounded, with a cove on its north-east
        cove = math.radians(-50)
        return lambda t: R * (1 + 0.09 * math.sin(2 * t + ph[0]) + 0.05 * math.sin(3 * t + ph[1]) - 0.32 * math.exp(-((math.atan2(math.sin(t - cove), math.cos(t - cove))) / 0.38) ** 2))
    if kind == 'rock':                                     # long (south-west to north-east), jagged
        e, rot = 0.62, math.radians(-35)
        return lambda t: R * (1 / math.sqrt((math.cos(t - rot) / 1.28) ** 2 + (math.sin(t - rot) / (1.28 * e)) ** 2)) * (1 + 0.05 * math.sin(7 * t + ph[2]) + 0.035 * math.sin(11 * t + ph[3]) + 0.025 * math.sin(17 * t + ph[4]))
    return lambda t: R * (1 + 0.2 * math.sin(3 * t + ph[5]) + 0.06 * math.sin(5 * t + ph[6]) + 0.03 * math.sin(8 * t + ph[7]))   # blight: three lobes


def _grid(poly, step, rng, keep=1.0):
    out = []; x0, y0, x1, y1 = poly.bounds; y = y0
    while y <= y1:
        x = x0 + rng.uniform(0, step)
        while x <= x1:
            p = (x + rng.uniform(-step * .35, step * .35), y + rng.uniform(-step * .35, step * .35))
            if poly.contains(Point(p)) and rng.random() < keep: out.append(p)
            x += step
        y += step * 0.85
    return out


def apply(town, wild, pos):
    G = wild['geo']; land = _parity(G['land']); E = wild['bounds']; out = {}; made = []
    others = [Polygon(wild['fireball']['isle']), Polygon(wild['hurricane']['isle'])]
    R4 = lambda v: round(v, 3)
    for k, (name, tints, side, D, kind, da, route, sea) in enumerate(ISLES):
        rng = random.Random(5050 + k)
        U = unary_union([Polygon(p).buffer(0) for t in tints for p in G[t] if len(p) > 2]); cy = round((U.bounds[1] + U.bounds[3]) / 2, 2)
        cut = land.intersection(LineString([(E[0], cy), (E[2], cy)])); gs = list(cut.geoms) if hasattr(cut, 'geoms') else [cut]
        coast = max(g.bounds[2] for g in gs) if side == 'east' else min(g.bounds[0] for g in gs)
        edge = E[2] if side == 'east' else E[0]; sx = 1 if side == 'east' else -1
        cx = (coast + edge) / 2; rf = _shape(kind, D / 2, rng)
        while True:
            C = (round(cx, 2), cy); isle = _radial(C, rf).buffer(0.2).buffer(-0.2)
            if isle.distance(land) >= CLEAR and all(isle.distance(o) > 6 for o in others + made): break
            cx += sx * 0.5
        made.append(isle)
        ring = lambda g: [[R4(x), R4(y)] for x, y in list(g.exterior.coords)[:-1]]
        poly = ring(isle); G['land'] = list(G['land']) + [poly]; G['water'] = list(G['water']) + [poly]
        rim = 0.32 if kind == 'meadow' else 0.18 if kind == 'rock' else 0.12
        inner = isle.buffer(-rim)
        d = {'kind': kind, 'isle': poly, 'inner': ring(inner), 'wash': [ring(isle.buffer(-0.12))]}
        if kind == 'meadow':
            d['flowers'] = [[R4(x), R4(y), rng.randrange(3)] for x, y in _grid(inner.buffer(-0.1), 0.28, rng, 0.55)]
            d['trees'] = [[R4(x), R4(y), round(rng.uniform(.28, .4), 2)] for x, y in _grid(inner.buffer(-0.45), 0.9, rng, 0.45)][:7]
            d['rocks'] = [[R4(x), R4(y), round(rng.uniform(.1, .17), 2)] for x, y in _grid(inner.buffer(-0.3), 1.0, rng, 0.25)][:4]
            d['swirls'] = [[R4(x), R4(y)] for x, y in _grid(inner.buffer(-0.3), 0.7, rng, 0.5)]
        elif kind == 'rock':
            top = inner.buffer(-0.35); d['top'] = ring(top)
            ex = top.exterior; n = int(ex.length / 0.16); hach = []
            for i in range(n):
                p = ex.interpolate(i * ex.length / n); q = ex.interpolate((i * ex.length / n + 0.05) % ex.length)
                tx, ty = q.x - p.x, q.y - p.y; tl = math.hypot(tx, ty) or 1; nx, ny = ty / tl, -tx / tl
                if top.contains(Point(p.x + nx * .1, p.y + ny * .1)): nx, ny = -nx, -ny
                L = rng.uniform(.22, .42); hach.append([R4(p.x), R4(p.y), R4(p.x + nx * L), R4(p.y + ny * L)])
            d['hach'] = hach
            d['pines'] = [[R4(x), R4(y), round(rng.uniform(.75, 1.0), 2)] for x, y in _grid(top.buffer(-0.2), 0.36, rng, 0.75)
                          if (x - C[0]) * 0.8 + (y - C[1]) * -0.6 > -0.4]       # (the pines on its north-east half)
            d['scree'] = [[R4(x), R4(y), round(rng.uniform(.035, .07), 3)] for x, y in _grid(top, 0.3, rng, 0.35)]
        else:
            veins = []
            for j in range(5):
                a = 2 * math.pi * j / 5 + rng.uniform(-.3, .3); p = (C[0] + rng.uniform(-.3, .3), C[1] + rng.uniform(-.3, .3)); line = [p]
                for s in range(30):
                    a += rng.uniform(-.55, .55); q = (line[-1][0] + .16 * math.cos(a), line[-1][1] + .16 * math.sin(a))
                    if not inner.buffer(-0.08).contains(Point(q)): break
                    line.append(q)
                if len(line) > 3: veins.append([[R4(x), R4(y)] for x, y in line])
                if len(line) > 8:                          # a branch
                    b = a + rng.choice([-1, 1]) * 0.9; line2 = [line[len(line) // 2]]
                    for s in range(12):
                        b += rng.uniform(-.5, .5); q = (line2[-1][0] + .14 * math.cos(b), line2[-1][1] + .14 * math.sin(b))
                        if not inner.buffer(-0.08).contains(Point(q)): break
                        line2.append(q)
                    if len(line2) > 3: veins.append([[R4(x), R4(y)] for x, y in line2])
            d['veins'] = veins
            d['dead'] = [[R4(x), R4(y), round(rng.uniform(.75, 1.05), 2), rng.randrange(3)] for x, y in _grid(inner.buffer(-0.25), 0.62, rng, 0.6)]
            d['pools'] = [[R4(x), R4(y), round(rng.uniform(.12, .2), 2)] for x, y in _grid(inner.buffer(-0.35), 1.1, rng, 0.3)][:4]
            d['mist'] = [[R4(x), R4(y), round(rng.uniform(.35, .6), 2)] for x, y in _grid(isle, 0.9, rng, 0.5)]
        # ---- the marker on the dock side's beach, the dock out from it ----
        a = math.radians(da); ux, uy = math.cos(a), math.sin(a)
        ray = LineString([C, (C[0] + ux * 10, C[1] + uy * 10)]); sh = ray.intersection(isle.exterior)
        sh = min(list(sh.geoms) if hasattr(sh, 'geoms') else [sh], key=lambda q: Point(C).distance(q))
        pin = [round(sh.x - ux * 0.3, 2), round(sh.y - uy * 0.3, 2)]
        d['dock'] = [pin[0], pin[1], round(sh.x + ux * 1.0, 2), round(sh.y + uy * 1.0, 2)]
        x0, y0, x1, y1 = isle.bounds; top_y = y0 - 1.25
        wild.setdefault('isles', []).append(d)
        wild['places'].append({'name': name, 'route': route, 'room': name, 'dir': 'here', 'group': 'af', 'where': 'in the ' + sea,
                               'card': 'Island in the ' + sea, 'rhead': 'Directions:', 'note': None, 'hidepath': True,
                               'path': [pin], 'at': pin, 'fs': 1.4, 'lbl': [round(C[0] - pin[0], 2), round(top_y - pin[1] - 0.15, 2), 'middle']})
        out[name] = {'level with (y)': cy, 'coast / edge x': (round(coast, 1), edge), 'centre': C, 'moved out to sea by': round(abs(C[0] - (coast + edge) / 2), 1),
                     'box': [round(c, 2) for c in isle.bounds], 'to land': round(isle.distance(land), 2), 'marker': pin, 'dock': d['dock']}
    return out
