"""Owner, Oct 24: the Forgotten Woods' and the Barren Peaks' trails tightened to their rooms: every shown room of those two areas lies within CAP of
its trail (CAP 0.35, owner, Oct 24: 0.15 and 0.25 were too tight; the old pipeline smoothed each chain of rooms into a curve that passed up to 1.2 rooms off them). Each trail keeps its own smooth
shape and only bends locally towards the rooms it was too far from:
  - a room belongs to its nearest trail (within NEAR) if it isn't hidden in the Barren Peaks + Forgotten Woods editor and it is linked by an exit
    (directly or through spacer rooms) to the room just before or just after it along that trail (so rooms of a neighbouring branch don't pull
    it; owner, Oct 24: the first version made trails seem to run between rooms that have no exit between them);
  - the trail (resampled every STEP) is moved, in up to ITER rounds, by a smooth bump (cosine, half-width SIGMA along the trail, narrower
    where the next room along is close) round each too-far room's own place on the original trail, just enough to bring it to CAP; its two ends never move (trails meet there), the bump easing out over
    END_EASE before them; lightly smoothed where it moved (SMOOTH passes, then pulled back to CAP), then simplified (SIMPLIFY) again;
  - a trail whose end lay on another trail that moved is re-attached to it (its end moved onto the nearest point);
  - a trail whose rooms, in the order it passes them, aren't joined room to room by exits (the old smoothing ran some tangles out of order) is
    redrawn along its exits instead, room to room, gently rounded, from its own two ends (owner, Oct 24: paths that shouldn't exist);
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
WIDE = 2.0                                          # (rooms this near a trail may be on its exit chain, when it is redrawn)
STEP, SIGMA, END_EASE, ITER = 0.1, 0.9, 0.3, 40
SIMPLIFY = 0.012
SMOOTH = 4                                            # smoothing passes over the moved stretches (between pulls)
CLEAR, MOVED_MIN = 0.3, 0.04
DEBUG = set()
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
    isspacer = lambda v: v in rooms and bool(rooms[v]['flags'] & 8) and rooms[v]['area'] == ''
    adj = {}
    for u, l in exits.items():
        for e in l: adj.setdefault(u, set()).add(e['to']); adj.setdefault(e['to'], set()).add(u)
    def linked(a, b, depth=12):                      # a - b by an exit, directly or through spacer rooms
        seen = {a}; fr = [a]
        for _ in range(depth):
            nx = []
            for v in fr:
                for t in adj.get(v, ()):
                    if t == b: return True
                    if t not in seen and isspacer(t): seen.add(t); nx.append(t)
            fr = nx
        return False
    cand = {}
    for v, (i, d) in near.items(): cand.setdefault(i, []).append(v)
    own = {}
    for i, vs in list(cand.items()):                       # keep only rooms linked to the room before or after them along the trail
        g = G[idx.index(i)]
        while True:
            order = sorted(vs, key=lambda v: g.project(Point(P[v])))
            keep = [v for n_, v in enumerate(order) if any(linked(v, u) for u in order[max(0, n_ - 1):n_ + 2] if u != v)]
            if len(keep) == len(order): break
            vs = keep
        if vs: own[i] = vs
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
    from collections import deque
    def soft(p, d=0.3):
        if len(p) < 3: return p
        out = [p[0]]
        for k in range(1, len(p) - 1):
            a, q, b = p[k - 1], p[k], p[k + 1]
            da = min(d, 0.45 * math.dist(a, q)); db = min(d, 0.45 * math.dist(q, b))
            out += [[q[0] + (a[0] - q[0]) * da / math.dist(a, q), q[1] + (a[1] - q[1]) * da / math.dist(a, q)], list(q),
                    [q[0] + (b[0] - q[0]) * db / math.dist(q, b), q[1] + (b[1] - q[1]) * db / math.dist(q, b)]]
        return out + [p[-1]]
    rebuilt, single, chains = [], set(), {}
    pool = [v for v in P if v in rooms and v not in hidden]; PT = STRtree([Point(P[v]) for v in pool])
    def rooms_near(g, d): return [pool[k] for k in PT.query(g.buffer(d)) if g.distance(Point(P[pool[k]])) < d]
    for i in idx:                                    # single exits (the two end rooms joined directly): never pulled
        g = G[idx.index(i)]; p0, p1 = Point(g.coords[0]), Point(g.coords[-1])
        ends = [pool[PT.nearest(p)] for p in (p0, p1)]
        if all(p.distance(Point(P[v])) < 0.25 for p, v in zip((p0, p1), ends)) and linked(*ends): single.add(i)
    for i in idx:                                    # a trail whose rooms, in its own order, aren't joined room to room: redrawn along its exits
        g = G[idx.index(i)]
        allv = [v for v in rooms_near(g, 0.4) if rooms[v]['name']]
        vs = [v for v in allv if rooms[v]['area'] in AREAS]
        if len(vs) < 3 or len(vs) < 0.5 * len(allv): continue
        order = sorted(vs, key=lambda v: g.project(Point(P[v])))
        bad = [(a, b) for a, b in zip(order, order[1:]) if not linked(a, b)]
        if not bad: continue
        p0, p1 = Point(g.coords[0]), Point(g.coords[-1])
        a0 = min(allv, key=lambda v: p0.distance(Point(P[v]))); b0 = min(allv, key=lambda v: p1.distance(Point(P[v])))
        if linked(a0, b0): single.add(i); continue    # (a single exit between its two end rooms: left as drawn)
        if DEBUG and i in DEBUG: print('DBG', i, 'bad', bad, 'a0', a0, round(p0.distance(Point(P[a0])), 2), 'b0', b0, round(p1.distance(Point(P[b0])), 2))
        if a0 == b0 or p0.distance(Point(P[a0])) > 1.0 or p1.distance(Point(P[b0])) > 1.0: continue
        wide = rooms_near(g, WIDE)
        import heapq                                 # (the exit path that keeps closest to the old line: rooms far off it cost more)
        cost = {a0: 0.0}; prev = {a0: None}; hq = [(0.0, a0)]; done = set()
        while hq:
            c, v = heapq.heappop(hq)
            if v in done: continue
            done.add(v)
            if v == b0: break
            for u in wide:
                if u in done or not linked(v, u): continue
                cu = c + math.dist(P[v], P[u]) + 4.0 * g.distance(Point(P[u]))
                if cu < cost.get(u, 1e18): cost[u] = cu; prev[u] = v; heapq.heappush(hq, (cu, u))
        if b0 not in prev:
            if DEBUG and i in DEBUG: print('DBG', i, 'no chain', sorted(prev))
            continue
        ch = []; v = b0
        while v is not None: ch.append(v); v = prev[v]
        ch = ch[::-1]
        if len(ch) < 3: continue
        pts = [list(P[v]) for v in ch]
        if p0.distance(Point(pts[0])) > 0.02: pts = [list(p0.coords[0])] + pts
        if p1.distance(Point(pts[-1])) > 0.02: pts = pts + [list(p1.coords[0])]
        new = [[round(x, 3), round(y, 3)] for x, y in soft(pts)]
        moved_bands.append(LineString(new).buffer(CLEAR)); moved_lines += 1
        fw[i] = new; rebuilt.append((i, ch[0], ch[-1], len(ch), len(bad))); chains[i] = ch; own.pop(i, None)
    for i, vs in own.items():
        if i in single or not any(near[v][1] > CAP for v in vs): continue
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
            rm = min(chains.get(i2, []), key=lambda v: pe.distance(Point(P[v])), default=None)   # (a redrawn trail: join at its room, if one is close)
            if rm is not None and pe.distance(Point(P[rm])) < 0.8: q = Point(P[rm])
            else: q = g2.interpolate(g2.project(pe))
            fw[j][e] = [round(q.x, 3), round(q.y, 3)] + list(fw[j][e][2:]); rejoined += 1
    band = unary_union(moved_bands) if moved_bands else None; gone = {}
    if band is not None:
        for k in SPRITES:
            Lk = wild.get(k) or []; keep = [q for q in Lk if not band.contains(Point(q[:2]))]
            if len(keep) != len(Lk): gone[k] = len(Lk) - len(keep); wild[k] = keep
    after = sorted(LineString([q[:2] for q in fw[i]]).distance(Point(P[v])) for i, vs in own.items() for v in vs)
    q = lambda a, f: round(a[min(len(a) - 1, int(len(a) * f))], 2)
    return {'rooms on these trails': len(after), 'trails tightened': moved_lines, 'trails redrawn along their exits (line, from, to, rooms, breaks)': rebuilt, 'single-exit trails left as drawn': len(single), 'trail ends re-attached to a moved trail': (rejoined, len(joins)),
            'room to trail before (median, 90th, max; over CAP)': (q(before, .5), q(before, .9), round(before[-1], 2), sum(d > CAP for d in before)),
            'after': (q(after, .5), q(after, .9), round(after[-1], 2), sum(d > CAP + 0.02 for d in after)),
            'still over CAP (room, distance; ends of trails stay put)': sorted(left, key=lambda t: -t[1])[:20], 'sprites cleared': gone}
