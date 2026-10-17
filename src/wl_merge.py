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
NO_LINK = {frozenset((8557, 8645))}             # not drawn (owner, Oct 17)
TOWN = {8726, 18259} | set(range(8743, 8770))   # Camden
SEA_AREAS = ('The Blood Sea', 'Sea of Sorrows')
LAND_R, SEA_R, TERR_R = 4.2, 8.0, 3.2
PAD, SQ, CELL_MAX, MIN_PATCH = 0.55, 1.1, 6.0, 3.0                  # (the range's rule, owner Oct 14: clumps follow the exits, not the spacing)
SEED = 173


def section(name, terrain):
    for k, pat in (('road', r'Ancient Road|Fork in the Road|Tired Wooden Bridge'), ('salt', r'Salt Flats'), ('volcano', r'Atop the Volcano|Upon the Volcano'),
                   ('volc', r'Volcanic'), ('desert', r'Fringes|Desert|Golden Sands'), ('shore', r'Shore|Beach|Ahtborne'),
                   ('cliff', r'Cliff|Narrow Path|Promontory|Junction in the Path|Small Cave|Stone Spire'), ('river', r'River|Crumbling Bridge'),
                   ('under', r'Darkness|Tunnel|Hole In The Ground'), ('canyon', r'Canyon|Chasm|Cavern|Crevice'),
                   ('hills', r'Foothill|Hills|Gully|Hill|Slope|Pass')):
        if re.search(pat, name or ''): return k
    return 'field'


def _setup(layout, edges):
    rooms, _ = AF._world()
    pos = dict(zip(layout['ids'], zip(layout['xs'], layout['ys'])))
    info = {r['id']: r for r in edges['rooms']}
    hidden = set(layout.get('hidden', []))
    WL = {v for v, r in info.items() if r.get('area') == 'WL' and r.get('grp') == 'wl' and v in pos}
    shown = lambda v: v in pos and v not in hidden
    void = lambda v: bool(info.get(v, {}).get('void'))
    terr = lambda v: rooms[v]['terrain'] if v in rooms else ''
    sec = {v: section(rooms[v]['name'], terr(v)) for v in WL}
    for v in WL:                                                                     # (a spacer takes its neighbours' section below)
        if void(v): sec[v] = None
    UW = {v for v in WL if terr(v) == 'Underwater'}
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
    road = {v for v in WL if sec[v] == 'road'}
    under = {v for v in WL if sec[v] == 'under' or terr(v) == 'Underground'}
    return rooms, pos, info, hidden, WL, shown, void, terr, sec, UW, E, road, under


def wl_land(layout, edges, store, seed=SEED):
    """land_edit for smr_merge: the Wastelands' land added to the grid, the sea kept out of it (and remembered in store for merge_wl)"""
    rooms, pos, info, hidden, WL, shown, void, terr, sec, UW, E, road, under = _graphs(layout, edges)
    dry = [v for v in WL if shown(v) and v not in UW]
    land_lines = []; sea_pts = [pos[v] for v in UW if v in pos]
    for a, b, k in E:
        if k == 'ud': continue
        wa, wb = a in UW, b in UW
        if not wa and not wb: land_lines.append([pos[a], pos[b]])
        elif wa != wb:
            m = ((pos[a][0] + pos[b][0]) / 2, (pos[a][1] + pos[b][1]) / 2); d_ = b if wa else a
            land_lines.append([m, pos[d_]])
    for v in WL:                                                                     # the exits into the seas (not drawn): the sea lies that way
        if not shown(v): continue
        for e in AF._world()[1].get(v, []):
            t = e['to']
            if t in rooms and (rooms[t]['area'] in SEA_AREAS or (void(t) and t not in pos)) and e['dir'] in AF.DV:
                d = AF.DV[e['dir']]
                if d[2] or not (rooms[t]['area'] in SEA_AREAS or any(rooms.get(e2['to'], {}).get('area') in SEA_AREAS for e2 in AF._world()[1].get(t, []))): continue
                sea_pts.append((pos[v][0] + 2.2 * d[0], pos[v][1] + 2.2 * d[1]))
    xs = [pos[v][0] for v in dry] + [p[0] for p in sea_pts]; ys = [pos[v][1] for v in dry] + [p[1] for p in sea_pts]
    box = (math.floor(min(xs)) - 14, math.floor(min(ys)) - 10, math.ceil(max(xs)) + 14, math.ceil(max(ys)) + 14)
    bw, bh = int((box[2] - box[0]) * R8), int((box[3] - box[1]) * R8)
    gy, gx = np.mgrid[0:bh, 0:bw]; X = (gx + .5) / R8 + box[0]; Y = (gy + .5) / R8 + box[1]; P = np.c_[X.ravel(), Y.ravel()]
    lp = np.r_[np.array([pos[v] for v in dry]), _samples(land_lines, 0.15)]
    d_l = cKDTree(lp).query(P)[0].reshape(bh, bw)
    d_s = cKDTree(np.array(sea_pts)).query(P)[0].reshape(bh, bw) if sea_pts else np.full((bh, bw), np.inf)
    rng = np.random.default_rng(seed)
    wob = ndi.gaussian_filter(rng.normal(size=(bh, bw)), 1.8 * R8); wob = (wob - wob.min()) / (wob.max() - wob.min())
    sea = (d_s <= SEA_R * (0.8 + 0.4 * wob)) & (d_s < d_l)
    sea = ndi.gaussian_filter(sea.astype(float), 0.8 * R8) > 0.5
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
        if a in UW or b in UW:
            if k != 'ud' or (a in UW) == (b in UW): sdash.append((a, b))
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
    withsp = lambda core: core | {v for v in WL if void(v) and shown(v) and sum(1 for u in nbs[v] if u in core) >= 2}
    def roompatch(S_):                                                               # (owner, Oct 17: exactly the rooms and the exits between them, holes filled)
        im = Image.new('L', (bw, bh), 0); dr = ImageDraw.Draw(im); s_ = int(SQ * R8)
        for v in S_:
            p = px(pos[v]); dr.rectangle([p[0] - s_ / 2, p[1] - s_ / 2, p[0] + s_ / 2, p[1] + s_ / 2], fill=255)
        for a, b, k in E:
            if a in S_ and b in S_ and k != 'ud': dr.line([px(pos[a]), px(pos[b])], fill=255, width=s_)
        return ndi.gaussian_filter(ndi.binary_fill_holes(np.array(im, bool)).astype(float), 0.3 * R8) > 0.5
    STEPPE = withsp({v for v in WL if shown(v) and nm(v) == 'Arid Steppes'})        # every Arid Steppes room a clearing (owner, Oct 17)
    SALTR = withsp({v for v in WL if shown(v) and sec[v] == 'salt'})                 # the Salt Flats: a salt field on exactly its rooms (owner, Oct 17)
    VOLC = withsp({v for v in WL if shown(v) and sec[v] == 'volc'})                  # the Volcanic Plains rooms: an ash-coloured clearing (owner, Oct 17)
    SW = {v for v in WL if shown(v) and not void(v) and pos[v][0] <= 1 and pos[v][1] >= 96 and sec[v] not in ('road', 'salt') and nm(v) != 'Arid Steppes'}
    salt_cells = [c for c in cells if c & (SALTR | VOLC)]
    dirt_cells = [c for c in cells if c not in salt_cells]
    saltm = roompatch(SALTR); volcm = roompatch(VOLC)
    clear = (cellmask(dirt_cells) | roompatch(STEPPE)) & ~volcm & ~saltm
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
    old = [p for p in (w.get('smrpatch') or []) if (AA._raster([p], box[0], box[1], bw, bh) & ndi.binary_dilation(footm, iterations=3)).any()]
    allm = clear | footm
    if old:
        allm |= AA._raster(old, box[0], box[1], bw, bh)
        w['smrpatch'] = [p for p in w['smrpatch'] if p not in old]
    patches = AA._contours(allm, box[0], box[1], sigma=1.0, tol=0.35, minarea=MIN_PATCH * 0.5)
    w['smrpatch'] = list(w.get('smrpatch') or []) + patches
    w['wlash'] = AA._contours(volcm & ~sea, box[0], box[1], sigma=1.0, tol=0.35, minarea=0.5)
    rep['sections'] = dict(steppe_rooms=len(STEPPE), salt_rooms=len(SALTR), volcanic_rooms=len(VOLC), south_west_rooms=len(SW), salt_sq=round(float(saltm.sum()) / R8 / R8, 1), volcanic_clearing_sq=round(float(volcm.sum()) / R8 / R8, 1))
    rep['clearings'] = dict(cells=len(dirt_cells), sq=round(float(clear.sum()) / R8 / R8, 1), foothills_sq=round(float(footm.sum()) / R8 / R8, 1),
                            range_clearings_joined=len(old), salt_cells=len(salt_cells))
    patchm = AA._raster(patches, box[0], box[1], bw, bh)

    # ---------------------------------------------------------------- Camden: a small town (streets, inn, church, shops, homes)
    T = [v for v in TOWN if shown(v) and not void(v)]
    tx = [pos[v][0] for v in T]; ty = [pos[v][1] for v in T]
    tb = (min(tx) - 0.9, min(ty) - 0.9, max(tx) + 0.9, max(ty) + 0.9)
    street = lambda v: re.search(r'Streets of Camden|Narrow Road|Outskirts|Camden by the Sea|Entering the Cove|Piers', nm(v))
    SG = defaultdict(set)
    for a, b, k in E:
        if k != 'ud' and a in TOWN and b in TOWN and (street(a) or void(a)) and (street(b) or void(b)): SG[a].add(b); SG[b].add(a)
    streets = _chains(SG, pos, set(), 0.4) if SG else []
    sst = _samples(streets, 0.1) if streets else np.zeros((0, 2))
    roofs = ['#7A4638', '#86503C', '#6B4A36', '#5F4B3A', '#7E5A40', '#704034']
    blds = []
    for v in sorted(T):
        n_ = nm(v)
        if re.search(r'Dancing Pony Inn', n_): k, bw_, bh_ = 'inn', 1.7, 1.05
        elif re.search(r'Church', n_): k, bw_, bh_ = 'church', 1.1, 1.15
        elif re.search(r'Mercantile|Savings|Fishery|Boatyards', n_): k, bw_, bh_ = 'shop', 0.95, 0.8
        elif re.search(r'Home|Lofts', n_): k, bw_, bh_ = 'house', 0.8, 0.65
        else: continue
        cx, cy = pos[v]
        for step in (0, 0.1, 0.2, 0.3, 0.4, 0.5):                                    # off the streets by the smallest step
            ok = [(cx + dx, cy + dy) for dx, dy in ((0, 0), (step, 0), (-step, 0), (0, step), (0, -step))
                  if not (len(sst) and np.any((np.abs(sst[:, 0] - cx - dx) < bw_ / 2 + 0.3) & (np.abs(sst[:, 1] - cy - dy) < bh_ / 2 + 0.3)))]
            if ok: cx, cy = ok[0]; break
        blds.append({'x': round(cx, 2), 'y': round(cy, 2), 'w': bw_, 'h': bh_, 'k': k, 'roof': '#5E5B55' if k == 'church' else '#6A3C30' if k == 'inn' else roofs[v % len(roofs)], 'room': v})
    w['smrtowns'] = list(w.get('smrtowns') or []) + [{'name': 'Camden', 'ground': [round(q, 2) for q in tb], 'streets': streets, 'plaza': None, 'buildings': blds,
                                                       'trees': [], 'road': None, 'road2': None, 'gate_s': None, 'road_w': 0.95, 'gate': None}]
    townm = (X >= tb[0]) & (X <= tb[2]) & (Y >= tb[1]) & (Y <= tb[3])
    rep['camden'] = dict(box=[round(q, 2) for q in tb], streets=len(streets), buildings=[(b['k'], b['room']) for b in blds])
    for a in list(GD):                                                               # (the town's own paths are its streets)
        for b in list(GD[a]):
            if a in TOWN and b in TOWN: GD[a].discard(b); GD[b].discard(a)
    for v in [v for v in GD if not GD[v]]: del GD[v]

    # ---------------------------------------------------------------- lines: trails, the wide road, links
    blocked = patchm | townm | saltm | volcm
    def trails(G):
        Tg = defaultdict(set)
        for a in G:
            for b in G[a]:
                if a >= b: continue
                n_ = max(2, int(math.dist(pos[a], pos[b]) * 3)); inside = True
                for i in range(n_ + 1):
                    x = pos[a][0] + (pos[b][0] - pos[a][0]) * i / n_; y = pos[a][1] + (pos[b][1] - pos[a][1]) * i / n_
                    c, r = int((x - box[0]) * R8), int((y - box[1]) * R8)
                    if not (0 <= r < bh and 0 <= c < bw and blocked[r, c]): inside = False; break
                if not inside: Tg[a].add(b); Tg[b].add(a)
        return Tg
    river = {v for v in GD if sec.get(v) == 'river'}
    GS_ = defaultdict(set)                                                           # the river: a stream along its rooms
    for a in list(GD):
        for b in list(GD[a]):
            if a in river and b in river: GS_[a].add(b); GD[a].discard(b)
    for v in [v for v in GD if not GD[v]]: del GD[v]
    dirt = _chains(trails(GD), pos, set(), 0.8)
    roadl = _chains(GR, pos, set(), 0.8) if GR else []
    stream = _chains(GS_, pos, set(), 0.8) if GS_ else []
    road_ext = []; pads = []
    smr_road = [_drawn(l) for l in (w.get('smrroad') or [])]
    for a, b in links:
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
    dirt = clip(dirt, blocked)
    roadl = roadl + road_ext
    w['fwtracks'] = list(w['fwtracks']) + dirt
    w['dirtroads'] = list(w.get('dirtroads') or []) + roadl
    w['streams'] = list(w.get('streams') or []) + stream
    w['ntrjoins'] = list(w['ntrjoins']) + pads
    dl = [[[round(pos[a][0], 2), round(pos[a][1], 2)], [round(pos[b][0], 2), round(pos[b][1], 2)]] for a, b in dash if math.dist(pos[a], pos[b]) <= 30]
    w['smrdash'] = list(w.get('smrdash') or []) + dl
    sd = [[[round(pos[a][0], 2), round(pos[a][1], 2)], [round(pos[b][0], 2), round(pos[b][1], 2)]] for a, b in sdash if math.dist(pos[a], pos[b]) <= 30]
    w['seadash'] = list(w.get('seadash') or []) + sd
    rep['lines'] = dict(trails=len(dirt), road=len(roadl), stream=len(stream), underground_dashed=len(dl), underwater_dashed=len(sd), offramps=pads,
                        links=[(a, b) for a, b in links])

    # ---------------------------------------------------------------- the sea, the sand along it
    water = w['geo']['water']
    w['geo']['water'] = list(water) + AA._contours(sea, box[0], box[1], sigma=1.5)
    rep['sea'] = dict(sq=round(float(sea.sum()) / R8 / R8, 1), seeds=store['sea_pts'], land_new_sq=store.get('land_new_sq'))
    land_wl = landm & ~sea
    d_sea = ndi.distance_transform_edt(~sea) / R8
    sand = land_wl & (d_sea <= 0.45) & ~townm

    # ---------------------------------------------------------------- ground: what each spot is nearest to
    allL = [l for l in dirt + roadl + stream + streets]
    d_path = cKDTree(_samples([_drawn(l) for l in allL], 0.1)).query(P)[0].reshape(bh, bw) if allL else np.full((bh, bw), np.inf)
    d_path = np.minimum(d_path, ndi.distance_transform_edt(~patchm) / R8)
    rs = [v for v in WL if shown(v) and not void(v) and v not in UW and v not in under and (v in GD or v in GR or v in GS_ or v in TOWN or v in FOOT or any(v in e for e in links + uds))]
    tr = cKDTree(np.array([pos[v] for v in rs])); dist, idx = tr.query(P)
    S = np.array([sec[v] for v in rs])[idx].reshape(bh, bw); dist = dist.reshape(bh, bw)
    inSW = np.array([v in SW for v in rs])[idx].reshape(bh, bw)
    on = land_wl & (dist <= TERR_R) & ~sand
    own = land_wl & (dist <= LAND_R + 3)                                            # (the Wastelands' own ground: not the range's)
    rng = np.random.default_rng(seed + 3)
    nz = ndi.gaussian_filter(rng.normal(size=(bh, bw)), 1.4 * R8); nz = (nz - nz.min()) / (nz.max() - nz.min())
    sm = lambda m, s=0.6: ndi.gaussian_filter(m.astype(float), s * R8) > 0.5
    zone = lambda *ks: sm(on & np.isin(S, ks))
    swm = sm(land_wl & inSW & (dist <= TERR_R + 1.5), 0.8)                        # the south-west corner: one ground, ash (owner, Oct 17)
    fieldz = own & ~sand & ~zone('desert', 'cliff', 'canyon', 'shore') & ~townm & ~swm & ~saltm
    tints = {}
    tints['wheat'] = _put(w, 'wheat', fieldz, box, sigma=2.0)
    blob = lambda m: ndi.binary_opening(m, structure=disk(R8))                     # (no thin strips)
    tints['wheat2'] = _put(w, 'wheat2', blob(fieldz & (nz > 0.6)), box, sigma=2.5, minarea=1.5)
    tints['wheat3'] = _put(w, 'wheat3', blob(fieldz & (nz < 0.35)), box, sigma=2.5, minarea=1.5)
    tints['salt'] = _put(w, 'salt', saltm & land_wl, box, sigma=1.0)
    volc = swm
    tints['ash'] = _put(w, 'ash', swm, box, sigma=2.0)
    des = zone('desert') & ~swm
    tints['dunes'] = _put(w, 'dunes', des, box, sigma=2.0)
    cliff = zone('cliff') & ~swm
    tints['clifftop'] = _put(w, 'clifftop', cliff, box, sigma=1.5)
    can = zone('canyon') & ~swm
    tints['barren'] = _put(w, 'barren', can, box, sigma=2.0)
    shore = (zone('shore') | sand) & ~swm
    tints['sand'] = _put(w, 'sand', shore, box, sigma=1.0)
    rep['tints_sq'] = tints

    # ---------------------------------------------------------------- sprites (clear of paths, clearings, the town, the sea)
    onway = (d_path <= 0.55) | patchm | townm | sea | saltm | volcm                                 # (the range's sprites, placed before these paths existed, give way to them)
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
    free = land_wl & (d_path > 0.6) & ~townm & ~patchm & ~saltm & ~volcm & own
    spr = {}
    hillz = free & zone('hills') & ~swm & (d_path > 1.0)                                  # (the bigger sprites first, then the grass between them)
    hills = _place(hillz, X, Y, 1.8, 87, old)
    w['hills'] = list(w['hills']) + [[x, y, round(0.8 + 0.3 * float(_hash(x, y, 88)), 2), 'h', int(float(_hash(x, y, 89)) * 3)] for x, y in hills]
    crz = free & (volc | can) & (d_path > 0.8)
    crags = _place(crz, X, Y, 1.5, 90, old + hills)
    w['crags'] = sorted(list(w.get('crags') or []) + [[x, y, round(0.55 + 0.3 * float(_hash(x, y, 91)), 2), int(float(_hash(x, y, 92)) * 3)] for x, y in crags], key=lambda b: b[1])
    rocks = _place(free & cliff & (d_path > 0.5), X, Y, 1.0, 93, old + hills + crags)
    w['boulders'] = list(w.get('boulders') or []) + [[x, y, round(0.4 + 0.3 * float(_hash(x, y, 94)), 2)] for x, y in rocks]
    rip = _place(free & des & (d_path > 0.6), X, Y, 1.3, 95, old)
    w['ripples'] = sorted(list(w.get('ripples') or []) + [[x, y, round(0.6 + 0.3 * float(_hash(x, y, 96)), 2), int(float(_hash(x, y, 97)) * 3)] for x, y in rip], key=lambda b: b[1])
    brush = _place(free & fieldz & (nz <= 0.45) & (d_path > 0.9), X, Y, 2.6, 84, old + hills + crags + rocks)
    w['brush'] = sorted(list(w.get('brush') or []) + [[x, y, round(0.7 + 0.3 * float(_hash(x, y, 85)), 2), int(float(_hash(x, y, 86)) * 2)] for x, y in brush], key=lambda b: b[1])
    tufts = _place(free & fieldz & (nz > 0.25), X, Y, 1.0, 81, old + hills + crags + rocks + brush)
    w['wheattufts'] = sorted(list(w.get('wheattufts') or []) + [[x, y, round(0.75 + 0.3 * float(_hash(x, y, 82)), 2), int(float(_hash(x, y, 83)) * 2)] for x, y in tufts], key=lambda b: b[1])
    vr = [v for v in WL if shown(v) and sec[v] == 'volcano']                         # the volcano: a peak over its top rooms
    if vr:
        cx = sum(pos[v][0] for v in vr) / len(vr); cy = sum(pos[v][1] for v in vr) / len(vr)
        w['peaks'] = list(w['peaks']) + [[round(cx, 2), round(cy - 0.6, 2), 1.6, 'm', 2]]
        spr['volcano_peak'] = [round(cx, 2), round(cy - 0.6, 2)]
    spr.update(wheattufts=len(tufts), brush=len(brush), hills=len(hills), crags=len(crags), boulders=len(rocks), dune_ripples=len(rip))
    rep['sprites'] = spr

    # ---------------------------------------------------------------- the map grows south
    ys_ = [q[1] for k in ('land', 'water') for p in w['geo'][k] for q in p]; xs_ = [q[0] for k in ('land', 'water') for p in w['geo'][k] for q in p]
    b0 = list(w['bounds'])
    w['bounds'] = [b0[0], b0[1], max(b0[2], int(math.ceil(max(xs_)))), max(b0[3], int(math.ceil(max(ys_))) + 1)]
    rep['bounds'] = [b0, w['bounds']]
    rep['rooms'] = dict(shown=len([v for v in WL if shown(v) and not void(v)]), hidden=len([v for v in WL if v in hidden]), underwater=len([v for v in UW if not void(v)]))
    return w, rep
