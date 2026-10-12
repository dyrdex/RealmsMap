"""Puts the Northern Plains you arranged in the layout editor on the map (np_layout_final.json, np_editor_edges.json).
Owner's instructions (Oct 10):
- The Plains are a field: no pathways for the field itself, only terrain: a tan/wheat ground with lighter and grassier patches,
  grass tufts and low brush (like the Forest of Tears, which is drawn as ground, not paths).
- Drawn as pathways (dirt trails): every exit between a Plains room and a Barren Peaks room on the map, and the linear paths
  listed in PATHS (from a start room, in a direction, along the string of rooms until it rejoins the field / ends).
- The Northern Trade Route is drawn by the Barren Peaks merge as usual (build.py gives it the road rooms' positions from this save).
Runs after the Barren Peaks merge (the last land change before it) on its own taller raster grid (same x origin and pixel size).
"""
import math, random, json
import numpy as np
from collections import defaultdict, deque
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from PIL import Image, ImageDraw
import arrange_apply as AA
import gap_fill as GF
from ntr_merge import _chains, _samples, _nearest_on

R8 = GF.R8
X0, X1, Y0, Y1 = GF.X0, GF.X1, -215.0, GF.Y1             # 45 rooms taller than the Peaks' grid
W, H = int((X1 - X0) * R8), int((Y1 - Y0) * R8)
BRIDGE = [4780, 4781, 4782]                              # 'Along a Rope Bridge': part of the wide dirt road along the Peaks
CANYON = {4152, 4153, 4154, 4155}                         # road rooms in the Peaks' canyon: movable in the Plains editor (owner, Oct 11) but on the Peaks' side
VEC = {'n': (0, -1), 's': (0, 1), 'e': (1, 0), 'w': (-1, 0)}
# (start room, direction, rooms where the path stops being a path) - the owner's coordinates in the comments
PATHS = [(4737, 's', ()),            # -29.76,-153.23 south
         (4707, 's', ()),            # -14.07,-143.31 south
         (4732, 's', ()),            # -12.71,-143.32 south
         (4718, 's', ()),            # -1.17,-146.51 south
         (4562, 's', ()),            # 25.24,-166.82 south
         (4313, 'n', ()),            # 26.43,-187.70 north
         (4389, 'w', (4364, 4330))]  # -37.15,-174.81 west; exits at -19.11,-187.85 (4364) and -3.34,-187.63 (4330)


def _components(G):
    seen = set(); out = []
    for s in sorted(G):
        if s in seen: continue
        q = [s]; seen.add(s)
        for x in q:
            for u in G[x]:
                if u not in seen: seen.add(u); q.append(u)
        out.append(q)
    return out


def dirt_road(layout, edges):
    """The wide dirt road along the Barren Peaks (owner, Oct 11): the Plains rooms joined to the Peaks form a single string from 4742 (west)
    to 4791 (east), crossing the rope bridge 4780-4782. Returns (the Peaks rooms joined to it, its lines). Used by the Barren Peaks merge
    too, which lets this road stand for the little trails of the Peaks rooms beside it (owner, Oct 12)."""
    pos = dict(zip(layout['ids'], zip(layout['xs'], layout['ys'])))
    hidden = set(layout.get('hidden', []))
    info = {r['id']: r for r in edges['rooms']}
    shown = lambda v: v in pos and v not in hidden
    plains = {v for v, r in info.items() if r.get('area') == 'NP' and shown(v)}
    peaks = {v for v, r in info.items() if (r.get('src') == 'BP' or r.get('area') == 'PK') and shown(v)}
    G = defaultdict(set)
    for a, b, k in edges['edges']:
        if k != 'ud' and shown(a) and shown(b): G[a].add(b); G[b].add(a)
    plinks = sorted((a, b) for a in plains for b in G[a] if b in peaks)
    fh = {a for a, b in plinks}
    rs_ = set(fh) | {v for v in plains if sum(1 for u in G[v] if u in fh) >= 2} | set(BRIDGE)
    GR = {v: {u for u in G[v] if u in rs_} for v in rs_ if shown(v)}
    return {b for a, b in plinks}, _chains(GR, pos, set(), 0.8), rs_, plinks


def merge_np(w, layout, edges, seed=37):
    import ashen_forest as AF
    _rooms = AF._world()[0]; rooms_name = lambda v: _rooms[v]['name'] if v in _rooms else ''
    rng = random.Random(seed)
    pos = dict(zip(layout['ids'], zip(layout['xs'], layout['ys'])))
    hidden = set(layout.get('hidden', []))
    info = {r['id']: r for r in edges['rooms']}
    shown = lambda v: v in pos and v not in hidden
    void = lambda v: bool(info[v].get('void'))
    plains = {v for v, r in info.items() if r.get('area') == 'NP' and shown(v)}
    proad = {v for v, r in info.items() if r.get('area') == 'RD' and shown(v)} - CANYON
    peaks = {v for v, r in info.items() if (r.get('src') == 'BP' or r.get('area') == 'PK') and shown(v)}
    G = defaultdict(set)
    for a, b, k in edges['edges']:
        if k != 'ud' and shown(a) and shown(b): G[a].add(b); G[b].add(a)

    # ---- the paths ----
    GT = defaultdict(set); pins = set(); report = []; westnet = set()
    def add(a, b): GT[a].add(b); GT[b].add(a)
    for start, d, stops in PATHS:
        vx, vy = VEC[d]
        first = max(sorted(G[start]), key=lambda t: ((pos[t][0] - pos[start][0]) * vx + (pos[t][1] - pos[start][1]) * vy) / (math.dist(pos[t], pos[start]) or 1))
        if stops:                                       # the whole string of rooms between the start and its exits
            seen = {start, first}; q = deque([first]); add(start, first)
            while q:
                x = q.popleft()
                if x in stops: continue
                for u in G[x]:
                    if u == start: continue
                    add(x, u)
                    if u not in seen: seen.add(u); q.append(u)
            assert len(seen) < 80, 'path leaked into the field'
            pins |= set(stops); report.append((start, d, len(seen))); westnet = set(seen) - {start} - set(stops)
        else:                                           # a single string: on while each room has exactly one way on
            path = [start, first]
            while True:
                cur = path[-1]; nx = [u for u in G[cur] if u != path[-2] and u not in path]
                if info[cur].get('area') != 'NP' or len(G[cur]) != 2 or len(nx) != 1: break
                path.append(nx[0])
            for a, b in zip(path, path[1:]): add(a, b)
            report.append((start, d, len(path)))
        pins.add(start)
    # ---- the wide dirt road along the Barren Peaks (see dirt_road). It stands for every link between the Plains and the Peaks: the Peaks
    #      rooms beside it get no spurs of their own (owner, Oct 12; the Barren Peaks merge runs their other trails on to the road) ----
    pruned = set()
    while True:                                         # dead-end spacer stubs are left off
        sp = [v for v in GT if len(GT[v]) <= 1 and void(v) and v not in pins]
        if not sp: break
        for v in sp:
            for u in list(GT[v]): GT[u].discard(v)
            del GT[v]; pruned.add(v)
    trails = _chains(GT, pos, pins, 0.6)
    _K, droad, rs_, plinks = dirt_road(layout, edges)
    conn = []
    # ---- off-ramps: wherever the Trade Route has an exit into a Plains room ----
    roads = list(w.get('etrtracks', [])); joins = []; ramp_conn = []
    for r_ in sorted(proad):
        outs = [u for u in G[r_] if u in plains]
        if not outs: continue
        q = _nearest_on(roads, pos[r_])
        if any(math.dist(q, j) < 1.2 for j in list(w.get('ntrjoins', [])) + joins): continue
        joins.append([round(q[0], 2), round(q[1], 2)])
        for u in outs:
            if u in GT or u in rs_: ramp_conn.append([[round(q[0], 2), round(q[1], 2)], [round(pos[u][0], 2), round(pos[u][1], 2)]])
    w['ntrjoins'] = list(w.get('ntrjoins', [])) + joins
    w['fwtracks'] = list(w['fwtracks']) + trails + conn + ramp_conn
    w['dirtroads'] = list(w.get('dirtroads', [])) + droad
    lines_all = trails + conn + ramp_conn + droad
    drawn = set(GT) | set(rs_)

    # ---- the Plains' ground ----
    real = [v for v in plains if not void(v)]
    # a city drawing just north of the Town of Solace marker (room 4309) (owner, Oct 12); the land grows round it like round a room
    cw, ch = 2.6, 2.15; cx_, cy_ = pos[4309][0], pos[4309][1] - 0.5 - ch / 2 - 0.1
    city = [(cx_ + a * cw / 2, cy_ + b * ch / 2) for a in (-1, 0, 1) for b in (-1, 0, 1)]
    # a few small gravestones just south of the Unholy Grounds marker (room 4221) (owner, Oct 12); the land grows round them too
    gx_, gy_ = pos[4221][0] - 0.3, pos[4221][1] + 2.4
    GRAVES = [(-1.0, -0.25, 0, 1.0), (-0.35, 0.05, 1, 1.05), (0.3, -0.3, 0, 0.9), (0.95, 0.0, 0, 1.0), (-0.7, 0.55, 0, 0.85), (0.1, 0.5, 1, 0.9), (0.75, 0.6, 0, 0.8)]   # (dx, dy, cross?, size)
    pts = np.array([pos[v] for v in real] + [pos[v] for v in proad] + [pos[v] for v in drawn if v in plains] + city + [(gx_ + a, gy_ + b) for a, b, k, r in GRAVES], float)
    lo, hi = pts.min(0) - 9, pts.max(0) + 9
    assert lo[1] > Y0 and hi[0] < X1 and lo[0] > X0, 'the Plains reach past the edge of the grid'
    ix0, ix1 = int((lo[0] - X0) * R8), int((hi[0] - X0) * R8); iy0, iy1 = int((lo[1] - Y0) * R8), int((hi[1] - Y0) * R8)
    sub = (slice(iy0, iy1), slice(ix0, ix1)); hh, ww = iy1 - iy0, ix1 - ix0
    img = Image.new('L', (ww, hh), 0); dr = ImageDraw.Draw(img)
    px = lambda x, y: ((x - X0) * R8 - ix0, (y - Y0) * R8 - iy0)
    Rd = 3.0
    for x, y in pts: cx, cy = px(x, y); dr.ellipse([cx - Rd * R8, cy - Rd * R8, cx + Rd * R8, cy + Rd * R8], fill=255)
    for t in lines_all:
        if len(t) > 1: dr.line([px(*q) for q in t], fill=255, width=int(2 * Rd * R8), joint='curve')
    m0 = np.array(img) > 0
    Rc = 3.5 * R8
    m = ndi.distance_transform_edt(~m0) <= Rc
    m = ndi.distance_transform_edt(m) > Rc
    m = ndi.binary_fill_holes(m | m0)
    nrng = np.random.default_rng(seed)
    noise = ndi.gaussian_filter(nrng.normal(size=m.shape), 2.4 * R8); n01 = (noise - noise.min()) / (noise.max() - noise.min())
    soft = ndi.gaussian_filter(m.astype(float), 1.3 * R8)
    area = np.zeros((H, W), bool); area[sub] = soft > (0.5 + 0.22 * (n01 - 0.5) * 2)
    land = AA._raster(w['geo']['land'], X0, Y0, W, H); water = AA._raster(w['geo']['water'], X0, Y0, W, H)
    area &= ~water
    new_land = land | area
    w['geo']['land'] = AA._contours(new_land, X0, Y0)
    grown = new_land & ~land

    # the wheat ground: the part of that land nearer a Plains room (or a road room in the Plains) than any other room on the map
    others = np.array([p for v, p in pos.items() if v not in plains and v not in proad and v not in hidden and (info.get(v, {}).get('fixed') or info.get(v, {}).get('area') == 'PK' or v in CANYON)], float)
    mine = np.array([pos[v] for v in plains] + [pos[v] for v in proad], float)
    yy, xx = np.mgrid[iy0:iy1, ix0:ix1]; P = np.c_[(xx.ravel() + .5) / R8 + X0, (yy.ravel() + .5) / R8 + Y0]
    d_m = cKDTree(mine).query(P)[0]; d_o = cKDTree(others).query(P)[0]
    pref = ndi.gaussian_filter((d_o - d_m).reshape(hh, ww), 0.8 * R8)
    wheat = np.zeros((H, W), bool); wheat[sub] = pref > 0
    wheat &= new_land
    wheat = ndi.binary_erosion(wheat, iterations=int(0.6 * R8))
    w['geo']['wheat'] = AA._contours(wheat, X0, Y0, sigma=2.0)
    nz = ndi.gaussian_filter(nrng.normal(size=(H, W))[sub], 3.0 * R8); nz = (nz - nz.min()) / (nz.max() - nz.min())
    nz2 = ndi.gaussian_filter(nrng.normal(size=(H, W))[sub], 2.2 * R8); nz2 = (nz2 - nz2.min()) / (nz2.max() - nz2.min())
    light = np.zeros((H, W), bool); light[sub] = nz > 0.6                 # paler, riper stretches
    grass = np.zeros((H, W), bool); grass[sub] = nz2 > 0.62               # greener, grassier stretches
    grass_m = grass                                                        # (kept: 'grass' is reused below)
    w['geo']['wheat2'] = AA._contours(ndi.binary_erosion(wheat & light, iterations=R8 // 2), X0, Y0, sigma=2.5)
    w['geo']['wheat3'] = AA._contours(ndi.binary_erosion(wheat & grass & ~light, iterations=R8 // 2), X0, Y0, sigma=2.5)
    # the Peaks' tints stop where the wheat begins (gotcha 3)
    clipped = {}
    for key in ('barren', 'barren2'):
        if w['geo'].get(key):
            b = AA._raster(w['geo'][key], X0, Y0, W, H); before = b.sum(); b &= ~wheat
            w['geo'][key] = AA._contours(b, X0, Y0, sigma=1.0); clipped[key] = round(float(before - b.sum()) / R8 / R8, 1)

    # ---- sprites: clear the old ones off the wheat and the paths; then grass tufts and brush ----
    inwheat = lambda x, y: 0 <= int((y - Y0) * R8) < H and 0 <= int((x - X0) * R8) < W and wheat[int((y - Y0) * R8), int((x - X0) * R8)]
    rs = _samples(lines_all + list(w.get('etrtracks', []))); rt = cKDTree(rs)
    cleared = 0
    for key in ('trees', 'tufts', 'hills', 'thorns', 'peaks', 'boulders'):
        kept = [q for q in w.get(key, []) if not inwheat(q[0], q[1])]; cleared += len(w.get(key, [])) - len(kept); w[key] = kept
    inner = ndi.binary_erosion(wheat, iterations=int(0.5 * R8))
    ys, xs = np.nonzero(inner); sq = float(inner.sum()) / R8 / R8
    ok = lambda x, y: inner[int((y - Y0) * R8), int((x - X0) * R8)] and rt.query([x, y])[0] > 0.55
    tufts = []
    for _ in range(int(sq * 1.1)):
        j = rng.randrange(len(xs)); x = xs[j] / R8 + X0 + rng.uniform(0, 1 / R8); y = ys[j] / R8 + Y0 + rng.uniform(0, 1 / R8)
        if ok(x, y): tufts.append([round(x, 3), round(y, 3), round(rng.uniform(0.75, 1.3), 2)])
    brush = []; centres = int(sq / 9)
    for _ in range(centres * 4):
        if len(brush) >= centres * 3: break
        j = rng.randrange(len(xs)); cx = xs[j] / R8 + X0; cy = ys[j] / R8 + Y0
        if rt.query([cx, cy])[0] < 1.0: continue
        for _k in range(rng.choice((1, 2, 2, 3, 4))):
            x = cx + rng.uniform(-0.6, 0.6); y = cy + rng.uniform(-0.4, 0.4)
            if not ok(x, y) or any(math.hypot(x - b[0], y - b[1]) < 0.4 for b in brush[-5:]): continue
            brush.append([round(x, 3), round(y, 3), round(rng.uniform(0.7, 1.2), 2)])

    # ---- the thicket (owner, Oct 11): the strip between the field's south edge and the Barren Peaks, where no rooms are, is overgrown and
    #      impassable; only the southern paths and the rooms by the Peaks cross it, with about one room of clear ground beside them ----
    rest = {v for v in real if v not in drawn}                               # the open field: the big connected body of Plains rooms off the drawn paths
    FG = {v: {u for u in G[v] if u in rest} for v in rest}                #   (small groups such as the rope bridge and the cliff path are not field)
    field = [v for c in _components(FG) if len(c) >= 20 for v in c]
    fimg = np.zeros((H, W), bool)
    for v in field:
        r_, c_ = int((pos[v][1] - Y0) * R8), int((pos[v][0] - X0) * R8); fimg[r_, c_] = True
    fimg = ndi.binary_dilation(fimg, iterations=int(1.0 * R8))
    pad_ = 6 * R8; RC = 4.5 * R8                                         # close gaps between the field's rows (they lie up to ~8 rooms apart)
    fp = np.pad(fimg, pad_); fp = ndi.distance_transform_edt(~fp) <= RC; fp = ndi.distance_transform_edt(fp) > RC
    fimg = ndi.binary_fill_holes(fp)[pad_:-pad_, pad_:-pad_] | fimg
    import os
    south = [v for v in drawn if v in plains]
    sx0 = min(pos[v][0] for v in south) - 2; sx1 = max(pos[v][0] for v in south) + 2
    rows = np.arange(H)[:, None]; cols = (np.arange(W) + .5) / R8 + X0
    # the field's south edge: in each column, the lowest field room within 2.5 rooms either side (owner, Oct 12: the thicket reaches north
    # until it is about one room from the real rooms, rather than stopping at the outline of the field)
    ey = np.full(W, -np.inf)
    for v in field:
        c0_, c1_ = int((pos[v][0] - 2.5 - X0) * R8), int((pos[v][0] + 2.5 - X0) * R8) + 1
        ey[max(c0_, 0):c1_] = np.maximum(ey[max(c0_, 0):c1_], pos[v][1])
    ok_ = np.isfinite(ey); ey = np.interp(np.arange(W), np.nonzero(ok_)[0], ey[ok_])
    edge = ((ey - Y0) * R8).astype(int)
    strip = (rows > edge[None, :]) & ((cols >= sx0) & (cols <= sx1))[None, :] & wheat
    rsm = _samples(droad, 0.1); rcol = np.full(W, -1)                       # and above the wide dirt road
    for x, y in rsm:
        c_ = int((x - X0) * R8); rcol[c_] = max(rcol[c_], int((y - Y0) * R8))
    rcol = ndi.maximum_filter1d(rcol, 5)
    strip &= ~((rcol[None, :] >= 0) & (rows > rcol[None, :]))
    joins_ = [[list(pos[a]), list(pos[b])] for a in sorted(GT) if a in plains for b in sorted(G[a]) if b in field]   # where a path meets the field: kept clear too (owner, Oct 12)
    clr_pts = np.r_[_samples(lines_all + joins_ + list(w.get('etrtracks', []))), np.array([p for v, p in pos.items() if shown(v) and (not void(v) or v in drawn)], float)]   # spacer rooms off the drawn paths are not walkable ground
    ys_, xs_ = np.nonzero(strip)
    dd = cKDTree(clr_pts).query(np.c_[(xs_ + .5) / R8 + X0, (ys_ + .5) / R8 + Y0])[0]
    thick = np.zeros((H, W), bool); thick[ys_[dd > 1.0], xs_[dd > 1.0]] = True
    thick = ndi.binary_opening(thick, iterations=R8 // 4)
    lab, n = ndi.label(thick)
    if n:
        sz = ndi.sum(thick, lab, range(1, n + 1)) / R8 / R8
        cm = ndi.center_of_mass(thick, lab, range(1, n + 1))
        lp = np.array([pos[a] for a, b in plinks])                        # the Plains rooms by the Peaks
        def beyond(c):                                                    # a small scrap south of the line of rooms by the Peaks
            x, y = c[1] / R8 + X0, c[0] / R8 + Y0; near_ = lp[np.abs(lp[:, 0] - x) < 4]
            return len(near_) and y > near_[:, 1].mean()
        thick = np.isin(lab, [i + 1 for i, s in enumerate(sz) if s >= 1.0 and not (s < 15 and beyond(cm[i]))])
    w['geo']['thicket'] = AA._contours(thick, X0, Y0, sigma=1.5)
    inth = lambda x, y: thick[int((y - Y0) * R8), int((x - X0) * R8)]
    tufts = [q for q in tufts if not inth(q[0], q[1])]; brush = [q for q in brush if not inth(q[0], q[1])]
    core = ndi.binary_erosion(thick, iterations=int(0.25 * R8))
    ys2, xs2 = np.nonzero(core); tsq = float(thick.sum()) / R8 / R8
    trees = []; rocks = []; shrubs = []; grass = []; placed = []
    for _ in range(int(tsq * 12)):
        if len(placed) >= int(tsq * 2.6) or not len(xs2): break
        j = rng.randrange(len(xs2)); x = xs2[j] / R8 + X0 + rng.uniform(0, 1 / R8); y = ys2[j] / R8 + Y0 + rng.uniform(0, 1 / R8)
        if any(math.hypot(x - a, y - b) < 0.42 for a, b in placed[-40:]): continue
        placed.append((x, y)); k = len(placed) % 3                          # an even mix: trees, rocks, brush
        if k == 0: trees.append([round(x, 3), round(y, 3), round(rng.uniform(0.7, 1.0), 2), 'h', rng.randrange(3)])       # bare, dead trees in dark brown (no greens: owner)
        elif k == 1: rocks.append([round(x, 3), round(y, 3), round(rng.uniform(0.6, 1.15), 2)])
        else: shrubs.append([round(x, 3), round(y, 3), round(rng.uniform(0.85, 1.3), 2), 1])       # brown brush
    for _ in range(int(tsq * 3)):                                         # overgrown grass between them
        j = rng.randrange(len(xs2)); x = xs2[j] / R8 + X0 + rng.uniform(0, 1 / R8); y = ys2[j] / R8 + Y0 + rng.uniform(0, 1 / R8)
        grass.append([round(x, 3), round(y, 3), round(rng.uniform(1.2, 1.7), 2), 1])       # darker, dry grass
    w['trees'] = list(w['trees']) + trees; w['boulders'] = sorted(list(w.get('boulders', [])) + rocks, key=lambda b: b[1])
    brush += shrubs; tufts += grass
    thicket = dict(sq=round(tsq, 1), trees=len(trees), rocks=len(rocks), brush=len(shrubs), grass=len(grass), x=[round(sx0, 1), round(sx1, 1)])

    # ---- the sea (owner, Oct 12): beyond the north-west path (the Grey Beach / Grey Dunes / Dark Cliffs path from 4389 round to 4330) the
    #      ground is sea, out to the edge of the map, with a strip of beach along the path. Bounded: only within 9 rooms of the path (less near
    #      its two ends), on the far side of the path from the field (gotcha 1) ----
    wset = westnet | {4389, 4330, 4364}
    wedges = [(pos[a], pos[b]) for a in sorted(wset) for b in sorted(GT[a]) if b in wset and a < b]
    ws = _samples(wedges, 0.1); wt = cKDTree(ws)
    bx0 = max(0, int((ws[:, 0].min() - 12 - X0) * R8)); bx1 = int((ws[:, 0].max() + 3 - X0) * R8); by1 = int((ws[:, 1].max() + 3 - Y0) * R8)
    yy_, xx_ = np.mgrid[0:by1, bx0:bx1]; PB = np.c_[(xx_.ravel() + .5) / R8 + X0, (yy_.ravel() + .5) / R8 + Y0]
    d_path, i_path = wt.query(PB); d_path = d_path.reshape(yy_.shape)
    d_room = cKDTree(np.array([p for v, p in pos.items() if shown(v)], float)).query(PB)[0].reshape(yy_.shape)
    e_s = np.linalg.norm(ws[i_path] - np.array(pos[4389]), axis=1).reshape(yy_.shape); e_e = np.linalg.norm(ws[i_path] - np.array(pos[4330]), axis=1).reshape(yy_.shape)
    barrier = (d_path <= 0.9) | (d_room <= 1.0) | fimg[:by1, bx0:bx1] | ndi.binary_dilation(thick, iterations=R8)[:by1, bx0:bx1]
    south_ = PB[:, 1].reshape(yy_.shape) > ws[:, 1].max() + 1.5           # not past the south end of the path
    south_ |= ((PB[:, 0] > -6) & (PB[:, 1] > -191.8)).reshape(yy_.shape)   # nor into the bay east of From the Stars (owner, Oct 12): the coast runs on smoothly
    lab, n = ndi.label(~barrier); outside = lab == lab[0, 0]
    reach = np.minimum(np.minimum(9.0, 1.5 + 0.8 * e_s), 1.0 + 0.45 * e_e)   # narrows to a point toward From the Stars (owner, Oct 12: no bay, a smooth coast)
    sea_b = outside & (d_path <= reach) & ~south_
    srng = np.random.default_rng(seed + 1)
    wob = ndi.gaussian_filter(srng.normal(size=sea_b.shape), 1.5 * R8); wob = (wob - wob.min()) / (wob.max() - wob.min())
    sea_b = (ndi.gaussian_filter(sea_b.astype(float), 0.8 * R8) > 0.4 + 0.2 * wob) & outside & ~south_ & (d_path > 0.8) & (d_room > 1.0)
    lab, n = ndi.label(sea_b)
    if n: sz = ndi.sum(sea_b, lab, range(1, n + 1)); sea_b = lab == (int(np.argmax(sz)) + 1)          # one body of water, no puddles
    sea = np.zeros((H, W), bool); sea[:by1, bx0:bx1] = sea_b
    beach = ndi.binary_dilation(sea, iterations=int(0.7 * R8)) & ~sea & new_land
    w['geo']['water'] = list(w['geo']['water']) + AA._contours(sea, X0, Y0, sigma=1.5)
    w['geo']['sand'] = list(w['geo'].get('sand', [])) + AA._contours(beach, X0, Y0, sigma=1.0)
    w['geo']['wheat'] = AA._contours(wheat & ~sea, X0, Y0, sigma=2.0)
    w['geo']['wheat2'] = AA._contours(ndi.binary_erosion(wheat & light, iterations=R8 // 2) & ~sea, X0, Y0, sigma=2.5)
    w['geo']['wheat3'] = AA._contours(ndi.binary_erosion(wheat & grass_m & ~light, iterations=R8 // 2) & ~sea, X0, Y0, sigma=2.5)
    assert not (thick & sea).any(), 'the sea reached the thicket'
    wet = sea | beach
    inwet = lambda x, y: 0 <= int((y - Y0) * R8) < H and 0 <= int((x - X0) * R8) < W and wet[int((y - Y0) * R8), int((x - X0) * R8)]
    for key in ('trees', 'tufts', 'hills', 'thorns', 'peaks', 'boulders'):
        w[key] = [q for q in w.get(key, []) if not inwet(q[0], q[1])]
    tufts = [q for q in tufts if not inwet(q[0], q[1])]; brush = [q for q in brush if not inwet(q[0], q[1])]
    seainfo = dict(sea_sq=round(float(sea.sum()) / R8 / R8, 1), beach_sq=round(float(beach.sum()) / R8 / R8, 1), sea_on_old_land_sq=round(float((sea & new_land).sum()) / R8 / R8, 1))

    # ---- the north-west (owner, Oct 11): the ground between the Dark Cliffs / Grey Dunes path and the field is impassable: rocky crags by the
    #      Dark Cliffs, grey dunes by the Grey Dunes and Beach; about one room kept clear beside the path and every room ----
    nwq = np.zeros((H, W), bool); r0 = int((-172 - Y0) * R8); c0 = int((0 - X0) * R8); nwq[:r0, :c0] = True
    zone = new_land & nwq & ~fimg & ~thick & ~wet
    ys_, xs_ = np.nonzero(zone)
    PZ = np.c_[(xs_ + .5) / R8 + X0, (ys_ + .5) / R8 + Y0]
    dd = cKDTree(clr_pts).query(PZ)[0]; keep = dd > 1.0
    zone = np.zeros((H, W), bool); zone[ys_[keep], xs_[keep]] = True
    zone = ndi.binary_opening(zone, iterations=R8 // 4)
    lab, n = ndi.label(zone)
    if n:
        sz = ndi.sum(zone, lab, range(1, n + 1)) / R8 / R8; zone = np.isin(lab, [i + 1 for i, s in enumerate(sz) if s >= 1.0])
    # no way west from Opallinoc (4387) to the coastal path (4393) (owner, Oct 12): dunes fill the gap between them, half a room off each
    ox0, ox1 = pos[4393][0] + 0.55, pos[4387][0] - 0.55; oy = pos[4387][1]
    gap = np.zeros((H, W), bool); gap[int((oy - 2.0 - Y0) * R8):int((oy + 2.0 - Y0) * R8), int((ox0 - X0) * R8):int((ox1 - X0) * R8)] = True
    zone |= gap & new_land & ~wet
    zone[:, int((pos[4330][0] - X0) * R8):] = False                         # none east of From the Stars (4330): the old bay there is plain ground
    wn = sorted(v for v in westnet if not void(v)); CL = set()           # owner, Oct 12: all of it grey dunes now (was crags by 'Dark Cliffs', 'The Valley Floor')
    iscl = np.array([rooms_name(v) in CL for v in wn])
    ys_, xs_ = np.nonzero(zone); near_ = cKDTree([pos[v] for v in wn]).query(np.c_[(xs_ + .5) / R8 + X0, (ys_ + .5) / R8 + Y0])[1]
    crag = np.zeros((H, W), bool); dune = np.zeros((H, W), bool)
    crag[ys_[iscl[near_]], xs_[iscl[near_]]] = True; dune[ys_[~iscl[near_]], xs_[~iscl[near_]]] = True
    w['geo']['crags'] = AA._contours(crag, X0, Y0, sigma=1.5); w['geo']['dunes'] = AA._contours(dune, X0, Y0, sigma=1.5)
    inz = lambda x, y: zone[int((y - Y0) * R8), int((x - X0) * R8)]
    tufts = [q for q in tufts if not inz(q[0], q[1])]; brush = [q for q in brush if not inz(q[0], q[1])]
    crags = []; ripples = []; nrocks = 0
    for m_, out_, per, sp_ in ((ndi.binary_erosion(crag, iterations=int(0.3 * R8)), crags, 1.6, 0.55), (ndi.binary_erosion(dune, iterations=int(0.3 * R8)), ripples, 1.1, 0.7)):
        yy_, xx_ = np.nonzero(m_); placed = []
        for _ in range(int(m_.sum() / R8 / R8 * per * 5)):
            if len(placed) >= int(m_.sum() / R8 / R8 * per) or not len(xx_): break
            j = rng.randrange(len(xx_)); x = xx_[j] / R8 + X0 + rng.uniform(0, 1 / R8); y = yy_[j] / R8 + Y0 + rng.uniform(0, 1 / R8)
            if any(math.hypot(x - a, y - b) < sp_ for a, b in placed[-40:]): continue
            placed.append((x, y)); out_.append([round(x, 3), round(y, 3), round(rng.uniform(0.75, 1.35), 2), rng.randrange(3)])
    for x, y, s_, k_ in crags[::2]:                                       # loose rocks between the crags
        bx, by = x + rng.uniform(-.45, .45), y + rng.uniform(.15, .45)
        if inz(bx, by): w['boulders'].append([round(bx, 3), round(by, 3), round(rng.uniform(.5, .9), 2)]); nrocks += 1
    w['boulders'] = sorted(w['boulders'], key=lambda b: b[1])
    w['crags'] = sorted(crags, key=lambda b: b[1]); w['ripples'] = sorted(ripples, key=lambda b: b[1])
    nw = dict(crag_sq=round(float(crag.sum()) / R8 / R8, 1), dune_sq=round(float(dune.sum()) / R8 / R8, 1), crags=len(crags), ripples=len(ripples), rocks=nrocks)

    # ---- The Barrow Mound (4374-4376) with Inside the Barrow (4377-4379) behind it: one drawing ----
    bv = [v for v in (4374, 4375, 4376, 4377, 4378, 4379) if shown(v)]
    bx, by = sum(pos[v][0] for v in bv) / len(bv), sum(pos[v][1] for v in bv) / len(bv) - 0.15
    gfx = [dict(k='barrow', at='xy', x=round(bx, 2), y=round(by, 2), w=4.6, h=2.3)]
    citygfx = dict(k='stonecity', at='xy', x=round(cx_, 2), y=round(cy_, 2), w=cw, h=ch)
    # a watery path out to sea from the most north-westerly room, 4405 (owner, Oct 12: 4407 preferred, but it is hidden), named Otherland
    ox_, oy_ = pos[4405]; OL = 3.4
    extra = [citygfx, dict(k='waterway', at='xy', x=round(ox_, 2), y=round(oy_, 2), w=1, h=1, len=OL),

             dict(k='graves', at='xy', x=round(gx_, 2), y=round(gy_, 2), w=1, h=1, t=[[a, b, k, r] for a, b, k, r in GRAVES])]
    # ---- groves where the rooms are named 'The Fringe of Trees' and 'Tall Trees': a few big trees per room, one drawing per group ----
    TREE = ('The Fringe of Trees', 'Tall Trees')
    tv = sorted((v for v in real if rooms_name(v) in TREE), key=lambda v: pos[v][1]); groups = []
    for v in tv:
        if groups and pos[v][1] - pos[groups[-1][-1]][1] <= 3.5: groups[-1].append(v)
        else: groups.append([v])
    for gv in groups:
        cx = sum(pos[v][0] for v in gv) / len(gv); cy = sum(pos[v][1] for v in gv) / len(gv); tr = []
        for v in gv:
            tall = rooms_name(v) == 'Tall Trees'
            for k_ in range(2 if tall else 1):
                tr.append([round(pos[v][0] - cx + rng.uniform(-.35, .35) + (k_ * .55 - .27 if tall else 0), 2), round(pos[v][1] - cy + rng.uniform(-.3, .25), 2), round(rng.uniform(.62, .78) if tall else rng.uniform(.45, .58), 2), 1 if tall else 0])
        tr.sort(key=lambda q: q[1])
        gfx.append(dict(k='grove', at='xy', x=round(cx, 2), y=round(cy, 2), w=1, h=1, t=tr))
    w['gfx'] = list(w.get('gfx', [])) + gfx + extra                       # (appended, gotcha 6)
    w['tags'] = list(w.get('tags', [])) + [[round(ox_ + 2.1, 2), round(oy_ - OL + 0.35, 2), 'Otherland', 0.55]]   # map-only name beside the end of the watery path
    def under(x, y):
        if abs(x - bx) < 2.6 and abs(y - by) < 1.4: return True
        if abs(x - cx_) < cw / 2 + .2 and abs(y - cy_) < ch / 2 + .2: return True
        if -1.6 < x - gx_ < 1.55 and -1.1 < y - gy_ < 1.0: return True
        return any(abs(x - g['x'] - q[0]) < q[2] + .25 and -q[2] * 1.6 < y - g['y'] - q[1] < q[2] * .6 for g in gfx[1:] for q in g['t'])
    tufts = [q for q in tufts if not under(q[0], q[1])]; brush = [q for q in brush if not under(q[0], q[1])]
    drawings = dict(barrow=[round(bx, 2), round(by, 2)], solace_city=[round(cx_, 2), round(cy_, 2)], otherland=[round(ox_, 2), round(oy_, 2)], graves=[round(gx_, 2), round(gy_, 2)], groves=[[round(g['x'], 2), round(g['y'], 2), len(g['t'])] for g in gfx[1:]])
    w['wheattufts'] = sorted(tufts, key=lambda b: b[1]); w['brush'] = sorted(brush, key=lambda b: b[1])

    # the area's name (owner, Oct 12): in the open field, centred between the Trade Route (x -6.4) and the west coast (x -46.6) at y -164
    w['arealabels'] = list(w.get('arealabels', [])) + [dict(x=-26.5, y=-164.0, lh=2.6, sag=1.0, hw=12, lines=['Northern Plains'])]
    pts_ = np.array([q for poly in w['geo']['land'] for q in poly])
    w['bounds'] = [int(pts_[:, 0].min()) - 3, int(pts_[:, 1].min()) - 3, int(pts_[:, 0].max()) + 3, int(pts_[:, 1].max()) + 3]
    return w, dict(paths=report, peaks_links=len(plinks), dirt_road=[len(droad), len(rs_)], spurs=len(conn), off_ramps=joins, ramp_paths=len(ramp_conn), path_rooms=len(GT), trail_lines=len(trails), spacer_stubs_left_off=sorted(pruned),
                   new_land_sq=round(float(grown.sum()) / R8 / R8, 1), wheat_sq=round(float(wheat.sum()) / R8 / R8, 1), peaks_tint_clipped_sq=clipped,
                   sprites_cleared=cleared, tufts=len(tufts), brush=len(brush), thicket=thicket, sea=seainfo, northwest=nw, drawings=drawings, bounds=w['bounds'],
                   rooms_off_land=sum(1 for v in real if not new_land[int((pos[v][1] - Y0) * R8), int((pos[v][0] - X0) * R8)]))
