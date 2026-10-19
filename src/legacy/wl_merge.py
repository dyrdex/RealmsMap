"""The Wastelands (owner, Oct 17): wl_layout_final.json, wl_editor_edges.json (the owner's layout from tools/wastelands_editor; the Southern Mountain
Trade Route rooms 9327-9346 the owner moved there are drawn by smr_merge at their new spots: build.py passes them in).
Owner's notes (Oct 17):
  1. The area is a field with clearings and some paths. Range rooms 34 and 35 join 664 and 665; those and the foothill rooms after them (8548-8563,
     ending at 8557) are drawn as a continuation of the range's clearing that 34 and 35 are in. The connection 8557 - 8645 is not drawn.
     (The other foothill pass, 663 and 7840-7842 off range room 36, is drawn like the rest of the area.)
  2. An Ancient Road is a wide pathway (a wide dirt road: owner's choice, Oct 17).
  3. The other sections are painted to fit their theme in broad strokes (details later).
  4. Sea beyond the coast; the underwater rooms out in the water (dashed links). Markers stay as they are.
Decided here, in broad strokes: the ground is a dry field (the Northern Plains' wheat tints, grass tufts and brush); clumps of mutually joined rooms are
dirt clearings (the Southern Mountain Range's rule), except in the Salt Flats (a pale salt crust) and in Camden (a town: streets, inn, church, shops,
homes); Volcanic Plains = ash ground with crags, the volcano a peak; Fringes of the Desert = dunes; cliffs = grey rocky ground with boulders; the canyon =
barren ground with crags; the shore and beaches = sand; the river = a stream; the foothills = hills; underground rooms = thin dashed lines.
Land: wl_land(), called from smr_merge's land_edit (so it is traced with the rest); the sea is worked out there too and added by merge_wl."""
import math, re
import numpy as np
from collections import defaultdict
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from scipy.spatial import cKDTree, ConvexHull
from skimage.morphology import disk
import arrange_apply as AA
import gap_fill as GF
import ashen_forest as AF
from ntr_merge import _chains, _samples, _nearest_on
from smr_merge import _hash, _drawn

R8 = GF.R8
UN = list(range(9327, 9347))                    # the Southern Mountain Trade Route rooms the owner moved in the Wastelands editor (Oct 17)
FOOT = {664, 665} | set(range(8548, 8564))      # the foothill rooms drawn as part of the range's clearing (owner, Oct 17)
FOOT_JOIN = (34, 35)                            # ... the range rooms whose clearing they continue
NO_LINK = {frozenset((8557, 8645)), frozenset((8722, 8889))} | {frozenset((a, b)) for a in (8731, 8732, 8733, 8723) for b in (8731, 8732, 8733, 8723) if a < b}             # not drawn (owner, Oct 17)
EXTRA_HIDDEN = {7854: (9.0, 92.5)}               # Gateway to Aurora, one south of 7853 (its south exit): on the map for routes, hidden (owner, Oct 17)
PASS = [36, 663, 7840, 7841, 7842, 7843, 7844, 7845, 7846]   # the pass from range room 36 down to 7846: a wide path that looks like the clearings (owner, Oct 17)
VOLCANO = (14965, 14966, 14967)                 # one volcano graphic over these three rooms (owner, Oct 17)
VOLC_TOP = (-10.0, 102.42)                       # the Volcanic Plains clearing north of 8684-8687's line: only the strip down 8615-8616-8617 and 8616-8684 (owner, Oct 17)
PIERS = (8763, 8764)                            # Camden Piers: a wooden pier out over the coast route into the sea (owner, Oct 17)
TOWN = {8726, 18259} | set(range(8743, 8770))   # Camden
SEA_AREAS = ('The Blood Sea', 'Sea of Sorrows')
LAND_R, SEA_R, TERR_R = 4.2, 8.0, 3.2
PAD, SQ, CELL_MAX, MIN_PATCH = 0.55, 1.1, 6.0, 3.0                  # (the range's rule, owner Oct 14: clumps follow the exits, not the spacing)
SEED = 173


def section(name, terrain):
    for k, pat in (('road', r'Ancient Road|Fork in the Road|Tired Wooden Bridge'), ('salt', r'Salt Flats'), ('volcano', r'Atop the Volcano|Upon the Volcano'),
                   ('volc', r'Volcanic'), ('desert', r'Fringes of the Desert|Entering the Desert|Overlooking the Desert'), ('shore', r'Shore|Beach|Ahtborne'),
                   ('cliff', r'Cliff|Narrow Path|Promontory|Junction in the Path|Small Cave|Stone Spire'), ('river', r'River|Crumbling Bridge'),
                   ('under', r'Darkness|Tunnel|Hole In The Ground'), ('canyon', r'Canyon|Chasm|Cavern|Crevice'),
                   ('hills', r'Foothill|Hills|Gully|Hill|Slope|Pass')):
        if re.search(pat, name or ''): return k
    return 'field'


def _setup(layout, edges):
    rooms, _ = AF._world()
    pos = dict(zip(layout['ids'], zip(layout['xs'], layout['ys'])))
    info = {r['id']: r for r in edges['rooms']}
    hidden = set(layout.get('hidden', [])) | {8700, 8754}                           # (8700, 8754 hidden too: owner, Oct 17)
    WL = {v for v, r in info.items() if r.get('area') == 'WL' and r.get('grp') == 'wl' and v in pos}
    shown = lambda v: v in pos and v not in hidden
    void = lambda v: bool(info.get(v, {}).get('void'))
    terr = lambda v: rooms[v]['terrain'] if v in rooms else ''
    sec = {v: section(rooms[v]['name'], terr(v)) for v in WL}
    for v in WL:                                                                     # (a spacer takes its neighbours' section below)
        if void(v): sec[v] = None
    UW = {v for v in WL if terr(v) == 'Underwater' or re.search(r'Wasted Shores of Ahtborne|Beaches of Sorrow', rooms[v]['name'])}   # the coast path: land, a dashed blue line (owner, Oct 17)
    return rooms, pos, info, hidden, WL, shown, void, terr, sec, UW


def _graphs(layout, edges):
    rooms, pos, info, hidden, WL, shown, void, terr, sec, UW = _setup(layout, edges)
    nb = defaultdict(set); E = []
    for a, b, k in edges['edges']:
        if not (shown(a) and shown(b)) or frozenset((a, b)) in NO_LINK: continue
        if not ({a, b} & WL): continue
        E.append((a, b, k)); nb[a].add(b); nb[b].add(a)
    for _ in range(4):                                                               # spacers: the section most of their real neighbours have
        for v in WL:
            if sec.get(v) is None:
                s = [sec[u] for u in nb[v] if u in WL and sec.get(u)]
                if s: sec[v] = max(sorted(set(s)), key=s.count)
    for v in WL:
        if sec.get(v) is None: sec[v] = 'field'
    for v in WL:                                                                     # (a spacer between coast rooms is coast)
        if void(v) and nb[v] and all(u in UW for u in nb[v] if u in WL and not void(u)) and any(u in UW for u in nb[v]): UW.add(v)
    road = {v for v in WL if sec[v] == 'road'} - {8754}                             # (8754: no stub of wide road there: owner, Oct 17)
    under = {v for v in WL if sec[v] == 'under' or terr(v) == 'Underground'}
    return rooms, pos, info, hidden, WL, shown, void, terr, sec, UW, E, road, under


def wl_land(layout, edges, store, seed=SEED):
    """land_edit for smr_merge: the Wastelands' land added to the grid, the sea kept out of it (and remembered in store for merge_wl)"""
    rooms, pos, info, hidden, WL, shown, void, terr, sec, UW, E, road, under = _graphs(layout, edges)
    dry = [v for v in WL if shown(v) and v not in UW and v not in PIERS]             # (the coast path is in the sea, its north edge: owner, Oct 17)
    land_lines = [[pos[a], pos[b]] for a, b, k in E if k != 'ud' and not ({a, b} & (UW | set(PIERS)))]; sea_pts = []
    cpath = _samples([[pos[a], pos[b]] for a, b, k in E if a in UW and b in UW and k != 'ud'], 0.1)
    exits = AF._world()[1]                                                           # (read once: each call parses the whole world file)
    for v in WL:                                                                     # the exits into the seas (not drawn): the sea lies that way
        if not shown(v): continue
        for e in exits.get(v, []):
            t = e['to']
            if t in rooms and (rooms[t]['area'] in SEA_AREAS or (void(t) and t not in pos)) and e['dir'] in AF.DV:
                d = AF.DV[e['dir']]
                if d[2] or d[1] <= 0 or not (rooms[t]['area'] in SEA_AREAS or any(rooms.get(e2['to'], {}).get('area') in SEA_AREAS for e2 in exits.get(t, []))): continue
                sea_pts.append((pos[v][0] + 1.0 * d[0], pos[v][1] + 1.8))                # (the sea starts just south of the coast path)
    sea_pts += [(pos[v][0], pos[v][1] + 1.8) for v in UW if shown(v)]                # (the sea south of the whole coast path)
    _lt = cKDTree(np.r_[np.array([pos[v] for v in dry]), _samples(land_lines, 0.15)])
    sea_pts = [p for p in sea_pts if _lt.query(p)[0] >= 1.2]                         # (not on a room or path further south: the coast path stays on land)
    xs = [pos[v][0] for v in dry] + [p[0] for p in sea_pts]; ys = [pos[v][1] for v in dry] + [p[1] for p in sea_pts]
    box = (math.floor(min(xs)) - 14, math.floor(min(ys)) - 10, math.ceil(max(xs)) + 14, math.ceil(max(ys)) + 14)
    bw, bh = int((box[2] - box[0]) * R8), int((box[3] - box[1]) * R8)
    gy, gx = np.mgrid[0:bh, 0:bw]; X = (gx + .5) / R8 + box[0]; Y = (gy + .5) / R8 + box[1]; P = np.c_[X.ravel(), Y.ravel()]
    lp = np.r_[np.array([pos[v] for v in dry]), _samples(land_lines, 0.15)]
    d_l = cKDTree(lp).query(P)[0].reshape(bh, bw)
    d_s = cKDTree(np.array(sea_pts)).query(P)[0].reshape(bh, bw) if sea_pts else np.full((bh, bw), np.inf)
    rng = np.random.default_rng(seed)
    wob = ndi.gaussian_filter(rng.normal(size=(bh, bw)), 1.8 * R8); wob = (wob - wob.min()) / (wob.max() - wob.min())
    sea = (d_s <= SEA_R * (0.8 + 0.4 * wob)) & (d_s < d_l) & (d_l > 0.9)                # (every room and path on land)
    if len(cpath):                                                                   # the coast route is the sea's north edge: the sea south of it, a little past it for a rounded shore
        cc = ((cpath[:, 0] - box[0]) * R8).astype(int); top = np.full(bw, np.inf)
        np.minimum.at(top, np.clip(cc, 0, bw - 1), cpath[:, 1])
        top = ndi.minimum_filter1d(np.where(np.isfinite(top), top, 1e9), 3)
        south = (Y >= top[None, :]) & np.isfinite(top)[None, :] & (top[None, :] < 1e8)
        d_c = cKDTree(cpath).query(P)[0].reshape(bh, bw)
        cov = (top[None, :] < 1e8) & np.ones((bh, 1), bool)                         # (columns the route crosses: no sea north of it there, beyond a rounded margin)
        sea &= ~cov | south | (d_c <= 0.45)
        sea |= (south & (d_c <= SEA_R * (0.8 + 0.4 * wob))) | (d_c <= 0.45)
        sea &= d_l > 0.9
    sea = ndi.gaussian_filter(sea.astype(float), 0.8 * R8) > 0.5
    if len(cpath): sea |= d_c <= 0.35                                                # (the route itself always in the water)
    near = d_l <= LAND_R * (0.7 + 0.6 * wob)
    near = ndi.binary_closing(near, structure=np.ones((3, 3), bool), iterations=int(1.5 * R8))
    near = ndi.binary_fill_holes(near)
    near = (ndi.gaussian_filter(near.astype(float), 0.8 * R8) > 0.5) & ~sea
    store.update(box=box, sea=sea, land=near, sea_pts=len(sea_pts))

    def edit(land_n, water0, gx0, gy0):
        c0, r0 = int(round((box[0] - gx0) * R8)), int(round((box[1] - gy0) * R8))
        assert c0 >= 0 and r0 >= 0 and r0 + bh <= land_n.shape[0] and c0 + bw <= land_n.shape[1], (box, land_n.shape)
        sub = (slice(r0, r0 + bh), slice(c0, c0 + bw))
        old = land_n[sub].copy()
        store['sea'] = sea & ~old & ~water0[sub]                                    # (the sea only where there was no land or water)
        add = near & ~water0[sub] & ~store['sea']
        land_n[sub] = old | add
        store['land_new_sq'] = round(float((add & ~old).sum()) / R8 / R8, 1)
        store['land'] = land_n[sub].copy()
        return land_n
    return edit


def _put(w, key, mask, box, sigma=1.5, minarea=0.15):
    """a ground tint, clear of what that tint already covers (tints are drawn even-odd: overlapping pieces would cancel)"""
    bw, bh = mask.shape[1], mask.shape[0]
    old = [p for p in (w['geo'].get(key) or []) if any(box[0] <= q[0] < box[2] and box[1] <= q[1] < box[3] for q in p)]
    if old: mask = mask & ~AA._raster(old, box[0], box[1], bw, bh)
    w['geo'][key] = list(w['geo'].get(key) or []) + AA._contours(mask, box[0], box[1], sigma=sigma, minarea=minarea)
    return round(float(mask.sum()) / R8 / R8, 1)


def _place(mask, X, Y, spacing, salt, avoid=None):
    ys, xs = np.nonzero(mask); placed = []; grid = {}
    if avoid is not None and len(avoid):
        for q in avoid: grid.setdefault((int(q[0] // spacing), int(q[1] // spacing)), []).append((q[0], q[1]))
    for i in np.argsort(_hash(X[ys, xs], Y[ys, xs], salt), kind='stable'):
        x, y = X[ys[i], xs[i]], Y[ys[i], xs[i]]; gk = (int(x // spacing), int(y // spacing))
        if any(math.dist(q, (x, y)) < spacing for dx in (-1, 0, 1) for dy in (-1, 0, 1) for q in grid.get((gk[0] + dx, gk[1] + dy), ())): continue
        grid.setdefault(gk, []).append((x, y)); placed.append((round(float(x), 3), round(float(y), 3)))
    return placed


def merge_wl(w, layout, edges, store, seed=SEED):
    rooms, pos, info, hidden, WL, shown, void, terr, sec, UW, E, road, under = _graphs(layout, edges)
    rep = {}
    box = store['box']; sea = store['sea']; landm = store['land']
    bh, bw = sea.shape
    gy, gx = np.mgrid[0:bh, 0:bw]; X = (gx + .5) / R8 + box[0]; Y = (gy + .5) / R8 + box[1]; P = np.c_[X.ravel(), Y.ravel()]
    px = lambda p: ((p[0] - box[0]) * R8, (p[1] - box[1]) * R8)
    nm = lambda v: rooms[v]['name'] if v in rooms else ''

    # ---------------------------------------------------------------- the graphs
    GD = defaultdict(set); GR = defaultdict(set); links = []; uds = []; dash = []; sdash = []
    for a, b, k in E:
        if a in FOOT and b in FOOT: continue                                         # (inside the foothill clearing)
        if {a, b} & FOOT and {a, b} & set(FOOT_JOIN): continue                       # (34/35 - 664/665: the clearing joins them)
        if a in UW and b in UW:
            sdash.append((a, b, k))                                                  # (the coast route: a solid water route; its up/down exits dashed: owner, Oct 17)
            continue
        if a in under or b in under: dash.append((a, b)); continue
        if not (a in WL and b in WL): links.append((a, b)); continue                 # to the range / the trade route
        if k == 'ud': uds.append((a, b)); continue
        if a in road and b in road: GR[a].add(b); GR[b].add(a)
        else: GD[a].add(b); GD[b].add(a)
    def prune(G, extra):
        n = 0
        while True:
            sp = [v for v in G if void(v) and len(G[v]) + extra.get(v, 0) <= 1]
            if not sp: break
            for v in sp:
                for u in list(G[v]): G[u].discard(v)
                del G[v]; n += 1
        for v in [v for v in G if not G[v]]: del G[v]
        return n
    ext = defaultdict(int)
    for G2 in (GD, GR):
        for v in G2:
            for G3 in (GD, GR):
                if G3 is not G2 and v in G3: ext[v] += 1
    for a, b in links + uds + dash: ext[a] += 1; ext[b] += 1
    rep['spacer_stubs_dropped'] = prune(GD, ext) + prune(GR, ext)

    # ---------------------------------------------------------------- clearings: cells of mutually joined real rooms (the range's rule)
    real = {v for v in GD if not void(v) and v not in TOWN}
    nbr = {v: {u for u in GD[v] if u in real and math.dist(pos[u], pos[v]) <= CELL_MAX} for v in real}
    cells = set()
    for a in real:
        for b in nbr[a]:
            for c in nbr[a] & nbr[b]:
                if len({a, b, c}) == 3: cells.add(frozenset((a, b, c)))
        for b in nbr[a]:
            for c in nbr[a]:
                if b < c:
                    for d in (nbr[b] & nbr[c]) - {a}:
                        if len({a, b, c, d}) == 4: cells.add(frozenset((a, b, c, d)))
    def cellmask(cs):
        im = Image.new('L', (bw, bh), 0); dr = ImageDraw.Draw(im)
        for cell in cs:
            pts = np.array([pos[v] for v in cell])
            try: hull = ConvexHull(pts)
            except Exception: continue
            if hull.volume < 0.45: continue
            dr.polygon([px(p) for p in pts[hull.vertices]], fill=255, outline=255)
        m = ndi.binary_dilation(np.array(im, bool), structure=disk(int(PAD * R8)))
        return ndi.gaussian_filter(m.astype(float), 0.45 * R8) > 0.5
    nbs = defaultdict(set)
    for a, b, k in E:
        if k != 'ud': nbs[a].add(b); nbs[b].add(a)
    def withsp(core):                                                                # spacers are what the rooms they join are (owner, Oct 17): a run of spacers whose real ends are all in core
        out = set(core); seen = set()
        for s in [v for v in WL if void(v) and shown(v)]:
            if s in seen: continue
            comp = {s}; st = [s]
            while st:
                x = st.pop()
                for u in nbs[x]:
                    if u not in comp and void(u) and shown(u): comp.add(u); st.append(u)
            seen |= comp
            ends = {u for x in comp for u in nbs[x] if not void(u)}
            if ends and ends <= core: out |= comp
        return out
    def roompatch(S_):                                                               # (owner, Oct 17: exactly the rooms and the exits between them, holes filled)
        im = Image.new('L', (bw, bh), 0); dr = ImageDraw.Draw(im); s_ = int(SQ * R8)
        for v in S_:
            p = px(pos[v]); dr.rectangle([p[0] - s_ / 2, p[1] - s_ / 2, p[0] + s_ / 2, p[1] + s_ / 2], fill=255)
        for a, b, k in E:
            if a in S_ and b in S_ and k != 'ud': dr.line([px(pos[a]), px(pos[b])], fill=255, width=s_)
        return ndi.gaussian_filter(ndi.binary_fill_holes(np.array(im, bool)).astype(float), 0.3 * R8) > 0.5
    WCAM = {v for v in WL if shown(v) and 14 <= pos[v][0] <= 25 and 107 <= pos[v][1] <= 114.5} - {8732, 8733, 8736}   # (west of Camden, north of the shore path: owner, Oct 17)
    STEPPE = withsp({v for v in WL if shown(v) and (nm(v) == 'Arid Steppes' or sec[v] == 'road')} | WCAM)   # all the Arid Steppes one clearing, the Ancient Road drawn over it (owner, Oct 17)
    SALTR = withsp({v for v in WL if shown(v) and sec[v] == 'salt'})                 # the Salt Flats: a salt field on exactly its rooms (owner, Oct 17)
    SW = {v for v in WL if shown(v) and not void(v) and pos[v][0] <= 1 and pos[v][1] >= 96 and sec[v] not in ('road', 'salt', 'river') and nm(v) != 'Arid Steppes' and v not in UW}
    _rv = [pos[v][0] for v in WL if shown(v) and sec[v] == 'river' and pos[v][1] >= 96]
    SWX = (max(_rv) + 1.0) if _rv else -1e9                                          # (the clearing's west edge: a straight north-south line east of the river rooms: owner, Oct 17)
    SW = {v for v in SW if pos[v][0] > SWX}
    SPIRE = {8705, 8706}                                                             # a path on top of the south-west clearing (owner, Oct 17)
    VOLC = withsp(SW - SPIRE)                                                        # the whole south-west: one ash-coloured clearing (owner, Oct 17)
    salt_cells = [c for c in cells if c & (SALTR | VOLC)]
    dirt_cells = [c for c in cells if c not in salt_cells]
    saltm = roompatch(SALTR); volcm = roompatch(VOLC)
    volcm &= X >= SWX
    _rg = np.random.default_rng(seed + 7); _wb = ndi.gaussian_filter(_rg.normal(size=(bh, bw)), 0.7 * R8); _wb = (_wb - _wb.min()) / (_wb.max() - _wb.min())
    saltm = ndi.distance_transform_edt(~saltm) / R8 <= 0.15 + 0.5 * _wb                # (wavy edges: owner, Oct 17)
    volcm = ndi.binary_fill_holes(ndi.binary_closing(volcm, structure=disk(2 * R8))) & ~ndi.binary_dilation(saltm, iterations=2) & (X >= SWX)   # (one piece)
    _sp = [pos[v] for v in SPIRE if shown(v)]
    _ne = np.array(pos[8684]) - np.array(pos[8616]); _ne = _ne / np.hypot(*_ne); _pp = np.array([_ne[1], -_ne[0]]) * PAD   # (the diagonal 8616-8684, PAD to its north-east)
    _a = np.array(pos[8616]) + _pp; _b = np.array(pos[8684]) + _pp
    _side = (X - _a[0]) * (_b[1] - _a[1]) - (Y - _a[1]) * (_b[0] - _a[0])           # (< 0: south-west of the diagonal)
    _keep = (Y >= VOLC_TOP[1]) | (X <= pos[8616][0] + PAD) | ((_side <= 0) & (Y >= pos[8616][1] - PAD))
    volcm &= _keep
    if _sp: volcm &= cKDTree(_samples([_sp], 0.1)).query(np.c_[X.ravel(), Y.ravel()])[0].reshape(bh, bw) > 0.9   # (a hole for 8705, 8706: owner, Oct 17)
    _im = Image.new('L', (bw, bh), 0); ImageDraw.Draw(_im).rectangle([px((16.5 - SQ / 2, 110.5 - SQ / 2)), px((19 + SQ / 2, 116 + SQ / 2))], fill=255)   # (16.5,110.5 - 19,116 all clearing: owner, Oct 17)
    stepm = roompatch(STEPPE) | np.array(_im, bool); stepm = ndi.binary_fill_holes(ndi.binary_closing(stepm, structure=disk(R8)))
    clear = (cellmask(dirt_cells) | stepm) & ~volcm & ~saltm
    lab, n = ndi.label(clear); keep = np.zeros_like(clear)
    for i in range(1, n + 1):
        comp = lab == i
        if comp.sum() / R8 / R8 >= MIN_PATCH: keep |= comp
    clear = keep & ~sea

    # ---- the foothills: the range's clearing carried on over 664, 665 and 8548-8563 (owner, Oct 17)
    fim = Image.new('L', (bw, bh), 0); fd = ImageDraw.Draw(fim); sq = int(SQ * R8)
    F = [v for v in FOOT if shown(v)]
    for v in F:
        p = px(pos[v]); fd.rectangle([p[0] - sq / 2, p[1] - sq / 2, p[0] + sq / 2, p[1] + sq / 2], fill=255)
    for a, b, k in E:
        if a in FOOT and b in FOOT: fd.line([px(pos[a]), px(pos[b])], fill=255, width=sq)
    jp = {v: pos[v] for v in FOOT_JOIN if v in pos}
    for a, b, k in E:
        for f_, j_ in ((a, b), (b, a)):
            if f_ in FOOT and j_ in jp: fd.line([px(pos[f_]), px(jp[j_])], fill=255, width=sq)
    footm = np.array(fim, bool)
    footc = [c for c in cells if c <= FOOT]
    footm |= cellmask(footc) if footc else False
    footm = ndi.gaussian_filter(ndi.binary_dilation(footm, iterations=2).astype(float), 0.45 * R8) > 0.5
    old = [p for p in (w.get('smrpatch') or []) if any(box[0] <= q[0] < box[2] and box[1] <= q[1] < box[3] for q in p)]
    oldm = AA._raster(old, box[0], box[1], bw, bh) if old else np.zeros((bh, bw), bool)
    pim = Image.new('L', (bw, bh), 0); pd_ = ImageDraw.Draw(pim); pw = int(SQ * R8)
    pp_ = [px(pos[v]) for v in PASS if v in pos and shown(v)]
    pd_.line(pp_, fill=255, width=pw, joint='curve')
    for q in pp_: pd_.ellipse([q[0] - pw / 2, q[1] - pw / 2, q[0] + pw / 2, q[1] + pw / 2], fill=255)
    passm = ndi.gaussian_filter(np.array(pim, bool).astype(float), 0.3 * R8) > 0.5
    rep['pass_sq'] = round(float((passm & ~oldm).sum()) / R8 / R8, 1)
    clear = clear | passm
    allm = (clear | footm) & ~oldm                                                   # (the range's own clearings are left exactly as they are; ours only meet them)
    patches = AA._contours(allm, box[0], box[1], sigma=1.0, tol=0.35, minarea=MIN_PATCH * 0.5)
    w['smrpatch'] = list(w.get('smrpatch') or []) + patches
    w['wlash'] = AA._contours(volcm & ~sea, box[0], box[1], sigma=1.0, tol=0.35, minarea=0.5)
    rep['sections'] = dict(steppe_rooms=len(STEPPE), salt_rooms=len(SALTR), volcanic_rooms=len(VOLC), south_west_rooms=len(SW), salt_sq=round(float(saltm.sum()) / R8 / R8, 1), volcanic_clearing_sq=round(float(volcm.sum()) / R8 / R8, 1))
    rep['clearings'] = dict(cells=len(dirt_cells), sq=round(float(clear.sum()) / R8 / R8, 1), foothills_sq=round(float(footm.sum()) / R8 / R8, 1),
                            range_clearings_joined=len(old), salt_cells=len(salt_cells))
    patchm = AA._raster(patches, box[0], box[1], bw, bh)

    # ---------------------------------------------------------------- Camden (owner, Oct 17): a soft, wavy town ground (no border), the sea its south edge; dirt streets;
    # front-view medieval / Renaissance buildings; a western saloon for the Dancing Pony Inn; a wooden pier out over the coast route
    T = [v for v in TOWN if shown(v) and not void(v) and v not in PIERS]
    street = lambda v: re.search(r'Streets of Camden|Narrow Road|Outskirts|Camden by the Sea|Entering the Cove', nm(v))
    SG = defaultdict(set)
    for a, b, k in E:
        if k != 'ud' and a in TOWN and b in TOWN and not {a, b} & set(PIERS) and (street(a) or void(a)) and (street(b) or void(b)): SG[a].add(b); SG[b].add(a)
    streets = _chains(SG, pos, set(), 0.4) if SG else []
    sst = _samples(streets, 0.1) if streets else np.zeros((0, 2))
    core = np.zeros((bh, bw), bool)
    for v in T: core |= (np.abs(X - pos[v][0]) <= 1.2) & (np.abs(Y - pos[v][1]) <= 1.2)
    if len(sst): core |= cKDTree(sst).query(P)[0].reshape(bh, bw) <= 1.0
    core = ndi.binary_closing(core, structure=disk(int(1.5 * R8)))
    _tw = ndi.gaussian_filter(np.random.default_rng(seed + 11).normal(size=(bh, bw)), 0.8 * R8); _tw = (_tw - _tw.min()) / (_tw.max() - _tw.min())
    townm = (ndi.distance_transform_edt(~core) / R8 <= 0.2 + 0.7 * _tw) & landm & ~sea   # (wavy edges; the sea is its south edge)
    townm = ndi.gaussian_filter(townm.astype(float), 0.4 * R8) > 0.5
    w['wltown'] = AA._contours(townm, box[0], box[1], sigma=1.2, tol=0.3, minarea=0.5)
    kinds = []
    for v in sorted(T):
        n_ = nm(v)
        if re.search(r'Church', n_): kinds.append((v, 'church', 1.3, 1.9))
        elif re.search(r'Mercantile|Savings|Fishery|Boatyards', n_): kinds.append((v, 'renaissance', 1.3, 1.3))
        elif re.search(r'Home|Lofts', n_): kinds.append((v, 'english', 1.15, 1.1))
    blds = []
    for v, k, bw_, bh_ in kinds:
        cx, cy = pos[v]
        for step in (0, 0.1, 0.2, 0.3, 0.4, 0.5):                                    # off the streets by the smallest step
            ok = [(cx + dx, cy + dy) for dx, dy in ((0, 0), (step, 0), (-step, 0), (0, -step), (0, step))
                  if not (len(sst) and np.any((np.abs(sst[:, 0] - cx - dx) < bw_ / 2 + 0.25) & (np.abs(sst[:, 1] - cy - dy) < bh_ / 2 + 0.25)))]
            if ok: cx, cy = ok[0]; break
        blds.append({'x': round(cx, 2), 'y': round(cy, 2), 'w': bw_, 'h': bh_, 'k': k, 'roof': '', 'rot': 0, 'room': v})
    w['smrhouses'] = list(w.get('smrhouses') or []) + [{q: b[q] for q in ('x', 'y', 'w', 'h', 'k', 'roof', 'rot')} for b in blds]
    gfx = []
    if 8744 in pos and shown(8744):
        gfx.append({'k': 'saloon', 'at': 'xy', 'x': pos[8744][0], 'y': round(pos[8744][1] - 0.1, 2), 'w': 2.2, 'h': 1.7})   # (the Dancing Pony Inn)
    pr = [pos[v] for v in PIERS if v in pos and shown(v)]
    if pr:
        px_ = pr[0][0]; c_ = int((px_ - box[0]) * R8); y_top = min(p[1] for p in pr)
        for r_ in range(int((y_top - box[1]) * R8), bh):                             # (from the shore)
            if sea[r_, c_]: y_top = (r_ + .5) / R8 + box[1]; break
        y_top -= 0.35; y_bot = max(p[1] for p in pr) + 0.6
        gfx.append({'k': 'pier', 'at': 'xy', 'x': round(px_, 2), 'y': round((y_top + y_bot) / 2, 2), 'w': 0.7, 'h': round(y_bot - y_top, 2)})
    for v, k, sz in ((8557, 'ladderhole', 0.95), (8645, 'ladderexit', 0.95)):          # the hidden way down 8557 -> 8645: a ladder into a hole, and where it comes out (owner, Oct 17)
        if v in pos: gfx.append({'k': k, 'at': 'xy', 'x': pos[v][0], 'y': pos[v][1], 'w': sz, 'h': sz})
    if 8706 in pos: gfx.append({'k': 'darktower', 'at': 'xy', 'x': pos[8706][0], 'y': round(pos[8706][1] - 1.25, 2), 'w': 1.4, 'h': 2.6})   # the Tower of Despair, standing over 8706 (owner, Oct 17)
    w['gfx'] = list(w['gfx']) + gfx
    tb = (float(X[townm].min()), float(Y[townm].min()), float(X[townm].max()), float(Y[townm].max())) if townm.any() else (0, 0, 0, 0)
    rep['camden'] = dict(box=[round(q, 2) for q in tb], ground_sq=round(float(townm.sum()) / R8 / R8, 1), streets=len(streets), buildings=[(b['k'], b['room']) for b in blds], gfx=gfx)
    for a in list(GD):                                                               # (the town's own paths are its streets)
        for b in list(GD[a]):
            if a in TOWN and b in TOWN: GD[a].discard(b); GD[b].discard(a)
    for v in [v for v in GD if not GD[v]]: del GD[v]

    # ---------------------------------------------------------------- lines: trails, the wide road, links
    saltd = ndi.binary_dilation(saltm | AA._raster(AA._contours(saltm, box[0], box[1], sigma=2.0, tol=0.3, minarea=0.5), box[0], box[1], bw, bh), iterations=int(0.35 * R8))
    blocked = patchm | ndi.binary_dilation(saltm | AA._raster(AA._contours(saltm, box[0], box[1], sigma=2.0, tol=0.3, minarea=0.5), box[0], box[1], bw, bh), iterations=int(0.35 * R8)) | volcm   # (the salt as drawn reaches a little past its mask)
    def trails(G):
        Tg = defaultdict(set)
        for a in G:
            for b in G[a]:
                if a >= b: continue
                if {a, b} & SPIRE: Tg[a].add(b); Tg[b].add(a); continue          # (drawn on top of the clearing)
                n_ = max(2, int(math.dist(pos[a], pos[b]) * 3)); inside = True
                for i in range(n_ + 1):
                    x = pos[a][0] + (pos[b][0] - pos[a][0]) * i / n_; y = pos[a][1] + (pos[b][1] - pos[a][1]) * i / n_
                    c, r = int((x - box[0]) * R8), int((y - box[1]) * R8)
                    if not (0 <= r < bh and 0 <= c < bw and blocked[r, c]): inside = False; break
                if not inside: Tg[a].add(b); Tg[b].add(a)
        return Tg
    river = set()                                                                    # (the river rooms are plain paths: owner, Oct 17)
    GS_ = defaultdict(set)                                                           # the river: a stream along its rooms
    for a in list(GD):
        for b in list(GD[a]):
            if a in river and b in river: GS_[a].add(b); GD[a].discard(b)
    for v in [v for v in GD if not GD[v]]: del GD[v]
    JUN = {u for e in uds for u in e if u not in UW}                                  # (the rooms where a way down to the coast leaves a path: the path runs through them exactly)
    dirt = _chains(trails(GD), pos, set(), 0.8, exact=JUN | {u for v in JUN for u in GD.get(v, ())})   # (and their neighbours: no kinks beside them)
    roadl = _chains(GR, pos, set(), 0.8) if GR else []
    stream = _chains(GS_, pos, set(), 0.8) if GS_ else []
    road_ext = []; pads = []
    smr_road = [_drawn(l) for l in (w.get('smrroad') or [])]
    _pe = {frozenset(e) for e in zip(PASS[:-1], PASS[1:])}
    for a, b in links:
        if frozenset((a, b)) in _pe: continue                                       # (inside the pass's wide path)
        o, f = (a, b) if a in WL else (b, a)
        q = pos[f]
        if f in UN and smr_road:                                                    # (a link to the trade route ends on its drawn road, with an off-ramp)
            q = _nearest_on(smr_road, pos[f]); pads.append([round(q[0], 2), round(q[1], 2)])
        ln = [[round(pos[o][0], 2), round(pos[o][1], 2)], [round(q[0], 2), round(q[1], 2)]]
        (road_ext if o in road else dirt).append(ln)
    for a, b in uds:
        if math.dist(pos[a], pos[b]) <= 30: dirt.append([[round(pos[a][0], 2), round(pos[a][1], 2)], [round(pos[b][0], 2), round(pos[b][1], 2)]])
    def clip(lines, mask):
        out = []
        for ln in lines:
            pts = []
            for p, q in zip(ln[:-1], ln[1:]):
                n_ = max(1, int(math.dist(p, q) / 0.08)); pts += [(p[0] + (q[0] - p[0]) * k / n_, p[1] + (q[1] - p[1]) * k / n_) for k in range(n_)]
            pts.append(tuple(ln[-1]))
            ins = []
            for x, y in pts:
                c, r = int((x - box[0]) * R8), int((y - box[1]) * R8); ins.append(0 <= r < bh and 0 <= c < bw and bool(mask[r, c]))
            if not any(ins): out.append(ln); continue
            run = []
            for pt, i_ in zip(pts + [None], ins + [True]):
                if i_ or pt is None:
                    if len(run) >= 2:
                        th = run[::4] + ([run[-1]] if run[::4][-1] != run[-1] else [])
                        l2 = [[round(x, 2), round(y, 2)] for x, y in th]
                        if math.dist(l2[0], l2[-1]) >= 0.25: out.append(l2)
                    run = []
                else: run.append(pt)
        return out
    spire = [l for l in dirt if any(math.dist(q, pos[v]) < 0.05 for v in SPIRE | {u for e in uds for u in e if u in UW} for q in (l[0], l[-1]))]   # (and the up/down links to the coast, whole)
    _jm = np.zeros_like(blocked)
    for v in JUN: _jm |= (X - pos[v][0]) ** 2 + (Y - pos[v][1]) ** 2 <= 0.7 ** 2
    dirt = clip([l for l in dirt if l not in spire], blocked & ~(_jm & ~saltd)) + spire
    _au = [pos.get(7852), pos.get(7853), EXTRA_HIDDEN.get(7854)]                       # (a regular path 7852 - 7853 - the City of Aurora marker at 7854, over the clearing: owner, Oct 17)
    if all(_au): dirt.append([[round(q[0], 2), round(q[1], 2)] for q in _au])          # (paths reach those rooms even at a clearing's edge)
    roadl = roadl + road_ext
    w['fwtracks'] = list(w['fwtracks']) + dirt + streets                           # (Camden's streets: dirt streets on its ground)
    w['dirtroads'] = list(w.get('dirtroads') or []) + roadl
    w['streams'] = list(w.get('streams') or []) + stream
    w['ntrjoins'] = list(w['ntrjoins']) + pads
    dl = [[[round(pos[a][0], 2), round(pos[a][1], 2)], [round(pos[b][0], 2), round(pos[b][1], 2)]] for a, b in dash if math.dist(pos[a], pos[b]) <= 30]
    w['smrdash'] = list(w.get('smrdash') or []) + dl
    sd = [[[round(pos[a][0], 2), round(pos[a][1], 2)], [round(pos[b][0], 2), round(pos[b][1], 2)]] for a, b, k in sdash if k == 'ud' and math.dist(pos[a], pos[b]) <= 30]
    w['seadash'] = list(w.get('seadash') or []) + sd
    CG = defaultdict(set)
    for a, b, k in sdash:
        if k != 'ud': CG[a].add(b); CG[b].add(a)
    sw_ = _chains(CG, pos, set(), 0.8) if CG else []
    w['seaways'] = list(w.get('seaways') or []) + sw_
    rep['lines'] = dict(trails=len(dirt), road=len(roadl), stream=len(stream), underground_dashed=len(dl), underwater_dashed=len(sd), coast_route=len(sw_), offramps=pads,
                        links=[(a, b) for a, b in links])

    # ---------------------------------------------------------------- the sea, the sand along it
    water = w['geo']['water']
    seap = AA._contours(sea, box[0], box[1], sigma=1.5)
    w['geo']['water'] = list(water) + seap
    rep['sea'] = dict(sq=round(float(sea.sum()) / R8 / R8, 1), seeds=store['sea_pts'], land_new_sq=store.get('land_new_sq'))
    sea = sea | ndi.binary_dilation(AA._raster(seap, box[0], box[1], bw, bh), iterations=2)   # (the sea as drawn: no ground or sprites under it)
    land_wl = landm & ~sea
    d_sea = ndi.distance_transform_edt(~sea) / R8
    sand = land_wl & (d_sea <= 0.45) & ~townm

    # ---------------------------------------------------------------- ground: what each spot is nearest to
    allL = [l for l in dirt + roadl + stream + streets]
    d_path = cKDTree(_samples([_drawn(l) for l in allL], 0.1)).query(P)[0].reshape(bh, bw) if allL else np.full((bh, bw), np.inf)
    d_path = np.minimum(d_path, ndi.distance_transform_edt(~patchm) / R8)
    rs = [v for v in WL if shown(v) and not void(v) and v not in under and (v in GD or v in GR or v in GS_ or v in TOWN or v in FOOT or any(v in e for e in links + uds))]
    tr = cKDTree(np.array([pos[v] for v in rs])); dist, idx = tr.query(P)
    S = np.array([sec[v] for v in rs])[idx].reshape(bh, bw); dist = dist.reshape(bh, bw)
    inSW = np.array([v in SW for v in rs])[idx].reshape(bh, bw)
    on = land_wl & (dist <= TERR_R) & ~sand
    fx = [pos[v] for v, r in info.items() if r.get('fixed') and v in pos]
    d_fix = cKDTree(np.array(fx)).query(P)[0].reshape(bh, bw) if fx else np.full((bh, bw), np.inf)
    own = land_wl & (dist <= LAND_R + 8) & (dist < d_fix)                         # (the Wastelands' own ground: nearer its rooms than the range's: owner, Oct 17)
    on &= own
    rng = np.random.default_rng(seed + 3)
    nz = ndi.gaussian_filter(rng.normal(size=(bh, bw)), 1.4 * R8); nz = (nz - nz.min()) / (nz.max() - nz.min())
    sm = lambda m, s=0.6: ndi.gaussian_filter(m.astype(float), s * R8) > 0.5
    zone = lambda *ks: sm(on & np.isin(S, ks))
    swm = sm(land_wl & inSW & (dist <= TERR_R + 1.5), 0.8) & (X >= SWX)                       # the south-west corner: one ground, ash (owner, Oct 17)
    fieldz = own                                                                   # (ONE ground in the Wastelands, under everything: owner, Oct 17)
    tints = {}
    clipped = {}                                                                   # (no other tint under or over it: the range's own, cut back to where the Wastelands' ground starts)
    inbox = lambda p: all(box[0] <= q[0] < box[2] and box[1] <= q[1] < box[3] for q in p)
    for k in [k for k in w['geo'] if k not in ('land', 'water')]:
        hit = [p for p in w['geo'][k] if inbox(p) and (AA._raster([p], box[0], box[1], bw, bh) & own).any()]
        part = [p for p in w['geo'][k] if not inbox(p) and any(box[0] <= q[0] < box[2] and box[1] <= q[1] < box[3] for q in p)]
        if part: rep.setdefault('tints_not_clipped', {})[k] = len(part)
        if not hit: continue
        bb = lambda p: (min(q[0] for q in p), min(q[1] for q in p), max(q[0] for q in p), max(q[1] for q in p))
        grp = [p for p in w['geo'][k] if inbox(p) and (p in hit or any(bb(h)[0] <= bb(p)[0] and bb(h)[1] <= bb(p)[1] and bb(p)[2] <= bb(h)[2] and bb(p)[3] <= bb(h)[3] for h in hit))]   # (with their holes)
        m = AA._raster(grp, box[0], box[1], bw, bh)
        cut = float((m & own).sum()) / R8 / R8
        w['geo'][k] = [p for p in w['geo'][k] if not any(p is g for g in grp)] + AA._contours(m & ~own, box[0], box[1], sigma=1.0, tol=0.3, minarea=0.15)
        clipped[k] = round(cut, 1)
    rep['other_tints_clipped_sq'] = clipped
    tints['wheat'] = _put(w, 'wheat', fieldz, box, sigma=2.0)
    blob = lambda m: ndi.binary_opening(m, structure=disk(R8))                     # (no thin strips)
    tints['wheat2'] = 0
    _cst = cKDTree(np.array([pos[v] for v in UW if shown(v)])).query(P)[0].reshape(bh, bw) if UW else np.full((bh, bw), np.inf)
    tints['wheat3'] = 0
    w['wlsalt'] = AA._contours(saltm & land_wl, box[0], box[1], sigma=2.0, tol=0.3, minarea=0.5)   # (one salt ground, drawn on top with a clean edge: owner, Oct 17)
    tints['salt'] = round(float((saltm & land_wl).sum()) / R8 / R8, 1)
    gr = _place(saltm & land_wl, X, Y, 0.28, 99)                                    # (a granular crust: owner, Oct 17)
    w['wlgrain'] = [[x, y, round(0.035 + 0.04 * float(_hash(x, y, 98)), 3), int(float(_hash(x, y, 97)) * 2)] for x, y in gr]
    rep['salt_grains'] = len(gr)
    volc = swm
    tints['ash'] = 0
    des = zone('desert') & ~swm
    tints['dunes'] = 0
    cliff = zone('cliff') & ~swm
    tints['clifftop'] = 0
    can = zone('canyon') & ~swm
    tints['barren'] = 0
    shore = (zone('shore') | sand) & ~swm
    tints['sand'] = 0
    rep['tints_sq'] = tints

    # ---------------------------------------------------------------- sprites (clear of paths, clearings, the town, the sea)
    _vr = [pos[v] for v in VOLCANO if v in pos]
    VB = (min(p[0] for p in _vr) - 1.0, min(p[1] for p in _vr) - 0.9, max(p[0] for p in _vr) + 1.0, max(p[1] for p in _vr) + 0.6) if _vr else None
    volm = ((X >= VB[0]) & (X <= VB[2]) & (Y >= VB[1]) & (Y <= VB[3])) if VB else np.zeros((bh, bw), bool)
    onway = volm | (d_path <= 0.55) | patchm | townm | sea | saltm | volcm                                 # (the range's sprites, placed before these paths existed, give way to them)
    def off(q):
        c, r = int((q[0] - box[0]) * R8), int((q[1] - box[1]) * R8)
        return 0 <= r < bh and 0 <= c < bw and bool(onway[r, c])
    cl = {}
    for k in ('trees', 'tufts', 'peaks', 'hills', 'boulders', 'crags', 'brush', 'wheattufts', 'ripples'):
        n0 = len(w.get(k) or []); w[k] = [q for q in (w.get(k) or []) if not off(q)]
        if n0 - len(w[k]): cl[k] = n0 - len(w[k])
    rep['old_sprites_cleared'] = cl
    old = [q[:2] for k in ('trees', 'tufts', 'peaks', 'hills', 'boulders', 'crags', 'brush', 'wheattufts', 'ripples') for q in (w.get(k) or [])
           if box[0] <= q[0] <= box[2] and box[1] <= q[1] <= box[3]]
    free = land_wl & ~volm & (d_path > 0.6) & ~townm & ~patchm & ~saltm & ~volcm & own
    spr = {}
    hillz = free & zone('hills') & ~swm & (d_path > 1.0)                                  # (the bigger sprites first, then the grass between them)
    hills = _place(hillz, X, Y, 1.8, 87, old)
    w['hills'] = list(w['hills']) + [[x, y, round(0.8 + 0.3 * float(_hash(x, y, 88)), 2), 'h', int(float(_hash(x, y, 89)) * 3)] for x, y in hills]
    crz = free & (volc | can) & (d_path > 0.8)
    crags = _place(crz, X, Y, 1.5, 90, old + hills)
    w['crags'] = sorted(list(w.get('crags') or []) + [[x, y, round(0.55 + 0.3 * float(_hash(x, y, 91)), 2), int(float(_hash(x, y, 92)) * 3)] for x, y in crags], key=lambda b: b[1])
    rocks = _place(free & cliff & (d_path > 0.5), X, Y, 1.0, 93, old + hills + crags)
    w['boulders'] = list(w.get('boulders') or []) + [[x, y, round(0.4 + 0.3 * float(_hash(x, y, 94)), 2)] for x, y in rocks]
    rip = []
    w['ripples'] = sorted(list(w.get('ripples') or []) + [[x, y, round(0.6 + 0.3 * float(_hash(x, y, 96)), 2), int(float(_hash(x, y, 97)) * 3)] for x, y in rip], key=lambda b: b[1])
    brush = _place(free & fieldz & (nz <= 0.45) & (d_path > 0.9), X, Y, 2.6, 84, old + hills + crags + rocks)
    w['brush'] = sorted(list(w.get('brush') or []) + [[x, y, round(0.7 + 0.3 * float(_hash(x, y, 85)), 2), int(float(_hash(x, y, 86)) * 2)] for x, y in brush], key=lambda b: b[1])
    tufts = _place(free & fieldz & (nz > 0.25), X, Y, 1.0, 81, old + hills + crags + rocks + brush)
    w['wheattufts'] = sorted(list(w.get('wheattufts') or []) + [[x, y, round(0.75 + 0.3 * float(_hash(x, y, 82)), 2), int(float(_hash(x, y, 83)) * 2)] for x, y in tufts], key=lambda b: b[1])
    if VB:                                                                           # the volcano graphic over its three rooms (owner, Oct 17)
        g = {'k': 'volcano', 'at': 'xy', 'x': round((VB[0] + VB[2]) / 2, 2), 'y': round((VB[1] + VB[3]) / 2, 2), 'w': round(VB[2] - VB[0], 2), 'h': round(VB[3] - VB[1], 2)}
        w['gfx'] = list(w['gfx']) + [g]; spr['volcano'] = g
    spr.update(wheattufts=len(tufts), brush=len(brush), hills=len(hills), crags=len(crags), boulders=len(rocks), dune_ripples=len(rip))
    rep['sprites'] = spr

    w['arealabels'] = list(w.get('arealabels', [])) + [dict(x=34.0, y=96.8, lh=2.6, sag=1.0, hw=11, lines=['Wastelands'])]   # the area's name in the open steppes clearing east of the Ancient Road (owner, Oct 17)

    # ---------------------------------------------------------------- the map grows south
    ys_ = [q[1] for k in ('land', 'water') for p in w['geo'][k] for q in p]; xs_ = [q[0] for k in ('land', 'water') for p in w['geo'][k] for q in p]
    b0 = list(w['bounds'])
    w['bounds'] = [b0[0], b0[1], max(b0[2], int(math.ceil(max(xs_)))), max(b0[3], int(math.ceil(max(ys_))) + 1)]
    rep['bounds'] = [b0, w['bounds']]
    rep['rooms'] = dict(shown=len([v for v in WL if shown(v) and not void(v)]), hidden=len([v for v in WL if v in hidden]), underwater=len([v for v in UW if not void(v)]))
    return w, rep


SUBAREAS = ("Camden", "City of Aurora", "Badlands", "Mulciber's Forge", "Realm of Worship", "Shattered Temple of Naetrelle", "Tayalardian Rangelands", "Thalos",
            "Tower of Despair")   # the Wastelands' sub-areas with directions in data.py (owner, Oct 17: not The Mire, the Desert of Despair, the Sea of Sorrows)


def add_wl_places(w, layouts):
    """the Wastelands' sub-area destinations, traced from the owner's directions: the marker where the route leaves the drawn rooms"""
    import data as DT
    from route_fix import make_tracer
    from extra_places import segments
    rooms, walk, at = make_tracer(w, layouts)
    lines = (DT.AREAS + '\n' + DT.MORE_DIRECTIONS).split('\n')
    rep = {}
    for name in SUBAREAS:
        if any(p['name'] == name for p in w['places']): rep[name] = 'already on the map'; continue
        route = next(l.split('|', 1)[1].strip().rstrip(';') for l in lines if l.startswith(name + '|'))
        t = walk(route)
        last = max(i for i, v in enumerate(t) if at(v))
        upto = t[:last + 1]; segs = segments([at(v) for v in upto])
        d = 'here' if last == len(t) - 1 else re.sub(r'^#\s*\d+\s*', '', route.split(';')[-1].strip())   # (the way out of the map: '#5 n' -> 'n')
        w['places'].append(dict(name=name, route=route, room=rooms[upto[-1]]['name'], dir=d, path=[q for s_ in segs for q in s_], segs=segs,
                                group='af', where='in the Wastelands' if name == 'Camden' else 'off the Wastelands',
                                note=None if len(segs) == 1 else "Part of your directions passes through areas that aren't drawn yet, so the traced line breaks there."))
        rep[name] = dict(end_room=upto[-1], walked=len(t), dir=d, pieces=len(segs), marker=segs[-1][-1])
    DV = {'n': (0, -1), 's': (0, 1), 'e': (1, 0), 'w': (-1, 0), 'ne': (.7, -.7), 'nw': (-.7, -.7), 'se': (.7, .7), 'sw': (-.7, .7)}
    def pin(name):                                                                   # (where the template puts the pin)
        p = next((p for p in w['places'] if p['name'] == name), None)
        if not p: return None
        e = p['path'][-1]; v = DV.get(p['dir'], (0, 0)); return (e[0] + v[0] * .62, e[1] + v[1] * .62)
    g = []
    for name in ('City of Aurora', 'Thalos'):                                        # a city south of each marker (owner, Oct 17)
        q = pin(name)
        if q: g.append({'k': 'stonecity', 'at': 'xy', 'x': round(q[0], 2), 'y': round(q[1] + 0.55 + 2.15 / 2, 2), 'w': 2.6, 'h': 2.15})
    q = pin('Shattered Temple of Naetrelle')                                         # the shattered temple north of its marker (owner, Oct 17)
    if q: g.append({'k': 'shatteredtemple', 'at': 'xy', 'x': round(q[0], 2), 'y': round(q[1] - 0.55 - 1.6 / 2, 2), 'w': 2.4, 'h': 1.6})
    th = next((x for x in g if x['k'] == 'stonecity' and abs(x['x'] - (pin('Thalos') or (1e9,))[0]) < 0.01), None)
    inn = next((x for x in w['gfx'] if x.get('k') == 'saloon'), None)
    if th and inn:                                                                   # the inn centred between the Thalos city's east edge and the street east of it (8750-8752, x 28.5) (owner, Oct 17)
        inn['x'] = round(((th['x'] + th['w'] / 2) + (28.5 - 0.3)) / 2, 2); rep['inn_x'] = inn['x']
    w['gfx'] = list(w['gfx']) + g; rep['gfx'] = g
    return w, rep
