# Starting spots for the layout editors' movable rooms, spread out so they don't land on top of each other (owner, Oct 16: "so many overlapping
# rooms ... a nightmare to drag apart"). Two steps:
#  1. grow out from the rooms already on the map in TinTin exit order: each room goes one step along its exit from the room it was reached from;
#     if that spot is taken (by any room, fixed or movable), the nearest free spot on the same unit lattice round it, preferring spots further
#     along the exit, then spots on the exit's side of the room it came from;
#  2. relax: every exit pulls its two rooms towards one step apart in its direction, every pair of rooms closer than MINSEP is pushed apart
#     (fixed rooms don't move), so loops that don't close in the game stretch a little instead of piling up.
# A room on another level: up = one step north-east, down = one step south-west (as the editors drew them before).
# spread_clear (what the editors use): the area laid out on its own from its first root, then moved as one block next to the map, clear of its rooms.
#   spread(S, links, fixed, roots, step) / spread_clear(...) -> {room: [x, y]};  report(start, fixed, links, step=...) -> numbers to check
#     S: the movable rooms; links(v) -> [(t, (dx, dy, dz)), ...] both ways; fixed: {room: (x, y)} (rooms on the map near these); roots: the fixed
#     rooms to grow from, in order. Rooms that can't be reached from a root (no exit to the rest) are grown from the first free spot east of the rest.
import math
from collections import deque, defaultdict

MINSEP = 1.0          # no two rooms closer than this (the editor flags non-adjacent rooms closer than 0.8)
FREE = 0.95           # step 1: a spot is free when no room is within FREE * MINSEP
FIXSEP = 1.6          # movable rooms keep this far from rooms already on the map (so the new area doesn't thread through them)
LINESEP = 0.45        # step 2: a room is pushed off any exit line (not its own) that passes closer than this

def _vec(d):
    dx, dy, dz = d
    if dz and not (dx or dy): return (1.0, -1.0) if dz > 0 else (-1.0, 1.0)
    return (float(dx), float(dy))

class _Grid:
    def __init__(s, c=1.0): s.c = c; s.g = defaultdict(set); s.p = {}
    def _k(s, p): return (math.floor(p[0] / s.c), math.floor(p[1] / s.c))
    def add(s, v, p):
        if v in s.p: s.g[s._k(s.p[v])].discard(v)
        s.p[v] = (p[0], p[1]); s.g[s._k(p)].add(v)
    def near(s, p, r):
        kx, ky = s._k(p); n = int(math.ceil(r / s.c))
        for i in range(-n, n + 1):
            for j in range(-n, n + 1):
                for v in s.g.get((kx + i, ky + j), ()):
                    q = s.p[v]
                    if math.hypot(q[0] - p[0], q[1] - p[1]) < r: yield v

def _ring_offsets(R=14):
    offs = [(i, j) for i in range(-R, R + 1) for j in range(-R, R + 1) if (i, j) != (0, 0)]
    return sorted(offs, key=lambda o: (math.hypot(*o), o))
_OFFS = _ring_offsets()

def spread_clear(S, links, fixed, roots, step=1.5, R=80, **kw):
    """The area laid out on its own (only the roots it grows from are fixed), then moved as one block to the nearest spot where no room comes
    within FIXSEP of a room already on the map (nearest = shortest total length of its exits to the map)."""
    S = set(S); rt = {r: fixed[r] for r in roots[:1] if r in fixed}                   # one root only: two far-apart roots squeeze the area between them
    pos = spread(S, links, rt, roots[:1], step=step, **kw)
    G = _Grid(2.0)
    for v, p in fixed.items(): G.add(v, p)
    ext = [(v, fixed[t]) for v in S for t, _ in links(v) if t in fixed]
    best = None
    for dx in range(-R, R + 1):
        for dy in range(-R, R + 1):
            cost = sum(math.hypot(pos[v][0] + dx - q[0], pos[v][1] + dy - q[1]) for v, q in ext)
            if best and cost >= best[0]: continue
            if any(True for v in S for _ in G.near((pos[v][0] + dx, pos[v][1] + dy), FIXSEP)): continue
            best = (cost, dx, dy)
    _, dx, dy = best
    return {v: [round(p[0] + dx, 2), round(p[1] + dy, 2)] for v, p in pos.items()}

def spread(S, links, fixed, roots, iters=600, step=1.0):
    S = set(S); G = _Grid(); pos = {}; ms = MINSEP
    _v = lambda d: tuple(c * step for c in _vec(d))
    for v, p in fixed.items(): G.add(v, p)
    free = lambda p: not any(True for _ in G.near(p, FREE * ms)) and not any(o in fixed for o in G.near(p, FIXSEP))
    def place(v, base, d):
        vx, vy = _v(d); tgt = (base[0] + vx, base[1] + vy)
        for k in (1, 2, 3):                                                   # further along the exit
            p = (base[0] + vx * k, base[1] + vy * k)
            if free(p): return p
        best = None
        for ox, oy in _OFFS:                                                  # nearest free lattice spot round the target, on the exit's side
            p = (tgt[0] + ox * step, tgt[1] + oy * step)
            if not free(p): continue
            side = (p[0] - base[0]) * vx + (p[1] - base[1]) * vy
            score = math.hypot(ox, oy) + (0 if side > 0 else 1.5)
            if best is None or score < best[0]: best = (score, p)
            if best[0] <= math.hypot(ox, oy): break
        return best[1]
    def grow(q):
        while q:
            x = q.popleft(); bx = pos.get(x) or fixed[x]
            for t, d in links(x):
                if t in S and t not in pos:
                    pos[t] = list(place(t, bx, d)); G.add(t, pos[t]); q.append(t)
    grow(deque(r for r in roots if r in fixed))
    while S - set(pos):                                                       # pieces with no exit to the rest: east of everything placed
        v = min(S - set(pos)); P = list(pos.values()) or list(fixed.values())
        x0 = max(p[0] for p in P) + 3; y0 = min(p[1] for p in P)
        p = next((x0, y0 + k * step) for k in range(0, 400) if free((x0, y0 + k * step)))
        pos[v] = list(p); G.add(v, p); grow(deque([v]))
    # ---- relax ----
    E = []
    for v in S:
        for t, d in links(v):
            if t in S or t in fixed: E.append((v, t, _v(d)))
    for it in range(iters):
        a = 0.5 * (1 - it / iters) + 0.05
        mv = {v: [0.0, 0.0, 0] for v in S}
        for v, t, (vx, vy) in E:                                              # v -> t should be one step along (vx, vy)
            pv = pos[v]; pt = pos[t] if t in pos else fixed[t]
            rx = pt[0] - pv[0] - vx; ry = pt[1] - pv[1] - vy
            if t in S: mv[v][0] += rx / 2; mv[v][1] += ry / 2; mv[t][0] -= rx / 2; mv[t][1] -= ry / 2; mv[t][2] += 1
            else: mv[v][0] += rx; mv[v][1] += ry
            mv[v][2] += 1
        for v, (dx, dy, n) in mv.items():
            if n: pos[v][0] += a * dx / n; pos[v][1] += a * dy / n
        for v in S: G.add(v, pos[v])
        for _ in range(2):                                                    # push apart (fixed rooms stay)
            for v in S:
                p = pos[v]
                for o in list(G.near(p, FIXSEP)):
                    if o == v: continue
                    sep = ms if o in S else FIXSEP
                    q = pos[o] if o in pos else fixed[o]; dx = p[0] - q[0]; dy = p[1] - q[1]; dist = math.hypot(dx, dy)
                    if dist >= sep: continue
                    if dist < 1e-6: dx, dy, dist = 0.3 + (v % 7) * 0.01, 0.2, 0.36
                    push = (sep - dist) / dist
                    if o in S: p[0] += dx * push / 2; p[1] += dy * push / 2; pos[o][0] -= dx * push / 2; pos[o][1] -= dy * push / 2; G.add(o, pos[o])
                    else: p[0] += dx * push; p[1] += dy * push
                    G.add(v, p)
        if it >= iters // 3 and it % 3 == 0:                                  # rooms off other rooms' exit lines
            for v, t, _ in E:
                if t not in S or v > t: continue
                p, q = pos[v], pos[t]; L = math.hypot(q[0] - p[0], q[1] - p[1])
                if L < 1e-6: continue
                for o in list(G.near(((p[0] + q[0]) / 2, (p[1] + q[1]) / 2), L / 2 + LINESEP)):
                    if o in (v, t) or o not in S: continue
                    c = pos[o]; u = ((c[0] - p[0]) * (q[0] - p[0]) + (c[1] - p[1]) * (q[1] - p[1])) / L ** 2
                    if not 0.05 < u < 0.95: continue
                    fx, fy = p[0] + u * (q[0] - p[0]), p[1] + u * (q[1] - p[1]); dx, dy = c[0] - fx, c[1] - fy; dist = math.hypot(dx, dy)
                    if dist >= LINESEP: continue
                    if dist < 1e-6: dx, dy, dist = -(q[1] - p[1]) / L, (q[0] - p[0]) / L, 1.0
                    push = (LINESEP - dist) / dist
                    c[0] += dx * push * 0.6; c[1] += dy * push * 0.6; G.add(o, c)
                    for e_ in (v, t): pos[e_][0] -= dx * push * 0.2; pos[e_][1] -= dy * push * 0.2; G.add(e_, pos[e_])
    return {v: [round(p[0], 2), round(p[1], 2)] for v, p in pos.items()}

def report(start, fixed, links, adjacent_ok=True, r=0.8, step=1.0):
    """(close pairs: non-adjacent rooms closer than r, at least one movable; exits stretched past 2 steps; exits pointing against their direction;
    exit lines passing within 0.35 of another room)"""
    G = _Grid(); allp = dict(fixed); allp.update(start)
    for v, p in allp.items(): G.add(v, p)
    adj = defaultdict(set); far = 0; wrong = 0
    for v in start:
        for t, d in links(v):
            adj[v].add(t); adj[t].add(v)
            if t in allp:
                vx, vy = _vec(d); p, q = allp[v], allp[t]; dx, dy = q[0] - p[0], q[1] - p[1]
                if math.hypot(dx, dy) > 2 * step: far += 1
                if dx * vx + dy * vy <= 0: wrong += 1
    close = 0
    for v in start:
        for o in G.near(allp[v], r):
            if o != v and (o not in start or o > v) and not (adjacent_ok and o in adj[v]): close += 1
    thru = 0; seen = set()
    for v in start:
        for t, d in links(v):
            k = (min(v, t), max(v, t))
            if t not in allp or k in seen: continue
            seen.add(k); p, q = allp[v], allp[t]; L = math.hypot(q[0] - p[0], q[1] - p[1])
            if L < 1e-6: continue
            m = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
            for o in G.near(m, L / 2 + 0.35):
                if o in (v, t): continue
                c = allp[o]; u = ((c[0] - p[0]) * (q[0] - p[0]) + (c[1] - p[1]) * (q[1] - p[1])) / L ** 2
                if 0 < u < 1 and math.hypot(p[0] + u * (q[0] - p[0]) - c[0], p[1] + u * (q[1] - p[1]) - c[1]) < 0.35: thru += 1; break
    return close, far, wrong, thru
