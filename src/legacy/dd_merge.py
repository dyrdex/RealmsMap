"""The Desert of Despair (owner, Oct 20): dd_layout_final.json, dd_editor_edges.json (the owner's layout from tools/desert_of_despair_editor).
First pass, in broad strokes (as the Mire's first pass; the owner reviews it):
  - land round every shown desert room and the exits between them (traced with the mainland: dd_land is chained last into smr_merge's
    land_edit, whose grid now reaches 24 rooms further east); the gaps it closes against the map filled; no sea of its own;
  - ONE ground under the whole area: the sand tint (other tints cut back to where the desert's ground starts: nearer its rooms than the map's);
  - clumps of mutually joined rooms = clearings (the range's rule); dirt trails elsewhere, clipped at the clearings; links to the map and
    up/down exits as trails.
The Wastelands and Coral Depths rooms the owner moved in this editor are drawn by wl_merge / cd_merge (build_legacy puts the save's spots into
their layouts). No sprites, markers, labels or names (none asked for yet)."""
import math
import numpy as np
from collections import defaultdict
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from scipy.spatial import cKDTree, ConvexHull
from skimage.morphology import disk
import arrange_apply as AA
import gap_fill as GF
from ntr_merge import _chains, _samples, _sharp
from smr_merge import _drawn
from mi_merge import _put
import ashen_forest as AF

R8 = GF.R8
LAND_R = 4.2
INLET = 60.0                                     # (sq) narrow inlets in the desert's coast smaller than this are filled
PAD, SQ, CELL_MAX, MIN_PATCH = 0.55, 1.1, 6.0, 3.0
STEP_GRID = 2.6                                  # (the steppes' grid: exits this short)
STX_BOX = (44.0, 88.0, 56.0, 116.0)              # (the Arid Steppes clearing grows only here: the desert side)
WAVY = 8.0                                       # (links longer than this: still straight; the owner placed them)
SPRITES = ('trees', 'tufts', 'peaks', 'hills', 'boulders', 'crags', 'brush', 'wheattufts', 'ripples', 'reeds', 'thorns')
SEED = 307
EXTRA_CLEAR = [{6495, 6498, 6499, 6463, 6464, 6465, 6496, 6497, 6500,                     # the ruins' clearing round 6464 ...
                23735, 6462, 6494, 23736, 23734, 6466, 23737}]                        # ... with the single rooms east and west of it (owner, Oct 20)


def _setup(layout, edges):
    pos = dict(zip(layout['ids'], zip(layout['xs'], layout['ys'])))
    info = {r['id']: r for r in edges['rooms']}
    hidden = set(layout.get('hidden', []))
    DD = {v for v, r in info.items() if r.get('grp') == 'dd' and v in pos}
    shown = lambda v: v in pos and v not in hidden
    void = lambda v: bool(info.get(v, {}).get('void'))
    E = [(a, b, k) for a, b, k in edges['edges'] if shown(a) and shown(b) and {a, b} & DD]
    return pos, info, hidden, DD, shown, void, E


def dd_land(layout, edges, store, seed=SEED, seas=()):
    """land_edit for smr_merge: the desert's land added to the grid, and the gaps it closes between itself and the map filled with land.
    seas: other merges' stores whose 'sea' (drawn later, not yet in the grid's water) the desert's land keeps off (the Wastelands' south sea)"""
    pos, info, hidden, DD, shown, void, E = _setup(layout, edges)
    dry = [v for v in DD if shown(v)]
    lines = [[pos[a], pos[b]] for a, b, k in E if k != 'ud' and a in DD and b in DD]
    lp = np.r_[np.array([pos[v] for v in dry]), _samples(lines, 0.15)]
    box = (math.floor(lp[:, 0].min()) - 8, math.floor(lp[:, 1].min()) - 8, math.ceil(lp[:, 0].max()) + 8, math.ceil(lp[:, 1].max()) + 8)
    bw, bh = int((box[2] - box[0]) * R8), int((box[3] - box[1]) * R8)
    gy, gx = np.mgrid[0:bh, 0:bw]; X = (gx + .5) / R8 + box[0]; Y = (gy + .5) / R8 + box[1]; P = np.c_[X.ravel(), Y.ravel()]
    d_l = cKDTree(lp).query(P)[0].reshape(bh, bw)
    rng = np.random.default_rng(seed)
    wob = ndi.gaussian_filter(rng.normal(size=(bh, bw)), 1.8 * R8); wob = (wob - wob.min()) / (wob.max() - wob.min())
    near = d_l <= LAND_R * (0.7 + 0.6 * wob)
    near = ndi.binary_closing(np.pad(near, 2 * R8), structure=np.ones((3, 3), bool), iterations=int(1.5 * R8))[2 * R8:-2 * R8, 2 * R8:-2 * R8]
    near = ndi.binary_fill_holes(near)
    near = ndi.gaussian_filter(near.astype(float), 0.8 * R8) > 0.5
    store.update(box=box, land=near)

    def edit(land_n, water0, gx0, gy0):
        c0, r0 = int(round((box[0] - gx0) * R8)), int(round((box[1] - gy0) * R8))
        assert c0 >= 0 and r0 >= 0 and r0 + bh <= land_n.shape[0] and c0 + bw <= land_n.shape[1], (box, land_n.shape, gx0, gy0)
        sub = (slice(r0, r0 + bh), slice(c0, c0 + bw))
        old = land_n[sub].copy()
        wet = water0.copy()
        for s_ in seas:                                                              # (seas worked out by earlier merges, drawn after the land is traced)
            b_ = s_['box']; m_ = s_['sea']; c1, r1 = int(round((b_[0] - gx0) * R8)), int(round((b_[1] - gy0) * R8))
            wet[r1:r1 + m_.shape[0], c1:c1 + m_.shape[1]] |= m_
        add = near & ~wet[sub]
        land_n[sub] = old | add
        added = add & ~old
        full = np.zeros(land_n.shape, bool); full[sub] = added
        solid = land_n | wet                                                      # gaps: ground enclosed by the desert and the map, next to the new land
        holes = ndi.binary_fill_holes(solid) & ~solid
        lab, n = ndi.label(holes)
        ids = np.unique(lab[ndi.binary_dilation(full, iterations=3) & holes]); ids = ids[ids > 0]
        inbox = np.zeros(land_n.shape, bool); inbox[sub] = True
        out_ = [i for i in ids if ((lab == i) & ~inbox).any()]                       # (a hole reaching out of the box is not a gap the desert closes: left as it is)
        store['holes_left'] = [(round(float((lab == i).sum()) / R8 / R8, 1), [round(float(c) / R8 + g, 1) for c, g in zip(ndi.center_of_mass(lab == i)[::-1], (gx0, gy0))]) for i in out_]
        ids = [i for i in ids if i not in out_]
        gaps = np.isin(lab, ids)
        so = solid[sub] | gaps[sub]; pad = 4 * R8                                   # (+ narrow inlets in the desert's own coast: closed by 3 rooms, smaller than INLET sq)
        cl = ndi.binary_closing(np.pad(so, pad), structure=disk(3 * R8))[pad:-pad, pad:-pad] & ~so
        lab2, n2 = ndi.label(cl)
        for i in range(1, n2 + 1):
            m_ = lab2 == i
            if m_.sum() / R8 / R8 < INLET and (ndi.binary_dilation(m_, iterations=3) & added).any(): gaps[sub] |= m_
        assert not (gaps & ~np.pad(np.ones((bh, bw), bool), ((r0, land_n.shape[0] - r0 - bh), (c0, land_n.shape[1] - c0 - bw)))).any(), 'a gap reaches out of the box'
        land_n |= gaps
        store['gaps'] = gaps[sub].copy()
        store['gap_pieces'] = [round(float((lab == i).sum()) / R8 / R8, 1) for i in ids]
        store['land_new_sq'] = round(float(added.sum()) / R8 / R8, 1); store['added'] = added | store['gaps']
        store['land'] = land_n[sub].copy()
        return land_n
    return edit


def merge_dd(w, layout, edges, store):
    pos, info, hidden, DD, shown, void, E = _setup(layout, edges)
    rep = {}
    box = store['box']; landm = store['land']
    bh, bw = landm.shape
    gy, gx = np.mgrid[0:bh, 0:bw]; X = (gx + .5) / R8 + box[0]; Y = (gy + .5) / R8 + box[1]; P = np.c_[X.ravel(), Y.ravel()]
    px = lambda p: ((p[0] - box[0]) * R8, (p[1] - box[1]) * R8)
    sqm = lambda m: round(float(m.sum()) / R8 / R8, 1)

    # ---------------------------------------------------------------- the graphs
    GD = defaultdict(set); links = []; uds = []
    for a, b, k in E:
        if not (a in DD and b in DD): links.append((a, b)); continue                 # to the map
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

    # ---------------------------------------------------------------- clearings: cells of mutually joined real rooms (the range's rule)
    real = {v for v in GD if not void(v)}
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
    for S_ in EXTRA_CLEAR:                                                           # (owner) these rooms, the exits between them, holes filled: one clearing each
        S_ = {v for v in S_ if shown(v)}; im = Image.new('L', (bw, bh), 0); dr = ImageDraw.Draw(im); s_ = int(SQ * R8)
        for v in S_:
            p = px(pos[v]); dr.rectangle([p[0] - s_ / 2, p[1] - s_ / 2, p[0] + s_ / 2, p[1] + s_ / 2], fill=255)
        for a, b, k in E:
            if a in S_ and b in S_ and k != 'ud': dr.line([px(pos[a]), px(pos[b])], fill=255, width=s_)
        m_ = ndi.binary_fill_holes(ndi.binary_closing(np.pad(np.array(im, bool), R8), structure=disk(int(1.2 * R8)))[R8:-R8, R8:-R8])
        clear |= ndi.gaussian_filter(ndi.binary_dilation(m_, structure=disk(int(PAD * R8))).astype(float), 0.45 * R8) > 0.5
    clear &= landm
    lab, n = ndi.label(clear); keep = np.zeros_like(clear)
    for i in range(1, n + 1):
        comp = lab == i
        if comp.sum() / R8 / R8 >= MIN_PATCH: keep |= comp
    clear = keep
    rep['clearings'] = dict(cells=len(cells), sq=sqm(clear))

    # ---------------------------------------------------------------- the Arid Steppes clearing carried on over the rooms that join its grid (owner, Oct 20):
    # the rooms reached from the Arid Steppes by short n/s/e/w exits on the desert side (the Wastelands' Fringes of the Desert and the desert's rooms
    # beside them), exactly those rooms and the exits between them, holes filled (as the steppes); joined with the steppes' clearing and the desert's
    rooms, exits = AF._world()
    WLR = {v for v, r in info.items() if r.get('grp') == 'wl' and shown(v)}
    seed_ = {v for v in WLR if rooms[v]['name'] == 'Arid Steppes'}
    STX = set(); q_ = list(seed_); seen_ = set(seed_)
    while q_:
        v = q_.pop()
        for e in exits.get(v, []):
            t_ = e['to']
            if t_ in seen_ or e['name'] not in ('n', 's', 'e', 'w') or not shown(t_) or t_ not in (DD | WLR) or math.dist(pos[v], pos[t_]) > STEP_GRID: continue
            seen_.add(t_); q_.append(t_)
            if STX_BOX[0] <= pos[t_][0] <= STX_BOX[2] and STX_BOX[1] <= pos[t_][1] <= STX_BOX[3]: STX.add(t_)
    near_ = STX | {v for v in seed_ if any(e['to'] in STX for e in exits.get(v, []))}
    im = Image.new('L', (bw, bh), 0); dr = ImageDraw.Draw(im); s_ = int(SQ * R8)
    for v in near_:
        p = px(pos[v]); dr.rectangle([p[0] - s_ / 2, p[1] - s_ / 2, p[0] + s_ / 2, p[1] + s_ / 2], fill=255)
    for v in near_:
        for e in exits.get(v, []):
            if e['to'] in near_ and e['dir'] in AF.DV and not AF.DV[e['dir']][2]: dr.line([px(pos[v]), px(pos[e['to']])], fill=255, width=s_)
    stx = ndi.gaussian_filter(ndi.binary_fill_holes(np.array(im, bool)).astype(float), 0.3 * R8) > 0.5
    stx = ndi.binary_fill_holes(ndi.binary_closing(np.pad(stx, R8), structure=disk(R8))[R8:-R8, R8:-R8]) & landm
    rep['arid_steppes_extended'] = dict(desert_rooms=sorted(v for v in STX if v in DD), wastelands_rooms=sorted(v for v in STX if v in WLR), sq=sqm(stx))
    old_ = [p for p in (w.get('smrpatch') or []) if any(box[0] <= q[0] < box[2] and box[1] <= q[1] < box[3] for q in p)]
    grow = ndi.binary_dilation(stx | clear, iterations=2)
    hit = [p for p in old_ if (AA._raster([p], box[0], box[1], bw, bh) & grow).any()]
    bb = lambda p: (min(q[0] for q in p), min(q[1] for q in p), max(q[0] for q in p), max(q[1] for q in p))
    gb = [math.floor(min([bb(p)[0] for p in hit] + [box[0]])) - 1, math.floor(min([bb(p)[1] for p in hit] + [box[1]])) - 1,
          math.ceil(max([bb(p)[2] for p in hit] + [box[2]])) + 1, math.ceil(max([bb(p)[3] for p in hit] + [box[3]])) + 1]   # (a grid round them all: the steppes' clearing traced whole)
    gw, gh = int((gb[2] - gb[0]) * R8), int((gb[3] - gb[1]) * R8)
    c0, r0 = int(round((box[0] - gb[0]) * R8)), int(round((box[1] - gb[1]) * R8))
    m0 = AA._raster(hit, gb[0], gb[1], gw, gh) if hit else np.zeros((gh, gw), bool)
    mn = m0.copy(); mn[r0:r0 + bh, c0:c0 + bw] |= stx | clear
    w['smrpatch'] = [p for p in (w.get('smrpatch') or []) if not any(p is h for h in hit)] + AA._contours(mn, gb[0], gb[1], sigma=1.0, tol=0.35, minarea=MIN_PATCH * 0.5)
    patchm = mn[r0:r0 + bh, c0:c0 + bw]
    added_clear = patchm & ~m0[r0:r0 + bh, c0:c0 + bw]                              # (new clearing ground: older trails and sprites there go)
    rep['clearings']['joined_with_old'] = len(hit); rep['clearings']['new_clearing_sq'] = sqm(added_clear)

    # ---------------------------------------------------------------- the Ancient Road carried on over the desert's rooms of that name (owner, Oct 20): a wide dirt road
    ROAD = {v for v in DD if shown(v) and rooms[v]['name'] == 'An Ancient Road'}
    GR = defaultdict(set)
    for a in list(GD):
        for b in list(GD[a]):
            if a in ROAD and b in ROAD: GR[a].add(b); GD[a].discard(b)
    for v in [v for v in GD if not GD[v]]: del GD[v]
    roadl = _chains(GR, pos, set(), 0.8, exact=set(GR)) if GR else []
    for a, b in list(links):                                                          # (its links to the Wastelands' road: road too)
        if {a, b} & ROAD and rooms[a]['name'] == rooms[b]['name'] == 'An Ancient Road':
            links.remove((a, b)); roadl.append([[round(pos[a][0], 2), round(pos[a][1], 2)], [round(pos[b][0], 2), round(pos[b][1], 2)]])
    w['dirtroads'] = list(w.get('dirtroads') or []) + [_sharp(l) for l in roadl]      # (through every room exactly: points doubled, the template draws curves)
    rep['road'] = dict(rooms=sorted(ROAD), lines=len(roadl))

    # ---------------------------------------------------------------- lines: trails (clipped at the clearings), links, up/down exits
    def trails(G):
        Tg = defaultdict(set)
        for a in G:
            for b in G[a]:
                if a >= b: continue
                k_ = max(2, int(math.dist(pos[a], pos[b]) * 3)); inside = True
                for i in range(k_ + 1):
                    x = pos[a][0] + (pos[b][0] - pos[a][0]) * i / k_; y = pos[a][1] + (pos[b][1] - pos[a][1]) * i / k_
                    c, r = int((x - box[0]) * R8), int((y - box[1]) * R8)
                    if not (0 <= r < bh and 0 <= c < bw and patchm[r, c]): inside = False; break
                if not inside: Tg[a].add(b); Tg[b].add(a)
        return Tg
    dirt = _chains(trails(GD), pos, set(), 0.8, exact=set(GD))                      # (straight through every room: the owner placed them exactly, Oct 20)
    for a, b in links + uds:
        dirt.append([[round(pos[a][0], 2), round(pos[a][1], 2)], [round(pos[b][0], 2), round(pos[b][1], 2)]])
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
    dirt = clip(dirt, patchm)
    n0 = len(w['fwtracks']); w['fwtracks'] = clip(w['fwtracks'], added_clear)          # (older trails inside the new clearing ground)
    rep['old_trails_clipped'] = dict(before=n0, after=len(w['fwtracks']))
    w['fwtracks'] = list(w['fwtracks']) + [_sharp(l) for l in dirt]                  # (through every room exactly: points doubled, the template draws curves)
    rep['lines'] = dict(trails=len(dirt), links_to_map=len(links), up_down=len(uds))
    rep['land'] = dict(new_sq=store.get('land_new_sq'), enclosed_gaps_sq=store.get('gap_pieces'), holes_left=store.get('holes_left'), all_gaps_and_inlets_sq=sqm(store['gaps']))

    # ---------------------------------------------------------------- ground: one sand ground, where the land is nearer the desert's rooms than the map's
    rs = [v for v in DD if shown(v) and not void(v)] + [v for v, r in info.items() if r.get('grp') == 'un' and shown(v)]   # (+ the entrance 6365: a desert room)
    dist = cKDTree(np.array([pos[v] for v in rs])).query(P)[0].reshape(bh, bw)
    fx = [pos[v] for v, r in info.items() if (r.get('fixed') or r.get('grp') in ('wl', 'cd')) and v in pos and v not in hidden]   # (map rooms)
    d_fix = cKDTree(np.array(fx)).query(P)[0].reshape(bh, bw) if fx else np.full((bh, bw), np.inf)
    gaps = store['gaps'] & landm
    own = landm & ((dist <= LAND_R + 8) | (store['added'] & ~gaps)) & (dist < d_fix)
    own |= gaps & (dist < d_fix)
    own = ndi.gaussian_filter(own.astype(float), 0.6 * R8) > 0.5
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
    rep['sand_sq'] = _put(w, 'sand', own, box, sigma=2.0)

    # ---------------------------------------------------------------- old sprites make way for the desert's ground and paths
    def off(q):
        c, r = int((q[0] - box[0]) * R8), int((q[1] - box[1]) * R8)
        return 0 <= r < bh and 0 <= c < bw and bool(own[r, c] or patchm[r, c] or added_clear[r, c])
    cl = {}
    for k in SPRITES:
        n0 = len(w.get(k) or []); w[k] = [q for q in (w.get(k) or []) if not off(q)]
        if n0 - len(w[k]): cl[k] = n0 - len(w[k])
    rep['old_sprites_cleared'] = cl

    # ---------------------------------------------------------------- the map grows east and south
    xs_ = [q[0] for k in ('land', 'water') for p in w['geo'][k] for q in p]; ys_ = [q[1] for k in ('land', 'water') for p in w['geo'][k] for q in p]
    b0 = list(w['bounds'])
    w['bounds'] = [b0[0], b0[1], max(b0[2], int(math.ceil(max(xs_))) + 1), max(b0[3], int(math.ceil(max(ys_))) + 1)]
    rep['bounds'] = [b0, w['bounds']]
    rep['rooms'] = dict(shown=len([v for v in DD if shown(v) and not void(v)]), hidden=len([v for v in DD if v in hidden]))
    return w, rep


def drop_dangling(w, pts):
    """trails that now end at nothing (owner, Oct 20): a fwtracks line with an end at one of pts (spacer rooms whose room on the far side was moved
    away) where no other line passes is removed"""
    def touches(L, p): return any(math.dist(q[:2], p) < 0.3 for q in L)
    gone = []
    for p in pts:
        ends = [L for L in w['fwtracks'] if math.dist(L[0][:2], p) < 0.05 or math.dist(L[-1][:2], p) < 0.05]
        others = [L for L in w['fwtracks'] if touches(L, p) and not any(L is e for e in ends)]
        if len(ends) == 1 and not others:
            w['fwtracks'] = [L for L in w['fwtracks'] if L is not ends[0]]; gone.append([ends[0][0], ends[0][-1]])
    return gone
