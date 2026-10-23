"""The Ashen Forest's far east beach from the owner's Ashen editor save of Oct 23 14:30Z (legacy/ashen_layout_oct23.json; the editor's rooms and
exits then: legacy/ashen_editor_edges_oct23.json, with the 65 Azure Sea beach rooms added that day). Owner, Oct 23: ONLY the rooms the owner
moved (and the new rooms) change; every unmoved room is drawn exactly as before (its trail points kept as they were).
  - trails: the old trails (as legacy merge_saved_layout drew them from legacy/ashen_layout_final.json) are kept point for point wherever
    both rooms are unmoved and still joined; every exit that touches a moved or new room is drawn again from the new spots:
    - between Outskirts / forest rooms: an ordinary dirt trail (fwtracks), starting on the old trail's own point at an unmoved room;
    - to or between the Beach / Sand Dunes / Surf rooms (through their spacer rooms): a thin land-coloured line (`ashbeachways`,
      template ASHBEACH; Harbor of Icebergs style, type C, in the dirt colour);
  - the sea pushed east so the shown moved and new rooms stand on land: land added up to SHORE_M east of the easternmost of them, row by
    row, easing back into the old coast; never any land cut. The added land is sand, joined into the beach's own sand shape. geo.water
    loses the same area (its rings redone);
  - 3201, 3202, 3205, 3206 a clearing (Ashen clearing colours), trees/tufts inside it cleared;
  - room_pos: the moved and new rooms; route lines through the moved rooms' old spots follow them (Shadar Logoth)."""
import json, math, os
from collections import defaultdict
import numpy as np
from scipy import ndimage as ndi
from shapely.geometry import Polygon, box, Point, LineString
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__)); LEG = os.path.join(HERE, '..', 'legacy')
BEACH = {'The Beach along the Ashen Forest', 'Miles and Miles of Sand Dunes', 'Wading into the Surf'}
CLEAR_ROOMS = [3201, 3202, 3205, 3206]
CLEAR_FILL, CLEAR_EDGE = '#484C43', '#2A2D27'              # the Ashen Forest's other clearings
SMOOTH_W = 4.0                                              # the coast follows the farthest room within this many rooms (no inlets)
SOUTH = (9.0, 13.4)                                         # the south end: the beach's coast to y 9, then back to the old coast at y 13.4
ROUND_COAST, ROOM_CLEAR = 1.2, 0.6                         # the coast smoothed over this many rooms; never nearer a shown room than this
EASE_R = 3.5                                                # (the old coast's farthest point is looked for this far out)
SHORE_M, EASE = 1.0, 2.0                                    # the coast this far east of the rooms; eased back into the old coast over EASE rooms
NUDGES = {2980: (0, -0.5), 19840: (0, -0.5), 19841: (0, -0.5), 19836: (0, -0.5), 19834: (0, -0.5), 2990: (0, -0.5), 2988: (0, -0.5),
          2987: (0, 0.5), 19838: (0, 0.5), 19833: (0, 0.5), 2986: (0, 0.5), 19839: (0, 0.5), 19835: (0, 0.5), 2985: (0, 0.5)}   # legacy visual_nudges
HWAVE_A, HWAVE_L = 0.05, 1.6                                # type C's slight wave (applied/v2.4/001)
OWNER_THIN = [(3201, 3209), (3215, 3216), (3217, 14369), (14369, 14354), (14354, 14338), (3240, 14365), (14365, 14350), (14350, 14334)]   # owner, Oct 23: thin lines too
THIN_EXTRA = [(2819, 2818)]                                 # owner, Oct 23: 2819 south through its 7 spacer rooms (19858-19854, not placed) to 2818 (Coral Depths, on the map): straight
ROUND_D = 0.3                                              # the redrawn trails' bends: rounded over the last 0.3 rooms either side
SPRITES = ('trees', 'tufts', 'hills', 'thorns', 'brush', 'boulders', 'crags', 'reeds', 'wheattufts', 'peaks')


def _graphs(layout, edges, fixed_from=None):
    pos = {i: (x, y) for i, x, y in zip(layout['ids'], layout['xs'], layout['ys'])}
    for v, (dx, dy) in NUDGES.items():
        if v in pos: pos[v] = (pos[v][0] + dx, pos[v][1] + dy)
    hidden = set(layout.get('hidden', [])); info = {r['id']: r for r in edges['rooms']}
    etr = {v for v, r in info.items() if r.get('area') == 'ETR'}
    G, GR = defaultdict(set), defaultdict(set)
    for a, b, k in edges['edges']:
        if a not in pos or b not in pos or k == 'ud' or a in hidden or b in hidden: continue
        H = GR if (a in etr and b in etr) else G; H[a].add(b); H[b].add(a)
    fx = fixed_from or info
    pinned = {v for v in set(G) | set(GR) if fx.get(v, {}).get('fixed')} | (set(G) & set(GR))
    return pos, hidden, info, G, GR, pinned


def _chains(G, pinned):
    chains = []; seen = set()
    for v in [v for v in G if len(G[v]) != 2 or v in pinned] + list(G):
        for u in G[v]:
            k = (min(v, u), max(v, u))
            if k in seen: continue
            ch = [v, u]; seen.add(k)
            while len(G[ch[-1]]) == 2 and ch[-1] not in pinned:
                nx = [q for q in G[ch[-1]] if q != ch[-2]][0]; k = (min(ch[-1], nx), max(ch[-1], nx))
                if k in seen: break
                seen.add(k); ch.append(nx)
            chains.append(ch)
    return chains


def _line(ch, pos, sigma=0.8, start=None, end=None):
    p = [[pos[v][0], pos[v][1]] for v in ch]
    if start: p[0] = list(start)
    if end: p[-1] = list(end)
    if len(p) >= 4 and sigma:
        xs = ndi.gaussian_filter1d(np.array([q[0] for q in p]), sigma, mode='nearest'); ys = ndi.gaussian_filter1d(np.array([q[1] for q in p]), sigma, mode='nearest')
        q = [[float(a), float(b)] for a, b in zip(xs, ys)]; q[0] = p[0]; q[-1] = p[-1]; p = q
    return [[round(a, 2), round(b, 2)] for a, b in p]


def _soft(line, d=ROUND_D):
    """each inner room flanked by a point d before and after it (at most 0.45 of the segment), so the template's curve runs straight from room
    to room and only rounds the last d/2 into each bend (owner, Oct 23: small rounding, only these trails)"""
    p = [line[0]] + [q for a, q in zip(line, line[1:]) if math.dist(a, q) > 1e-6]
    if len(p) < 3: return p
    out = [p[0]]
    for i in range(1, len(p) - 1):
        a, q, b = p[i - 1], p[i], p[i + 1]
        da = min(d, 0.45 * math.dist(a, q)); db = min(d, 0.45 * math.dist(q, b))
        pa = [q[0] + (a[0] - q[0]) * da / math.dist(a, q), q[1] + (a[1] - q[1]) * da / math.dist(a, q)]
        pb = [q[0] + (b[0] - q[0]) * db / math.dist(q, b), q[1] + (b[1] - q[1]) * db / math.dist(q, b)]
        out += [[round(pa[0], 3), round(pa[1], 3)], q, [round(pb[0], 3), round(pb[1], 3)]]
    return out + [p[-1]]


def _wave(pts):
    pts = [pts[0]] + [q for a, q in zip(pts, pts[1:]) if math.dist(a, q) > 1e-6]
    out = [[round(pts[0][0], 3), round(pts[0][1], 3)]]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        L = math.hypot(bx - ax, by - ay); n = max(1, round(L / HWAVE_L)); m = max(4, int(L / 0.06))
        nx, ny = -(by - ay) / L, (bx - ax) / L
        for i in range(1, m + 1):
            t = i / m; o = HWAVE_A * math.sin(2 * math.pi * n * t) * min(1, L / 0.8)
            out.append([round(ax + (bx - ax) * t + nx * o, 3), round(ay + (by - ay) * t + ny * o, 3)])
    return out


def _parity(rings):
    A = Polygon()
    for p in rings:
        if len(p) > 2: A = A.symmetric_difference(Polygon(p).buffer(0))
    return A


def _rings(S):
    out = []
    for P in getattr(S, 'geoms', [S]):
        if P.is_empty or P.geom_type != 'Polygon': continue
        out.append([[round(x, 3), round(y, 3)] for x, y in list(P.exterior.coords)[:-1]])
        out += [[[round(x, 3), round(y, 3)] for x, y in list(h.coords)[:-1]] for h in P.interiors]
    return out


def _edit(rings, band, fn):
    """the rings touching band, read even-odd, changed by fn (only inside band), written back; the other rings untouched"""
    touch = [i for i, r in enumerate(rings) if len(r) > 2 and Polygon(r).buffer(0).intersects(band)]
    T = _parity([rings[i] for i in touch])
    return [r for i, r in enumerate(rings) if i not in touch] + _rings(fn(T).buffer(0)), len(touch)


def apply(town, wild, pos):
    L0 = json.load(open(os.path.join(LEG, 'ashen_layout_final.json'))); E0 = json.load(open(os.path.join(LEG, 'ashen_editor_edges.json')))
    L1 = json.load(open(os.path.join(LEG, 'ashen_layout_oct23.json'))); E1 = json.load(open(os.path.join(LEG, 'ashen_editor_edges_oct23.json')))
    p0, h0, i0, G0, R0, pin0 = _graphs(L0, E0)
    p1, h1, i1, G1, R1, _ = _graphs(L1, E1)
    old_ch = _chains(G0, pin0)
    old_lines = {id(c): _line(c, p0) for c in old_ch}
    F = wild['fwtracks']; key = lambda l: tuple(map(tuple, l))
    where = defaultdict(list)
    for i, l in enumerate(F): where[key(l)].append(i)
    idx = {}; refit = []
    for c in old_ch:
        k = key(old_lines[id(c)])
        if where.get(k): idx[id(c)] = where[k][0]; continue
        l = old_lines[id(c)]                                             # redrawn by a later step (670 by smr_merge, 14360 by cd_merge): the map's own line
        j = min((i for i, f in enumerate(F) if len(f) == len(l)), key=lambda i: math.dist(F[i][0], l[0]) + math.dist(F[i][-1], l[-1]))
        assert math.dist(F[j][0], l[0]) + math.dist(F[j][-1], l[-1]) < 6, ('old trail not on the map', c[:3])
        idx[id(c)] = j; old_lines[id(c)] = F[j]; refit.append(c[:3])
    moved = {v for v in p1 if v not in p0 or math.dist(p0[v], p1[v]) > 0.004}
    fixed = {v for v, r in i1.items() if r.get('fixed')}
    moved -= fixed
    E_new = {(min(a, b), max(a, b)) for a in G1 for b in G1[a]}
    # ---- the old trails: kept point for point along unmoved, still-joined rooms; cut where a moved room or a gone exit begins ----
    keep_lines, cut, kept_pt = [], 0, {}
    covered = set()
    for c in old_ch:
        line = old_lines[id(c)]; runs = []; cur = [0]
        for j in range(1, len(c)):
            a, b = c[j - 1], c[j]
            ok = a not in moved and b not in moved and (min(a, b), max(a, b)) in E_new
            if ok: cur.append(j)
            else:
                if len(cur) > 1: runs.append(cur)
                cur = [j]
        if len(cur) > 1: runs.append(cur)
        if len(runs) == 1 and len(runs[0]) == len(c): keep_lines.append(None); continue          # untouched
        cut += 1
        for r in runs:
            keep_lines.append(line[r[0]:r[-1] + 1])
            for j in r: kept_pt[c[j]] = line[j]
            for j in range(1, len(r)): covered.add((min(c[r[j - 1]], c[r[j]]), max(c[r[j - 1]], c[r[j]])))
        for j, v in enumerate(c): kept_pt.setdefault(v, line[j])
    untouched = set()
    for c in old_ch:
        line = old_lines[id(c)]
        if all(not (a in moved or b in moved or (min(a, b), max(a, b)) not in E_new) for a, b in zip(c, c[1:])):
            untouched.add(id(c))
            for a, b in zip(c, c[1:]): covered.add((min(a, b), max(a, b)))
            for j, v in enumerate(c): kept_pt.setdefault(v, line[j])
    # ---- the exits drawn again: every shown exit touching a moved or new room ----
    redo = {k for k in E_new if k not in covered and (k[0] in moved or k[1] in moved)}
    nameof = lambda v: (i1.get(v, {}).get('name') or '')
    void = lambda v: bool(i1.get(v, {}).get('void')) or nameof(v) in ('', 'spacer room')
    def end(a, b):                                                       # walk from a away from b through spacer rooms to a real room
        prev, cur, k = b, a, 0
        while void(cur) and len(G1[cur]) == 2 and k < 50:
            nx = [q for q in G1[cur] if q != prev][0]; prev, cur = cur, nx; k += 1
        return cur
    own = {(min(a, b), max(a, b)) for a, b in OWNER_THIN}
    assert own <= redo, sorted(own - redo)
    thin = {k for k in redo if nameof(end(k[0], k[1])) in BEACH or nameof(end(k[1], k[0])) in BEACH} | own
    dirt = redo - thin
    def sub(es):
        G = defaultdict(set)
        for a, b in es: G[a].add(b); G[b].add(a)
        return G
    Gd = sub(dirt); pin = {v for v in Gd if v not in moved}                                    # a new trail starts / stops at unmoved rooms
    new_dirt = []
    for ch in _chains(Gd, pin):
        s = kept_pt.get(ch[0]) if ch[0] not in moved else None; e = kept_pt.get(ch[-1]) if ch[-1] not in moved else None
        new_dirt.append(_soft(_line(ch, p1, sigma=0, start=s, end=e)))          # straight room to room (owner, Oct 23: follow the real exits)
    Gt = sub(thin); new_thin = []
    for ch in _chains(Gt, set()):
        pts = [tuple(kept_pt[v]) if (v not in moved and v in kept_pt) else p1[v] for v in ch]
        new_thin.append(_wave(pts))
    for a, b in THIN_EXTRA: new_thin.append(_wave([p1[a], tuple(pos[str(b)][:2])]))
    # the old trails: untouched ones stay where they are; the cut ones are replaced by their kept runs
    drop = {idx[id(c)] for c in old_ch if id(c) not in untouched}
    wild['fwtracks'] = [l for i, l in enumerate(F) if i not in drop] + [l for l in keep_lines if l] + new_dirt
    wild['ashbeachways'] = new_thin
    # ---- the sea pushed east: land for the shown moved and new rooms ----
    g = wild['geo']; Lold = _parity(g['land'])
    show = [p1[v] for v in moved if v not in h1 and p1[v][0] > 55]
    ys = np.arange(min(q[1] for q in show) - 1.0, max(q[1] for q in show) + 1.0 + 1e-9, 0.05)
    raw = np.array([max([x + SHORE_M for x, y in show if abs(y - yy) <= 1.0] or [np.nan]) for yy in ys])
    ok = ~np.isnan(raw); raw = np.interp(ys, ys[ok], raw[ok])
    # a smooth outer edge, no inlets between rooms (owner, Oct 23): the farthest room within SMOOTH_W rooms, smoothed, never inside a room's margin
    sx = ndi.maximum_filter1d(raw, int(SMOOTH_W / 0.05) + 1)
    for _ in range(4): sx = ndi.gaussian_filter1d(np.maximum(sx, raw), 20, mode='nearest')
    sx = np.maximum(sx, raw - 0.1) + 0.12 * np.sin(0.9 * ys + 0.6)
    def coast(y):                                                        # the old coast's x on this row (east edge of the land, x 55-90)
        L = Lold.intersection(box(55, y - 1e-4, 90, y + 1e-4)); return L.bounds[2] if not L.is_empty else 55.0
    ya, yb = float(ys[0]), float(ys[-1])
    # north: eased in a straight line from the old coast's farthest point within EASE_R rooms (so no notch is left beside it)
    ua = max(np.arange(ya - EASE_R, ya - EASE + 1e-9, 0.05), key=coast); ca = coast(ua)
    prof = [(ca + (sx[0] - ca) * (y - ua) / (ya - ua), y) for y in np.arange(ua, ya, 0.05)] + [(x, y) for x, y in zip(sx, ys) if y <= SOUTH[0]]
    # south (owner, Oct 23): the old coast's right-angled corner at y 12.9 cut off: an S-curve from the beach back to the old coast at SOUTH[1]
    (x0, y0), y3 = prof[-1], SOUTH[1]; x3 = coast(y3); d = (y3 - y0) / 2.4
    for t in np.linspace(0, 1, 61)[1:]:
        c = [(x0, y0), (x0, y0 + d), (x3, y3 - d), (x3, y3)]
        prof.append((sum(w_ * q[0] for w_, q in zip([(1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3], c)),
                     sum(w_ * q[1] for w_, q in zip([(1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3], c))))
    # the whole line smoothed along its length (rounder corners, owner Oct 23), ends pinned; never nearer a shown room than ROOM_CLEAR
    X = np.array(prof); n = len(X); k = max(1, int(ROUND_COAST / 0.05))
    pad = np.vstack([np.repeat(X[:1], 3 * k, 0), X, np.repeat(X[-1:], 3 * k, 0)])
    S_ = np.c_[ndi.gaussian_filter1d(pad[:, 0], k), ndi.gaussian_filter1d(pad[:, 1], k)][3 * k:-3 * k]
    wgt = np.clip(np.minimum(np.arange(n), np.arange(n)[::-1]) / (2 * k), 0, 1)[:, None]          # eased into the old coast at both ends
    X = X * (1 - wgt) + S_ * wgt
    pts = [(float(x), float(y)) for x, y in X]
    for _ in range(3):                                                  # pushed out where it came too near a shown room (along x)
        line = LineString(pts); bad = 0
        for q in show:
            if line.distance(Point(q)) < ROOM_CLEAR:
                pts = [(max(x, q[0] + ROOM_CLEAR + 0.05) if abs(y - q[1]) < ROOM_CLEAR else x, y) for x, y in pts]; bad += 1
        if not bad: break
    west = Polygon([(54, pts[0][1])] + pts + [(54, pts[-1][1])]).buffer(0)
    band = box(54, pts[0][1], 95, pts[-1][1])
    add = west.difference(Lold)                                         # sea that becomes land
    add = unary_union([q for q in getattr(add, 'geoms', [add]) if q.area > 0.02])
    corner = band.intersection(box(54, SOUTH[0] - 3, 95, pts[-1][1])).difference(west).intersection(Lold)   # land corner: only the south corner
    corner = unary_union([q for q in getattr(corner, 'geoms', [corner]) if q.area > 0.002]) if not corner.is_empty else corner
    g['land'], nl = _edit(g['land'], band, lambda T: T.union(add).difference(corner))
    g['water'], nw = _edit(g['water'], band, lambda T: T.difference(add).union(corner))
    g['sand'], ns = _edit(g['sand'], band, lambda T: T.union(add).difference(corner))
    for k_ in ('seafill', 'shallows'):
        if g.get(k_): g[k_], _ = _edit(g[k_], band, lambda T: T.difference(add))
    tints = {}
    if not corner.is_empty:                                                # the ground tints and sprites on the corner corner go with it
        for k_, rs in g.items():
            if k_ in ('land', 'water', 'sand', 'seafill', 'shallows') or not isinstance(rs, list) or not rs or not isinstance(rs[0], list): continue
            if any(len(r) > 2 and Polygon(r).buffer(0).intersects(corner) for r in rs):
                before = _parity(rs).area; g[k_], _ = _edit(rs, corner.buffer(0.01), lambda T: T.difference(corner)); tints[k_] = round(before - _parity(g[k_]).area, 3)
        for k_ in SPRITES + ('hach',):
            if k_ in wild:
                n0 = len(wild[k_]); wild[k_] = [q for q in wild[k_] if not corner.contains(Point(q[0], q[1]))]
                if n0 - len(wild[k_]): tints['sprites ' + k_] = n0 - len(wild[k_])
    lost = Lold.difference(_parity(g['land'])).area
    # ---- the clearing ----
    cp = [p1[v] for v in CLEAR_ROOMS]
    C = box(min(q[0] for q in cp), min(q[1] for q in cp), max(q[0] for q in cp), max(q[1] for q in cp)).buffer(0.85, 8)
    ring = list(C.exterior.coords)[:-1]; cx, cy = C.centroid.x, C.centroid.y
    ring = [[round(cx + (x - cx) * (1 + 0.06 * math.sin(3 * math.atan2(y - cy, x - cx) + 1.3)), 3), round(cy + (y - cy) * (1 + 0.06 * math.sin(3 * math.atan2(y - cy, x - cx) + 1.3)), 3)] for x, y in ring]
    wild['clearings'].append({'polys': [ring], 'fill': CLEAR_FILL, 'edge': CLEAR_EDGE})
    CP = Polygon(ring); gone = defaultdict(int)
    for k in SPRITES:
        if k not in wild: continue
        keep = []
        for q in wild[k]:
            if CP.contains(Point(q[0], q[1])) or add.contains(Point(q[0], q[1])): gone[k] += 1
            else: keep.append(q)
        wild[k] = keep
    # ---- the rooms' spots, and route lines through the moved rooms' old spots ----
    oldat = {v: tuple(pos[str(v)][:2]) for v in moved if str(v) in pos}
    amb = {v for v in oldat if sum(1 for u in oldat if math.dist(oldat[u], oldat[v]) < 0.006) > 1}
    nrt = [0]
    def fix(o):
        if isinstance(o, list):
            if len(o) >= 2 and all(isinstance(t, (int, float)) for t in o[:2]):
                for v, q in oldat.items():
                    if v not in amb and abs(o[0] - q[0]) < 0.006 and abs(o[1] - q[1]) < 0.006: o[0], o[1] = p1[v]; nrt[0] += 1; return
                return
            for x in o: fix(x)
        elif isinstance(o, dict):
            for x in o.values(): fix(x)
    fix(wild['places'])
    for v in moved: pos[str(v)] = [round(p1[v][0], 2), round(p1[v][1], 2)]
    return {'old trails matched to a later redraw': refit, 'rooms moved / new': (len([v for v in moved if v in p0]), len([v for v in moved if v not in p0])),
            'old trails kept as they were / cut to their unmoved runs (pieces kept)': (len(untouched), cut, len([l for l in keep_lines if l])),
            'exits drawn again: dirt trail lines, thin beach lines (exits)': (len(new_dirt), len(new_thin), (len(dirt), len(thin))),
            'land added (sea pushed east), land lost (the south corner cut); rings touched land/water/sand': (round(add.area, 1), round(lost, 3), (nl, nw, ns)), 'cut corner: tints/sprites removed': tints,
            'coast x range': (round(min(x for x, y in pts), 1), round(max(x for x, y in pts), 1)),
            'clearing area, sprites cleared': (round(CP.area, 1), dict(gone)), 'route points moved (ambiguous spots skipped)': (nrt[0], len(amb))}
