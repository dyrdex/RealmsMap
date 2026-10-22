# Morte's Peak (owner, Oct 22): a mountain seen straight from above, in the style of the owner's examples (several peaks in one massif):
# stepped terraces, each step an inked edge with a short cliff face below it (hachured, deepest on the side away from the light, lower right),
# flat pale ledges, a faceted cap on each summit. No height shading or blurred relief (owner: never those 3D effects).
# Base = the approved circle (001 preview); peaks from the room names. wild.olmassif = [{levels, caps}] (template OLMASSIF).
import math, random
from shapely.geometry import Point, Polygon, LineString, MultiPolygon
from shapely.affinity import translate
from shapely.ops import unary_union
import maplib

BASE_C, BASE_R = (65.88, 193.37), 10.78     # the base (owner, Oct 22: set)
PEAKS = [((67.0, 191.0), 7.0, 5, 0.3),      # The Fury of Morte's Peak: the summit (owner)      (centre, height in steps, ridge arms, arm turn)
         ((73.6, 193.6), 5.0, 4, 1.1),      # east: over Entombed within Morte's Peak; Nestled Between the Peaks in the saddle west of it
         ((67.4, 200.6), 5.0, 4, 0.2)]      # south: over the Heart of Morte's Peak
STEP = 1.25                                  # rooms per terrace step (horizontal)
ARM_A, JAG_A = 0.28, 0.07                    # ridge arms (share of the radius), jagged edges (rooms)
MIN_LEDGE = 0.35                             # a ledge never narrower than this
LIGHT = (0.17, 0.24)                         # cliff face: drops this far towards the lower right (away from the light)
SIDE = 0.07                                  # ... and this far all round
HACH_D = 0.13                                # hachure spacing along an edge


def apply(town, wild, pos):
    rnd = random.Random(2210)
    base = Point(*BASE_C).buffer(BASE_R, 128)
    ph = [rnd.uniform(0, 6.283) for _ in range(6)]
    base = Polygon([(x + (x - BASE_C[0]) / BASE_R * 0.22 * math.sin(3 * math.atan2(y - BASE_C[1], x - BASE_C[0]) + ph[0]) * math.sin(7 * math.atan2(y - BASE_C[1], x - BASE_C[0]) + ph[1]),
                     y + (y - BASE_C[1]) / BASE_R * 0.22 * math.sin(3 * math.atan2(y - BASE_C[1], x - BASE_C[0]) + ph[0]) * math.sin(7 * math.atan2(y - BASE_C[1], x - BASE_C[0]) + ph[1]))
                    for x, y in base.exterior.coords])

    names = ("The Fury of Morte's Peak", 'Nestled Between the Peaks', 'An Icy Pass', 'A Snow Clogged Pass', "Dead Man's Pass", "Entombed within Morte's Peak", "Within the Heart of Morte's Peak", 'Upon the Roof')
    return build(wild, pos, base, PEAKS, 100, names, "Morte's Peak")


def build(wild, pos, base, PEAKS, jseed, names, title, sheer=None):
    """a massif on base (Polygon) with PEAKS [(centre, height in steps, arms, arm turn)]; jseed seeds its jagged edges; names: rooms to report;
    sheer: where the terraces may all reach the base's edge (one sheer face, no ledges: a summit at the coast)"""
    def jag(poly, seed):
        r = random.Random(seed); out = []
        for g in (poly.geoms if isinstance(poly, MultiPolygon) else [poly]):
            ring = list(g.segmentize(0.22).exterior.coords)[:-1]; n = len(ring); c = g.centroid
            noise = [r.uniform(-1, 1) for _ in range(n)]
            noise = [(noise[i - 1] + 2 * noise[i] + noise[(i + 1) % n]) / 4 for i in range(n)]
            pts = []
            for (x, y), e in zip(ring, noise):
                d = math.hypot(x - c.x, y - c.y) or 1; pts.append((x + (x - c.x) / d * e * JAG_A * 2.2, y + (y - c.y) / d * e * JAG_A * 2.2))
            out.append(Polygon(pts).buffer(0))
        return unary_union(out)

    def cone(k, p):
        (cx, cy), h, arms, turn = p
        if h - k <= 0.15: return Polygon()
        R = (h - k) * STEP; pts = []
        for i in range(160):
            t = i / 160 * 2 * math.pi
            arm = abs(math.cos(arms * (t - turn) / 2)) ** 4
            rr = R * (1 + ARM_A * (arm - 0.35) + 0.06 * math.sin(2 * t + h))
            pts.append((cx + rr * math.cos(t), cy + rr * math.sin(t)))
        return Polygon(pts)

    levels = [base]
    for k in range(1, 8):
        R = unary_union([cone(k, p) for p in PEAKS]).buffer(0.55).buffer(-0.55)
        R = jag(R, jseed + k).intersection(levels[-1].buffer(-MIN_LEDGE) if sheer is None else levels[-1].buffer(-MIN_LEDGE).union(levels[-1].intersection(sheer))).buffer(0)
        R = unary_union([g for g in (R.geoms if hasattr(R, 'geoms') else [R]) if g.geom_type == 'Polygon' and g.area > 0.25])
        if R.is_empty: break
        levels.append(R)

    def rings(g):     # outer rings and holes (drawn evenodd)
        return [[[round(x, 3), round(y, 3)] for x, y in r_.coords] for q in (g.geoms if hasattr(g, 'geoms') else [g]) if q.geom_type == 'Polygon' and not q.is_empty
                for r_ in [q.exterior, *q.interiors]]
    lx, ly = LIGHT; ln = math.hypot(lx, ly)
    out = []; nh = 0
    for k, R in enumerate(levels):
        face = unary_union([translate(R, lx, ly), R.buffer(SIDE, 8)]).difference(R)
        if k: face = face.intersection(levels[k - 1])
        hach, rim = [], []
        for q in (R.geoms if hasattr(R, 'geoms') else [R]):
            ring = list(q.exterior.coords); ccw = LinearRingIsCCW(ring)
            L = LineString(ring); n = max(int(L.length / HACH_D), 1)
            for i in range(n):
                a = L.interpolate(i * HACH_D); b = L.interpolate(i * HACH_D + 0.05)
                tx, ty = b.x - a.x, b.y - a.y; tl = math.hypot(tx, ty) or 1
                nx, ny = (ty / tl, -tx / tl) if ccw else (-ty / tl, tx / tl)       # outward normal
                dot = (nx * lx + ny * ly) / ln
                if dot > -0.1:
                    s = LineString([(a.x - nx * .01, a.y - ny * .01), (a.x + lx * 1.1 + nx * SIDE, a.y + ly * 1.1 + ny * SIDE)]).intersection(face)
                    if s.geom_type == 'LineString' and s.length > 0.06: hach.append([[round(c, 3) for c in s.coords[0]], [round(c, 3) for c in s.coords[-1]]])
                if dot < -0.35: rim.append([round(a.x, 3), round(a.y, 3), round(b.x, 3), round(b.y, 3)])
        nh += len(hach)
        out.append({'ledge': rings(R), 'face': rings(face),
                    'hach': hach, 'rim': rim})
    caps = []
    for (cx, cy), h, arms, turn in PEAKS:
        top = [g for R in levels[::-1] for g in (R.geoms if hasattr(R, 'geoms') else [R]) if g.contains(Point(cx, cy))][0]
        ring = list(top.exterior.coords); creases = []; facets = []
        angs = [turn + j * 2 * math.pi / arms for j in range(arms)]
        hit = []
        for t in angs:
            far = LineString([(cx, cy), (cx + 30 * math.cos(t), cy + 30 * math.sin(t))]).intersection(top.exterior)
            p = min((far.geoms if hasattr(far, 'geoms') else [far]), key=lambda g: Point(cx, cy).distance(g))
            hit.append((p.x, p.y)); creases.append([[cx, cy], [round(p.x, 3), round(p.y, 3)]])
        for j in range(arms):
            t0 = angs[j]; t1 = t0 + 2 * math.pi / arms; tm = (t0 + t1) / 2
            if math.cos(tm) * lx + math.sin(tm) * ly > 0:     # a facet facing away from the light: shaded, clipped to the cap
                w = Polygon([(cx, cy)] + [(cx + 30 * math.cos(t), cy + 30 * math.sin(t)) for t in (t0, (t0 + tm) / 2, tm, (tm + t1) / 2, t1)]).intersection(top)
                facets += [r_ for r_ in rings(w)]
        caps.append({'creases': creases, 'shade': facets})
    # the top two tiers of each peak a little lighter (owner, Oct 22: the peaks stand out a little); a tier shared by several peaks is split
    # between them (nearest peak), so a peak lights only its own top
    from shapely.ops import voronoi_diagram
    from shapely.geometry import MultiPoint
    cells = voronoi_diagram(MultiPoint([c for c, _, _, _ in PEAKS]), envelope=base.envelope.buffer(5)) if len(PEAKS) > 1 else None
    crown = [Polygon(), Polygon()]                 # [the tier below the top, the top tier]
    for (cx, cy), h, arms, turn in PEAKS:
        c = Point(cx, cy); t = max(k for k, R in enumerate(levels) if R.buffer(1e-6).contains(c))
        own = [g for g in cells.geoms if g.contains(c)][0] if cells else base
        for j, k in enumerate((t - 1, t)):
            if k < 1: continue                     # never the base
            piece = [g for g in (levels[k].geoms if hasattr(levels[k], 'geoms') else [levels[k]]) if g.buffer(1e-6).contains(c)][0]
            crown[j] = crown[j].union(piece.intersection(own))
    wild['olmassif'] = wild.get('olmassif', []) + [{'levels': out, 'caps': caps, 'crown': [rings(crown[0].difference(crown[1])), rings(crown[1])]}]

    # the terraces are bare: no plants, drifts or icy patches on them
    # (owner, Oct 22: the ground round it keeps its plants, drifts and ice, as the snow round it: only the terraces are cleared)
    bare = levels[1].buffer(SIDE + math.hypot(*LIGHT) + 0.15) if len(levels) > 1 else Polygon()   # level 1 with its cliff face and a margin
    nf = len(wild['olflora']); wild['olflora'] = [t for t in wild['olflora'] if not bare.contains(Point(t[0], t[1]))]
    S = wild['olsnow']; nd = len(S['drifts']); S['drifts'] = [d for d in S['drifts'] if not bare.buffer(0.1).contains(Point(d[0], d[1]))]
    ni = len(S['ice']); S['ice'] = [p for p in S['ice'] if not bare.intersects(Polygon(p))]

    rooms, _ = maplib.world()
    lev = lambda p: max([k for k, R in enumerate(levels) if R.buffer(1e-6).contains(Point(p))], default=-1)
    named = {n: [lev(pos[v][:2]) for v in pos if int(v) in rooms and rooms[int(v)]['name'] == n and rooms[int(v)]['area'] == 'Otherland']
             for n in names}
    return {title + ' massif (terraces per peak, levels, hachures, cap creases)': ([h for _, h, _, _ in PEAKS], len(levels), nh, sum(len(c['creases']) for c in caps)),
            'lighter top tiers (area below the top, top)': (round(crown[0].difference(crown[1]).area, 1), round(crown[1].area, 1)),
            'level of rooms (0 = base)': named,
            'removed on the terraces (plants, drifts, icy patches)': (nf - len(wild['olflora']), nd - len(S['drifts']), ni - len(S['ice']))}


def LinearRingIsCCW(ring):
    return sum((b[0] - a[0]) * (b[1] + a[1]) for a, b in zip(ring, ring[1:])) < 0


