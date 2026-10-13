"""Puts the Forest of Tears, the Lake of Tich'Pyga and the Western Trade Route you arranged in the layout editor on the map
(ft_layout_final.json, fot_editor_edges.json), replacing the old drawing of the forest and the lake.
Owner's instructions (Oct 13):
- Lake of Tich'Pyga: the rooms left shown are a path round the lake: a dirt trail through them, a lake drawn inside the ring, small dirt
  pathways to the Forgotten Woods rooms they link to.
- Western Trade Route: one continuous formal road (like the other trade routes) with an off-ramp pad where it joins a Forest of Tears room.
- The central forest is a field: ground and trees, no rooms, no paths.
- The linear threads outside the field are drawn as dirt trails: Lost Between Woods, the Sparse Woodlands, Alongside a Swampland, the Fog
  Cliffs, and Lost Between Woods to the Forgotten Woods (1669 -> 5491). The ground between the field and these paths is impassable: dense
  forest. A short band of dense forest lies beyond each path, then open map background; except on the north, where the land runs on to a
  smooth coast that meets the Forgotten Woods' and everything empty is dense forest.
- The Fog Cliffs path is the cliff edge of the area: its own terrain (rock, crags, peaks, fog); west of it is the sea.
- Markers (and their routes) of the sub-areas follow your rooms; Widow's Peak (Woods rooms 5634-5638) is moved and its Woods trail follows.
Runs right after the new west coast (the earliest land change) on gap_fill's raster grid (x -130..96, y -118..42).
"""
import math, random, re
import numpy as np
from collections import defaultdict, deque, Counter
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from PIL import Image, ImageDraw
import arrange_apply as AA
import gap_fill as GF
from ntr_merge import _chains, _samples, _nearest_on

X0, Y0, W, H, R8 = GF.X0, GF.Y0, GF.W, GF.H, GF.R8
WX, WY = GF.WX, GF.WY
XE = -19.5                         # the east edge of what is redrawn (the old land, tints and trees east of it stay)
FIELD_RE = re.compile(r'Misery|Drowning|Weeping|Trail of Tears')
CLIFF_RE = re.compile(r'Cliff|Wall|Edge|Rockslide|Canyon|Fault|Sandstone|Dry|Terrain')
WIDOWS = [5634, 5635, 5636, 5637, 5638]            # Woods rooms the owner moved (joined to 5632 and 5639)
# the new north-west coast: the west coast's curve (west_coast.CURVE, from the Woods' westernmost edge to the north coast of the forest), then on to the
# first room of the Lost Between Woods path in the west
COAST = [(-60.0, -64.0), (-62.5, -56.0), (-65.5, -47.0), (-69.0, -38.5), (-72.5, -31.0), (-75.6, -25.5), (-79.0, -21.6), (-88.0, -18.3), (-97.0, -15.8), (-106.0, -14.0)]


def _pts_mask(pts, r, shape, org):
    """Discs of radius r (rooms) round points, on a sub-grid whose top-left cell is org=(ix0, iy0)."""
    img = Image.new('L', (shape[1], shape[0]), 0); dr = ImageDraw.Draw(img)
    for x, y in pts:
        cx, cy = (x - X0) * R8 - org[0], (y - Y0) * R8 - org[1]; dr.ellipse([cx - r * R8, cy - r * R8, cx + r * R8, cy + r * R8], fill=255)
    return np.array(img) > 0


def _lines_mask(lines, width, shape, org):
    img = Image.new('L', (shape[1], shape[0]), 0); dr = ImageDraw.Draw(img)
    for t in lines:
        if len(t) > 1: dr.line([((x - X0) * R8 - org[0], (y - Y0) * R8 - org[1]) for x, y in t], fill=255, width=max(1, int(width * R8)), joint='curve')
    return np.array(img) > 0


def _components(G, keep):
    seen = set(); out = []
    for s in sorted(keep):
        if s in seen: continue
        c = {s}; st = [s]
        while st:
            x = st.pop()
            for t in G[x]:
                if t in keep and t not in c: c.add(t); st.append(t)
        seen |= c; out.append(c)
    return out


YN = -215.0; HN = int((GF.Y1 - YN) * R8); OFF = int((Y0 - YN) * R8)            # the taller grid the Plains and Azure merges use (the map reaches y -215); ground layers are edited on it
E = lambda m: np.vstack([np.zeros((OFF, W), bool), m])                       # a mask on gap_fill's grid, placed on the taller one
REGION = (-131.0, -66.0, -9.5, 34.0)           # the redrawn region's box (x0, y0, x1, y1): only layer polygons that touch it are traced again


def _edit_layer(w, key, edit, sigma=1.5):
    """Change one ground layer inside the region: the polygons that touch the region are rasterised, edited and traced again; the others stay as they were."""
    polys = w['geo'].get(key) or []
    def hit(p):
        xs = [q[0] for q in p]; ys = [q[1] for q in p]
        return min(xs) < REGION[2] and max(xs) > REGION[0] and min(ys) < REGION[3] and max(ys) > REGION[1]
    sel = [p for p in polys if hit(p)]; keep = [p for p in polys if not hit(p)]
    r = AA._raster(sel, X0, YN, W, HN) if sel else np.zeros((HN, W), bool)
    w['geo'][key] = keep + AA._contours(edit(r), X0, YN, sigma=sigma)


def _chaikin(pts, n=3):
    for _ in range(n):
        out = [pts[0]]
        for a, b in zip(pts[:-1], pts[1:]):
            out += [(0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]), (0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1])]
        out.append(pts[-1]); pts = out
    return pts


def merge_ft(w, layout, edges, seed=53):
    import ashen_forest as AF
    rooms, exits = AF._world()
    rng = random.Random(seed); nrng = np.random.default_rng(seed)
    pos = dict(zip(layout['ids'], zip(layout['xs'], layout['ys'])))
    hidden = set(layout.get('hidden', []))
    info = {r['id']: r for r in edges['rooms']}
    track = w['track']
    shown = lambda v: v in pos and v not in hidden
    void = lambda v: bool(info[v].get('void'))
    cxp = lambda v: tuple(track['cx%d' % v][:2]) if 'cx%d' % v in track else None
    grp = lambda v: info.get(v, {}).get('grp')
    G = defaultdict(set)
    for a, b, k in edges['edges']:
        if k != 'ud' and shown(a) and shown(b): G[a].add(b); G[b].add(a)
    report = {}

    # ---------------------------------------------------------------- what is where
    chain = {int(k[2:]) for k in track if k.startswith('wt')}                       # the road's 54 rooms (53 Western Trade Route rooms + its crossing room)
    FT = {v for v in pos if grp(v) == 'ft' and shown(v) and pos[v][0] < -12 and v not in chain}     # (a stray room parked beside the lake is x > -12)
    LK = {v for v in pos if grp(v) == 'lk' and shown(v)}
    field = {v for v in FT if not void(v) and FIELD_RE.search(rooms[v]['name'])}
    rest = FT - field
    comps = _components(G, rest)
    nbr = defaultdict(set)
    for v_, l_ in exits.items():
        for e_ in l_: nbr[v_].add(e_['to']); nbr[e_['to']].add(v_)
    touches_dh = lambda c: any(info.get(u, {}).get('src') == 'DH' for v in c for u in nbr[v])
    threads = [c for c in comps if len(c) >= 20 or touches_dh(c)]       # (the path west out of Darkhaven is a thread however short)
    thread = set().union(*threads) if threads else set()
    fpts = np.array([pos[v] for v in field]); ftree = cKDTree(fpts)
    small = set().union(*[c for c in comps if c not in threads]) if comps else set()
    stray_field = {v for v in small if not void(v) and ftree.query(pos[v])[0] < 3.5}         # single rooms inside the field's body
    field |= stray_field
    ignored = sorted(small - stray_field)
    fpts = np.array([pos[v] for v in field])
    # the Fog Cliffs path: the cliff-named rooms of the western thread
    west = next(c for c in threads if min(pos[v][0] for v in c) < -100)
    fog = {v for v in west if not void(v) and CLIFF_RE.search(rooms[v]['name'])}
    report['field_rooms'] = len(field); report['threads'] = [len(c) for c in threads]; report['fog_cliff_rooms'] = len(fog); report['small_rooms_ignored'] = ignored

    # ---------------------------------------------------------------- the pathways (dirt trails)
    def graph(nodes):
        g = {v: {u for u in G[v] if u in nodes} for v in nodes}
        return g
    def prune_stubs(g, pins=()):
        pruned = set()
        while True:
            sp = [v for v in g if len(g[v]) <= 1 and void(v) and v not in pins]
            if not sp: break
            for v in sp:
                for u in list(g[v]): g[u].discard(v)
                del g[v]; pruned.add(v)
        return pruned
    GT = graph(thread); pruned_t = prune_stubs(GT)
    trails = _chains(GT, pos, set(), 0.6)
    ring = graph(LK); pruned_l = prune_stubs(ring)
    ring_lines = _chains(ring, pos, set(), 0.6)
    # the Lost Between Woods path on to the Forgotten Woods, and the lake's short links to the Woods
    fwlinks = []
    for v in sorted(thread | LK):
        for e in exits.get(v, []):
            t = e['to']
            if info.get(t, {}).get('src') == 'FW' and e['dir'] in (1, 2, 3, 4, 6, 8, 9, 12, 16, 32) and (v in LK or v in west):
                fwlinks.append((v, t))
    fwl_lines = []
    for v, t in fwlinks:
        a = pos[v]; b = cxp(t) if t not in pos else pos[t]
        L_ = math.dist(a, b)
        if L_ > 10:                                                          # the long Lost Between Woods link bows gently (about 6%) rather than run dead straight
            nx_, ny_ = -(b[1] - a[1]) / L_, (b[0] - a[0]) / L_; bow = 0.06 * L_ * (1 if nx_ < 0 else -1)
            fwl_lines.append([[round(a[0], 3), round(a[1], 3)]] + [[round(a[0] + (b[0] - a[0]) * t + nx_ * bow * math.sin(math.pi * t), 3), round(a[1] + (b[1] - a[1]) * t + ny_ * bow * math.sin(math.pi * t), 3)] for t in (0.25, 0.5, 0.75)] + [[round(b[0], 3), round(b[1], 3)]])
        else: fwl_lines.append([[round(a[0], 3), round(a[1], 3)], [round(b[0], 3), round(b[1], 3)]])
    dht = [[[round(cxp(u)[0], 3), round(cxp(u)[1], 3)], [round(pos[v][0], 3), round(pos[v][1], 3)]] for v in sorted(thread) for u in sorted(nbr[v]) if info.get(u, {}).get('src') == 'DH' and cxp(u)]
    FIELD_LINKS = [(1755, 1754), (1782, 1736)]                            # owner (Oct 13): Lost Between Woods paths run into the field here
    fl_lines = [[[round(pos[a][0], 3), round(pos[a][1], 3)], [round(pos[b][0], 3), round(pos[b][1], 3)]] for a, b in FIELD_LINKS if a in pos and b in pos]
    report['darkhaven_path_links'] = len(dht); report['field_links'] = [(a, b, round(math.dist(pos[a], pos[b]), 1)) for a, b in FIELD_LINKS if a in pos and b in pos]
    report['thread_lines'] = len(trails); report['thread_rooms_drawn'] = len(GT); report['ring_lines'] = len(ring_lines); report['ring_rooms'] = len(ring)
    report['woods_links'] = [(v, t, round(math.dist(pos[v], cxp(t) or pos[t]), 1)) for v, t in fwlinks]
    report['stubs_left_off'] = sorted(pruned_t | pruned_l)

    # ---------------------------------------------------------------- the road
    RD = {v for v in chain if shown(v)}
    GR = graph(RD)
    assert all(len(GR[v]) <= 2 for v in GR) and len(_components(GR, RD)) == 1, 'the road is not one string'
    road = _chains(GR, pos, set(), 0.8); assert len(road) == 1
    dh_links = []
    for v in sorted(RD):
        for e in exits.get(v, []):
            t = e['to']
            if info.get(t, {}).get('src') == 'DH' and cxp(t): dh_links.append((v, t))
    dh_lines = [[[round(cxp(t)[0], 3), round(cxp(t)[1], 3)], [round(pos[v][0], 3), round(pos[v][1], 3)]] for v, t in dh_links]
    joins = []; joined_with = []
    for v in sorted(RD):
        for u in sorted(G[v]):
            if u in FT or u in field:
                q = _nearest_on(road, pos[v])
                if any(math.dist(q, j) < 1.2 for j in joins + list(w.get('ntrjoins', []))): continue
                joins.append([round(q[0], 2), round(q[1], 2)]); joined_with.append((v, u))
    report['road_rooms'] = len(RD); report['off_ramps'] = joined_with; report['dh_links'] = dh_links

    # ---------------------------------------------------------------- geometry on a sub-grid
    allpts = np.array([pos[v] for v in (FT | LK | RD)])
    lo, hi = allpts.min(0) - 16, allpts.max(0) + 16
    ix0, ix1 = max(0, int((lo[0] - X0) * R8)), min(W, int((hi[0] - X0) * R8)); iy0, iy1 = max(0, int((lo[1] - Y0) * R8)), min(H, int((hi[1] - Y0) * R8))
    sub = (slice(iy0, iy1), slice(ix0, ix1)); hh, ww = iy1 - iy0, ix1 - ix0; org = (ix0, iy0); shape = (hh, ww)
    sx = (np.arange(ix0, ix1) + .5) / R8 + X0; sy = (np.arange(iy0, iy1) + .5) / R8 + Y0
    SX, SY = np.meshgrid(sx, sy)
    px_ = lambda x, y: ((x - X0) * R8 - ix0, (y - Y0) * R8 - iy0)
    def close(m, rr, pad=None):
        pad = pad or int(rr * R8) + 4; a = np.pad(m, pad); a = ndi.distance_transform_edt(~a) <= rr * R8; a = ndi.distance_transform_edt(a) > rr * R8
        return a[pad:-pad, pad:-pad]
    # the field: the body of rooms, gaps between rows closed
    fm = _pts_mask([tuple(p) for p in fpts], 1.3, shape, org)
    fm = ndi.binary_fill_holes(close(fm, 3.2) | fm)
    path_lines = trails + ring_lines + road + fwl_lines + dht + fl_lines
    pm = _lines_mask(path_lines, 1.6, shape, org)
    struct = fm | pm
    # the whole body inside the paths: the field, the paths and the impassable ground between
    inner = ndi.binary_fill_holes(close(struct, 9.0))
    # the band beyond the paths
    band = ndi.distance_transform_edt(~inner) <= 2.4 * R8
    soft = ndi.gaussian_filter(band.astype(float), 1.1 * R8)
    wob = ndi.gaussian_filter(nrng.normal(size=band.shape), 2.0 * R8); wob = (wob - wob.min()) / (wob.max() - wob.min())
    bandm = (soft > 0.5 + 0.18 * (wob - 0.5) * 2) | inner
    # the north: land on to a smooth coast that meets the Woods' (the coast curve, then a line to the west path's first room)
    cpoly = _chaikin(list(COAST), 3)
    wc = Image.new('L', (ww, hh), 0)
    ImageDraw.Draw(wc).polygon([px_(x, y) for x, y in cpoly + [(-106.0, -14.0), (-140.0, -14.0), (-140.0, -70.0), (-60.0, -70.0)]], fill=255)
    W_of_C = np.array(wc) > 0                                       # open background: west and north of the coast
    ytop = np.full(ww, np.inf)
    for c in range(ww):
        col = bandm[:, c]
        if col.any(): ytop[c] = np.nonzero(col)[0].min()
    ok = np.isfinite(ytop)
    ytop = np.interp(np.arange(ww), np.nonzero(ok)[0], ytop[ok])
    rowsx = np.arange(hh)[:, None]
    # north fill: between the coast and the top of the body, so no gap is left (dense forest everywhere up there)
    nfill = (rowsx <= ytop[None, :] + 2) & ~W_of_C & (SY < -9.5) & (SX < XE) & (SX > -112.0) & (SY > -25.5)
    def full(m, dtype=bool):
        f = np.zeros((H, W), dtype); f[sub] = m; return f

    # ---------------------------------------------------------------- the old drawing, and what replaces it
    land0 = AA._raster(w['geo']['land'], X0, Y0, W, H); water0 = AA._raster(w['geo']['water'], X0, Y0, W, H)
    wcf = full(W_of_C)
    inpoly = GF._fillpoly(cpoly + [(-106.0, -14.0), (-140.0, -14.0), (-140.0, -70.0), (-60.0, -70.0)])
    Wc = inpoly                                                                  # (the same shape on the whole grid)
    A_ = (WX < XE) & (WY > -66.0)
    NZ = (WY < -25.0) & ~Wc & (WX < XE)                                          # north of here the old land (up to the old west coast) stays
    Pk = (WX > -27.0) & (WY > 8.5)                                               # 'Along the Forest Path' patch with its big tree stays
    Ez = A_ & ~NZ & ~Pk
    new_in = full(bandm | nfill) & Ez & ~Wc
    # the lake: inside the ring of shore rooms
    rm = _lines_mask(ring_lines, 1.0, shape, org)
    rc = ndi.binary_fill_holes(close(rm, 2.5) | rm)
    lake_in = rc & ~ndi.binary_dilation(rm, iterations=int(0.95 * R8))
    lab, n = ndi.label(lake_in)
    if n: sz = ndi.sum(lake_in, lab, range(1, n + 1)); lake_in = lab == (int(np.argmax(sz)) + 1)
    lake_in = ndi.gaussian_filter(lake_in.astype(float), 0.7 * R8) > 0.5
    lake = full(lake_in)
    beach = ndi.binary_dilation(lake, iterations=int(0.55 * R8)) & ~lake
    report['lake_sq'] = round(float(lake.sum()) / R8 / R8, 1); report['ring_enclosed_sq'] = round(float(rc.sum()) / R8 / R8, 1)
    # the sea west of the Fog Cliffs path (bounded: on the far side of the path, within 7 rooms of it, from just above to just below its ends)
    fsm = _samples([[pos[v] for v in c] for c in [sorted(fog, key=lambda v: pos[v][1])]], 0.1); ft_ = cKDTree(fsm)
    d_fog, i_fog = ft_.query(np.c_[SX.ravel(), SY.ravel()]); d_fog = d_fog.reshape(SX.shape)
    ytop_f, ybot_f = fsm[:, 1].min(), fsm[:, 1].max()
    # which side: a cell is "west" if it lies west of the nearest path point
    west_of = (SX < fsm[i_fog.reshape(SX.shape), 0] - 0.2)
    reach = np.minimum(7.0, 2.2 + 1.1 * np.minimum(SY - ytop_f + 3.0, ybot_f + 3.0 - SY).clip(0, None))
    sea_in = west_of & (d_fog >= 0.9) & (d_fog <= reach) & (SY > ytop_f - 3.0) & (SY < ybot_f + 3.0)
    srow = ndi.gaussian_filter(nrng.normal(size=sea_in.shape), 1.4 * R8); srow = (srow - srow.min()) / (srow.max() - srow.min())
    sea_in = (ndi.gaussian_filter(sea_in.astype(float), 0.8 * R8) > 0.42 + 0.2 * srow) & west_of & (d_fog >= 0.85)
    lab, n = ndi.label(sea_in)
    if n: sz = ndi.sum(sea_in, lab, range(1, n + 1)); sea_in = lab == (int(np.argmax(sz)) + 1)
    sea = full(sea_in)
    report['sea_sq'] = round(float(sea.sum()) / R8 / R8, 1)
    # the dense forest: everything left of the body (not field, lake, sea, cliffs), clear of the paths and the field rooms' own lines
    land_ft = new_in & ~lake & ~sea
    wlines = trails + ring_lines + road + fwl_lines + dht + fl_lines
    clr = _samples(wlines, 0.15)
    ctree = cKDTree(np.r_[clr, np.array([pos[v] for v in (thread | RD | LK)])])
    # cliff zone along the Fog Cliffs path (land side), its sea edge, then the rest of the dense forest
    cz = (d_fog <= 3.6) & (SX >= fsm[i_fog.reshape(SX.shape), 0] - 0.2) & (SY > ytop_f - 1.2) & (SY < ybot_f + 1.2)
    cliffz = full(cz) & land_ft
    fieldf = full(fm) & land_ft & ~cliffz
    # the Lost Between Woods path west and the Fog Cliffs path ends: dense forest keeps one room clear beside paths
    dd_all = np.full((H, W), 9.0)
    ys_, xs_ = np.nonzero(land_ft[sub])
    dd = ctree.query(np.c_[SX[ys_, xs_], SY[ys_, xs_]])[0]
    dsub = np.full(shape, 9.0); dsub[ys_, xs_] = dd; dd_all[sub] = dsub
    dense = land_ft & ~fieldf & ~cliffz & (dd_all > 1.0)
    dense = ndi.binary_opening(dense, iterations=R8 // 4)
    report['dense_sq'] = round(float(dense.sum()) / R8 / R8, 1); report['field_sq'] = round(float(fieldf.sum()) / R8 / R8, 1); report['cliff_sq'] = round(float(cliffz.sum()) / R8 / R8, 1)
    # ---- land
    oldlake = (WX > -45.0) & (WX < -10.5) & (WY > -45.0) & (WY < -1.5)
    land1 = (land0 & ~Ez) | new_in | (water0 & oldlake & ~lake)                    # (what was the old lake and is not the new one is forest)
    land1 &= ~sea
    land1 |= lake                                                                # (the lake lies on land; its water is drawn on top)
    zs = (WX > -37.0) & (WX < -19.0) & (WY > 6.0)                                # where the redrawn zone meets 'Along the Forest Path' patch: round off the corner
    land1 = np.where(zs, ndi.gaussian_filter(land1.astype(float), 1.8 * R8) > 0.5, land1)
    land_n = AA._raster(w['geo']['land'], X0, YN, W, HN); land_n[OFF:] = land1      # (taller grid: the land north of y -118 is kept)
    w['geo']['land'] = AA._contours(land_n, X0, YN)
    report['land_sq_before_after'] = (round(float(land0.sum()) / R8 / R8), round(float(land1.sum()) / R8 / R8))

    # ---- water: the old lake goes; the new lake and the sea come
    _edit_layer(w, 'water', lambda r: (r & ~E(oldlake)) | E(lake) | E(sea))
    _edit_layer(w, 'sand', lambda r: (r & ~E(Ez | lake | sea)) | E(beach & land1 & ~lake), sigma=1.0)

    # ---- ground tints: the old forest's go from the redrawn zone; the new ones come
    clip = Ez | lake | sea
    for k in ('deep', 'bog', 'sparse', 'cliff', 'meadow1', 'meadow2', 'meadow3', 'fill', 'fill2'):
        if w['geo'].get(k): _edit_layer(w, k, lambda r: r & ~E(clip), sigma=1.0)
    # the dense forest, and the field's ground: wood tint, paler patches, bog under 'Drowning in Sorrow'
    fz = ndi.binary_erosion(fieldf, iterations=int(0.4 * R8))
    nz1 = ndi.gaussian_filter(nrng.normal(size=(hh, ww)), 3.0 * R8); nz1 = (nz1 - nz1.min()) / (nz1.max() - nz1.min())
    drown = np.array([pos[v] for v in field if 'Drowning' in rooms[v]['name']])
    bogm = full(_pts_mask([tuple(p) for p in drown], 1.7, shape, org)) & fz
    bogm = ndi.binary_opening(ndi.binary_closing(bogm, iterations=R8), iterations=R8 // 3)
    _edit_layer(w, 'deep', lambda r: r | E(ndi.binary_erosion(dense, iterations=int(0.3 * R8))), sigma=2.0)
    _edit_layer(w, 'fill', lambda r: r | E(fz), sigma=2.0)
    _edit_layer(w, 'fill2', lambda r: r | E(fz & full(nz1 > 0.55)), sigma=2.5)
    _edit_layer(w, 'bog', lambda r: r | E(bogm), sigma=2.0)
    # the Fog Cliffs: rock tint, darker crag ground, a dark cast over it
    _edit_layer(w, 'cliff', lambda r: r | E(cliffz))
    crz = ndi.binary_erosion(cliffz, iterations=int(0.35 * R8))
    w['geo']['crags'] = list(w['geo'].get('crags') or []) + AA._contours(crz, X0, Y0, sigma=1.5)
    _edit_layer(w, 'dread2', lambda r: r | E(ndi.binary_dilation(cliffz, iterations=int(0.5 * R8)) & land1), sigma=2.0)

    # ---- sprites: clear the old ones from the redrawn zone, under the lake and the sea
    def inm(m, x, y):
        ix, iy = int((x - X0) * R8), int((y - Y0) * R8)
        return 0 <= ix < W and 0 <= iy < H and m[iy, ix]
    zone_clear = Ez | ndi.binary_dilation(lake | sea, iterations=int(0.3 * R8))
    cleared = {}
    for key in ('trees', 'tufts', 'reeds', 'hills', 'thorns', 'peaks', 'boulders', 'crags', 'mist', 'darkfog', 'wheattufts', 'brush'):
        arr = w.get(key) or []; kept = [q for q in arr if not inm(zone_clear, q[0], q[1])]
        if len(kept) != len(arr): cleared[key] = len(arr) - len(kept)
        w[key] = kept
    off = zs & ~land1                                                            # (and nothing stands where that corner now has no land)
    for key in ('trees', 'tufts', 'hills', 'thorns', 'boulders', 'reeds'):
        arr = w.get(key) or []; kept = [q for q in arr if not inm(off, q[0], q[1])]
        if len(kept) != len(arr): cleared[key] = cleared.get(key, 0) + len(arr) - len(kept)
        w[key] = kept
    kh = [h for h in w['hach'] if not inm(zone_clear, h[0], h[1])]; cleared['hach'] = len(w['hach']) - len(kh); w['hach'] = kh
    rbs = w.get('ribbons') or []; cleared['ribbons'] = len(rbs); w['ribbons'] = []
    w['road'] = []; w['link'] = []                                               # the old west road and the fading link to it (the new road comes from the layout)
    report['cleared'] = cleared

    # ---- new trees and ground
    def sample(mask, per_sq, spacing, ok=None, cap=None):
        m = ndi.binary_erosion(mask, iterations=int(0.2 * R8)); yy, xx = np.nonzero(m); out = []
        if not len(xx): return out
        n = int(float(mask.sum()) / R8 / R8 * per_sq); placed = []; grid = defaultdict(list)
        for _ in range(n * 6):
            if len(out) >= n: break
            j = rng.randrange(len(xx)); x = xx[j] / R8 + X0 + rng.uniform(0, 1 / R8); y = yy[j] / R8 + Y0 + rng.uniform(0, 1 / R8)
            gx, gy = int(x / spacing), int(y / spacing)
            if any(math.hypot(x - a, y - b) < spacing for dx in (-1, 0, 1) for dy in (-1, 0, 1) for a, b in grid[(gx + dx, gy + dy)]): continue
            if ok and not ok(x, y): continue
            grid[(gx, gy)].append((x, y)); out.append((x, y))
        return out
    ctree1 = cKDTree(np.r_[clr, np.array([pos[v] for v in (thread | RD | LK) if not void(v)])])
    notpath = lambda r: (lambda x, y: ctree1.query([x, y])[0] > r)
    trees = []
    for x, y in sample(dense, 3.0, 0.40, notpath(1.0)):
        trees.append([round(x, 3), round(y, 3), round(rng.uniform(0.85, 1.2), 2), 'x' if rng.random() < 0.3 else 'd', rng.randrange(3)])
    bg = ndi.gaussian_filter(nrng.normal(size=(hh, ww)), 1.8 * R8); bgf = full(bg > np.quantile(bg, 0.7))
    for x, y in sample(fieldf, 1.7, 0.55, notpath(0.7)):
        r_ = rng.random(); inbog = inm(bogm, x, y)
        if inbog and r_ < 0.6: continue
        trees.append([round(x, 3), round(y, 3), round(rng.uniform(0.85, 1.2), 2), 'd' if r_ < 0.5 else ('w' if r_ < 0.92 else 'x'), rng.randrange(3)])
    w['trees'] = list(w['trees']) + trees
    tufts = [[round(x, 3), round(y, 3), round(rng.uniform(0.8, 1.3), 2), 'g', rng.randrange(2)] for x, y in sample(fieldf, 0.9, 0.5, notpath(0.5))]
    w['tufts'] = list(w['tufts']) + tufts
    report['trees'] = Counter(t[3] for t in trees); report['tufts'] = len(tufts)

    # ---- the Fog Cliffs: peaks, crags, rocks, edge hachures, mist
    fl = [[round(float(a), 3), round(float(b), 3)] for a, b in fsm[::3]]
    ftree2 = cKDTree(fsm)
    def peak_ok(x, y): d = ftree2.query([x, y])[0]; return 0.6 < d < 3.5 and ctree1.query([x, y])[0] > 0.45
    peaks = [[round(x, 3), round(y, 3), round(rng.uniform(1.3, 2.1), 2), 'm', rng.randrange(2)] for x, y in sample(cliffz, 3.4, 0.75, peak_ok)]
    crags = [[round(x, 3), round(y, 3), round(rng.uniform(0.75, 1.35), 2), rng.randrange(3)] for x, y in sample(cliffz, 2.6, 0.5, lambda x, y: ctree1.query([x, y])[0] > 0.4)]
    rocks = [[round(x, 3), round(y, 3), round(rng.uniform(0.5, 0.95), 2)] for x, y in sample(cliffz, 1.4, 0.5, lambda x, y: ctree1.query([x, y])[0] > 0.4)]
    # edge hachures: short ticks off the path toward the sea
    hach = []; arc = _samples([[pos[v] for v in sorted(fog, key=lambda v: pos[v][1])]], 0.33)
    for k_ in range(2, len(arc) - 2):
        t = arc[k_ + 2] - arc[k_ - 2]; L_ = math.hypot(*t) or 1; n_ = np.array([-t[1], t[0]]) / L_
        if n_[0] > 0: n_ = -n_
        a_ = arc[k_] + n_ * 0.18; b_ = a_ + n_ * rng.uniform(0.35, 0.6) + np.array([0, rng.uniform(-0.08, 0.08)])
        if not inm(sea | cliffz | land1, a_[0], a_[1]): continue
        hach.append([round(float(a_[0]), 3), round(float(a_[1]), 3), round(float(b_[0]), 3), round(float(b_[1]), 3)])
    # mist and dark fog drifting along the cliffs and over the water below them
    mist = []; fog_ = []
    for k_ in range(0, len(arc), int(2.6 / 0.33)):
        mist.append([round(float(arc[k_][0]) + rng.uniform(-0.5, 0.2), 2), round(float(arc[k_][1]), 2), round(rng.uniform(1.5, 2.2), 2)])
    for k_ in range(int(1.8 / 0.33), len(arc), int(5.0 / 0.33)):
        fog_.append([round(float(arc[k_][0]) + rng.uniform(0.6, 1.8), 2), round(float(arc[k_][1]), 2), round(rng.uniform(1.5, 2.1), 2)])
    w['peaks'] = sorted(list(w['peaks']) + peaks, key=lambda q: q[1]); w['crags'] = sorted(list(w.get('crags') or []) + crags, key=lambda q: q[1])
    w['boulders'] = sorted(list(w.get('boulders') or []) + rocks, key=lambda q: q[1]); w['hach'] = list(w['hach']) + hach
    w['mist'] = list(w['mist']) + mist; w['darkfog'] = list(w['darkfog']) + fog_
    report['cliffs'] = dict(peaks=len(peaks), crags=len(crags), rocks=len(rocks), hach=len(hach), mist=len(mist), dark_fog=len(fog_))

    # ---- trails, the road and its off-ramps
    def inz(pl): return all(inm(Ez, x, y) for x, y in pl)
    oldt = list(w['fwtracks']); w['fwtracks'] = [t for t in oldt if not (len(t) and inz(t))]
    report['old_trails_dropped'] = len(oldt) - len(w['fwtracks'])
    w['fwtracks'] = list(w['fwtracks']) + trails + ring_lines + fwl_lines + dh_lines + dht + fl_lines
    w['etrtracks'] = list(w.get('etrtracks', [])) + road
    w['ntrjoins'] = list(w.get('ntrjoins', [])) + joins
    # the Woods trail through Widow's Peak (5634-5638) follows the rooms to where they were put
    oldc = {v: tuple(track['cx%d' % v][:2]) for v in WIDOWS + [5632, 5639] if 'cx%d' % v in track}
    wp = []
    for t_ in w['fwtracks']:
        if len(t_) < 3: continue
        a = [math.dist(q, oldc[5632]) for q in t_]; b = [math.dist(q, oldc[5639]) for q in t_]
        i, j = int(np.argmin(a)), int(np.argmin(b))
        if a[i] < 1.2 and b[j] < 1.2 and i != j:
            mid = [[round(pos[v][0], 3), round(pos[v][1], 3)] for v in WIDOWS]
            t_[:] = (t_[:i + 1] + mid + t_[j:]) if i < j else (t_[:j + 1] + mid[::-1] + t_[i:]); wp.append((i, j, len(t_)))
    report['widows_peak_trails'] = wp

    # ---- markers and routes of the sub-areas that open off the forest and the road
    isspacer = lambda v: bool(rooms[v]['flags'] & 8) and rooms[v]['area'] == ''
    DIRS = {'n', 'e', 's', 'w', 'ne', 'nw', 'se', 'sw', 'u', 'd'}
    def walk(route):
        v = 764; trail = [v]
        for tok in [x.strip() for x in route.split(';') if x.strip()]:
            tok = re.sub(r'^l ', 'look ', tok)
            m = re.match(r'^#\s*(\d+)\s*(.+)$', tok); n, dd = (int(m.group(1)), m.group(2)) if m else (1, tok)
            for _ in range(n):
                nx = [e for e in exits.get(v, []) if e['name'] == dd or e['cmd'].split(';')[-1] == dd or e['cmd'] == tok]
                if not nx and dd not in DIRS: break
                if not nx: return trail, tok
                v = nx[0]['to']; trail.append(v); k = 0
                while isspacer(v) and k < 40:
                    c = [x['to'] for x in exits.get(v, []) if x['name'] == dd]
                    if not c: break
                    v = c[0]; trail.append(v); k += 1
        return trail, None
    P = lambda v: pos[v] if v in pos else cxp(v)
    moved = []; failed = []
    KEEP = {'Along the Forest Path'}
    for p in w['places']:
        if p.get('group') not in ('fot', 'wtr') or p['name'] in KEEP or not p.get('route'): continue
        trail, fail = walk(p['route'])
        idx = [i for i, v in enumerate(trail) if rooms[v]['area'] in ('Forest of Tears', 'Western Trade Route') and P(v)]
        if fail or not idx: failed.append((p['name'], fail)); continue
        trail = trail[:idx[-1] + 1]
        segs = []; cur = []
        for v in trail:
            q = P(v)
            if q: cur.append([round(q[0], 3), round(q[1], 3)])
            elif cur: segs.append(cur); cur = []
        if cur: segs.append(cur)
        old = p['path'][-1]; end = segs[-1][-1]
        p['segs'] = segs; p['path'] = [q for s_ in segs for q in s_]
        moved.append((p['name'], [round(old[0], 1), round(old[1], 1)], [round(end[0], 1), round(end[1], 1)], len(segs)))
    report['markers_moved'] = moved; report['markers_failed'] = failed
    fnt = next((p for p in w['places'] if p['name'] == "Falcon's Nest Tavern"), None)
    for b in w['buildings']:
        if b['name'] == "Falcon's Nest Tavern" and fnt: b['x'], b['y'] = round(fnt['path'][-1][0], 3), round(fnt['path'][-1][1] - 1.05, 3)

    # ---- the lake's name: across the widest row of the new lake
    lyy, lxx = np.nonzero(lake); rows = Counter(lyy.tolist()); widest = [r for r, c in rows.items() if c >= 0.93 * max(rows.values())]
    ry = int(np.median(widest)); xs_l = lxx[lyy == ry]
    w['lakelabel'] = dict(x=round(float((xs_l.min() + xs_l.max()) / 2 / R8 + X0), 2), y=round(float(ry / R8 + Y0 - 0.5), 2), a=-5.0, size=1.5, ls=0.28, drop=1.85, fixed=True)
    report['lakelabel'] = w['lakelabel']
    # ---- the forest's name, in the middle of the field
    fy, fx = np.nonzero(fieldf)
    cxf = float(np.median(fx / R8 + X0)); cyf = float(np.median(fy / R8 + Y0))
    w['label'] = dict(x0=round(cxf - 24.5, 2), x1=round(cxf + 24.5, 2), y=round(cyf + 0.8, 2), fixed=True)
    report['label'] = w['label']
    import os
    if os.environ.get('FT_DEBUG'): report['_masks'] = dict(land1=land1, lake=lake, sea=sea, dense=dense, fieldf=fieldf, cliffz=cliffz, Ez=Ez, beach=beach)
    return w, report
