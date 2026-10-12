"""The Ashen Forest, east of Darkhaven.

It is laid out from your TinTin map by its own exits (all 320 rooms, following spacer chains), then stretched smoothly so that the
rooms that touch Darkhaven, the Shadow Grove and the Forgotten Woods land exactly on those anchor points, wherever the finished map
has put them. It is painted on the finished map: land, a grey ash tint, bare grey trees mixed with dark pines, and trails drawn from
every real exit.
"""
import os, math, random
import numpy as np
from collections import defaultdict, deque, Counter
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from scipy.interpolate import RBFInterpolator
from scipy.spatial import cKDTree
from matplotlib.path import Path
import arrange_apply as AA
import gap_fill as GF

X0, Y0, W, H, R8 = GF.X0, GF.Y0, GF.W, GF.H, GF.R8
DV = {1: (0, -1, 0), 2: (1, 0, 0), 4: (0, 1, 0), 8: (-1, 0, 0), 3: (1, -1, 0), 9: (-1, -1, 0), 6: (1, 1, 0), 12: (-1, 1, 0), 16: (0, 0, 1), 32: (0, 0, -1)}
WEST_DOOR = 1234                      # "Before the Ashen Forest", the forest's door on the Darkhaven side


def _world():
    ns = {}
    for p in ('parse_world.py', '/home/claude/parse_world.py'):
        if os.path.exists(p): exec(open(p).read(), ns); break
    return ns['rooms'], ns['exits']


def layout():
    rooms, exits = _world()
    A = {v for v, r in rooms.items() if r['area'] == 'The Ashen Forest'}
    spacer = lambda v: bool(rooms[v]['flags'] & 8) and rooms[v]['area'] == ''
    rev = defaultdict(list)
    for v, l in exits.items():
        for e in l: rev[e['to']].append(v)
    S = set(A); dq = deque(A)
    while dq:                                                    # spacer rooms that hang off the forest, however long the chain
        v = dq.popleft()
        for t in [e['to'] for e in exits.get(v, [])] + rev[v]:
            if t not in S and spacer(t): S.add(t); dq.append(t)
    nb = defaultdict(list); edges = []
    for v in S:
        for e in exits.get(v, []):
            t = e['to']
            if t in S and e['dir'] in DV:
                d = DV[e['dir']]; edges.append((v, t, d)); nb[v].append((t, d)); nb[t].append((v, (-d[0], -d[1], -d[2])))
    pos = {WEST_DOOR: (0, 0, 0)}; dq = deque([WEST_DOOR])
    while dq:
        v = dq.popleft()
        for t, d in nb[v]:
            if t not in pos: pos[t] = (pos[v][0] + d[0], pos[v][1] + d[1], pos[v][2] + d[2]); dq.append(t)
    return rooms, A, S, pos, edges


def stitch(w):
    """The forest's own layout, stretched so that every room touching an already-mapped room lands on its anchor."""
    rooms, A, S, pos, edges = layout()
    # ---- the stitch: every room that touches an already-mapped room has to land on its anchor ----
    tr = w.get('track') or {}
    want = defaultdict(list)
    for i, a in enumerate(w['ashlinks']):
        if a['ash'] in pos: want[a['ash']].append(tr[f'ash{i}'])
    ids = [v for v in want]
    Sx = np.array([pos[v][:2] for v in ids], float); Dx = np.array([np.mean(want[v], axis=0) for v in ids], float)
    M = np.linalg.lstsq(np.column_stack([Sx, np.ones(len(Sx))]), Dx, rcond=None)[0]
    allv = [v for v in pos]
    P0 = np.array([pos[v][:2] for v in allv], float)
    gx = np.linspace(P0[:, 0].min() - 4, P0[:, 0].max() + 4, 6); gy = np.linspace(P0[:, 1].min() - 4, P0[:, 1].max() + 4, 7)
    G = np.array([[x, y] for x in gx for y in gy]); Gd = np.column_stack([G, np.ones(len(G))]) @ M
    src = np.vstack([Sx, G]); dst = np.vstack([Dx, Gd]); base = lambda P: np.column_stack([P, np.ones(len(P))]) @ M
    warp = None
    for sm in (0.5, 2.0, 6.0, 15.0):                                     # the least bending that keeps the forest from folding
        tps = RBFInterpolator(src, dst - base(src), kernel='thin_plate_spline', smoothing=sm)
        f = lambda P, tps=tps: base(P) + tps(P)
        h = 0.05; d = []
        for x, y in P0[::3]:
            J = np.column_stack([(f(np.array([[x + h, y]])) - f(np.array([[x - h, y]])))[0] / (2 * h), (f(np.array([[x, y + h]])) - f(np.array([[x, y - h]])))[0] / (2 * h)]); d.append(np.linalg.det(J))
        if min(d) > 0.2: warp = f; used = sm; break
    if warp is None: warp = base; used = None
    WP = warp(P0); wp = {v: (float(p[0]), float(p[1])) for v, p in zip(allv, WP)}
    err = np.hypot(*(warp(Sx) - Dx).T)
    return dict(rooms=rooms, A=A, S=S, pos=pos, edges=edges, wp=wp, err=err, used=used, want=want, Sx=Sx, Dx=Dx, warp=warp)


def _paint(w, pts, trails, rng, seed):
    """Land around every room and trail (closed up, with a wandering edge), the grey ash tint, and bare grey trees mixed with dark pines."""
    # ---- the ground: land around every room and trail, closed up, with a wandering edge ----
    lo, hi = pts.min(0) - 9, pts.max(0) + 9
    ix0, ix1 = int((lo[0] - X0) * R8), int((hi[0] - X0) * R8); iy0, iy1 = int((lo[1] - Y0) * R8), int((hi[1] - Y0) * R8)
    sub = (slice(iy0, iy1), slice(ix0, ix1)); hh, ww = iy1 - iy0, ix1 - ix0
    img = Image.new('L', (ww, hh), 0); dr = ImageDraw.Draw(img)
    px = lambda x, y: ((x - X0) * R8 - ix0, (y - Y0) * R8 - iy0)
    Rd = 3.0
    for x, y in pts: cx, cy = px(x, y); dr.ellipse([cx - Rd * R8, cy - Rd * R8, cx + Rd * R8, cy + Rd * R8], fill=255)
    for t in trails:
        if len(t) > 1: dr.line([px(*q) for q in t], fill=255, width=int(2 * Rd * R8), joint='curve')
    m0 = np.array(img) > 0
    Rc = 3.5 * R8
    m = ndi.distance_transform_edt(~m0) <= Rc                                         # close the gaps between rooms (by distance)
    m = ndi.distance_transform_edt(m) > Rc
    m = m | m0
    m = ndi.binary_fill_holes(m)
    noise = ndi.gaussian_filter(np.random.default_rng(seed).normal(size=m.shape), 2.4 * R8); n01 = (noise - noise.min()) / (noise.max() - noise.min())
    soft = ndi.gaussian_filter(m.astype(float), 1.3 * R8)
    mask_sub = soft > (0.5 + 0.22 * (n01 - 0.5) * 2)
    mask = np.zeros((H, W), bool); mask[sub] = mask_sub
    land = AA._raster(w['geo']['land'], X0, Y0, W, H)
    water = AA._raster(w['geo']['water'], X0, Y0, W, H)
    mask &= ~water                                                                    # never over the lake
    new_land = land | mask
    holes = ndi.binary_fill_holes(new_land) & ~new_land & ~water
    lab, nh = ndi.label(holes); fills = []
    for k in range(1, nh + 1):
        hm = lab == k
        if hm.sum() / R8 / R8 < 400:
            fills.append(('a pocket of sea beside the forest', ndi.binary_dilation(hm, iterations=2) & ~water)); new_land |= hm
    if fills:
        GF._populate(w, fills, new_land & ~water & ~np.any([f[1] for f in fills], axis=0), rng)
    w['geo']['land'] = AA._contours(new_land, X0, Y0)
    tint = ndi.binary_erosion(mask, iterations=int(0.9 * R8))
    w['geo']['ash'] = AA._contours(tint, X0, Y0, sigma=2.0)

    # ---- bare grey trees mixed with dark pines, in the same thick way as the other woods ----
    lines = []
    for k in ('fwtracks', 'swtracks', 'ashtracks', 'etrtracks'): lines += w.get(k, [])
    lines += [w['road'], w['southpath'], w['link']] + list(w['ring'])
    pp = []
    for ln in lines:
        for a, b in zip(ln[:-1], ln[1:]):
            n = max(1, int(math.dist(a, b) / 0.25)); pp += [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n + 1)]
    ptree = cKDTree(np.array(pp))
    exist = np.array([[t[0], t[1]] for t in w['trees']]); etree = cKDTree(exist)
    inner = ndi.binary_erosion(mask, iterations=int(0.3 * R8)) & (GF.WX > 10.8)
    ys, xs = np.nonzero(inner)
    area = float(inner.sum()) / R8 / R8
    want_n = int(area * 1.05); newt = []; placed_pts = []; tries = 0
    mix = ['a'] * 45 + ['d'] * 35 + ['w'] * 20
    while len(newt) < want_n and tries < want_n * 14:
        tries += 1
        j = rng.randrange(len(xs)); x = xs[j] / R8 + X0 + rng.uniform(0, 1 / R8); y = ys[j] / R8 + Y0 + rng.uniform(0, 1 / R8)
        if ptree.query([x, y])[0] < 0.55 or etree.query([x, y])[0] < 0.5: continue
        if placed_pts and np.min(np.hypot(*(np.array(placed_pts) - [x, y]).T)) < 0.5: continue
        ty = rng.choice(mix)
        newt.append([round(x, 3), round(y, 3), round(rng.uniform(0.85, 1.15), 3), ty, rng.randint(0, 2)]); placed_pts.append((x, y))
    newt = [q for q in newt if q[3] != 'a']                       # the little bare white-grey trees are left out (everything else is placed exactly as before)
    w['trees'] = list(w['trees']) + newt
    pts_ = np.array([q for poly in w['geo']['land'] for q in poly])
    w['bounds'] = [int(pts_[:, 0].min()) - 3, int(pts_[:, 1].min()) - 3, int(pts_[:, 0].max()) + 3, int(pts_[:, 1].max()) + 3]
    return len(newt), float((mask & ~land).sum()) / R8 / R8


def add_ashen_forest(w, seed=77, override=None):
    rng = random.Random(seed)
    if os.environ.get('ASHEN_DUMP'):                                   # (used once to build the editor's backdrop)
        import json as _j; _j.dump(w, open(os.environ['ASHEN_DUMP'], 'w'))
    st = stitch(w); rooms, A, S, pos, edges, wp, err, used = (st[k] for k in ('rooms', 'A', 'S', 'pos', 'edges', 'wp', 'err', 'used'))
    tr = w.get('track') or {}
    if override:                                                       # positions you set by hand in the editor win over the automatic stitch
        for v, p in override.items():
            if v in wp: wp[v] = (float(p[0]), float(p[1]))

    # ---- the rooms and trails that are on the surface ----
    surface = lambda v: v in A and rooms[v]['terrain'] not in ('Underground', 'Inside', 'Swimming', 'Water')
    node = lambda v: v in wp and (surface(v) or (v in S and v not in A))
    E = {}
    for v, t, d in edges:
        if d[2] != 0 or not (node(v) and node(t)): continue
        k = (min(v, t), max(v, t))
        E.setdefault(k, (v, t))
    # in open stretches a diagonal that two straight links already cover is left out
    dirs = {}
    for v, t, d in edges: dirs.setdefault((min(v, t), max(v, t)), []).append(d)
    diag = {k for k in E if all(abs(d[0]) + abs(d[1]) == 2 for d in dirs[k])}
    orth = defaultdict(set)
    for (a, b) in E:
        if (a, b) not in diag: orth[a].add(b); orth[b].add(a)
    E = {k: v for k, v in E.items() if not (k in diag and orth[k[0]] & orth[k[1]])}
    long_ = [k for k in E if math.dist(wp[k[0]], wp[k[1]]) > 10]
    E = {k: v for k, v in E.items() if k not in long_}
    import heapq
    adjw = defaultdict(list)
    for a, b in E: dd = math.dist(wp[a], wp[b]) * (1.0 + (0.15 if (a, b) in diag else 0)); adjw[a].append((b, dd)); adjw[b].append((a, dd))
    keep = set(); done = set()
    for root in [WEST_DOOR] + sorted(adjw, key=lambda v: wp[v][0]):         # one tree per connected piece, rooted at the west door when it is in the piece
        if root in done or root not in adjw: continue
        dist = {root: 0.0}; prev = {}; pq = [(0.0, root)]
        while pq:
            d0, v = heapq.heappop(pq)
            if d0 > dist.get(v, 1e18): continue
            for u, dd in adjw[v]:
                nd_ = d0 + dd
                if nd_ < dist.get(u, 1e18): dist[u] = nd_; prev[u] = v; heapq.heappush(pq, (nd_, u))
        for u, v in prev.items(): keep.add((min(u, v), max(u, v)))
        done |= set(dist)
    E = {k: v for k, v in E.items() if k in keep}
    G_ = defaultdict(set)
    for a, b in E: G_[a].add(b); G_[b].add(a)
    chains = []; seen = set()
    for v in [v for v in G_ if len(G_[v]) != 2] + list(G_):
        for u in G_[v]:
            k = (min(v, u), max(v, u))
            if k in seen: continue
            ch = [v, u]; seen.add(k)
            while len(G_[ch[-1]]) == 2:
                nx = [q for q in G_[ch[-1]] if q != ch[-2]][0]; k = (min(ch[-1], nx), max(ch[-1], nx))
                if k in seen: break
                seen.add(k); ch.append(nx)
            chains.append(ch)
    trails = []
    for ch in chains:
        p = [[wp[v][0], wp[v][1]] for v in ch]
        if len(p) >= 4:
            xs = ndi.gaussian_filter1d(np.array([q[0] for q in p]), 0.8, mode='nearest'); ys = ndi.gaussian_filter1d(np.array([q[1] for q in p]), 0.8, mode='nearest')
            q = [[float(a), float(b)] for a, b in zip(xs, ys)]; q[0] = p[0]; q[-1] = p[-1]; p = q
        trails.append([[round(a, 2), round(b, 2)] for a, b in p])
    links = 0
    for i, a in enumerate(w['ashlinks']):                                   # the short links out to Darkhaven, the Grove and the Woods
        if a['ash'] in wp:
            pa = wp[a['ash']]; pts_ = [[round(pa[0], 2), round(pa[1], 2)]] + [[round(tr[f'chain{i}_{k}'][0], 2), round(tr[f'chain{i}_{k}'][1], 2)] for k in range(len(a.get('chain') or [a['partner']]))]
            if math.dist(pa, pts_[1]) > 0.05 or len(pts_) > 2: trails.append(pts_); links += 1
    w['ashtracks'] = trails                                       # drawn as thinner footpaths than the Woods' trails

    pts = np.array([wp[v] for v in wp if surface(v)])
    n_trees, land_added = _paint(w, pts, trails, rng, seed)
    return w, dict(rooms=int(len(pts)), trails=len(trails), links=links, smoothing=used, anchor_error_max=round(float(err.max()), 2),
                   land_added=round(land_added, 1), trees=n_trees, covers=tuple(round(float(v), 1) for v in (pts[:, 0].min(), pts[:, 0].max(), pts[:, 1].min(), pts[:, 1].max())))


def merge_saved_layout(w, layout, edges, seed=77, nudges=None):
    """Put the layout you arranged in the editor on the map.
    Every room sits exactly where you left it. A trail is drawn between two rooms when the editor has an exit between them and
    neither room is hidden; hidden rooms still get ground (land, tint, trees), just no trails."""
    rng = random.Random(seed)
    pos = {i: (x, y) for i, x, y in zip(layout['ids'], layout['xs'], layout['ys'])}
    for v, (dx, dy) in (nudges or {}).items():                       # visual-only adjustments to where a few rooms are drawn (see visual_nudges.py)
        if v in pos: pos[v] = (pos[v][0] + dx, pos[v][1] + dy)
    hidden = set(layout.get('hidden', []))
    info = {r['id']: r for r in edges['rooms']}
    etr = {v for v, r in info.items() if r.get('area') == 'ETR'}     # the Eastern Trade Route's rooms and its own spacer rooms
    G_ = defaultdict(set); GR = defaultdict(set); kinds = Counter(); skipped_hidden = 0
    for a, b, k in edges['edges']:
        if a not in pos or b not in pos: continue
        if k == 'ud': continue                                   # up-and-down links join rooms on different levels: nothing to draw
        if a in hidden or b in hidden: skipped_hidden += 1; continue
        (GR if (a in etr and b in etr) else G_)[a].add(b); (GR if (a in etr and b in etr) else G_)[b].add(a); kinds[k] += 1
    # straight runs of rooms become one smooth trail; but a trail always starts and stops exactly on a fixed room (it is already on the map),
    # and exactly where a road meets a dirt path, so every junction really joins
    pinned = {v for v in set(G_) | set(GR) if info.get(v, {}).get('fixed')} | (set(G_) & set(GR))
    def build(G, sigma):
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
        out = []
        for ch in chains:
            p = [[pos[v][0], pos[v][1]] for v in ch]
            if len(p) >= 4:
                xs = ndi.gaussian_filter1d(np.array([q[0] for q in p]), sigma, mode='nearest'); ys = ndi.gaussian_filter1d(np.array([q[1] for q in p]), sigma, mode='nearest')
                q = [[float(a), float(b)] for a, b in zip(xs, ys)]; q[0] = p[0]; q[-1] = p[-1]; p = q
            out.append([[round(a, 2), round(b, 2)] for a, b in p])
        return out
    trails = build(G_, 0.8)                                       # dirt paths
    road = build(GR, 0.55)                                        # the Eastern Trade Route: a formal road, so it wanders less
    w['fwtracks'] = list(w['fwtracks']) + trails                  # drawn like the Woods' trails
    w['etrtracks'] = road                                         # drawn as a road
    w['ashtracks'] = []
    # the ground: every real room of the new area (hidden or not), not the fixed rooms that are already on the map
    pts = np.array([pos[v] for v in pos if v in info and not info[v]['void'] and not info[v]['fixed']])
    n_trees, land_added = _paint(w, pts, trails + road, rng, seed)
    rp = []                                                       # nothing grows on the road, nor close beside it
    for ln in road:
        for a, b in zip(ln[:-1], ln[1:]):
            n = max(1, int(math.dist(a, b) / 0.15)); rp += [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n + 1)]
    cleared = 0
    if rp:
        rt = cKDTree(np.array(rp))
        for key in ('trees', 'tufts', 'hills', 'thorns'):
            keep = [q for q in w[key] if q[0] < 12 or rt.query([q[0], q[1]])[0] > 1.15]; cleared += len(w[key]) - len(keep); w[key] = keep
    return w, dict(rooms=int(len(pts)), shown_trails=sum(kinds.values()), road_lines=len(road), trees_cleared_from_road=cleared, hidden_trails_skipped=skipped_hidden, trail_lines=len(trails), hidden_rooms=len(hidden), land_added=round(land_added, 1), trees=n_trees,
                   covers=tuple(round(float(v), 1) for v in (pts[:, 0].min(), pts[:, 0].max(), pts[:, 1].min(), pts[:, 1].max())))
