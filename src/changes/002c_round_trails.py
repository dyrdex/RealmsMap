"""Owner, Oct 24: the Woods' trails drawn room to room (2.12's Knights of the Round, 2.13's coast trail and the trails 002b redrew or tightened)
had hard angles: they were rounded over only 0.3 rooms either side of a bend (the page draws a trail as a curve that cuts each corner between
the midpoints of its stretches, so closely spaced points round very little). They are rounded over ROUND rooms instead (owner: 0.6):
  - which trails: every Woods-style trail (fwtracks) near a Forgotten Woods, Barren Peaks, Knights of the Round or Blood Sea room that is not
    one of the base map's own (old pipeline) trails, or that carries the old 0.3 rounding (a point FLANK from the bends on both sides);
  - each is reduced to its corners (SIMPLIFY), then every corner gets a point ROUND before and after it (never more than 45% of a stretch),
    so the drawn curve rounds it over about that distance; the ends never move;
  - the drawn curve (sampled as the page draws it) must keep every room it passed within CAP (or no further than it was): a corner that
    would carry it further off is rounded less (ROUND_STEP at a time, down to 0.3);
  - trail ends that lay on a rounded trail are re-attached to it.
Runs before the cliff (004), which follows the High-Cliff Trail as rounded here."""
import json, math, os
from shapely.geometry import LineString, Point
from shapely.strtree import STRtree
import maplib

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND, ROUND_STEP, ROUND_MIN = 0.6, 0.15, 0.3
CAP, SIMPLIFY, FLANK = 0.35, 0.03, 0.3
AREAS = ('The Forgotten Woods', 'Barren Peaks of Tahjliera', 'Knights of the Round', 'The Blood Sea')


def _drawn(p, n=8):
    """the curve the page draws (template curve()): quadratic pieces through the stretches' midpoints, each point a control point"""
    if len(p) < 3: return [tuple(q) for q in p]
    out = [tuple(p[0])]; cur = p[0]
    for i in range(1, len(p) - 1):
        c = p[i]; m = ((p[i][0] + p[i + 1][0]) / 2, (p[i][1] + p[i + 1][1]) / 2)
        for k in range(1, n + 1):
            t = k / n; a, b, d = (1 - t) ** 2, 2 * (1 - t) * t, t * t
            out.append((a * cur[0] + b * c[0] + d * m[0], a * cur[1] + b * c[1] + d * m[1]))
        cur = m
    out.append(tuple(p[-1]))
    return out


def _soften(key, ds):
    out = [list(key[0])]
    for k in range(1, len(key) - 1):
        a, q, b = key[k - 1], key[k], key[k + 1]
        la, lb = math.dist(a, q), math.dist(q, b)
        if la < 1e-6 or lb < 1e-6: continue
        da, db = min(ds[k], 0.45 * la), min(ds[k], 0.45 * lb)
        out += [[q[0] + (a[0] - q[0]) * da / la, q[1] + (a[1] - q[1]) * da / la], list(q),
                [q[0] + (b[0] - q[0]) * db / lb, q[1] + (b[1] - q[1]) * db / lb]]
    return out + [list(key[-1])]


def _has_flank(l):
    for k in range(1, len(l) - 1):
        if abs(math.dist(l[k - 1][:2], l[k][:2]) - FLANK) < 0.01 and abs(math.dist(l[k][:2], l[k + 1][:2]) - FLANK) < 0.01: return True
    return False


def apply(town, wild, pos):
    rooms, _ = maplib.world()
    base = json.load(open(os.path.join(HERE, '..', 'base', 'map.json')))['wild']['fwtracks']
    base_set = {tuple(tuple(round(c, 3) for c in q[:2]) for q in l) for l in base}
    P = {int(k): tuple(p[:2]) for k, p in pos.items()}
    for k, p in (wild.get('track') or {}).items():
        if k.startswith('cx'): P.setdefault(int(k[2:]), tuple(p[:2]))
    pool = [v for v in P if v in rooms and rooms[v]['name']]; PT = STRtree([Point(P[v]) for v in pool])
    near_area = lambda g: [pool[k] for k in PT.query(g.buffer(0.4)) if g.distance(Point(P[pool[k]])) < 0.4]
    fw = wild['fwtracks']
    ids = [i for i, l in enumerate(fw) if len(l) > 2]
    G = {i: LineString([q[:2] for q in fw[i]]) for i in ids}
    todo = []
    for i in ids:
        vs = near_area(G[i])
        if not any(rooms[v]['area'] in AREAS for v in vs): continue
        sig = tuple(tuple(round(c, 3) for c in q[:2]) for q in fw[i])
        if sig not in base_set or _has_flank(fw[i]): todo.append((i, vs))
    # trail ends lying on a trail that will be rounded (not at its own ends): re-attached afterwards
    allg = [(j, LineString([q[:2] for q in l])) for j, l in enumerate(fw) if len(l) > 1]; T = STRtree([g for _, g in allg])
    rset = {i for i, _ in todo}; joins = []
    for j, gj in allg:
        for e in (0, -1):
            pe = Point(fw[j][e][:2])
            for k in T.query(pe.buffer(0.03)):
                i2, g2 = allg[k]
                if i2 != j and i2 in rset and g2.distance(pe) < 0.02 and min(pe.distance(Point(g2.coords[0])), pe.distance(Point(g2.coords[-1]))) > 0.02:
                    joins.append((j, e, i2))
    reduced, worst = 0, 0.0
    for i, vs in todo:
        old = [q[:2] for q in fw[i]]
        before = {v: LineString(_drawn(old)).distance(Point(P[v])) for v in vs}
        key = [list(c) for c in LineString(old).simplify(SIMPLIFY).coords]
        key[0], key[-1] = list(old[0]), list(old[-1])
        ds = [ROUND] * len(key)
        for _ in range(12):
            new = _soften(key, ds); cur = LineString(_drawn(new)); bad = False
            for v in vs:
                d = cur.distance(Point(P[v]))
                if d > max(CAP, before[v] + 0.02):
                    k = min(range(1, len(key) - 1), key=lambda k_: math.dist(key[k_], P[v])) if len(key) > 2 else None
                    if k is not None and ds[k] > ROUND_MIN: ds[k] = max(ROUND_MIN, ds[k] - ROUND_STEP); bad = True; reduced += 1
            if not bad: break
        fw[i] = [[round(x, 3), round(y, 3)] for x, y in new]
        cur = LineString(_drawn(fw[i]))
        worst = max([worst] + [cur.distance(Point(P[v])) - before[v] for v in vs])
    rejoined = 0
    for j, e, i2 in joins:
        cur = LineString(_drawn(fw[i2])); pe = Point(fw[j][e][:2])
        if cur.distance(pe) > 0.01:
            q = cur.interpolate(cur.project(pe)); fw[j][e] = [round(q.x, 3), round(q.y, 3)] + list(fw[j][e][2:]); rejoined += 1
    return {'trails rounded': len(todo), 'corners rounded less (to keep a room within CAP)': reduced,
            'largest move away from a room (drawn curve)': round(worst, 3), 'trail ends re-attached': (rejoined, len(joins))}
