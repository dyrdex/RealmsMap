"""The Mire (owner, Oct 18): mi_layout_final.json, mi_editor_edges.json (the owner's layout from tools/mire_editor, saved Oct 18 01:03Z).
First pass, in broad strokes (as the Wastelands' first pass; the owner reviews it):
  - land round every shown room and exit (traced with the mainland: mi_land is chained into smr_merge's land_edit, whose grid now starts 20 rooms
    further west); the gaps it closes against the Forest of Tears and the range filled (owner, Oct 18: standard terrain, as the land round them;
    the parts nearer the Mire are the Mire's); no sea of its own (owner, Oct 18);
  - ONE ground under the whole area: the bog tint (other tints cut back to where the Mire's ground starts: nearer the Mire's rooms than the map's);
  - the rooms you wade or swim (terrain Swimming / Water: Wading amongst the Reeds, Blackpool Bog, the Dank Bog, river crossings) = shallow marsh
    water on exactly their rooms and the exits between them, wavy edges, reeds round it; clumps of mutually joined other rooms = mud clearings
    (the range's rule); dirt trails elsewhere, clipped at the water and the clearings; links to the map and up/down exits as trails;
  - Forest rooms: trees; Hills rooms: hills; Mountains rooms (the rocky delta): boulders; Desert rooms (the beaches): sand; reeds over the bog.
No markers, labels or names (none asked for yet)."""
import math
import numpy as np
from collections import defaultdict
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from scipy.spatial import cKDTree, ConvexHull
from skimage.morphology import disk
import arrange_apply as AA
import gap_fill as GF
import ashen_forest as AF
from ntr_merge import _chains, _samples
from smr_merge import _hash, _drawn, X0 as SX0                  # (SX0: the west edge of smr_merge's land grid, where the Mire's land is traced)

R8 = GF.R8
LAND_R, TERR_R = 4.2, 3.2
OLD_MARSH = set(range(8394, 8422)) | {21812}
NOT_MIRE = {655, 8209, 8212, 8214, 8221}         # Dragon's Pass rooms in the Mire editor (owner, Oct 18): hidden; routes pass through them (8221-8195 the shortcut: a plain route line, like the Ofcol Shortcut)
SHORTCUT = frozenset((8195, 8221))              # the Dragon's Pass shortcut: drawn as a faint dashed line across the map (owner, Oct 18)
SHOWN = {19582, 7938}                            # shown on the map whatever the save says (owner, Oct 18)
EXTRA_WATER = {8458, 8459, 8063, 8081, 8035, 8034, 17864, 17675, 17677, 17862, 17863, 8033, 8032, 8008}   # marsh water (owner, Oct 18): the Reeds carried to 8063/8081 and south to the clearing
EXTRA_CLEAR = [set(range(8082, 8114)),                                                       # one clearing from east of 8081 to 8113 (owner, Oct 18)
               {8118, 8119, 8120, 8121, 8171, 8177},                                         # the clearing at (-70.6, 84.4) taken west over 8118-8120
               {8059, 8060},
               {8057, 8030, 8031, 8056, 8054, 8026, 8027, 8048, 8053, 8055},
               {7958, 7960, 7961, 7962},
               {8408, 8409, 8410, 8412, 8413, 8414, 8415, 8416, 8417}]                     # the Old Marsh's central cluster: a regular clearing; its other rooms paths (owner, Oct 18)                                                     # no path showing between the water and the clearing at (-95, 51.5) (owner, Oct 18)                 # 8057, 8030, 8031, 8056, 8054 tied into the clearing south of them (owner, Oct 18)
LAKE = {8450, 8452, 8453, 8454, 8455, 8456, 8457, 8458, 8459}                              # the marsh lake's rooms: every link into or inside it a very faint dull blue dashed line, but 8459-8460 (owner, Oct 18)
LAKE_PATH = [(8440, 8439), (8439, 8438), (8438, 8451), (8451, 8462)]                         # a regular path along its south shore (owner, Oct 18)
WETLAND = 7873                                   # the clearing of this room's section (the Secluded Valley): a wet swamp, not dry ground (owner, Oct 18)
RIVER = [(-19.3, 86.3, .26), (-18.4, 88.0, .3), (-17.3, 90.0, .36), (-15.9, 93.5, .45), (-15.6, 96.5, .6),
         (-15.5, 99.6, .8), (-15.7, 102.0, 1.0), (-17.0, 104.6, 1.2), (-17.0, 107.5, 1.5), (-17.0, 110.5, 1.8), (-17.0, 114.0, 2.0), (-17.4, 117.0, 2.2),
         (-18.2, 119.5, 2.6), (-19.2, 121.5, 3.2), (-20.5, 124.0, 4.4), (-21.5, 127.0, 5.6), (-22.0, 130.0, 6.6), (-22.0, 133.0, 7.4), (-22.0, 137.5, 8.0)]
RIVER_END = 136.0                                # it runs off the map's south edge there, cut straight (the fan, not a round end)
# the river east of the "Along the River" rooms (owner, Oct 18): (x, y, half width): thin at its head, widening south, a fan (delta) below y 121
RIVER_STONES = (119.0, 125.5)                    # (stones just north and south of the last crossing path, 8491-8492-8640: owner, Oct 18)
RIVER_HEAD = [[(-22.1, 83.7, .24), (-21.0, 85.0, .25), (-19.6, 86.2, .26)], [(-20.0, 83.9, .24), (-19.7, 85.0, .25), (-19.4, 86.2, .26)], [(-24.4, 82.9, .24), (-23.6, 83.8, .25), (-22.8, 84.6, .24)], [(-18.4, 82.8, .24), (-18.7, 83.8, .25), (-18.9, 84.8, .24)]]   # the marsh's first fingers below the MacMillan farm: two that run together into the river, two longer ones beside them (owner, Oct 18); 0.24 at least, or they vanish when traced
WAVY_LINK = 8.0                                  # links to the map longer than this get a gentle wave (owner, Oct 18)                                                                # stones in its shallow, wide reach (rows)
MARSH_PONDS = [(-25.5, 83.3, .7, .3, 35), (-23.3, 82.5, .55, .28, -15), (-21.0, 82.6, .6, .3, 10), (-19.3, 83.0, .45, .26, 55), (-17.6, 83.4, .5, .26, -30),
               (-24.2, 85.6, .55, .28, 40), (-17.9, 85.9, .45, .24, -45), (-22.6, 86.6, .4, .24, 20)]   # a marsh of small lakes below the farm's marsh (owner, Oct 18): (x, y, rx, ry, angle)
MARSH_STREAMS = [[(-25.0, 82.4), (-25.5, 83.3)], [(-25.0, 83.6), (-24.4, 82.9)], [(-23.3, 82.5), (-22.1, 83.7)], [(-21.0, 82.6), (-20.0, 83.9)], [(-19.3, 83.0), (-18.4, 82.8)],
                 [(-17.6, 83.4), (-18.7, 83.8)], [(-22.8, 84.6), (-24.2, 85.6)], [(-24.0, 85.9), (-22.6, 86.6), (-21.0, 86.9)], [(-18.9, 84.8), (-17.9, 85.9), (-18.2, 87.2)]]   # streams joining them, south to the river
BRIDGE = dict(x0=-17.5, x1=-14.0, y=93.5)                                                    # the Crumbling Bridge (8591, 8612, 8590) over it                                                                 # 8060 joined to its clearing
SPRITES = ('trees', 'tufts', 'peaks', 'hills', 'boulders', 'crags', 'brush', 'wheattufts', 'ripples', 'reeds', 'thorns')
ISLAND_BOX, ISLAND_R, ISLAND_GAP = (-115.5, 72.0, -111.5, 78.5), 1.0, 2.2   # (owner, Oct 18) rooms 8073-8079 (+ spacers): a small island out at sea, ISLAND_GAP of water round it
IN_SEA = (8072,)                                 # A Shallow Channel: in the water between the island and the coast (owner, Oct 18)
THIN = {8038: 0.9, 8039: 0.9, 8040: 0.9, 8041: 0.8, 8042: 0.45, 8043: 0.45, 8044: 0.5}   # The Small Beach; The Narrow Beach and its tip 8044: a thin peninsula (owner, Oct 18)
SHORE_GAP = 1.6                                  # (rooms) other land kept off these
COAST_FILL = [[(-114.6, 108.8), (-114.6, 111.7), (-109.8, 111.7), (-109.4, 108.8)],      # north of the peninsula's clearing: the coast straight down to it
              [(-114.6, 114.3), (-114.6, 117.8), (-110.3, 117.8), (-110.3, 114.3)],     # south of it: the coast meets it just south of the clearing
              [(-111.0, 112.7), (-110.0, 111.8), (-108.2, 111.8), (-107.8, 113.0), (-108.2, 114.7), (-110.6, 114.7)],   # the gap north-east of the tavern (owner, Oct 18; the sea is kept)
              [(-36.2, 124.6), (-33.5, 123.4), (-29.0, 122.8), (-29.6, 126.5), (-30.0, 130.0), (-30.6, 133.0), (-30.6, 135.0), (-36.2, 135.0)]]   # between the land east of the Old Marsh and the Mire river: standard Mire ground (owner, Oct 18)
MANSION_DOOR_AT = 8421                           # Redferne's Residence's manor: its front door just north of this room, the trail's end (owner, Oct 18)
DRAGON = (3.7, 2.75)                             # (w, h) The Mire (Central)'s dragon (owner, Oct 18: redrawn, a little smaller than 4.25 x 3.1)
FINGER_LAKE = [8418, 21812, 8419]                # the Old Marsh's finger lake: a narrow north-south water clearing along these rooms (owner, Oct 18)
INLET = 60.0                                     # (sq) narrow inlets in the Mire's coast smaller than this are filled
PAD, SQ, CELL_MAX, MIN_PATCH = 0.55, 1.1, 6.0, 3.0
SEED = 211
CLASS = {'Swimming': 'water', 'Water': 'water', 'Forest': 'forest', 'Hills': 'hills', 'Mountains': 'rocks', 'Desert': 'beach'}


def _setup(layout, edges):
    rooms, exits = AF._world()
    pos = dict(zip(layout['ids'], zip(layout['xs'], layout['ys'])))
    info = {r['id']: r for r in edges['rooms']}
    hidden = (set(layout.get('hidden', [])) - SHOWN) | NOT_MIRE                  # (the Dragon's Pass rooms: hidden, on routes only: owner, Oct 18)
    MI = {v for v, r in info.items() if r.get('area') == 'MI' and r.get('grp') != 'un' and v in pos}   # (grp 'un': unlocked range rooms, drawn by smr_merge)
    shown = lambda v: v in pos and v not in hidden
    void = lambda v: bool(info.get(v, {}).get('void'))
    E = []; nb = defaultdict(set)
    for a, b, k in edges['edges']:
        if shown(a) and shown(b) and {a, b} & MI: E.append((a, b, k)); nb[a].add(b); nb[b].add(a)
    cls = {v: (None if void(v) else CLASS.get(rooms[v]['terrain'], 'bog')) for v in MI}
    for _ in range(4):                                                               # spacers: the class most of their real neighbours have
        for v in MI:
            if cls[v] is None:
                s = [cls[u] for u in nb[v] if u in MI and cls.get(u)]
                if s: cls[v] = max(sorted(set(s)), key=s.count)
    for v in MI:
        if cls[v] is None: cls[v] = 'bog'
    for v in EXTRA_WATER:
        if v in cls: cls[v] = 'water'
    for v in OLD_MARSH:
        if v in cls and cls[v] == 'water': cls[v] = 'bog'                          # (the Old Marsh: a clearing and paths, not water: owner, Oct 18)
    return rooms, exits, pos, info, hidden, MI, shown, void, E, cls


def mi_land(layout, edges, store, seed=SEED):
    """land_edit for smr_merge: the Mire's land added to the grid, and the gaps it closes between itself and the map filled with land
    (owner, Oct 18: no sea of its own)"""
    rooms, exits, pos, info, hidden, MI, shown, void, E, cls = _setup(layout, edges)
    dry = [v for v in MI if shown(v)]
    isl = {v for v in dry if ISLAND_BOX[0] <= pos[v][0] <= ISLAND_BOX[2] and ISLAND_BOX[1] <= pos[v][1] <= ISLAND_BOX[3]}   # (owner, Oct 18)
    rad = {v: ISLAND_R for v in isl}; rad.update(THIN); rad.update({v: 0.0 for v in IN_SEA})
    sp = {v for v in rad if v in pos}
    land_lines = [[pos[a], pos[b]] for a, b, k in E if k != 'ud' and not ({a, b} & sp) and frozenset((a, b)) != SHORTCUT]
    lp = np.r_[np.array([pos[v] for v in dry if v not in sp]), _samples(land_lines, 0.15)]
    thin_lines = [(pos[a], pos[b], min(rad.get(a, 9), rad.get(b, 9))) for a, b, k in E if k != 'ud' and {a, b} & sp and not ({a, b} & set(IN_SEA))]
    xs = [p[0] for p in lp] + [pos[v][0] for v in dry] + [p[0] for p in RIVER]; ys = [p[1] for p in lp] + [pos[v][1] for v in dry] + [p[1] for p in RIVER]   # (the river reaches past the area)
    box = (max(SX0, math.floor(min(xs)) - 16), math.floor(min(ys)) - 8, math.ceil(max(xs)) + 12, math.ceil(max(ys)) + 10)
    bw, bh = int((box[2] - box[0]) * R8), int((box[3] - box[1]) * R8)
    gy, gx = np.mgrid[0:bh, 0:bw]; X = (gx + .5) / R8 + box[0]; Y = (gy + .5) / R8 + box[1]; P = np.c_[X.ravel(), Y.ravel()]
    d_l = cKDTree(lp).query(P)[0].reshape(bh, bw)
    rng = np.random.default_rng(seed)
    wob = ndi.gaussian_filter(rng.normal(size=(bh, bw)), 1.8 * R8); wob = (wob - wob.min()) / (wob.max() - wob.min())
    near = d_l <= LAND_R * (0.7 + 0.6 * wob)
    near = ndi.binary_closing(near, structure=np.ones((3, 3), bool), iterations=int(1.5 * R8))
    near = ndi.binary_fill_holes(near)
    near = ndi.gaussian_filter(near.astype(float), 0.8 * R8) > 0.5
    thin = np.zeros((bh, bw), bool); d_sp = np.full((bh, bw), np.inf)          # the island and the beaches: their own thin land, the rest kept off them
    for v in sp:
        if v not in pos or rad[v] <= 0: continue
        dv = np.hypot(X - pos[v][0], Y - pos[v][1]); thin |= dv <= rad[v] * (0.85 + 0.3 * wob); d_sp = np.minimum(d_sp, dv - rad[v])
    for p, q, r in thin_lines:
        if r >= 9: continue
        dl = cKDTree(_samples([[p, q]], 0.05)).query(P)[0].reshape(bh, bw); thin |= dl <= r * (0.85 + 0.3 * wob); d_sp = np.minimum(d_sp, dl - r)
    d_isl = np.full((bh, bw), np.inf)
    for v in isl: d_isl = np.minimum(d_isl, np.hypot(X - pos[v][0], Y - pos[v][1]) - ISLAND_R)
    near &= (d_sp > SHORE_GAP) | (d_l <= 1.0)                                       # (other rooms keep a little land round them)
    near &= d_isl > ISLAND_GAP                                                      # (the island stands out at sea)
    near = (ndi.gaussian_filter(near.astype(float), 0.4 * R8) > 0.5) | (ndi.gaussian_filter(thin.astype(float), 0.25 * R8) > 0.5)
    for poly in COAST_FILL:                                                         # the coast round the Tipsy Lizard peninsula filled in (owner, Oct 18)
        im_ = Image.new('L', (bw, bh), 0); ImageDraw.Draw(im_).polygon([((x_ - box[0]) * R8, (y_ - box[1]) * R8) for x_, y_ in poly], fill=255); near |= np.array(im_, bool)
    store.update(box=box, sea=np.zeros((bh, bw), bool), land=near, nofill=d_sp < 6.0)

    def edit(land_n, water0, gx0, gy0):
        c0, r0 = int(round((box[0] - gx0) * R8)), int(round((box[1] - gy0) * R8))
        assert c0 >= 0 and r0 >= 0 and r0 + bh <= land_n.shape[0] and c0 + bw <= land_n.shape[1], (box, land_n.shape, gx0, gy0)
        sub = (slice(r0, r0 + bh), slice(c0, c0 + bw))
        old = land_n[sub].copy()
        add = near & ~water0[sub]
        land_n[sub] = old | add
        added = add & ~old
        full = np.zeros(land_n.shape, bool); full[sub] = added
        solid = land_n | water0                                                      # gaps (owner, Oct 18): ground enclosed by the Mire and the map, next to the Mire's new land
        holes = ndi.binary_fill_holes(solid) & ~solid
        lab, n = ndi.label(holes)
        ids = np.unique(lab[ndi.binary_dilation(full, iterations=3) & holes]); ids = ids[ids > 0]
        nf = np.zeros(land_n.shape, bool); nf[sub] = store['nofill']; ids = [i for i in ids if not ((lab == i) & nf).any()]
        gaps = np.isin(lab, ids)
        so = solid[sub] | gaps[sub]; pad = 4 * R8                                   # (+ narrow inlets in the Mire's own coast: closed by 3 rooms, smaller than INLET sq)
        cl = ndi.binary_closing(np.pad(so, pad), structure=disk(3 * R8))[pad:-pad, pad:-pad] & ~so
        lab2, n2 = ndi.label(cl)
        for i in range(1, n2 + 1):
            m_ = lab2 == i
            if m_.sum() / R8 / R8 < INLET and (ndi.binary_dilation(m_, iterations=3) & added).any() and not (m_ & store['nofill']).any(): gaps[sub] |= m_
        assert not (gaps & ~np.pad(np.ones((bh, bw), bool), ((r0, land_n.shape[0] - r0 - bh), (c0, land_n.shape[1] - c0 - bw)))).any(), 'a gap reaches out of the box'
        land_n |= gaps
        store['gaps'] = gaps[sub].copy()
        store['gap_pieces'] = [round(float((lab == i).sum()) / R8 / R8, 1) for i in ids]
        store['land_new_sq'] = round(float(added.sum()) / R8 / R8, 1); store['added'] = added | store['gaps']
        store['land'] = land_n[sub].copy()
        return land_n
    return edit


def avoid(store):
    """for add_west_sea: the land the Mire added (the west sea is worked out without it and kept off it)"""
    return store['box'], store['added']


def _place(mask, X, Y, spacing, salt, avoid=None):
    ys, xs = np.nonzero(mask); placed = []; grid = {}
    if avoid is not None and len(avoid):
        for q in avoid: grid.setdefault((int(q[0] // spacing), int(q[1] // spacing)), []).append((q[0], q[1]))
    for i in np.argsort(_hash(X[ys, xs], Y[ys, xs], salt), kind='stable'):
        x, y = X[ys[i], xs[i]], Y[ys[i], xs[i]]; gk = (int(x // spacing), int(y // spacing))
        if any(math.dist(q, (x, y)) < spacing for dx in (-1, 0, 1) for dy in (-1, 0, 1) for q in grid.get((gk[0] + dx, gk[1] + dy), ())): continue
        grid.setdefault(gk, []).append((x, y)); placed.append((round(float(x), 3), round(float(y), 3)))
    return placed


def _put(w, key, mask, box, sigma=1.5, minarea=0.15):
    """a ground tint, clear of what that tint already covers (tints are drawn even-odd: overlapping pieces would cancel)"""
    bw, bh = mask.shape[1], mask.shape[0]
    old = [p for p in (w['geo'].get(key) or []) if any(box[0] <= q[0] < box[2] and box[1] <= q[1] < box[3] for q in p)]
    if old: mask = mask & ~AA._raster(old, box[0], box[1], bw, bh)
    w['geo'][key] = list(w['geo'].get(key) or []) + AA._contours(mask, box[0], box[1], sigma=sigma, minarea=minarea)
    return round(float(mask.sum()) / R8 / R8, 1)


def merge_mi(w, layout, edges, store, seed=SEED):
    rooms, exits, pos, info, hidden, MI, shown, void, E, cls = _setup(layout, edges)
    rep = {}
    box = store['box']; sea = store['sea']; landm = store['land']
    bh, bw = sea.shape
    gy, gx = np.mgrid[0:bh, 0:bw]; X = (gx + .5) / R8 + box[0]; Y = (gy + .5) / R8 + box[1]; P = np.c_[X.ravel(), Y.ravel()]
    px = lambda p: ((p[0] - box[0]) * R8, (p[1] - box[1]) * R8)
    sqm = lambda m: round(float(m.sum()) / R8 / R8, 1)

    # ---------------------------------------------------------------- the graphs
    GD = defaultdict(set); links = []; uds = []
    _lp = {frozenset(e) for e in LAKE_PATH}; lakedash = []
    for a, b, k in E:
        if frozenset((a, b)) in _lp: continue                                       # (drawn whole, below)
        if ({a, b} & LAKE) and frozenset((a, b)) != frozenset((8459, 8460)): continue   # (no lines in the lake: owner, Oct 18)
        if frozenset((a, b)) == SHORTCUT: continue                                   # (a faint dashed line across the map, below)
        if not (a in MI and b in MI): links.append((a, b)); continue                 # to the map
        if k == 'ud': uds.append((a, b)); continue
        GD[a].add(b); GD[b].add(a)
    ext = defaultdict(int)
    for a, b in links + uds: ext[a] += 1; ext[b] += 1
    n_ = 0
    while True:                                                                      # spacer stubs: drawn only between two real rooms
        sp = [v for v in GD if void(v) and len(GD[v]) + ext.get(v, 0) <= 1]
        if not sp: break
        for v in sp:
            for u in list(GD[v]): GD[u].discard(v)
            del GD[v]; n_ += 1
    for v in [v for v in GD if not GD[v]]: del GD[v]
    rep['spacer_stubs_dropped'] = n_

    # ---------------------------------------------------------------- marsh water: the wading rooms and the exits between them
    WAT = {v for v in MI if shown(v) and cls[v] == 'water'} - LAKE
    im = Image.new('L', (bw, bh), 0); dr = ImageDraw.Draw(im); s_ = int(SQ * R8)
    for v in WAT:
        p = px(pos[v]); dr.rectangle([p[0] - s_ / 2, p[1] - s_ / 2, p[0] + s_ / 2, p[1] + s_ / 2], fill=255)
    for a, b, k in E:
        if a in WAT and b in WAT and k != 'ud': dr.line([px(pos[a]), px(pos[b])], fill=255, width=s_)
        elif k != 'ud' and ({a, b} & EXTRA_WATER) and math.dist(pos[a], pos[b]) <= 6: dr.line([px(pos[a]), px(pos[b])], fill=255, width=s_)   # (on to the clearing beyond: owner, Oct 18)
    watm = ndi.binary_fill_holes(np.array(im, bool))
    _wb = ndi.gaussian_filter(np.random.default_rng(seed + 7).normal(size=(bh, bw)), 0.7 * R8); _wb = (_wb - _wb.min()) / (_wb.max() - _wb.min())
    watm = (ndi.distance_transform_edt(~watm) / R8 <= 0.2 + 0.6 * _wb) & landm & ~sea   # (wavy edges)
    watm = ndi.gaussian_filter(watm.astype(float), 0.4 * R8) > 0.5
    _lk = Image.new('L', (bw, bh), 0); _ld = ImageDraw.Draw(_lk)                   # the Marshy Lake: exactly its rooms and the exits between them, out to the rooms it joins (owner, Oct 18)
    for v in LAKE:
        if shown(v): p = px(pos[v]); _ld.rectangle([p[0] - s_ / 2, p[1] - s_ / 2, p[0] + s_ / 2, p[1] + s_ / 2], fill=255)
    for a, b, k in E:
        if k != 'ud' and {a, b} & LAKE: _ld.line([px(pos[a]), px(pos[b])], fill=255, width=s_)
    watm |= ndi.gaussian_filter(ndi.binary_fill_holes(np.array(_lk, bool)).astype(float), 0.3 * R8) > 0.5
    _fl = [px(pos[v]) for v in FINGER_LAKE if shown(v)]
    if len(_fl) > 1:
        _fi = Image.new('L', (bw, bh), 0); _fd = ImageDraw.Draw(_fi); _fd.line(_fl, fill=255, width=s_, joint='curve')   # (half its first width: owner, Oct 18)
        for q in _fl: _fd.ellipse([q[0] - s_ / 2, q[1] - s_ / 2, q[0] + s_ / 2, q[1] + s_ / 2], fill=255)
        watm |= ndi.gaussian_filter(np.array(_fi, bool).astype(float), 0.3 * R8) > 0.5
    riv = np.zeros((bh, bw), bool)                                                   # the river (owner, Oct 18)
    for (xa, ya, wa), (xb, yb, wb_), hd in [s_ + (ci > 0,) for ci, ch in enumerate([RIVER] + RIVER_HEAD) for s_ in zip(ch[:-1], ch[1:])]:
        n_ = max(2, int(math.dist((xa, ya), (xb, yb)) / 0.1))
        for i in range(n_ + 1):
            f_ = i / n_; x, y, r = xa + (xb - xa) * f_, ya + (yb - ya) * f_, wa + (wb_ - wa) * f_
            if hd:                                                                    # (the slivers: as given, no winding, or they vanish)
                c, rr_ = (x - box[0]) * R8, (y - box[1]) * R8; k = int(r * R8) + 2
                sl = (slice(max(0, int(rr_) - k), int(rr_) + k + 1), slice(max(0, int(c) - k), int(c) + k + 1)); riv[sl] |= np.hypot(X[sl] - x, Y[sl] - y) <= r; continue
            x += min(r, 0.6) * 0.5 * (math.sin(y * 0.9 + 1.3) + 0.6 * math.sin(y * 2.3 + 0.4))   # (banks that wind: owner, Oct 18)
            r *= 0.82 + 0.18 * math.sin(y * 1.7 + 2.1) + 0.12 * math.sin(y * 3.9) + 0.06 * float(_hash(round(x, 1), round(y, 1), 201)); c, rr_ = (x - box[0]) * R8, (y - box[1]) * R8; k = int(r * R8) + 2
            sl = (slice(max(0, int(rr_) - k), int(rr_) + k + 1), slice(max(0, int(c) - k), int(c) + k + 1))
            riv[sl] |= np.hypot(X[sl] - x, Y[sl] - y) <= r
    for x_, y_, ax_, ay_, an_ in MARSH_PONDS:                                         # the marsh of small lakes and streams at the river's head (owner, Oct 18)
        ca, sa = math.cos(math.radians(an_)), math.sin(math.radians(an_)); u_ = (X - x_) * ca + (Y - y_) * sa; v_ = -(X - x_) * sa + (Y - y_) * ca
        riv |= (u_ / ax_) ** 2 + (v_ / ay_) ** 2 <= 1
    for ln in MARSH_STREAMS:
        for p_, q_ in zip(ln[:-1], ln[1:]):
            n_ = max(2, int(math.dist(p_, q_) / 0.08))
            for i in range(n_ + 1):
                x_, y_ = p_[0] + (q_[0] - p_[0]) * i / n_, p_[1] + (q_[1] - p_[1]) * i / n_; c, rr_ = (x_ - box[0]) * R8, (y_ - box[1]) * R8; k = 4
                sl = (slice(max(0, int(rr_) - k), int(rr_) + k + 1), slice(max(0, int(c) - k), int(c) + k + 1)); riv[sl] |= np.hypot(X[sl] - x_, Y[sl] - y_) <= 0.22
    riv = ndi.gaussian_filter(riv.astype(float), 0.25 * R8) > 0.5
    riv &= Y <= RIVER_END

    # ---------------------------------------------------------------- clearings: cells of mutually joined other real rooms (the range's rule)
    real = {v for v in GD if not void(v) and v not in WAT}
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
    im = Image.new('L', (bw, bh), 0); dr = ImageDraw.Draw(im)
    for cell in cells:
        pts = np.array([pos[v] for v in cell])
        try: hull = ConvexHull(pts)
        except Exception: continue
        if hull.volume < 0.45: continue
        dr.polygon([px(p) for p in pts[hull.vertices]], fill=255, outline=255)
    clear = ndi.binary_dilation(np.array(im, bool), structure=disk(int(PAD * R8)))
    clear = ndi.gaussian_filter(clear.astype(float), 0.45 * R8) > 0.5
    for S_ in EXTRA_CLEAR:                                                           # (owner, Oct 18) these rooms, the exits between them, holes filled: one clearing each
        S_ = {v for v in S_ if shown(v)}; im = Image.new('L', (bw, bh), 0); dr = ImageDraw.Draw(im); s_ = int(SQ * R8)
        for v in S_:
            p = px(pos[v]); dr.rectangle([p[0] - s_ / 2, p[1] - s_ / 2, p[0] + s_ / 2, p[1] + s_ / 2], fill=255)
        for a, b, k in E:
            if a in S_ and b in S_ and k != 'ud': dr.line([px(pos[a]), px(pos[b])], fill=255, width=s_)
        m_ = ndi.binary_fill_holes(ndi.binary_closing(np.array(im, bool), structure=disk(int(1.2 * R8))))
        clear |= ndi.binary_dilation(m_, structure=disk(int(PAD * R8)))
    clear &= ~watm & ~sea & ~ndi.binary_dilation(riv, iterations=2)
    _wsec = info.get(WETLAND, {}).get('piece'); _wr = [pos[v] for v in MI if shown(v) and info[v].get('piece') == _wsec]
    labw, nw = ndi.label(clear); wet = np.zeros_like(clear)
    for x_, y_ in _wr:
        c_, r_ = int((x_ - box[0]) * R8), int((y_ - box[1]) * R8)
        if 0 <= r_ < bh and 0 <= c_ < bw and labw[r_, c_]: wet |= labw == labw[r_, c_]
    clear &= ~wet
    lab, n = ndi.label(clear); keep = np.zeros_like(clear)
    for i in range(1, n + 1):
        comp = lab == i
        if comp.sum() / R8 / R8 >= MIN_PATCH: keep |= comp
    clear = keep
    patches = AA._contours(clear, box[0], box[1], sigma=1.0, tol=0.35, minarea=MIN_PATCH * 0.5)
    w['smrpatch'] = list(w.get('smrpatch') or []) + patches
    patchm = AA._raster(patches, box[0], box[1], bw, bh)
    rep['water'] = dict(rooms=len(WAT), sq=sqm(watm)); rep['clearings'] = dict(cells=len(cells), patches=len(patches), sq=sqm(clear))

    # ---------------------------------------------------------------- lines: trails (clipped at the water and the clearings), links, up/down exits
    blocked = patchm | watm | wet
    def trails(G):
        Tg = defaultdict(set)
        for a in G:
            for b in G[a]:
                if a >= b: continue
                k_ = max(2, int(math.dist(pos[a], pos[b]) * 3)); inside = True
                for i in range(k_ + 1):
                    x = pos[a][0] + (pos[b][0] - pos[a][0]) * i / k_; y = pos[a][1] + (pos[b][1] - pos[a][1]) * i / k_
                    c, r = int((x - box[0]) * R8), int((y - box[1]) * R8)
                    if not (0 <= r < bh and 0 <= c < bw and blocked[r, c]): inside = False; break
                if not inside: Tg[a].add(b); Tg[b].add(a)
        return Tg
    dirt = _chains(trails(GD), pos, set(), 0.8)
    for a, b in links + uds:
        L_ = math.dist(pos[a], pos[b])
        if L_ > 60: continue
        if L_ <= WAVY_LINK: dirt.append([[round(pos[a][0], 2), round(pos[a][1], 2)], [round(pos[b][0], 2), round(pos[b][1], 2)]]); continue
        (ax, ay), (bx_, by_) = pos[a], pos[b]; nx_, ny_ = -(by_ - ay) / L_, (bx_ - ax) / L_; n_ = max(6, int(L_ / 1.6)); ph = float(_hash(ax, ay, 211)) * 6.28
        dirt.append([[round(ax + (bx_ - ax) * s + nx_ * o, 2), round(ay + (by_ - ay) * s + ny_ * o, 2)] for s in [i / n_ for i in range(n_ + 1)]
                     for o in [math.sin(math.pi * s) * (0.9 * math.sin(s * L_ / 4.5 + ph) + 0.4 * math.sin(s * L_ / 1.9 + 2 * ph))]])   # (a gentle wave, none at the ends)
    def clip(lines, mask):
        out = []
        for ln in lines:
            pts = []
            for p, q in zip(ln[:-1], ln[1:]):
                k_ = max(1, int(math.dist(p, q) / 0.08)); pts += [(p[0] + (q[0] - p[0]) * k / k_, p[1] + (q[1] - p[1]) * k / k_) for k in range(k_)]
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
    w['fwtracks'] = list(w['fwtracks']) + dirt
    w['fwtracks'] = list(w['fwtracks']) + [[[round(pos[a][0], 2), round(pos[a][1], 2)], [round(pos[b][0], 2), round(pos[b][1], 2)]] for a, b in LAKE_PATH if shown(a) and shown(b)]
    w['geo']['water'] = list(w['geo']['water']) + AA._contours(riv, box[0], box[1], sigma=1.0, tol=0.15, minarea=0.05)
    w['micrumble'] = [BRIDGE]
    rep['lines'] = dict(trails=len(dirt), links=links, up_down=uds)

    land_mi = landm
    rep['land'] = dict(new_sq=store.get('land_new_sq'), enclosed_gaps_sq=store.get('gap_pieces'), all_gaps_and_inlets_sq=sqm(store['gaps']))

    # ---------------------------------------------------------------- ground: one bog ground; zones by the nearest room's terrain
    rs = [v for v in MI if shown(v) and not void(v) and v not in NOT_MIRE]       # (the Dragon's Pass rooms get no Mire ground round them)
    dist, idx = cKDTree(np.array([pos[v] for v in rs])).query(P)
    Z = np.array([cls[v] for v in rs])[idx].reshape(bh, bw); dist = dist.reshape(bh, bw)
    fx = [pos[v] for v, r in info.items() if (r.get('fixed') or r.get('grp') == 'un') and v in pos]   # (unlocked map rooms are map rooms)
    d_fix = cKDTree(np.array(fx)).query(P)[0].reshape(bh, bw) if fx else np.full((bh, bw), np.inf)
    gaps = store['gaps'] & land_mi
    _ry = np.array([p[1] for p in RIVER]); _rx = np.array([p[0] for p in RIVER])
    east = (Y >= _ry[0]) & (Y <= _ry[-1]) & (X > np.interp(Y, _ry, _rx))           # (east of the river is the Wastelands' ground: owner, Oct 18)
    own = land_mi & ((dist <= LAND_R + 8) | (store['added'] & ~gaps)) & (dist < d_fix)   # (the Mire's own ground: its new land, and land nearer its rooms than the map's)
    own |= gaps & (dist < d_fix)                                                   # (a gap's part nearer the Mire is the Mire's, however far)
    own &= ~east
    clipped = {}                                                                   # (no other tint under or over it)
    bb = lambda p: (min(q[0] for q in p), min(q[1] for q in p), max(q[0] for q in p), max(q[1] for q in p))
    for k in [k for k in w['geo'] if k not in ('land', 'water')]:
        hit = [p for p in w['geo'][k] if any(box[0] <= q[0] < box[2] and box[1] <= q[1] < box[3] for q in p) and (AA._raster([p], box[0], box[1], bw, bh) & own).any()]
        if not hit: continue
        grp = [p for p in w['geo'][k] if p in hit or any(bb(h)[0] <= bb(p)[0] and bb(h)[1] <= bb(p)[1] and bb(p)[2] <= bb(h)[2] and bb(p)[3] <= bb(h)[3] for h in hit)]   # (with their holes)
        gb = [math.floor(min(bb(p)[0] for p in grp + [[box[:2]]])) - 1, math.floor(min(bb(p)[1] for p in grp + [[box[:2]]])) - 1,
              math.ceil(max(bb(p)[2] for p in grp + [[box[2:]]])) + 1, math.ceil(max(bb(p)[3] for p in grp + [[box[2:]]])) + 1]   # (a grid round them all: a polygon reaching out of the box is traced whole)
        gw, gh = int((gb[2] - gb[0]) * R8), int((gb[3] - gb[1]) * R8)
        m = AA._raster(grp, gb[0], gb[1], gw, gh); o_ = np.zeros((gh, gw), bool)
        c0, r0 = int(round((box[0] - gb[0]) * R8)), int(round((box[1] - gb[1]) * R8)); o_[r0:r0 + bh, c0:c0 + bw] = own
        clipped[k] = round(float((m & o_).sum()) / R8 / R8, 1)
        w['geo'][k] = [p for p in w['geo'][k] if not any(p is g for g in grp)] + AA._contours(m & ~o_, gb[0], gb[1], sigma=1.0, tol=0.3, minarea=0.15)
    rep['other_tints_clipped_sq'] = clipped
    sm = lambda m, s=0.6: ndi.gaussian_filter(m.astype(float), s * R8) > 0.5
    zone = lambda k: sm(own & (dist <= TERR_R) & (Z == k))
    tints = {'bog': _put(w, 'bog', own, box, sigma=2.0)}
    beach = zone('beach') & ~watm
    tints['sand'] = _put(w, 'sand', beach & ~patchm, box, sigma=1.5)
    w['migreen'] = AA._contours(wet, box[0], box[1], sigma=1.0, tol=0.35, minarea=0.3)   # the swampy valley at 7873: a clearing, mossy green (owner, Oct 18)
    w['miwater'] = AA._contours(watm, box[0], box[1], sigma=1.0, tol=0.35, minarea=0.3)   # the wading rooms (the Reeds, Blackpool Bog, the Marshy Lake): drawn like the clearings, in dull dark blue (owner, Oct 18)
    tints['wet_valley'] = sqm(wet)
    tints['marsh_water'] = sqm(watm)

    # ---------------------------------------------------------------- old sprites make way for the Mire's paths and ground
    d_path = cKDTree(_samples([_drawn(l) for l in dirt], 0.1)).query(P)[0].reshape(bh, bw) if dirt else np.full((bh, bw), np.inf)
    onway = (d_path <= 0.55) | patchm
    def off(q):
        c, r = int((q[0] - box[0]) * R8), int((q[1] - box[1]) * R8)
        return 0 <= r < bh and 0 <= c < bw and bool(onway[r, c] or own[r, c])
    cl = {}
    for k in SPRITES:
        n0 = len(w.get(k) or []); w[k] = [q for q in (w.get(k) or []) if not off(q)]
        if n0 - len(w[k]): cl[k] = n0 - len(w[k])
    rep['old_sprites_cleared'] = cl

    # ---------------------------------------------------------------- the gaps' other parts: standard terrain, as the land round them (gap_fill's way)
    std = gaps & ~own & (d_path > 0.6)
    lab, n = ndi.label(std); gstd = []
    rng = np.random.default_rng(seed + 21)
    tint_m = {}
    for i in range(1, n + 1):
        m = lab == i
        ring = ndi.binary_dilation(m, iterations=int(2.5 * R8)) & ~ndi.binary_dilation(m, iterations=2) & land_mi & ~gaps & ~own
        if not ring.any() or m.sum() < R8 * R8: continue
        got = {}
        for k in [k for k in w['geo'] if k not in ('land', 'water', 'shallows')]:
            if k not in tint_m:
                ps = [p for p in w['geo'][k] if any(box[0] <= q[0] < box[2] and box[1] <= q[1] < box[3] for q in p)]
                tint_m[k] = AA._raster(ps, box[0], box[1], bw, bh) if ps else None
            if tint_m[k] is not None and tint_m[k][ring].mean() >= 0.35:
                got[k] = _put(w, k, ndi.binary_dilation(m, iterations=3) & land_mi & ~own, box, sigma=1.5)
        ringsq = float(ring.sum()) / R8 / R8; area = float(m.sum()) / R8 / R8
        inner = m & ~ndi.binary_dilation(~m, iterations=2); ys_, xs_ = np.nonzero(inner)
        spr = {}
        for k in SPRITES:
            ref = [q for q in (w.get(k) or []) if 0 <= int((q[1] - box[1]) * R8) < bh and 0 <= int((q[0] - box[0]) * R8) < bw and ring[int((q[1] - box[1]) * R8), int((q[0] - box[0]) * R8)]]
            if not ref or not len(xs_): continue
            want = int(round(len(ref) / ringsq * area)); new = []; pts = []
            for _ in range(want * 4):
                if len(new) >= want: break
                j = rng.integers(len(xs_)); x = (xs_[j] + rng.random()) / R8 + box[0]; y = (ys_[j] + rng.random()) / R8 + box[1]
                if any(math.hypot(x - a, y - b) < 0.35 for a, b in pts[-60:]): continue
                q = list(ref[rng.integers(len(ref))]); q[0], q[1] = round(float(x), 3), round(float(y), 3); new.append(q); pts.append((x, y))
            w[k] = list(w[k]) + new; spr[k] = len(new)
        gstd.append(dict(sq=round(area, 1), at=[round(float(X[m].mean()), 1), round(float(Y[m].mean()), 1)], tints=got, sprites=spr))
    rep['gaps_standard_terrain'] = gstd

    # ---------------------------------------------------------------- the swamp (owner, Oct 18: "a miserable swamp"; the map's own pieces):
    # a darker mottled bog, mud patches, stagnant pools ringed with reeds, thickets of dead trees and brush, reeds all over, scattered swamp trees
    noise = lambda s, sd: (lambda a: (a - a.min()) / (a.max() - a.min()))(ndi.gaussian_filter(np.random.default_rng(seed + sd).normal(size=(bh, bw)), s * R8))
    n1, n2, n3, n4 = noise(1.6, 31), noise(1.3, 32), noise(1.1, 33), noise(0.5, 34)
    base = own & ~patchm & ~watm & ~beach
    bog2 = sm(base & (n1 > 0.55), 0.5)
    tints['bog2'] = _put(w, 'bog2', bog2, box, sigma=2.0)
    walk = d_path > 0.7
    mud = sm(base & walk & (n2 > 0.66) & (dist <= LAND_R + 4), 0.5)
    tints['mimud'] = _put(w, 'mimud', mud, box, sigma=1.5)
    thick = base & ~mud & (d_path > 1.1) & (n3 > 0.66) & ~ndi.binary_dilation(watm, iterations=R8)
    thick = ndi.binary_opening(thick, iterations=R8 // 2)
    lab, n = ndi.label(thick)
    if n: thick = np.isin(lab, [i + 1 for i, s in enumerate(ndi.sum(thick, lab, range(1, n + 1))) if s / R8 / R8 >= 1.5])
    tints['thicket'] = _put(w, 'thicket', thick, box, sigma=1.5)
    cand = base & ~mud & ~thick & (d_path > 1.5) & ~ndi.binary_dilation(watm, iterations=int(1.2 * R8))
    centres = [q for q in _place(cand, X, Y, 7.0, 141) if _hash(q[0], q[1], 144) < 0.55]   # (few, and of different sizes)
    from matplotlib.path import Path as _MP
    centres = [q for q in centres if not any(_MP(poly).contains_point(q) for poly in COAST_FILL)]   # (no pools in the filled gaps: no round puddles, owner)
    pool = np.zeros((bh, bw), bool)
    for x, y in centres:
        r = 0.4 + 1.1 * float(_hash(x, y, 142)) ** 2; c, rr_ = int((x - box[0]) * R8), int((y - box[1]) * R8); k = int((r * 1.4 + 0.2) * R8)
        sl = (slice(max(0, rr_ - k), rr_ + k + 1), slice(max(0, c - k), c + k + 1))
        pool[sl] |= np.hypot(X[sl] - x, Y[sl] - y) <= r * (0.7 + 0.6 * n4[sl])
    pool = sm(pool & cand, 0.25)
    w['geo']['mipool'] = list(w['geo'].get('mipool') or []) + AA._contours(pool, box[0], box[1], sigma=1.0, tol=0.2, minarea=0.12)
    tints['pools'] = dict(n=len(centres), sq=sqm(pool))
    rep['tints_sq'] = tints

    # ---------------------------------------------------------------- sprites (clear of paths, clearings, water)
    free = own & (d_path > 0.6) & ~patchm & ~watm & ~pool & ~wet
    hills = _place(free & zone('hills') & (d_path > 1.0), X, Y, 1.8, 187)
    w['hills'] = list(w['hills']) + [[x, y, round(0.8 + 0.3 * float(_hash(x, y, 188)), 2), 'h', int(float(_hash(x, y, 189)) * 3)] for x, y in hills]
    rocks = _place(free & zone('rocks') & ~beach & (d_path > 0.5), X, Y, 1.0, 193, hills)
    w['boulders'] = sorted(list(w.get('boulders') or []) + [[x, y, round(0.4 + 0.3 * float(_hash(x, y, 194)), 2)] for x, y in rocks], key=lambda b: b[1])
    trees = _place(free & zone('forest') & (d_path > 0.7), X, Y, 0.9, 181, hills + rocks)
    tk = [[x, y, round(0.85 + 0.3 * float(_hash(x, y, 182)), 2), 'w', int(float(_hash(x, y, 183)) * 3)] for x, y in trees]
    inth = free & thick & ndi.binary_erosion(thick, iterations=2)                 # thickets: dead trees and brown brush, packed (the Plains' thicket mix)
    tp = _place(inth, X, Y, 0.55, 151, hills + rocks + trees)
    dead = [q for q in tp if _hash(q[0], q[1], 152) < 0.45]; shrub = [q for q in tp if _hash(q[0], q[1], 152) >= 0.45]
    tk += [[x, y, round(0.7 + 0.3 * float(_hash(x, y, 153)), 2), 'h', int(float(_hash(x, y, 154)) * 3)] for x, y in dead]
    ring = ndi.binary_dilation(watm | pool, iterations=int(0.7 * R8)) & ~ndi.binary_erosion(watm | pool, iterations=int(0.25 * R8))
    reeds_w = _place(own & ring & (d_path > 0.45) & ~patchm & ~beach & ~thick, X, Y, 0.75, 171, hills + rocks + trees + tp)   # (round the water)
    lone = free & ~thick & ~beach & ~ring & (d_path > 0.9)
    st = _place(lone, X, Y, 2.3, 161, hills + rocks + trees + tp + reeds_w)       # (lone swamp trees, mostly dead)
    tk += [[x, y, round(0.75 + 0.35 * float(_hash(x, y, 162)), 2), 'h' if _hash(x, y, 163) < 0.65 else 'w', int(float(_hash(x, y, 164)) * 3)] for x, y in st]
    w['trees'] = list(w['trees']) + tk
    reeds_b = _place(free & ~thick & ~beach & ~ring & (n1 > 0.45), X, Y, 1.7, 172, hills + rocks + trees + tp + reeds_w + st)   # (reeds and sedge all over the bog)
    reeds_v = []
    w['reeds'] = list(w['reeds']) + [[x, y, round(0.75 + 0.45 * float(_hash(x, y, 173)), 2)] for x, y in reeds_w + reeds_b + reeds_v]
    w['brush'] = sorted(list(w.get('brush') or []) + [[x, y, round(0.8 + 0.4 * float(_hash(x, y, 155)), 2), 1] for x, y in shrub], key=lambda b: b[1])
    rv = ndi.binary_dilation(riv, iterations=2)
    for k in SPRITES:
        w[k] = [q for q in (w.get(k) or []) if not (0 <= int((q[1] - box[1]) * R8) < bh and 0 <= int((q[0] - box[0]) * R8) < bw and rv[int((q[1] - box[1]) * R8), int((q[0] - box[0]) * R8)])]
    sto = [q for q in _place(ndi.binary_erosion(riv, iterations=int(0.35 * R8)) & (Y >= RIVER_STONES[0]) & (Y <= RIVER_STONES[1]) & (d_path > 0.5), X, Y, 0.8, 205) if _hash(q[0], q[1], 206) < 0.6]
    w['mistones'] = [[x, y, round(0.09 + 0.08 * float(_hash(x, y, 207)), 3)] for x, y in sto]
    hz = np.zeros((bh, bw), bool)
    for x_, y_, ax_, ay_, an_ in MARSH_PONDS: hz |= np.hypot(X - x_, Y - y_) <= ax_ + 1.0
    hz &= ~riv & land_mi
    hr = _place(hz & (d_path > 0.4), X, Y, 0.45, 176)
    w['reeds'] = list(w['reeds']) + [[x, y, round(0.75 + 0.4 * float(_hash(x, y, 177)), 2)] for x, y in hr]
    tints['river'] = dict(sq=sqm(riv), stones=len(sto), head_marsh_reeds=len(hr))
    rep['sprites'] = dict(forest_trees=len(trees), thicket_dead_trees=len(dead), thicket_brush=len(shrub), swamp_trees=len(st), hills=len(hills), boulders=len(rocks),
                          reeds_round_water=len(reeds_w), reeds_on_bog=len(reeds_b))

    # ---------------------------------------------------------------- the map grows west and south
    xs_ = [q[0] for k in ('land', 'water') for p in w['geo'][k] for q in p]; ys_ = [q[1] for k in ('land', 'water') for p in w['geo'][k] for q in p]
    b0 = list(w['bounds'])
    w['bounds'] = [min(b0[0], int(math.floor(min(xs_))) - 1), b0[1], b0[2], max(b0[3], int(math.ceil(max(ys_))) + 1)]
    rep['bounds'] = [b0, w['bounds']]
    rep['rooms'] = dict(shown=len([v for v in MI if shown(v) and not void(v)]), hidden=len([v for v in MI if v in hidden]),
                        classes={k: sum(1 for v in MI if shown(v) and not void(v) and cls[v] == k) for k in sorted(set(cls.values()))})
    return w, rep


EXTRA_PLACES = [("Tipsy Lizard Tavern", "#6 s;ne;#2 s;se;#2 e;s;#2 sw;s;#10 sw;w;u;s;#2 e;#2 se;#2 s;sw;#2 nw;#3 w;sw;w;#4 sw;#4 s;se;s;sw;s;sw;w;#6 sw;s;#2 sw;e", None),
                ("Redferne's Residence", "#6 s;ne;#2 s;se;#2 e;s;#2 sw;s;#5 sw;nw;n;ne;nw;#2 n;ne;n;e;#2 se;e;s;se;sw;#2 s;sw;#2 s;sw;s;se;#2 e;se;e;se;sw;#2 se;#2 s;#2 se;e;se;sw;s;#2 e;#3 se;#2 s;#2 e;s;e;s;w", None),
                ("The Mire (Central)", "#6 s;ne;#2 s;se;#2 e;s;#2 sw;s;#5 sw;nw;n;ne;nw;#2 n;ne;n;e;#2 se;e;s;se;sw;s", None),   # (owner, Oct 18: ends at 8195)
                ("Shadowport", None, 'onhidden'),   # the marker on the hidden room 10099 (the route's end): its route from data.py (owner, Oct 18)
                ("Vaellys el Notrune", "#6 s;ne;#2 s;se;#2 e;s;#2 sw;s;#10 sw;w;u;s;#2 e;#2 se;#2 s;sw;#2 nw;#3 w;sw;w;#4 sw;#4 s;se;s;sw;s;sw;w;#6 sw;s;#2 sw;w;sw;w;n;nw;n", 'mob')]   # (owner, Oct 18)
SUBAREAS = ("Dragon Tower", "High Tower of Sorcery", "Ockwater Fens", "Old Marsh", "Tribal Swamplands (Lizardmen)")   # the areas off the Mire with directions in data.py (owner, Oct 18;
# not the Forest of Tears or the Wastelands; Dragon's Pass and Machine Dreams are already on the map by other routes; Asgard Nexus stays off the map)


def add_mi_places(w, layouts):
    """the Mire's sub-area destinations, traced from the owner's directions: the marker where the route leaves the drawn rooms (as add_wl_places)"""
    import re
    import data as DT
    from route_fix import make_tracer
    from extra_places import segments
    rooms, walk, at = make_tracer(w, layouts)
    exits = AF._world()[1]; hid = set().union(*(set(L.get('hidden', [])) for L in layouts[-2:])) | NOT_MIRE   # (the Mire layout and the unsaved editor rooms come last; hidden rooms are not drawn)
    lines = (DT.AREAS + '\n' + DT.HOMETOWNS + '\n' + DT.MORE_DIRECTIONS).split('\n')
    rep = {}
    for name in SUBAREAS:
        if any(p['name'] == name for p in w['places']): rep[name] = 'already on the map'; continue
        route = next(l.split('|', 1)[1].strip().rstrip(';') for l in lines if l.startswith(name + '|'))
        t = walk(route)
        last = max(i for i, v in enumerate(t) if at(v) and v not in hid)      # (the last drawn room: hidden rooms are not drawn)
        upto = t[:last + 1]; segs = segments([at(v) for v in upto])
        v_ = upto[-1]; base = name.split(' (')[0]
        out = [e for e in exits.get(v_, []) if rooms.get(e['to'], {}).get('area', '').startswith(base)]
        d = out[0]['name'] if out else ('here' if last == len(t) - 1 else re.sub(r'^#\s*\d+\s*', '', route.split(';')[-1].strip()))
        if d not in ('n', 's', 'e', 'w', 'ne', 'nw', 'se', 'sw'): d = 'here'
        w['places'].append(dict(name=name, route=route, room=rooms[upto[-1]]['name'], dir=d, path=[q for s_ in segs for q in s_], segs=segs,
                                group='af', where='off the Mire',
                                note=None if len(segs) == 1 else "Part of your directions passes through areas that aren't drawn yet, so the traced line breaks there."))
        rep[name] = dict(end_room=upto[-1], walked=len(t), left_at=len(upto), dir=d, pieces=len(segs), marker=segs[-1][-1])
    mp = next((p for p in w['places'] if p['name'] == 'The Mire'), None)
    if mp:                                                                           # the owner's new directions into the Mire (Oct 18): retraced over the Mire's rooms, the marker at the route's end
        route = next(l.split('|', 1)[1].strip().rstrip(';') for l in lines if l.startswith('The Mire|'))
        t = walk(route); last = max(i for i, v in enumerate(t) if at(v) and v not in hid)
        upto = t[:last + 1]; segs = segments([at(v) for v in upto])
        mp.update(route=route, room=rooms[upto[-1]]['name'], dir='here' if last == len(t) - 1 else mp.get('dir'), path=[q for s_ in segs for q in s_], segs=segs,
                  note=None if len(segs) == 1 else "Part of your directions passes through areas that aren't drawn yet, so the traced line breaks there.")
        rep['The Mire'] = dict(end_room=upto[-1], walked=len(t), left_at=len(upto), dir=mp['dir'], pieces=len(segs), marker=segs[-1][-1])
    pos = {}
    for L in layouts:
        for v, x, y in zip(L['ids'], L['xs'], L['ys']): pos.setdefault(v, (x, y))
    g = []
    if 7872 in pos:                                                                  # Machine Dreams' second entrance (7872 'enter'): a text label only (owner, Oct 18)
        g.append({'k': 'text', 'at': 'xy', 'x': round(pos[7872][0], 2), 'y': round(pos[7872][1] + 0.85, 2), 'text': 'Machine Dreams'})
    for b in w['gfx']:
        if b.get('k') == 'barn': b['y'] = round(b['y'] - 0.5, 2); rep['barn_moved_north'] = 0.5   # the MacMillan Family Farm's barn, a little north (owner, Oct 18)
    for name, route, kind in EXTRA_PLACES:                                           # owner's places (Oct 18), traced from Darkhaven Square
        if any(p['name'] == name for p in w['places']): continue
        if route is None: route = next(l.split('|', 1)[1].strip().rstrip(';') for l in lines if l.startswith(name + '|'))
        t = walk(route); last = max(i for i, v in enumerate(t) if at(v) and (v not in hid or kind == 'onhidden'))
        if kind == 'onhidden': kind = None
        upto = t[:last + 1]; segs = segments([at(v) for v in upto])
        d = 'here' if last == len(t) - 1 else re.sub(r'^#\s*\d+\s*', '', route.split(';')[-1].strip())
        pl = dict(name=name, route=route, room=rooms[upto[-1]]['name'], dir=d, path=[q for s_ in segs for q in s_], segs=segs, group='af', where='in the Mire',
                  note=None if len(segs) == 1 else "Part of your directions passes through areas that aren't drawn yet, so the traced line breaks there.")
        if kind: pl['kind'] = kind
        w['places'].append(pl); rep[name] = dict(end_room=upto[-1], walked=len(t), left_at=len(upto), dir=d, pieces=len(segs), marker=segs[-1][-1], kind=kind)
    pin = lambda p: (p['path'][-1][0] + {'n': 0, 's': 0, 'e': .62, 'w': -.62}.get(p['dir'], 0) * (1 if p['dir'] in ('e', 'w') else 0), p['path'][-1][1] + {'n': -.62, 's': .62}.get(p['dir'], 0))
    tl = next((p for p in w['places'] if p['name'] == 'Tipsy Lizard Tavern'), None)
    if tl:                                                                           # a small inn east of its marker, its name below the inn (owner, Oct 18)
        q = pin(tl); ix_, iy_ = q[0] + 1.4, q[1] - 0.65                              # (a dusty old outback shack: owner, Oct 18; 0.45 up, clear of the name below the dot)
        g.append({'k': 'shack', 'at': 'xy', 'x': round(ix_, 2), 'y': round(iy_, 2), 'w': 2.0, 'h': 1.6})
        # (its name: a standard place label centred below the marker dot, template LBL + PINNED: owner, Oct 18)
    rf = next((p for p in w['places'] if p['name'] == "Redferne's Residence"), None)
    if rf:                                                                           # a large, old, grand mansion above its marker, drawn like an old map's (owner, Oct 18)
        dx_, dy_ = pos[MANSION_DOOR_AT]                                              # north of the trail, its central front door just north of the trail's end 8421 (owner, Oct 18)
        g.append({'k': 'mansion', 'at': 'xy', 'x': round(dx_, 2), 'y': round(dy_ - 0.55 - 0.95 * 2.3 / 2.6, 2), 'w': 3.2, 'h': 2.3})   # (the door's foot at sprite y .95)
    mc = next((p for p in w['places'] if p['name'] == 'The Mire (Central)'), None)
    if mc:                                                                           # a small, dull, grim old-map dragon just north of its marker (owner, Oct 18)
        e = mc['path'][-1]
        g.append({'k': 'dragon', 'at': 'xy', 'x': round(e[0], 2), 'y': round(e[1] - 0.85 - DRAGON[1] / 2, 2), 'w': DRAGON[0], 'h': DRAGON[1]})
    for b in g:                                                                      # nothing grows under the new buildings
        if b['k'] in ('shack', 'mansion', 'dragon'):
            for k in SPRITES: w[k] = [s for s in (w.get(k) or []) if not (abs(s[0] - b['x']) < b['w'] / 2 + 0.2 and abs(s[1] - b['y']) < b['h'] / 2 + 0.2)]
    ht = next((p for p in w['places'] if p['name'] == 'High Tower of Sorcery'), None)
    if ht:                                                                           # a sorcerer's tower north of its marker (owner, Oct 18)
        e = ht['path'][-1]; v_ = {'n': (0, -1), 's': (0, 1), 'e': (1, 0), 'w': (-1, 0)}.get(ht['dir'], (0, 0)); px_, py_ = e[0] + v_[0] * .62, e[1] + v_[1] * .62
        g.append({'k': 'magetower', 'at': 'xy', 'x': round(px_, 2), 'y': round(py_ - 0.55 - 5.0 / 2, 2), 'w': 1.6, 'h': 5.0})   # (as big as Dragon Tower's: owner, Oct 18)
    if 8155 in pos:                                                                  # a tall grey stone tower north of Dragon Tower's gates (8155) up to y 43 (owner, Oct 18)
        x_, y0_ = pos[8155][0] - 0.1, pos[8155][1] - 0.6
        g.append({'k': 'stonetower', 'at': 'xy', 'x': round(x_, 2), 'y': round((y0_ + 43.0) / 2, 2), 'w': 1.1, 'h': round(y0_ - 43.0, 2)})
    w['gfx'] = list(w['gfx']) + g; rep['gfx'] = g
    return w, rep
