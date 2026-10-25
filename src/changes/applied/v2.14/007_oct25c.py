"""Owner, Oct 25 (third set):
  - The bare patch in the Forest of Tears by Abishai's Morgue filled: the small deep-forest piece inside the big one there (geo.deep,
    x -42.28..-39.83, y 5.52..8.0) cut a hole in it (evenodd), so it is removed; trees added in the hole to the density around it
    (own random.Random; none under the mausoleum or on the marker).
  - The Mire trails on the way to Tribal Swamplands redrawn from the Mire editor save (legacy/mi_layout_final.json, the save on file,
    Oct 18 15:43Z): the trail cutting from 8355 straight to 8362 and the one stopping short of 8357 are gone; every exit between the shown
    rooms of that corner (8350-8359, 8362) is a straight Woods-style trail, room to room. The stub from 8055 to 8355 stays. The trails stop
    at the edge of the clearing there (smrpatch, x -90.06..-86.22, y 117.44..120.56), as at every clearing (owner, Oct 25)."""
import json, math, os, random, maplib

SECTION = {8350, 8351, 8352, 8353, 8354, 8355, 8356, 8357, 8358, 8359, 8362}
HOLE = (-42.28, -39.83, 5.52, 8.0)
MAUS = (-43.9, -41.7, 6.5, 8.5); MARK = (-41.05, 7.64)


def inside(p, poly):
    x, y = p; c = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1): c = not c
    return c


def line(a, b, step=0.32):
    n = max(1, round(math.dist(a, b) / step))
    return [[round(a[0] + (b[0] - a[0]) * i / n, 2), round(a[1] + (b[1] - a[1]) * i / n, 2)] for i in range(n + 1)]


def apply(town, wild, pos):
    rep = {}
    # the forest hole
    deep = wild['geo']['deep']
    bb = lambda p: (min(q[0] for q in p), max(q[0] for q in p), min(q[1] for q in p), max(q[1] for q in p))
    hole = [i for i, p in enumerate(deep) if all(abs(u - v) < 0.01 for u, v in zip(bb(p), HOLE))]
    assert len(hole) == 1, hole
    poly = [q[:2] for q in deep.pop(hole[0])]
    trees = wild['trees']
    around = [t for t in trees if HOLE[0] - 3 <= t[0] <= HOLE[1] + 3 and HOLE[2] - 3 <= t[1] <= HOLE[3] + 3 and not inside(t[:2], poly)]
    area = abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]))) / 2
    dens = len(around) / ((HOLE[1] - HOLE[0] + 6) * (HOLE[3] - HOLE[2] + 6) - area)
    have = [t for t in trees if inside(t[:2], poly)]
    rnd = random.Random(7807); new = []
    want = round(dens * area) - len(have)
    for _ in range(4000):
        if len(new) >= want: break
        x, y = rnd.uniform(HOLE[0], HOLE[1]), rnd.uniform(HOLE[2], HOLE[3])
        if not inside((x, y), poly) or (MAUS[0] <= x <= MAUS[1] and MAUS[2] <= y <= MAUS[3]) or math.dist((x, y), MARK) < 0.6: continue
        if any(math.dist((x, y), t[:2]) < 0.5 for t in trees + new): continue
        src = rnd.choice(around)
        new.append([round(x, 3), round(y, 3), round(rnd.uniform(0.88, 1.15), 2), src[3], rnd.randint(0, 2)])
    trees.extend(new)
    rep['forest hole'] = {'deep piece removed': hole[0], 'area': round(area, 2), 'trees there before': len(have), 'added': len(new), 'density around': round(dens, 2)}
    # the Mire trails
    rooms, exits = maplib.world()
    mi = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'legacy', 'mi_layout_final.json')))
    sv = dict(zip(mi['ids'], zip(mi['xs'], mi['ys']))); assert not SECTION & set(mi['hidden'])
    for v in SECTION: assert math.dist(sv[v], pos[str(v)]) < 1e-6, v
    tr = wild['fwtracks']
    end = lambda t, a, b: math.dist(t[0], a) < 0.05 and math.dist(t[-1], b) < 0.5
    bad = [i for i, t in enumerate(tr) if end(t, sv[8355], sv[8362]) or end(t, sv[8355], sv[8357])]
    assert len(bad) == 2, bad
    pairs = sorted({tuple(sorted((v, e['to']))) for v in SECTION for e in exits.get(v, []) if e['to'] in SECTION and e['to'] != v})
    cl = [p for p in wild['smrpatch'] if -90.1 < min(q[0] for q in p) < -90 and 120.5 < max(q[1] for q in p) < 120.6]   # the clearing north of
    assert len(cl) == 1                                                                         # Tribal Swamplands (x -90.06..-86.22, y 117.44..120.56)
    poly = [q[:2] for q in cl[0]]
    def clip(ln):                                   # trails stop at a clearing's edge, as everywhere else (owner, Oct 25: none under it)
        fine = line(ln[0], ln[-1], 0.04); runs, cur = [], []
        for q in fine:
            if inside(q, poly):
                if len(cur) > 1: runs.append(cur)
                cur = []
            else: cur.append(q)
        if len(cur) > 1: runs.append(cur)
        return [line(r[0], r[-1]) for r in runs if math.dist(r[0], r[-1]) > 0.1]
    lines = [c for a, b in pairs for c in clip(line(sv[a], sv[b]))]
    for i, ln in zip(bad, lines[:2]): tr[i] = ln                 # (in place, so no other trail's index moves)
    tr.extend(lines[2:])
    rep['mire trails'] = {'removed': bad, 'exits': len(pairs), 'drawn pieces (cut at the clearing)': len(lines)}
    return rep
