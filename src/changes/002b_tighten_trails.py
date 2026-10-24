"""Owner, Oct 24: the Forgotten Woods' and the Barren Peaks' trails tightened to their rooms: every shown room of those two areas lies within CAP of
its trail (CAP 0.35, owner, Oct 24: 0.15 and 0.25 were too tight; the old pipeline smoothed each chain of rooms into a curve that passed up to 1.2 rooms off them). Each trail keeps its own smooth
shape and only bends locally towards the rooms it was too far from:
  - a room belongs to its nearest trail (within NEAR) if it isn't hidden in the Barren Peaks + Forgotten Woods editor and one of its exits leads to
    a room also within NEAR of that trail (so stray rooms that aren't on the trail don't pull it);
  - the trail (resampled every STEP) is moved, in up to ITER rounds, by a smooth bump (cosine, half-width SIGMA along the trail, narrower
    where the next room along is close) round each too-far room's own place on the original trail, just enough to bring it to CAP; its two ends never move (trails meet there), the bump easing out over
    END_EASE before them; lightly smoothed where it moved (SMOOTH passes, then pulled back to CAP), then simplified (SIMPLIFY) again;
  - a trail whose end lay on another trail that moved is re-attached to it (its end moved onto the nearest point);
  - trees, tufts and other sprites within CLEAR of the stretches that moved more than MOVED_MIN are cleared (as the new trails).
Runs before the cliff (004), which follows the tightened High-Cliff Trail."""
import json, math, os
from shapely.geometry import LineString, Point
from shapely.strtree import STRtree
from shapely.ops import unary_union
import maplib

HERE = os.path.dirname(os.path.abspath(__file__)); LEG = os.path.join(HERE, '..', 'legacy')
AREAS = ('The Forgotten Woods', 'Barren Peaks of Tahjliera')
CAP, NEAR = 0.35, 1.2
STEP, SIGMA, END_EASE, ITER = 0.1, 0.9, 0.3, 40
SIMPLIFY = 0.012
SMOOTH = 4                                            # smoothing passes over the moved stretches (between pulls)
CLEAR, MOVED_MIN = 0.3, 0.04
SPRITES = ('trees', 'tufts', 'hills', 'thorns', 'brush', 'boulders', 'crags', 'reeds', 'wheattufts')


def _resample(pts, d):
    g = LineString(pts); n = max(2, int(math.ceil(g.length / d)))
    return [list(g.interpolate(g.length * i / n).coords[0]) for i in range(n + 1)]


def apply(town, wild, pos):
    rooms, exits = maplib.world()
    hidden = set(json.load(open(os.path.join(LEG, 'bp_layout_oct24b.json')))['hidden'])
    T = wild.get('track') or {}
    P = {int(k): tuple(p[:2]) for k, p in pos.items()}
    for k, p in T.items():
        if k.startswith('cx'): P.setdefault(int(k[2:]), tuple(p[:2]))
    fw = wild['fwtracks']
    idx = [i for i, l in enumerate(fw) if len(l) > 1]
    G = [LineString([q[:2] for q in fw[i]]) for i in idx]; tree = STRtree(G)
    near = {}                                        # room -> (line, distance)
    for v, p in P.items():
        if v not in rooms or rooms[v]['area'] not in AREAS or v in hidden: continue
        j = tree.nearest(Point(p)); d = G[j].distance(Point(p))
        if d < NEAR: near[v] = (idx[j], d)
    own = {}
    for v, (i, d) in near.items():
        if any(e['to'] in near and near[e['to']][0] == i for e in exits.get(v, [])) or \
           any(u in near and near[u][0] == i for u, l in exits.items() for e in l if e['to'] == v and u != v and False):
            own.setdefault(i, []).append(v)
    before = sorted(d for v, (i, d) in near.items() if i in own and v in own[i])
    joins = []                                       # trail ends lying on another trail (not at its ends): re-attached after it moves
    for j, gj in zip(idx, G):
        for e in (0, -1):
            pe = Point(fw[j][e][:2])
            for k_ in tree.query(pe.buffer(0.03)):
                i2 = idx[k_]
                if i2 != j and G[k_].distance(pe) < 0.02 and min(pe.distance(Point(G[k_].coords[0])), pe.distance(Point(G[k_].coords[-1]))) > 0.02:
                    joins.append((j, e, i2))
    moved_lines, moved_bands, left = 0, [], []
    for i, vs in own.items():
        if not any(near[v][1] > CAP for v in vs): continue
        pts = _resample([q[:2] for q in fw[i]], STEP); L0 = LineString(pts); Ltot = L0.length
        orig = [p[:] for p in pts]
        S = [Ltot * k / (len(pts) - 1) for k in range(len(pts))]
        sr = {v: L0.project(Point(P[v])) for v in vs}                 # each room's place along the trail: fixed, on the original trail
        order = sorted(vs, key=lambda v: sr[v])
        sig = {}
        for n_, v in enumerate(order):                                 # the bump narrows where the next room along is close
            gaps = [abs(sr[v] - sr[u]) for u in order[max(0, n_ - 1):n_ + 2] if u != v]
            sig[v] = max(0.35, min(SIGMA, 0.8 * min(gaps))) if gaps else SIGMA
        def at_s(s_):
            k = min(len(pts) - 2, int(s_ / Ltot * (len(pts) - 1))); t = s_ / Ltot * (len(pts) - 1) - k
            return (pts[k][0] + (pts[k + 1][0] - pts[k][0]) * t, pts[k][1] + (pts[k + 1][1] - pts[k][1]) * t)
        def pull(n_iter):
            for _ in range(n_iter):
                g = LineString(pts); disp = [[0.0, 0.0, 0.0] for _ in pts]; any_far = False
                for v in vs:
                    p = P[v]
                    if g.distance(Point(p)) <= CAP: continue
                    q = at_s(sr[v]); d = math.dist(q, p)
                    if d <= CAP: continue
                    any_far = True; f = (d - CAP + 0.004) / d
                    vx, vy = (p[0] - q[0]) * f, (p[1] - q[1]) * f
                    for k, sk in enumerate(S):
                        u = abs(sk - sr[v]) / sig[v]
                        if u >= 1: continue
                        wgt = 0.5 * (1 + math.cos(math.pi * u)) * min(1.0, sk / END_EASE, (Ltot - sk) / END_EASE)
                        disp[k][0] += wgt * vx; disp[k][1] += wgt * vy; disp[k][2] += wgt
                if not any_far: return
                for k in range(1, len(pts) - 1):
                    n = max(1.0, disp[k][2]); pts[k][0] += disp[k][0] / n; pts[k][1] += disp[k][1] / n
        def smooth(passes):                                            # (a light smoothing of the moved stretches only: no small kinks)
            for _ in range(passes):
                prev = [p[:] for p in pts]
                for k in range(1, len(pts) - 1):
                    if math.dist(prev[k], orig[k]) < 1e-6 and math.dist(prev[k - 1], orig[k - 1]) < 1e-6 and math.dist(prev[k + 1], orig[k + 1]) < 1e-6: continue
                    e = min(1.0, S[k] / END_EASE, (Ltot - S[k]) / END_EASE)
                    for c in (0, 1): pts[k][c] = prev[k][c] + 0.5 * e * ((prev[k - 1][c] + prev[k + 1][c]) / 2 - prev[k][c])
        pull(ITER); smooth(SMOOTH); pull(ITER); smooth(1); pull(ITER)
        g = LineString(pts).simplify(SIMPLIFY)
        new = [[round(x, 3), round(y, 3)] for x, y in g.coords]
        new[0], new[-1] = list(fw[i][0][:2]), list(fw[i][-1][:2])
        moved = [k for k in range(len(pts)) if math.dist(pts[k], orig[k]) > MOVED_MIN]
        if moved:
            moved_lines += 1
            seg = LineString(pts[max(0, moved[0] - 1):moved[-1] + 2]) if len(moved) > 0 else None
            if seg is not None and seg.length > 0: moved_bands.append(seg.buffer(CLEAR))
        fw[i] = new
        gl = LineString([q[:2] for q in new])
        left += [(v, round(gl.distance(Point(P[v])), 2)) for v in vs if gl.distance(Point(P[v])) > CAP + 0.02]
    rejoined = 0
    for j, e, i2 in joins:
        g2 = LineString([q[:2] for q in fw[i2]]); pe = Point(fw[j][e][:2])
        if g2.distance(pe) > 0.005:
            q = g2.interpolate(g2.project(pe)); fw[j][e] = [round(q.x, 3), round(q.y, 3)] + list(fw[j][e][2:]); rejoined += 1
    band = unary_union(moved_bands) if moved_bands else None; gone = {}
    if band is not None:
        for k in SPRITES:
            Lk = wild.get(k) or []; keep = [q for q in Lk if not band.contains(Point(q[:2]))]
            if len(keep) != len(Lk): gone[k] = len(Lk) - len(keep); wild[k] = keep
    after = sorted(LineString([q[:2] for q in fw[i]]).distance(Point(P[v])) for i, vs in own.items() for v in vs)
    q = lambda a, f: round(a[min(len(a) - 1, int(len(a) * f))], 2)
    return {'rooms on these trails': len(after), 'trails tightened': moved_lines, 'trail ends re-attached to a moved trail': (rejoined, len(joins)),
            'room to trail before (median, 90th, max; over CAP)': (q(before, .5), q(before, .9), round(before[-1], 2), sum(d > CAP for d in before)),
            'after': (q(after, .5), q(after, .9), round(after[-1], 2), sum(d > CAP + 0.02 for d in after)),
            'still over CAP (room, distance; ends of trails stay put)': sorted(left, key=lambda t: -t[1])[:20], 'sprites cleared': gone}
