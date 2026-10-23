"""The Azure Sea Coast path redrawn from the owner's Azure Sea Coast editor save of Oct 23 (16:48Z, `legacy/az_layout_oct23.json`; editor data with
the 26 rooms added that day, `legacy/az_editor_edges_oct23.json`). Owner (Oct 23): only the coastal sea path's rooms change, nothing on the
mainland; near Ocean Keep the on-land stream may change.
  - the old path lines go: every type B route (`seawaysfaint`) through a moved or newly shown path room (the long coast line and the Ocean Keep
    stream); the lines through unmoved rooms only (4317 - 14314 - 22557, 4317 to Edo, Edo's own) stay as they are;
  - every exit between two shown path rooms is drawn again (owner, Oct 23): the primary water route (PRIMARY, the chain's western-most rooms) as
    the standard water path, straight room to room in maplib.warpline's bend (joined into lines between junctions, so no seams); every other
    exit as the secondary water path (type C, `olharborways`, as applied/v2.9/003), ending exactly on the primary line where it meets it;
  - the small dashed links to the mainland (`seadash`) follow their moved path room (the mainland end stays);
  - the name 'Azure Sea Coastal Path' moves beside the new path (LABEL; same size and style);
  - deathtrap 14279 (DEATHTRAPS): the primary route goes round it, the room gets a dark red skull and crossbones;
  - the stream by Ocean Keep: sprites within CLEAR of its new line cleared (as az_merge did; owner allowed changes there);
  - land, sea, cliffs and every other mainland drawing untouched."""
import json, math, os
from collections import defaultdict
from maplib import warp, warpline

HERE = os.path.dirname(os.path.abspath(__file__)); LEG = os.path.join(HERE, '..', 'legacy')
LABEL = [42.0, -201.6, 0]                           # [x, y, rotation]: north of the long straight 14315 - 4317 (text 13.7 rooms long, measured once;
                                                    #   0.7 from the path, 2.3 from any room, 3.9 from land, no other name within 20)
STREAM_BOX = (53.0, -38.0, 64.0, -27.0)             # the on-land stream by Ocean Keep (14257 .. 14263): nothing grows within CLEAR of it
CLEAR = 0.35
PRIMARY = [14257, 14293, 14259, 14295, 14261, 14262, 14263, 14264, 14265, 14266, 14267, 14268, 14269, 14270, 14271, 14272, 14273, 14274,
           14275, 14276, 14277, 14278, 14280, 14281, 14282, 14283, 14284, 14285, 14286, 14323, 14322, 14321, 14319, 14318, 14313, 14315, 4317]
                                                    # the primary water route (owner, Oct 23: the chain's western-most rooms, Ocean Keep to 4317;
                                                    #   round the deathtrap through 14280, owner Oct 23)
DEATHTRAPS = [14279]                                # 'Death on the Rocks' (owner, Oct 23: instant death): a dark red skull and crossbones (`deathtraps`, template SKULL; was an X)
STANDARD = [[22557, 14314, 4317], [4317, 5749, 5966, 5967, 5968, 15604, 5969, 5970, 7746]]
                                                    # the standard water paths that were already there (to 4316, to Edo): redrawn when a room on them moves
HWAVE_A, HWAVE_L = 0.05, 1.6                        # the secondary water path (type C, `olharborways`): applied/v2.9/003's wave
SPRITES = ('trees', 'tufts', 'hills', 'thorns', 'peaks', 'boulders', 'reeds', 'wheattufts', 'brush', 'crags', 'ripples')


def _chains(G, pins=()):
    chains = []; seen = set()
    for v in [v for v in sorted(G) if len(G[v]) != 2 or v in pins] + sorted(G):
        for u in sorted(G[v]):
            k = (min(v, u), max(v, u))
            if k in seen: continue
            ch = [v, u]; seen.add(k)
            while len(G[ch[-1]]) == 2 and ch[-1] not in pins:
                nx = [q for q in G[ch[-1]] if q != ch[-2]][0]; k = (min(ch[-1], nx), max(ch[-1], nx))
                if k in seen: break
                seen.add(k); ch.append(nx)
            chains.append(ch)
    return chains


def _wave(pts):                                      # applied/v2.9/003's _wave
    out = [[round(pts[0][0], 3), round(pts[0][1], 3)]]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        L = math.hypot(bx - ax, by - ay); n = max(1, round(L / HWAVE_L)); m = max(4, int(L / 0.06))
        nx, ny = -(by - ay) / L, (bx - ax) / L
        for i in range(1, m + 1):
            t = i / m; o = HWAVE_A * math.sin(2 * math.pi * n * t) * min(1, L / 0.8)
            out.append([round(ax + (bx - ax) * t + nx * o, 3), round(ay + (by - ay) * t + ny * o, 3)])
    return out


def apply(town, wild, pos):
    old = json.load(open(os.path.join(LEG, 'az_layout_final.json'))); new = json.load(open(os.path.join(LEG, 'az_layout_oct23.json')))
    E = json.load(open(os.path.join(LEG, 'az_editor_edges_oct23.json')))
    P0 = dict(zip(old['ids'], zip(old['xs'], old['ys']))); P1 = dict(zip(new['ids'], zip(new['xs'], new['ys'])))
    info = {r['id']: r for r in E['rooms']}; az = {v for v, r in info.items() if r.get('area') == 'AZ'}
    h0, h1 = set(old['hidden']), set(new['hidden'])
    moved = {v for v in az if v in P0 and math.dist(P0[v], P1[v]) > 1e-3}
    changed = moved | {v for v in az if (v not in P0 or v in h0) and v not in h1}     # moved, new, or shown again
    keep = {v for v in az if v not in changed and v not in h1}                         # (unmoved, shown before and now)

    # ---- the old lines through a changed room ----
    oldpts = [warp(*P0[v]) for v in changed if v in P0]
    hit = lambda l: any(math.dist(q[:2], p) < 0.05 for q in l for p in oldpts)
    F = wild['seawaysfaint']; gone = [i for i, l in enumerate(F) if len(l) > 1 and hit(l)]
    gone_pts = sum(len(F[i]) for i in gone)
    wild['seawaysfaint'] = [l for i, l in enumerate(F) if i not in gone]
    kept_pts = [q[:2] for l in wild['seawaysfaint'] for q in l]
    onkept = lambda v: any(math.dist(warp(*P1[v]), q) < 0.4 for q in kept_pts)            # (the kept lines were smoothed: up to 0.3 off a room)
    covered = set()                                                                    # (exits already in the kept lines: both rooms unmoved)
    G = defaultdict(set); n_ex = 0
    for a, b, k in E['edges']:
        if a not in az or b not in az or a in h1 or b in h1 or a == b: continue
        if a in keep and b in keep and onkept(a) and onkept(b): covered.add((a, b)); continue
        G[a].add(b); G[b].add(a); n_ex += 1
    prim = {(min(a, b), max(a, b)) for c in [PRIMARY] + STANDARD for a, b in zip(c, c[1:]) if a in G and b in G[a]} | {(min(a, b), max(a, b)) for a, b in zip(PRIMARY, PRIMARY[1:])}
    assert all(b in G[a] for a, b in prim), [k for k in prim if k[1] not in G[k[0]]]
    GC = defaultdict(set)                                                              # every other exit: the secondary water path
    for a in list(G):
        for b in list(G[a]):
            if (min(a, b), max(a, b)) not in prim: GC[a].add(b); G[a].discard(b)
    G = defaultdict(set, {a: s for a, s in G.items() if s})
    joined = 0
    lines = [warpline([list(P1[v]) for v in ch]) for ch in _chains(G, {v for v in G if v in keep and onkept(v)})]   # (lines end at rooms on a kept line)
    for l in lines:                                                                    # a new line meeting a kept one ends on it (as changes/006, BLEND 0.6)
        for end in (0, -1):
            q = l[end][:2]; near = min(kept_pts, key=lambda k: math.dist(k, q))
            if not 0.01 < math.dist(near, q) < 0.4: continue
            dx, dy = near[0] - q[0], near[1] - q[1]; run = 0.0; prev = None
            for i in (range(len(l)) if end == 0 else range(len(l) - 1, -1, -1)):
                if prev is not None: run += math.dist(l[i][:2], l[prev][:2])
                if run >= 0.6: break
                f = 1 - run / 0.6; l[i] = [round(l[i][0] + dx * f, 3), round(l[i][1] + dy * f, 3)]; prev = i
            joined += 1
    wild['seawaysfaint'] += lines
    Bpts = [q[:2] for l in wild['seawaysfaint'] for q in l]                           # (a secondary path meets a primary one exactly on its line)
    def knot(v):
        if v in G or v in keep: q = warp(*P1[v]); return min(Bpts, key=lambda k: math.dist(k, q))
        return P1[v]
    clines = [_wave([knot(v) for v in ch]) for ch in _chains(GC, set(G) | keep)]
    wild['olharborways'] = list(wild.get('olharborways') or []) + clines

    # ---- nothing grows in the stream (by Ocean Keep only) ----
    x0, y0, x1, y1 = STREAM_BOX
    segs = [(p, q) for l in lines for p, q in zip(l, l[1:]) if x0 <= p[0] <= x1 and y0 <= p[1] <= y1]
    def dseg(c, p, q):
        dx, dy = q[0] - p[0], q[1] - p[1]; L = dx * dx + dy * dy
        t = 0 if L == 0 else max(0, min(1, ((c[0] - p[0]) * dx + (c[1] - p[1]) * dy) / L))
        return math.dist(c, (p[0] + t * dx, p[1] + t * dy))
    cleared = {}
    for k in SPRITES:
        L0 = wild.get(k) or []
        kept = [q for q in L0 if not (x0 <= q[0] <= x1 and y0 <= q[1] <= y1 and any(dseg(q[:2], p, r) < CLEAR for p, r in segs))]
        if len(kept) != len(L0): cleared[k] = len(L0) - len(kept); wild[k] = kept

    # ---- the dashed links to the mainland ----
    D = wild['seadash']; nd = 0
    for a, b, k in E['edges']:
        if (a in az) == (b in az): continue
        v, f = (a, b) if a in az else (b, a)
        if v not in moved and v not in G: continue                                     # (a room whose line was redrawn: its link ends on the new line)
        near = lambda e: math.dist(e, P0[v]) < 0.3 or math.dist(e, warp(*P0[v])) < 0.3
        for l in D:
            for j, o in ((0, -1), (-1, 0)):
                if near(l[j][:2]) and str(f) in pos and math.dist(l[o][:2], pos[str(f)][:2]) < 0.05:
                    q = knot(v); l[j] = [round(q[0], 3), round(q[1], 3)]; nd += 1; break   # (on the primary line, or at the room for a secondary-only room)

    # ---- the name ----
    tag = [t for t in wild['seatags'] if t[2] == 'Azure Sea Coastal Path']
    assert len(tag) == 1
    was = list(tag[0])
    if LABEL: tag[0][0], tag[0][1], tag[0][4] = LABEL

    # ---- deathtraps: a dark red skull and crossbones on the room (its links stay secondary paths) ----
    wild['deathtraps'] = list(wild.get('deathtraps') or []) + [[round(P1[v][0], 3), round(P1[v][1], 3), 0.6] for v in DEATHTRAPS]

    # ---- traced routes (place cards) through a moved room follow it ----
    nr = 0
    def mv(line):
        nonlocal nr
        for q in line:
            for v in moved:
                if math.dist(q[:2], P0[v]) < 0.02: q[0], q[1] = round(P1[v][0], 3), round(P1[v][1], 3); nr += 1; break
    for pl in wild.get('places') or []:
        if pl.get('path'): mv(pl['path'])
        for sg in pl.get('segs') or []: mv(sg)
        for op in pl.get('opts') or []:
            if op.get('path'): mv(op['path'])
            for sg in op.get('segs') or []: mv(sg)

    return {'route points moved with their room': nr, 'old lines removed (lines, points)': (len(gone), gone_pts),
            'path rooms (moved, newly shown, hidden now)': (len(moved), len(changed - moved), len(h1 & az)),
            'primary lines (lines, exits, rooms); secondary (lines, exits, rooms); exits kept in old lines': ((len(lines), len(prim), len(G)), (len(clines), sum(len(s) for s in GC.values()) // 2, len(GC)), len(covered)),
            'new line ends moved onto kept lines': joined, 'dashed links moved': nd, 'sprites cleared off the stream': cleared, 'label': (was[:2], tag[0][:2], tag[0][4])}
