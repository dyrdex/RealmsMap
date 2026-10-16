"""The Coral Depths (owner's name, Oct 16, for the Azure Sea and Coral Depths rooms that tie the Ashen Forest and the Southern Mountains together):
cd_layout_final.json, cd_editor_edges.json (the owner's layout from tools/coral_depths_editor). Owner's notes (Oct 16):
  - up/down exits are drawn (7 to 8, 2808 to 2809, 2810 to 572, ...)
  - 569, 570, 571, 572 and the ledge 2806 ... 2818 are upon cliffs that overlook the area south and east of them: the whole path is a high cliff over
    the land south-east of it (high ground on its north-west side)
  - the empty area these rooms lie in is built from the rooms: the beach, dock and forest rooms are land, the land fills the gap north-west of the
    cliff (joining the Southern Mountains to the Ashen Forest); the land first, then the east coast's sea is simply carried on south to about y 70
  - (later, Oct 16) no brown high ground: the top of the cliff is grey rocky ground with rocks and boulders, about 4 rooms deep from 569 to 2817 and
    over the up/down path 572 - 2810; the rest of the new ground north-west of the cliff takes the ground of the old land next to it; the little
    inlet of the old sea there is land; where a water route meets a dirt path (1495) both run exactly through the room
  - room 6365 stays where the owner moved it
The Southern Mountain Range rooms the owner moved here (7-10, 569-572, 6365, 19863) are drawn by smr_merge at their new spots (build.py gives it them);
their land change is made inside smr_merge's own land trace (`land_edit`), so the land is traced once. This module draws the rest: paths (dirt on land,
the dark blue water route of the Azure Sea Coast in the water), the cliff (dark face and strokes down the slope), ground tints and sprites, the sea."""
import math
import numpy as np
from collections import defaultdict
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from skimage import measure
import arrange_apply as AA
import gap_fill as GF
from ntr_merge import _chains, _samples
from smr_merge import _drawn, _hash

R8 = GF.R8
BOX = (24.0, 0.0, 88.0, 86.0)                   # everything this module paints lies in it (the sea is bounded by it, gotcha 1)
SM_DRAWN = {7, 8, 9, 10, 569, 570, 571, 572, 6365, 19863}       # smr_merge draws these and the paths between them
CLIFF = [569, 570, 571, 572, 2806, 2807, 2808, 2809, 2810, 2811, 2814, 2815, 2816, 2817, 2818]
LAND_R = 3.4                                    # land reaches this far from a land room or path
SEA_X, SEA_E, SEA_N, SEA_S = 44.0, 78.0, 12.0, 70.0   # the east coast's sea is carried on south: from y 12 (where it ends now) down to y 70, east of x 44, out to its east edge
TOP_END = 2817                                  # the top of the cliff: from 569 to here (owner, Oct 16)
TOP_W = 4.0                                     # ... about this deep behind the cliff edge
TOP_PAST = 1.3                                  # ... and this far past the up/down path 572 - 2810
INN, SEAHOLE = 2526, 2528                       # the Beach Shoppe (inn graphic) and the secret way down into the sea (owner, Oct 16)
FACE = 0.8                                      # the cliff's face (dark band) on its south-east side
PLATEAU = (24.0, 8.0, 67.0, 41.5)               # the high ground NW of the cliff lies in this box (it fills the gap up to the old coast)
BLACK = {669, 6302, 1495, 6288}                 # 'Black Sand Beach(es)': dark ash-grey sand
SANDY = {6303, 2516, 2521, 2523, 2524, 6292, 6329, 2818, 6419, 24174}   # beaches, the sandy path, the pale sandy coastline
SEED = 97

_cache = {}


def _setup(layout, edges, smr_layout=None):
    key = id(layout)
    if key in _cache: return _cache[key]
    pos = dict(zip(layout['ids'], zip(layout['xs'], layout['ys'])))
    info = {r['id']: r for r in edges['rooms']}
    CD = {v for v, r in info.items() if r.get('area') == 'CD'}
    hidden = set(layout.get('hidden', []))
    terr = lambda v: info[v].get('terrain') or ''
    adj = defaultdict(set); kinds = {}
    for a, b, k in edges['edges']:
        if a in hidden or b in hidden: continue
        if not ({a, b} & CD): continue
        if {a, b} <= SM_DRAWN: continue                                            # (smr_merge draws those)
        adj[a].add(b); adj[b].add(a); kinds[(min(a, b), max(a, b))] = k
    wet = {v for v in CD if terr(v) == 'Swimming'}
    for v in CD:                                                                   # a spacer between two swimming rooms is in the water
        if info[v].get('void') and adj[v] and all(u in wet for u in adj[v]): wet.add(v)
    dry = (CD | {u for v in CD for u in adj[v]}) - wet
    S = dict(pos=pos, info=info, CD=CD, adj=adj, kinds=kinds, wet=wet, dry=dry)
    # the cliff line: as the template draws a trail through these rooms
    S['cliff'] = _drawn([list(pos[v]) for v in CLIFF], 10)
    # seeds: room spots and points along the exits; an exit between land and water is land to its middle, water beyond
    lp, wp = [], []
    for (a, b), k in kinds.items():
        if a not in pos or b not in pos: continue
        if a in wet and b in wet: wp += list(_samples([[pos[a], pos[b]]], 0.2))
        elif a in wet or b in wet:
            w_, d_ = (a, b) if a in wet else (b, a); m = ((pos[a][0] + pos[b][0]) / 2, (pos[a][1] + pos[b][1]) / 2)
            wp += list(_samples([[pos[w_], m]], 0.2)); lp += list(_samples([[m, pos[d_]]], 0.2))
        elif k != 'ud' or math.dist(pos[a], pos[b]) < 6: lp += list(_samples([[pos[a], pos[b]]], 0.2))
    lp += [pos[v] for v in dry if v in pos]; wp += [pos[v] for v in wet]
    S['lp_cd'] = np.array(lp); S['wp'] = np.array(wp)
    if smr_layout:                                                                 # the Southern Mountain Range's rooms nearby hold their land
        sh = set(smr_layout.get('hidden', []))
        lp += [(x, y) for v, x, y in zip(smr_layout['ids'], smr_layout['xs'], smr_layout['ys']) if v not in sh and BOX[0] <= x <= BOX[2] and BOX[1] <= y <= BOX[3]]
    S['lp'] = np.array(lp)
    _cache[key] = S
    return S


def _se_normal(a, b):
    """the unit normal of the piece a -> b that faces south-east (the cliff overlooks the land south and east of it)"""
    L = math.dist(a, b) or 1e-9; tx, ty = (b[0] - a[0]) / L, (b[1] - a[1]) / L; nx, ny = -ty, tx        # (right of the direction; y runs south)
    return (nx, ny) if nx + ny >= 0 else (-nx, -ny)


def _side(line, P):
    """for points P: distance to the polyline and which side of it they lie on (+1: the south-east side, -1: the north-west side)"""
    L = np.array(line, float); A = L[:-1]; B = L[1:]; D = B - A; L2 = (D ** 2).sum(1); L2[L2 == 0] = 1e-9
    best = np.full(len(P), np.inf); sgn = np.zeros(len(P))
    for i in range(len(A)):
        t = np.clip(((P - A[i]) * D[i]).sum(1) / L2[i], 0, 1)
        Q = A[i] + t[:, None] * D[i]; d = np.hypot(*(P - Q).T)
        n = _se_normal(A[i], B[i]); cr = (P[:, 0] - Q[:, 0]) * n[0] + (P[:, 1] - Q[:, 1]) * n[1]
        better = d < best; best[better] = d[better]; sgn[better] = np.sign(cr[better])
    return best, sgn


def _along(line, P):
    """for points P: distance to the polyline, side (as _side) and how far along the line (from its start) the nearest point lies"""
    L = np.array(line, float); A = L[:-1]; B = L[1:]; D = B - A; L2 = (D ** 2).sum(1); L2[L2 == 0] = 1e-9
    cum = np.r_[0, np.cumsum(np.sqrt((D ** 2).sum(1)))]
    best = np.full(len(P), np.inf); sgn = np.zeros(len(P)); s = np.zeros(len(P))
    for i in range(len(A)):
        t = np.clip(((P - A[i]) * D[i]).sum(1) / L2[i], 0, 1)
        Q = A[i] + t[:, None] * D[i]; d = np.hypot(*(P - Q).T)
        n = _se_normal(A[i], B[i]); cr = (P[:, 0] - Q[:, 0]) * n[0] + (P[:, 1] - Q[:, 1]) * n[1]
        better = d < best; best[better] = d[better]; sgn[better] = np.sign(cr[better]); s[better] = cum[i] + t[better] * (cum[i + 1] - cum[i])
    return best, sgn, s, cum


def masks(layout, edges, land0, water0, smr_layout=None):
    """land to add and sea to make, on the BOX grid. land0 / water0: the map's land and water on the same grid (before this change).
    The land first (round the land rooms and paths, the high ground NW of the cliff, the cliff face); then the sea: the east coast's sea simply carried
    on south to about y 70 over everything east of x 44 that is not land (owner, Oct 16)."""
    S = _setup(layout, edges, smr_layout)
    if 'masks' in S: return S['masks']
    nrng = np.random.default_rng(SEED)
    bw, bh = int((BOX[2] - BOX[0]) * R8), int((BOX[3] - BOX[1]) * R8)
    gy, gx = np.mgrid[0:bh, 0:bw]; X = (gx + .5) / R8 + BOX[0]; Y = (gy + .5) / R8 + BOX[1]
    P = np.c_[X.ravel(), Y.ravel()]
    d_l = cKDTree(S['lp']).query(P)[0].reshape(bh, bw)
    d_w = cKDTree(S['wp']).query(P)[0].reshape(bh, bw)
    dc, sc = _side(S['cliff'], P); dc = dc.reshape(bh, bw); sc = sc.reshape(bh, bw)
    wob = ndi.gaussian_filter(nrng.normal(size=(bh, bw)), 1.6 * R8); wob = (wob - wob.min()) / (wob.max() - wob.min())
    wob2 = ndi.gaussian_filter(nrng.normal(size=(bh, bw)), 1.1 * R8); wob2 = (wob2 - wob2.min()) / (wob2.max() - wob2.min())
    inplat = (X >= PLATEAU[0]) & (X <= PLATEAU[2]) & (Y >= PLATEAU[1]) & (Y <= PLATEAU[3])
    lobe = water0 & (sc < 0) & inplat & (X > 50) & (Y < 20)                     # the little inlet of the old sea north-west of the cliff: land now (owner, Oct 16)
    plateau = inplat & (sc < 0) & (~water0 | lobe)                              # the ground north-west of the cliff, up to the old coast
    face = (sc > 0) & (dc <= FACE * (0.8 + 0.4 * wob2))                         # the cliff's face
    land = ((d_l <= LAND_R * (0.75 + 0.5 * wob)) & (d_l < d_w)) | plateau | face   # (the swimming rooms stay off the land)
    land = ndi.gaussian_filter(land.astype(float), 0.5 * R8) > 0.5
    band = water0 & (Y >= SEA_N - 2) & (Y <= SEA_N + 2)
    east = float(X[band].max()) if band.any() else SEA_E                      # (the old sea's east edge where the new stretch starts)
    sea = (X >= SEA_X) & (X <= east + 2.0 * (wob2 - 0.5)) & (Y >= SEA_N) & (Y <= SEA_S + 3.0 * (wob - 0.5)) & ~land & ~land0 & ~water0
    sea = ndi.gaussian_filter(sea.astype(float), 0.4 * R8) > 0.5
    sea &= ~(land | land0 | water0)
    S['masks'] = dict(land=land, sea=sea, plateau=plateau & ~land0, face=face & land, lobe=lobe, land0=land0, X=X, Y=Y, dc=dc, sc=sc, bw=bw, bh=bh)
    return S['masks']


def land_edit(layout, edges, smr_layout, report):
    """for smr_merge: adds the new land and cuts the new sea in its full land grid, before it traces the land"""
    def edit(land_n, water_n, x0, y0):
        c0, r0 = int(round((BOX[0] - x0) * R8)), int(round((BOX[1] - y0) * R8))
        M = masks(layout, edges, land_n[r0:, c0:][:int((BOX[3] - BOX[1]) * R8), :int((BOX[2] - BOX[0]) * R8)].copy(),
                  water_n[r0:, c0:][:int((BOX[3] - BOX[1]) * R8), :int((BOX[2] - BOX[0]) * R8)].copy(), smr_layout)
        sub = (slice(r0, r0 + M['bh']), slice(c0, c0 + M['bw']))
        before = land_n[sub].copy()
        land_n[sub] = ndi.binary_fill_holes(land_n[sub] | M['land']) & ~M['sea']      # (a gap closed in by land is land)
        report['land_added_sq'] = round(float((land_n[sub] & ~before).sum()) / R8 / R8, 1)
        report['land_cut_sq'] = round(float((before & ~land_n[sub]).sum()) / R8 / R8, 1)
        lab, n = ndi.label(land_n[sub] & ~before); report['land_new_pieces'] = int(n)
        return land_n
    return edit


def merge_cd(w, layout, edges, smr_layout, seed=SEED):
    S = _setup(layout, edges, smr_layout)
    pos, info, CD, adj, kinds, wet = S['pos'], S['info'], S['CD'], S['adj'], S['kinds'], S['wet']
    rng = np.random.default_rng(seed)
    rep = {}
    bw, bh = int((BOX[2] - BOX[0]) * R8), int((BOX[3] - BOX[1]) * R8)
    land_now = AA._raster(w['geo']['land'], BOX[0], BOX[1], bw, bh)
    M = S['masks']; X, Y = M['X'], M['Y']; sea = M['sea']

    # ---- the sea: the east coast's sea polygon, drawn again with the new stretch south to about y 70 (one outline, no seam)
    water = w['geo']['water']
    grown = ndi.binary_dilation(sea, iterations=2)
    hit = [i for i, p in enumerate(water) if (AA._raster([p], BOX[0], BOX[1], bw, bh) & grown).any()]
    assert len(hit) == 1, hit
    p = water[hit[0]]; xs = [q[0] for q in p]; ys = [q[1] for q in p]
    gx0, gy0 = math.floor(min(min(xs), BOX[0])) - 2, math.floor(min(min(ys), BOX[1])) - 2
    gx1, gy1 = math.ceil(max(max(xs), BOX[2])) + 2, math.ceil(max(max(ys), BOX[3])) + 2
    G = AA._raster([p], gx0, gy0, int((gx1 - gx0) * R8), int((gy1 - gy0) * R8))
    c0, r0 = int(round((BOX[0] - gx0) * R8)), int(round((BOX[1] - gy0) * R8))
    G[r0:r0 + bh, c0:c0 + bw] &= ~M['lobe']
    gb = G[r0:r0 + bh, c0:c0 + bw]; lab_, n_ = ndi.label(gb)                     # (scraps of the inlet left cut off from the sea go too)
    for i_ in range(1, n_ + 1):
        if (lab_ == i_).sum() < 6 * R8 * R8: gb[lab_ == i_] = False; M['lobe'] |= lab_ == i_
    G[r0:r0 + bh, c0:c0 + bw] |= sea
    w['geo']['water'] = [q for i, q in enumerate(water) if i != hit[0]] + AA._contours(G, gx0, gy0, sigma=1.0)
    after = AA._raster(w['geo']['water'], BOX[0], BOX[1], bw, bh)
    rep['inlet_made_land_sq'] = round(float(M['lobe'].sum()) / R8 / R8, 1)
    rep['sea_added_sq'] = round(float(sea.sum()) / R8 / R8, 1); rep['sea_drawn_sq'] = round(float((after & sea).sum()) / R8 / R8, 1)

    # ---- what stood where the sea now is goes (gotcha 2): ground tints clipped (a polygon over a tint, drawn even-odd, is a hole), sprites removed
    clipped = {}
    for k in [k for k in w['geo'] if k not in ('land', 'water')]:
        polys = w['geo'].get(k) or []
        near = [p for p in polys if any(BOX[0] <= q[0] < BOX[2] and BOX[1] <= q[1] < BOX[3] for q in p)]
        if not near: continue
        inter = sea & AA._raster(near, BOX[0], BOX[1], bw, bh)
        if inter.sum() > 4:
            w['geo'][k] = list(polys) + AA._contours(inter, BOX[0], BOX[1], sigma=1.0, minarea=0.05); clipped[k] = round(float(inter.sum()) / R8 / R8, 1)
    rep['tints_clipped'] = clipped

    # ---- paths: dirt on land, the water route in the water (as the Azure Sea Coast's)
    GD = defaultdict(set); GW = defaultdict(set); uds = []
    for (a, b), k in kinds.items():
        if a not in pos or b not in pos: continue
        if k == 'ud': uds.append((a, b)); continue
        G = GW if (a in wet or b in wet) else GD
        G[a].add(b); G[b].add(a)
    pinned = {v for v in pos if v not in CD} | {2806} | (set(GW) & set(GD)) | {v for e in uds for v in e}   # (where a water route meets a dirt path, or an up/down path joins a trail, the lines run exactly through the room)
    dirt = _chains(GD, pos, pinned, 0.5)
    seaw = _chains(GW, pos, pinned, 0.6)
    udl = []
    for a, b in uds:                                                               # up/down exits (owner, Oct 16): dirt lines; a long one with a bend, like 7 to 8
        A_, B_ = np.array(pos[a], float), np.array(pos[b], float); d = np.linalg.norm(B_ - A_)
        if d > 8:
            dv = B_ - A_; nv = np.array([-dv[1], dv[0]]) / d
            pts = [A_] + [A_ + dv * f + nv * amp for f, amp in ((0.25, 1.6), (0.5, -1.1), (0.78, 1.0))] + [B_]
        else: pts = [A_, B_]
        udl.append([[round(float(q[0]), 2), round(float(q[1]), 2)] for q in pts])
    # room 14360 (an Ashen Forest spacer the owner moved): the Ashen trail's end that was there moves with it
    moved14360 = 0
    if 14360 in pos:
        import json, os
        _al = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ashen_layout_final.json')))
        old = dict(zip(_al['ids'], zip(_al['xs'], _al['ys'])))[14360]
        for ln in w['fwtracks']:
            for i in (0, -1):
                if math.dist(ln[i], old) < 0.06: ln[i] = [round(pos[14360][0], 2), round(pos[14360][1], 2)]; moved14360 += 1
    w['fwtracks'] = list(w['fwtracks']) + dirt + udl
    w['seaways'] = list(w.get('seaways') or []) + seaw
    rep['paths'] = dict(dirt_lines=len(dirt), water_lines=len(seaw), up_down=[(a, b) for a, b in uds], trail_end_moved_14360=moved14360)
    lines = dirt + udl + seaw
    pts = _samples([_drawn(l) for l in lines], 0.1)
    d_path = cKDTree(pts).query(np.c_[X.ravel(), Y.ravel()])[0].reshape(bh, bw)

    # ---- the cliff (owner, Oct 16): a dark face on its south-east side and strokes down the slope, from 569 to 2818
    face = M['face'] & land_now & ~after
    w['geo']['cliff'] = list(w['geo'].get('cliff') or []) + AA._contours(face, BOX[0], BOX[1], sigma=1.0, minarea=0.1)
    cl = S['cliff']; hach = []; acc = 0.0; last = None
    other = _samples([_drawn(l) for l in lines if not all(any(math.dist(q, pos[v]) < 0.05 for v in CLIFF) for q in (l[0], l[-1]))], 0.1)
    otree = cKDTree(other) if len(other) else None
    for a, b in zip(cl[:-1], cl[1:]):
        L = math.dist(a, b)
        if L == 0: continue
        tx, ty = (b[0] - a[0]) / L, (b[1] - a[1]) / L; nx, ny = _se_normal(a, b)          # (strokes down the slope, to the south-east)
        t = 0.0
        while t < L:
            if last is None or acc >= 0.28:
                x, y = a[0] + tx * t, a[1] + ty * t
                ln = 0.45 + 0.3 * float(_hash(x, y, 5))
                if otree is not None:
                    dd = otree.query([x + nx * 0.4, y + ny * 0.4])[0]
                    ln = min(ln, max(0.0, dd - 0.15))
                if ln >= 0.25:
                    hach.append([round(x + nx * 0.08, 3), round(y + ny * 0.08, 3), round(x + nx * ln, 3), round(y + ny * ln, 3)])
                acc = 0.0; last = (x, y)
            step = 0.04; t += step; acc += step
    w['hach'] = list(w['hach']) + hach
    rep['cliff'] = dict(face_sq=round(float(face.sum()) / R8 / R8, 1), strokes=len(hach))

    # ---- sprites: nothing stands in the new sea, on the cliff face or on the new paths
    def bad(q, clear):
        c_, r_ = int((q[0] - BOX[0]) * R8), int((q[1] - BOX[1]) * R8)
        if not (0 <= r_ < bh and 0 <= c_ < bw): return False
        return bool(after[r_, c_] and sea[r_, c_]) or bool(face[r_, c_]) or d_path[r_, c_] < clear
    removed = {}
    for k, clear in (('trees', 0.5), ('tufts', 0.35), ('peaks', 0.9), ('hills', 0.8), ('crags', 0.6), ('boulders', 0.4), ('brush', 0.4), ('reeds', 0.3), ('wheattufts', 0.3), ('ripples', 0.0)):
        if k not in w: continue
        n0 = len(w[k]); w[k] = [q for q in w[k] if not bad(q, clear)]; removed[k] = n0 - len(w[k])
    rep['sprites_removed'] = removed

    # ---- the top of the cliff (owner, Oct 16): grey rocky ground with rocks and boulders, about 4 rooms deep behind the cliff from 569 to 2817;
    #      between 572 and 2810 it reaches back over the up/down path between them and a little beyond
    landm = AA._raster(w['geo']['land'], BOX[0], BOX[1], bw, bh) & ~after
    P = np.c_[X.ravel(), Y.ravel()]
    topl = _drawn([list(pos[v]) for v in CLIFF[:CLIFF.index(TOP_END) + 1]], 10)
    d2, s2, al, cum = _along(topl, P); d2 = d2.reshape(bh, bw); s2 = s2.reshape(bh, bw); al = al.reshape(bh, bw)
    s572 = float(cum[np.argmin([math.dist(q, pos[572]) for q in topl])])           # (from 569 the top starts at nothing and widens evenly to full width at 572)
    ramp = np.clip(al / s572, 0, 1); ramp[al <= 1e-6] = 0
    ud = next(l for l in udl if {tuple(l[0]), tuple(l[-1])} == {tuple(map(lambda c: round(c, 2), pos[572])), tuple(map(lambda c: round(c, 2), pos[2810]))})
    udd = _drawn(ud, 10); d_ud = cKDTree(_samples([udd], 0.1)).query(P)[0].reshape(bh, bw)
    ring = [list(pos[v]) for v in CLIFF[CLIFF.index(572):CLIFF.index(2810) + 1]] + udd[::-1]
    between = AA._raster([ring], BOX[0], BOX[1], bw, bh)
    wt = ndi.gaussian_filter(rng.normal(size=(bh, bw)), 1.2 * R8); wt = (wt - wt.min()) / (wt.max() - wt.min())
    top = ((s2 <= 0) & (d2 <= TOP_W * (0.8 + 0.4 * wt) * ramp)) | between | ((s2 <= 0) & (d_ud <= TOP_PAST * (0.7 + 0.6 * wt)))
    top = ndi.gaussian_filter(top.astype(float), 0.5 * R8) > 0.5
    top &= landm & ~face & (al > 1e-6)
    nz = ndi.gaussian_filter(rng.normal(size=(bh, bw)), 0.7 * R8); nz = (nz - nz.min()) / (nz.max() - nz.min())
    w['geo']['clifftop'] = list(w['geo'].get('clifftop') or []) + AA._contours(top, BOX[0], BOX[1], sigma=1.5)
    w['geo']['clifftop2'] = list(w['geo'].get('clifftop2') or []) + AA._contours(top & (nz > 0.6), BOX[0], BOX[1], sigma=1.5, minarea=0.1)
    def place(mask, spacing, salt):
        ys, xs = np.nonzero(mask); placed = []; grid = {}
        for i in np.argsort(_hash(X[ys, xs], Y[ys, xs], salt), kind='stable'):
            x, y = X[ys[i], xs[i]], Y[ys[i], xs[i]]; gk = (int(x // spacing), int(y // spacing))
            if any(math.dist(q, (x, y)) < spacing for dx in (-1, 0, 1) for dy in (-1, 0, 1) for q in grid.get((gk[0] + dx, gk[1] + dy), ())): continue
            grid.setdefault(gk, []).append((x, y)); placed.append((round(float(x), 3), round(float(y), 3)))
        return placed
    inmask = lambda m, q: 0 <= int((q[1] - BOX[1]) * R8) < bh and 0 <= int((q[0] - BOX[0]) * R8) < bw and bool(m[int((q[1] - BOX[1]) * R8), int((q[0] - BOX[0]) * R8)])
    gone = {}
    for k in ('trees', 'tufts', 'peaks', 'hills', 'crags', 'boulders', 'brush', 'wheattufts'):     # what grew there gives way to the rock
        if k in w: n0 = len(w[k]); w[k] = [q for q in w[k] if not inmask(top, q)]; gone[k] = n0 - len(w[k])
    rz = top & (d_path > 0.55) & (d2 > 0.35)
    crags = place(rz, 2.3, 41)
    rocks = place(rz & ~ndi.binary_dilation(AA._raster([[[x - .5, y - .5], [x + .5, y - .5], [x + .5, y + .5], [x - .5, y + .5]] for x, y in crags], BOX[0], BOX[1], bw, bh), iterations=2), 1.15, 43)
    w['crags'] = list(w.get('crags') or []) + [[x, y, round(0.7 + 0.4 * float(_hash(x, y, 6)), 2), int(float(_hash(x, y, 7)) * 3)] for x, y in crags]
    w['boulders'] = list(w.get('boulders') or []) + [[x, y, round(0.45 + 0.35 * float(_hash(x, y, 8)), 2)] for x, y in rocks]
    rep['cliff_top'] = dict(sq=round(float(top.sum()) / R8 / R8, 1), crags=len(crags), boulders=len(rocks), sprites_replaced=gone)

    # ---- the rest of the new ground north-west of the cliff (owner, Oct 16: one open space where the Ashen Forest, the Southern Mountains and the cliff
    #      top meet; varied, and blending into its neighbours): the Ashen ground fades out from the north in patches, groves of the Ashen Forest's
    #      trees thin out southward with clumps scattered further on, meadow and sparse-ground patches, grass, a few hills toward the mountains and the cliff
    land0 = M['land0']
    rest = landm & ~land0 & ~top & ~face & (M['sc'] < 0)
    near = lambda m: ndi.distance_transform_edt(~m) / R8
    def field(sigma, salt):
        f_ = ndi.gaussian_filter(np.random.default_rng(seed + salt).normal(size=(bh, bw)), sigma * R8); return (f_ - f_.min()) / (f_.max() - f_.min())
    ashr = AA._raster([p for p in (w['geo'].get('ash') or []) if any(BOX[0] <= q[0] < BOX[2] and BOX[1] <= q[1] < BOX[3] for q in p)], BOX[0], BOX[1], bw, bh)
    dA = near(land0 & ashr & (Y < 22))                                            # from the Ashen Forest's ground
    dW = near(land0 & (X < 36) & (Y > 14) & ~ashr)                                # from the Southern Mountains' side
    dT = near(top)
    n1, n2, n3, n4, n5 = field(1.6, 1), field(2.2, 2), field(1.3, 3), field(1.8, 4), field(1.1, 5)
    tints = {'ash': rest & (0.75 * n1 + np.exp(-dA / 6.0) > 1.0),
             'meadow1': rest & (n2 > 0.6) & (dA > 3), 'meadow2': rest & (n3 > 0.66) & (dA > 2), 'sparse': rest & (n4 > 0.64)}
    for k, m_ in tints.items():
        m_ = ndi.gaussian_filter(m_.astype(float), 0.4 * R8) > 0.5
        w['geo'][k] = list(w['geo'].get(k) or []) + AA._contours(m_, BOX[0], BOX[1], sigma=1.5, minarea=0.3); tints[k] = round(float(m_.sum()) / R8 / R8, 1)
    SPACE = {'trees': 0.95, 'hills': 1.7, 'tufts': 1.0}
    cand = place(rest & (d_path > 0.6), 0.8, 47)
    made = defaultdict(list); grid = defaultdict(list)
    at_ = lambda m, x, y: float(m[int((y - BOX[1]) * R8), int((x - BOX[0]) * R8)])
    for x, y in cand:
        pa = math.exp(-at_(dA, x, y) / 6.0); gr = max(0.0, (at_(n5, x, y) - 0.55) / 0.45)
        p_tree = min(0.9, 0.85 * pa + 0.8 * gr)
        p_hill = 0.25 * math.exp(-at_(dW, x, y) / 8.0) + 0.15 * math.exp(-at_(dT, x, y) / 3.0)
        u = float(_hash(x, y, 51))
        k = 'trees' if u < p_tree else 'hills' if u < p_tree + p_hill else 'tufts' if u < p_tree + p_hill + 0.3 else None
        if not k: continue
        sp = SPACE[k]; gk = (k, int(x // sp), int(y // sp))
        if any(math.dist(p_, (x, y)) < sp for dx in (-1, 0, 1) for dy in (-1, 0, 1) for p_ in grid[(k, gk[1] + dx, gk[2] + dy)]): continue
        grid[gk].append((x, y)); h2, h3 = float(_hash(x, y, 52)), float(_hash(x, y, 53))
        if k == 'trees': made[k].append([x, y, round(0.85 + 0.3 * h2, 2), 'w' if h3 < 0.4 else 'd', int(float(_hash(x, y, 54)) * 3)])
        elif k == 'hills': made[k].append([x, y, round(0.85 + 0.3 * h2, 2), 'h', int(h3 * 3)])
        else: made[k].append([x, y, round(0.8 + 0.3 * h2, 2), 'g', int(h3 * 3)])
    for k, L in made.items(): w[k] = list(w.get(k) or []) + L
    rep['ground_nw'] = dict(sq=round(float(rest.sum()) / R8 / R8, 1), tints=tints, sprites={k: len(L) for k, L in made.items()})

    # ---- the Beach Shoppe (owner, Oct 16): a small, weathered wooden seaside inn at room 2526 (nets, crates), its small label just south;
    #      room 2528's secret way down into the sea: a small round pool with a shaft going down under the surface
    ix_, iy_ = pos[INN]
    w['gfx'] = list(w['gfx']) + [{'k': 'seainn', 'at': 'xy', 'x': round(ix_, 2), 'y': round(iy_ - 0.35, 2), 'w': 2.0, 'h': 1.7},
                                 {'k': 'text', 'at': 'xy', 'x': round(ix_, 2), 'y': round(iy_ + 1.05, 2), 'text': 'Beach Shoppe'}]
    hx_, hy_ = pos[SEAHOLE]
    w['gfx'] = list(w['gfx']) + [{'k': 'seahole', 'at': 'xy', 'x': round(hx_, 2), 'y': round(hy_, 2), 'w': 1.1, 'h': 1.1}]
    for k_ in ('trees', 'tufts', 'peaks', 'hills', 'boulders', 'crags'):         # nothing grows under the inn
        if k_ in w: w[k_] = [t for t in w[k_] if not (abs(t[0] - ix_) < 1.3 and abs(t[1] - iy_ + 0.35) < 1.1)]
    rep['gfx'] = dict(inn=[round(ix_, 2), round(iy_ - 0.35, 2)], sea_hole=[round(hx_, 2), round(hy_, 2)])

    # ---- the low ground: beaches (black sand: ash grey; the others: sand), the Coral Depths' forest (trees)
    P = np.c_[X.ravel(), Y.ravel()]
    def near_rooms(vs, r):
        vs = [v for v in vs if v in pos]
        if not vs: return np.zeros((bh, bw), bool)
        return (cKDTree(np.array([pos[v] for v in vs])).query(P)[0].reshape(bh, bw) <= r)
    d_sea = ndi.distance_transform_edt(~after) / R8
    wobs = ndi.gaussian_filter(rng.normal(size=(bh, bw)), 0.9 * R8); wobs = (wobs - wobs.min()) / (wobs.max() - wobs.min())
    shore = landm & (d_sea <= 1.3 + 0.9 * wobs)
    black = ndi.gaussian_filter((shore & near_rooms(BLACK, 3.2)).astype(float), 0.4 * R8) > 0.5
    sandy = ndi.gaussian_filter((shore & near_rooms(SANDY, 3.2) & ~black).astype(float), 0.4 * R8) > 0.5
    w['geo']['ash'] = list(w['geo'].get('ash') or []) + AA._contours(black, BOX[0], BOX[1], sigma=1.0, minarea=0.2)
    w['geo']['sand'] = list(w['geo'].get('sand') or []) + AA._contours(sandy, BOX[0], BOX[1], sigma=1.0, minarea=0.2)
    forest = [v for v in CD if (info[v].get('terrain') or '') == 'Forest']
    fz = landm & near_rooms(forest, 2.6) & ~black & ~sandy & (d_sea > 0.6) & (d_path > 0.55) & (M['sc'] > 0) & ~top
    trees = place(fz, 0.95, 31)
    w['trees'] = list(w['trees']) + [[x, y, round(0.85 + 0.3 * float(_hash(x, y, 2)), 2), 'd', int(float(_hash(x, y, 3)) * 3)] for x, y in trees]
    rep['ground_low'] = dict(black_sand_sq=round(float(black.sum()) / R8 / R8, 1), sand_sq=round(float(sandy.sum()) / R8 / R8, 1), trees=len(trees))
    on_land = lambda v: bool(landm[int((pos[v][1] - BOX[1]) * R8), int((pos[v][0] - BOX[0]) * R8)])
    in_sea = lambda v: bool(after[int((pos[v][1] - BOX[1]) * R8), int((pos[v][0] - BOX[0]) * R8)])
    rep['rooms_check'] = dict(dry_rooms_in_sea=sorted(v for v in S['dry'] if v in CD and in_sea(v)),
                              swimming_rooms_on_land=sorted(v for v in wet if not in_sea(v)))
    xs_ = [q[0] for k in ('land', 'water') for p in w['geo'][k] for q in p]; ys_ = [q[1] for k in ('land', 'water') for p in w['geo'][k] for q in p]
    w['bounds'] = [min(w['bounds'][0], int(min(xs_)) - 2), w['bounds'][1], max(w['bounds'][2], int(max(xs_)) + 2), max(w['bounds'][3], int(max(ys_)) + 2)]
    return w, rep


def add_cd_places(w, layouts):
    """the Coral Depths' sub-area destinations (owner, Oct 16), traced from the owner's directions in data.py: Coral Depths (its directions end at 2528,
    'Heading into the depths', where the way down is) and Octopus Garden (down from 12599: the marker is there, where the route leaves the map)"""
    import data as DT
    from route_fix import make_tracer
    from extra_places import segments
    rooms, walk, at = make_tracer(w, layouts)
    lines = (DT.AREAS + '\n' + DT.MORE_DIRECTIONS).split('\n')
    rep = {}
    for name in ('Coral Depths', 'Octopus Garden'):
        assert not any(p['name'] == name for p in w['places']), name
        route = next(l.split('|', 1)[1].strip().rstrip(';') for l in lines if l.startswith(name + '|'))
        t = walk(route)
        last = max(i for i, v in enumerate(t) if at(v))
        upto = t[:last + 1]; segs = segments([at(v) for v in upto])
        d = 'here' if last == len(t) - 1 else route.split(';')[-1]
        w['places'].append(dict(name=name, route=route, room=rooms[upto[-1]]['name'], dir=d, path=[q for s in segs for q in s], segs=segs,
                                group='af', where='in the Coral Depths' if name == 'Coral Depths' else 'off the Coral Depths',
                                note=None if len(segs) == 1 else "Part of your directions passes through areas that aren't drawn yet, so the traced line breaks there."))
        rep[name] = dict(end_room=upto[-1], dir=d, pieces=len(segs), marker=segs[-1][-1])
    return w, rep
