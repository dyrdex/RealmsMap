"""Owner, Oct 23: the Woods' coast trail is a clifftop, from Near the Cliffs 5669 east along the High-Cliff Trail to Blocked View 5628, then
round the Knights of the Round (below 5639) and along the new sea to Sand and Rocks 5494. The cliff face (`fwcliff`, template FWCLIFF, the
map's own cliff colours: --w-cliff face, --w-hach hachures and rim) runs along the trail's low side:
  - 5669 - 5628: the south side (owner, Oct 23), down towards the Knights of the Round and the 5629-5632 stretch;
  - 5628 - 5639: towards the Knights of the Round (owner, Oct 23): the trail's outside (north of 5631-5632, into the low strip below the
    High-Cliff Trail that opens west onto the Knights' land; west of 5632-5636; south of 5637-5639);
  - 5639 - 5494: the sea side (south, then the inlet's north-west shore), tapering out by 5494, where the inlet ends in a beach.
  Its rim is RIM off the trail's centre line, its face WIDE wide (tapering in over TAPER0 at 5669, out over TAPER1 at 5494).
  - 5644 d 13640, the only safe way down (owner, Oct 23): a notch cut through the face round the stairway (NOTCH each side), the stairway's
    steps redone closer together, all the way down (descents[-1], from 002).
  Trees and tufts on the face removed."""
import math, random
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

RIM, WIDE, TAPER0, TAPER1 = 0.22, 0.55, 0.8, 1.6
NOTCH = 0.3
HACH = 0.12                                         # hachures apart, along the rim
STEP, HALF0, HALF1 = 0.13, 0.22, 0.14               # the safe way down's steps: apart, half width at the top, at the bottom
SPRITES = ('trees', 'tufts', 'hills', 'thorns', 'brush', 'boulders', 'crags', 'reeds', 'wheattufts')


def _resample(pts, d=0.1):
    g = LineString(pts); n = max(2, int(g.length / d))
    return [g.interpolate(g.length * i / n).coords[0] for i in range(n + 1)], g.length


def _face(pts, low, wid, rng):
    """the cliff face along pts on the side `low` (a shape on the low side), width wid(s) (s = distance along); returns face, rim, hachures"""
    P, L = _resample(pts)
    N = []
    for i in range(len(P)):
        a, b = P[max(0, i - 1)], P[min(len(P) - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]; l = math.hypot(tx, ty) or 1; nx, ny = -ty / l, tx / l
        if not low.contains(Point(P[i][0] + nx * 0.45, P[i][1] + ny * 0.45)): nx, ny = -nx, -ny
        N.append((nx, ny))
    S = []                                          # (smoothed normals, so the rim runs evenly round the bends)
    for i in range(len(P)):
        w = N[max(0, i - 4):i + 5]; x = sum(q[0] for q in w); y = sum(q[1] for q in w); l = math.hypot(x, y) or 1; S.append((x / l, y / l))
    step = L / (len(P) - 1)
    rim = [(P[i][0] + S[i][0] * RIM, P[i][1] + S[i][1] * RIM) for i in range(len(P))]
    foot = [(P[i][0] + S[i][0] * (RIM + wid(i * step)), P[i][1] + S[i][1] * (RIM + wid(i * step))) for i in range(len(P))]
    quads = [Polygon([rim[i], rim[i + 1], foot[i + 1], foot[i]]).buffer(0) for i in range(len(P) - 1) if wid(i * step) > 0.01 or wid((i + 1) * step) > 0.01]
    face = unary_union(quads).buffer(0.03).buffer(-0.03)
    hach = []; s = rng.uniform(0, HACH)
    while s < L:
        i = min(len(P) - 1, int(round(s / step))); w = wid(s)
        if w > 0.08:
            k = rng.uniform(0.55, 0.95)
            hach.append(((P[i][0] + S[i][0] * (RIM + 0.04), P[i][1] + S[i][1] * (RIM + 0.04)),
                         (P[i][0] + S[i][0] * (RIM + w * k), P[i][1] + S[i][1] * (RIM + w * k))))
        s += HACH * rng.uniform(0.8, 1.2)
    rim = [rim[i] for i in range(len(P)) if wid(i * step) > 0.01]
    return face, LineString(rim) if len(rim) > 1 else None, hach


def apply(town, wild, pos):
    rng = random.Random(5669)
    R = lambda v: tuple(pos[str(v)][:2])
    fw = wild['fwtracks']
    t30 = [tuple(q[:2]) for q in fw[30]]; i69 = min(range(len(t30)), key=lambda i: math.dist(t30[i], R(5669)))
    assert math.dist(t30[0], R(5628)) < 0.01 and math.dist(t30[i69], R(5669)) < 0.3
    S1 = [R(5669)] + t30[:i69 + 1][::-1][1:] if math.dist(t30[i69], R(5669)) > 0.01 else t30[:i69 + 1][::-1]   # 5669 -> 5628
    t16 = [tuple(q[:2]) for q in fw[16]]
    at = lambda v: min(range(len(t16)), key=lambda i: math.dist(t16[i], R(v)))
    i28, i39, i94 = at(5628), at(5639), at(5494)
    assert i94 < i39 < i28 and math.dist(t16[i28], R(5628)) < 0.01
    S2 = t16[i39:i28 + 1][::-1]                     # 5628 -> 5639
    S3 = t16[i94:i39 + 1][::-1]                     # 5639 -> 5494
    far = 40
    low1 = Polygon(S1 + [(S1[-1][0], S1[-1][1] + 2.2), (S1[0][0], S1[0][1] + 2.2)]).buffer(0)          # south of 5669 - 5628 (not as far as 5629 - 5632)
    inner = Polygon(S2 + [(-48.8, -49.8), (-46.0, -50.5), (-44.5, -53.5), (-44.5, -56.3)]).buffer(0)   # the Woods ground the trail wraps round
    low2 = box(-70, -70, -30, -30).difference(inner)                                                 # the outside: the Knights of the Round's side
    low3 = Polygon(S3 + [(S3[-1][0] + 1.5, S3[-1][1] + far), (S3[0][0], S3[0][1] + far)]).buffer(0)  # the sea's side
    L1, L2, L3 = LineString(S1).length, LineString(S2).length, LineString(S3).length
    w1 = lambda s: WIDE * min(1, s / TAPER0)
    w2 = lambda s: WIDE
    w3 = lambda s: WIDE * max(0, min(1, (L3 - s) / TAPER1))
    parts = [_face(S1, low1, w1, rng), _face(S2, low2, w2, rng), _face(S3, low3, w3, rng)]
    d = wild['descents'][-1]; a, b = d['pts']
    assert math.dist(a, R(5644)) < 0.01 and math.dist(b, R(13640)) < 0.01
    stair = LineString([a, b])
    trails = unary_union([LineString([q[:2] for q in l]).buffer(0.17) for l in fw if len(l) > 1] + [LineString(q['pts']).buffer(0.2) for q in wild['descents']])
    notch = stair.buffer(NOTCH, cap_style=2)
    face = unary_union([p[0] for p in parts]).difference(trails).difference(notch)
    face = unary_union([q for q in getattr(face, 'geoms', [face]) if q.area > 0.01])
    cut = trails.union(notch)
    rims = []
    for p in parts:
        if p[1] is None: continue
        r = p[1].difference(notch)
        for g in getattr(r, 'geoms', [r]):
            if g.length > 0.15: rims.append([[round(x, 3), round(y, 3)] for x, y in g.coords])
    hach = [[[round(c, 3) for c in h[0]], [round(c, 3) for c in h[1]]] for p in parts for h in p[2] if not cut.intersects(LineString(h))]
    polys = []
    for P in getattr(face, 'geoms', [face]):
        polys.append([[round(x, 3), round(y, 3)] for x, y in list(P.exterior.coords)[:-1]])
        polys += [[[round(x, 3), round(y, 3)] for x, y in list(h.coords)[:-1]] for h in P.interiors]
    wild['fwcliff'] = list(wild.get('fwcliff') or []) + [{'face': polys, 'hach': hach, 'rim': rims}]
    # ---- the safe way down: steps all the way, closer together ----
    Ls = math.dist(a, b); ux, uy = (b[0] - a[0]) / Ls, (b[1] - a[1]) / Ls; nx, ny = -uy, ux
    steps = []; s = 0.12
    while s < Ls - 0.1:
        t = s / Ls; h = HALF0 + (HALF1 - HALF0) * t; x, y = a[0] + ux * s, a[1] + uy * s
        steps.append([[round(x - nx * h, 3), round(y - ny * h, 3)], [round(x + nx * h, 3), round(y + ny * h, 3)]]); s += STEP
    old_steps = len(d['steps']); d['steps'] = steps
    gone = {}
    zone = face.buffer(0.1)
    for k in SPRITES:
        Lk = wild.get(k) or []; keep = [q for q in Lk if not zone.contains(Point(q[:2]))]
        if len(keep) != len(Lk): gone[k] = len(Lk) - len(keep); wild[k] = keep
    # ---- checks ----
    def par(rs):
        A = Polygon()
        for r in rs:
            if len(r) > 2: A = A.symmetric_difference(Polygon(r).buffer(0))
        return A
    W = par(wild['geo']['water'])
    rooms_on = sorted(int(v) for v, q in pos.items() if face.contains(Point(q[:2])))
    others = unary_union([LineString([q[:2] for q in l]) for i, l in enumerate(fw) if len(l) > 1 and i not in (16, 30)])
    return {'stretches (length): 5669-5628, 5628-5639, 5639-5494': (round(L1, 1), round(L2, 1), round(L3, 1)), 'face (area, pieces)': (round(face.area, 2), len(polys)),
            'hachures': len(hach), 'rim pieces': len(rims), 'face in the sea (area)': round(face.intersection(W).area, 3),
            'rooms on the face': rooms_on, 'other trails over the face (length)': round(others.intersection(face).length, 3),
            'safe way down: length, steps (old -> new), notch width': (round(Ls, 2), (old_steps, len(steps)), 2 * NOTCH), 'sprites removed': gone,
            '13640 from the face': round(face.distance(Point(R(13640))), 2)}
