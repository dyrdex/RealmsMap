# The bases of Otherland's two mountains (owner, Oct 22: set; abstract shapes encircling each mountain): wild.olmtnbase = [Morte's Peak, Zenith of the Gods]
# rings, not drawn (002/003 build the mountains on them; Morte's Peak uses the same circle, BASE_C/BASE_R in 002).
import itertools, math, random
import maplib
from shapely.geometry import Point, Polygon, MultiPoint, box
from shapely.ops import unary_union

MP_NAMES = {'Nestled Between the Peaks', 'Upon the Roof', 'Platforms of Sacrifice', 'An Icy Pass', 'A Snow Clogged Pass', "Dead Man's Pass", 'The Drop-Off',
            'The Sudden Stop', 'Entombed in Ice', 'A Cavern of Ice', 'An Icy Burrow', 'The Cave', 'Home of the Jarl', 'A Crisp Path', 'Scratching the Surface',
            'Lost in the Darkness', 'The Last of the Foothills'}       # as applied/v2.4/001_otherland (Morte's Peak, east of x 50)
MP_SCALE = 2 / 3                                                        # owner (Oct 22): centred right, a third smaller
GODS_M, COAST_M, SMOOTH = 1.5, 0.5, 0.4
GODS_N, GODS_E, GODS_S, GODS_W = 3.5, 4.0, 1.0, 1.0           # owner (Oct 22): relaxed a good bit north and east, slightly south (y grows south)
WOB_A, WOB_K, ROUND = 0.7, 3, 2.0                                       # a loose abstract outline: gentle wobble (amplitude, waves round), rounded                                 # Gods: this far round its rooms + the Maze of Ice + Frost Mansion; this far in from the sea


def mec(pts):
    cands = [((a[0] + b[0]) / 2, (a[1] + b[1]) / 2) for a, b in itertools.combinations(pts, 2)]
    for a, b, c in itertools.combinations(pts, 3):
        d = 2 * (a[0] * (b[1] - c[1]) + b[0] * (c[1] - a[1]) + c[0] * (a[1] - b[1]))
        if abs(d) < 1e-9: continue
        sa, sb, sc = (q[0] ** 2 + q[1] ** 2 for q in (a, b, c))
        cands.append(((sa * (b[1] - c[1]) + sb * (c[1] - a[1]) + sc * (a[1] - b[1])) / d, (sa * (c[0] - b[0]) + sb * (a[0] - c[0]) + sc * (b[0] - a[0])) / d))
    return min(((c, max(math.dist(c, p) for p in pts)) for c in cands), key=lambda t: t[1])


def apply(town, wild, pos):
    rooms, _ = maplib.world()
    ol = [int(v) for v in pos if int(v) in rooms and rooms[int(v)]['area'] == 'Otherland']
    nm = lambda v: rooms[v]['name']
    land = Polygon()
    for r in wild['geo']['land']:
        if len(r) > 2: land = land.symmetric_difference(Polygon(r).buffer(0))     # evenodd
    MP = [v for v in ol if pos[str(v)][0] > 50 and (nm(v) in MP_NAMES or ("Morte's Peak" in nm(v) and 'View' not in nm(v)))]
    (cx, cy), r = mec(sorted({tuple(pos[str(v)][:2]) for v in MP}))
    morte = Point(cx, cy).buffer((r + 1.5) * MP_SCALE, 96)
    GODS = [v for v in ol if pos[str(v)][0] < 14 and ('Gods' in nm(v) or nm(v) == 'The Western Face')]
    maze = Polygon([m for m in wild['fwmazes'] if m.get('name') == 'The Maze of Ice'][0]['poly'])
    mx, my, mw, mh = wild['olmansion'][:4] if isinstance(wild['olmansion'][0], (int, float)) else wild['olmansion'][0][:4]
    pts = [tuple(pos[str(v)][:2]) for v in GODS] + list(maze.exterior.coords) + list(box(mx - mw / 2, my - mh / 2, mx + mw / 2, my + mh / 2).exterior.coords)
    hull = MultiPoint(pts).convex_hull
    K = [(-GODS_W, 0), (0, -GODS_N), (GODS_E * .8, -GODS_N * .8), (GODS_E, 0), (GODS_E * .6, GODS_S), (0, GODS_S)]   # spread: hull (+) K
    gods = MultiPoint([(x + a, y + b) for x, y in hull.exterior.coords for a, b in K]).convex_hull.buffer(GODS_M + ROUND, 32).buffer(-ROUND, 32)
    rnd = random.Random(2207); ph = [rnd.uniform(0, 2 * math.pi) for _ in range(2)]; c = gods.centroid
    wob = lambda x, y: (lambda t: WOB_A * (math.sin(WOB_K * t + ph[0]) * .6 + math.sin((WOB_K + 2) * t + ph[1]) * .4))(math.atan2(y - c.y, x - c.x))
    gods = Polygon([(x + (x - c.x) / math.hypot(x - c.x, y - c.y) * wob(x, y), y + (y - c.y) / math.hypot(x - c.x, y - c.y) * wob(x, y))
                    for x, y in gods.segmentize(0.3).exterior.coords]).buffer(0).buffer(0.6).buffer(-0.6)
    gods = gods.intersection(land.buffer(-COAST_M)).buffer(-SMOOTH).buffer(SMOOTH)
    if gods.geom_type != 'Polygon': gods = max(gods.geoms, key=lambda g: g.area)
    wild['olmtnbase'] = [[[round(x, 3), round(y, 3)] for x, y in g.exterior.coords] for g in (morte, gods)]
    inside = lambda g: sorted({nm(v) or '(spacer)' for v in ol if g.contains(Point(pos[str(v)][:2]))})
    return {"Morte's Peak base (centre, radius, area, rooms inside)": ((round(cx, 1), round(cy, 1)), round((r + 1.5) * MP_SCALE, 1), round(morte.area), len([v for v in ol if morte.contains(Point(pos[str(v)][:2]))])),
            'Zenith of the Gods base (x, y range, area, off land, rooms inside)': (tuple(round(q, 1) for q in gods.bounds), round(gods.area), round(gods.difference(land).area, 2),
                                                                                   len([v for v in ol if gods.contains(Point(pos[str(v)][:2]))])),
            'Gods names inside': inside(gods), 'Morte names inside': inside(morte)}
