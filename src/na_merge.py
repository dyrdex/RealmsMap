"""Angel's Landing, the Village of Edo and The Grimdog Port Authority (owner, Oct 16): na_layout_final.json, na_editor_edges.json (the owner's layout from
tools/new_areas_editor). Owner's notes (Oct 16):
  - Grimdog Port Authority: every room hidden; they are only there so a route through them is still drawn (the tracers get the whole save, hidden
    rooms included). The Grimdog route now runs on to 21076, where its directions end (add_na_places).
  - Angel's Landing is an island: land round its rooms with water between it and the mainland; its trail a very faint dashed line. The rooms north
    of 21142 are hidden, but the island is big enough to hold them (all its rooms count, apart from 21144 and 21151, which have no exit to the rest
    and were only parked beside it in the editor).
  - Village of Edo: the small island drawn round 7747 on Oct 12 is gone (az_merge ISLAND = None). The island holds the shown rooms that are not
    'Swimming' (the hidden rooms nearby do not count), with an even border of ground between the water and the paths and buildings. 'Inside' rooms
    are tiny huts, except the temple rooms (7777, 7779, 7780, 7781: 'Temple' or 'Rune' in the name), which one Japanese temple graphic covers. The
    rice field (7788-7792, each joined to 3+ others) is a small paddy field, like the Southern Mountains' clearings.
The sea is grown round both islands, only inside a box round each (gotcha 1), and the old sea there is traced again with it as one body."""
import math
import numpy as np
from collections import defaultdict
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
import arrange_apply as AA
import gap_fill as GF
from ntr_merge import _chains, _samples
from smr_merge import _drawn, _hash

R8 = GF.R8
PARKED = {21144, 21151}                         # (Angel's Landing rooms with no exit to the rest: parked by the editor, not placed by the owner)
TEMPLE = [7777, 7779, 7780, 7781]               # 'Temple' / 'Rune' rooms: one temple graphic over them (+ spacer 7783 between them)
TEMPLE_SPACER = 7783
RICE = [7788, 7789, 7790, 7791, 7792]           # the rice field: each joined to 3+ others
EDO_R, AL_R = 1.35, 1.45                        # the ground reaches this far from the island's rooms and paths
SEA_R = 6.0                                     # the sea grown round each island reaches about this far from it
SEED = 131


def _setup(layout, edges):
    pos = dict(zip(layout['ids'], zip(layout['xs'], layout['ys'])))
    info = {r['id']: r for r in edges['rooms']}
    hidden = set(layout.get('hidden', []))
    grp = {v: r.get('grp') for v, r in info.items() if r.get('area') == 'NA'}
    return pos, info, hidden, grp


def _grid(box):
    bw, bh = int((box[2] - box[0]) * R8), int((box[3] - box[1]) * R8)
    gy, gx = np.mgrid[0:bh, 0:bw]
    return bw, bh, (gx + .5) / R8 + box[0], (gy + .5) / R8 + box[1]


def _field(shape, sigma, seed):
    f = ndi.gaussian_filter(np.random.default_rng(seed).normal(size=shape), sigma * R8); return (f - f.min()) / (f.max() - f.min())


def _island(box, pos, dry, wet, edges_dry, edges_mixed, R, seed, wobble=0.12):
    """land within R of the dry rooms and the paths between them, closer to them than to the swimming rooms (an exit between land and water is land
    to its middle), smoothed and with its holes filled"""
    bw, bh, X, Y = _grid(box); P = np.c_[X.ravel(), Y.ravel()]
    lp = [pos[v] for v in dry] + list(_samples([[pos[a], pos[b]] for a, b in edges_dry], 0.15))
    wp = [pos[v] for v in wet]
    for a, b in edges_mixed:
        w_, d_ = (a, b) if a in wet else (b, a); m = ((pos[a][0] + pos[b][0]) / 2, (pos[a][1] + pos[b][1]) / 2)
        wp += list(_samples([[pos[w_], m]], 0.15)); lp += list(_samples([[m, pos[d_]]], 0.15))
    d_l = cKDTree(np.array(lp)).query(P)[0].reshape(bh, bw)
    d_w = cKDTree(np.array(wp)).query(P)[0].reshape(bh, bw) if wp else np.full((bh, bw), np.inf)
    wob = _field((bh, bw), 1.4, seed)
    m = (d_l <= R * (1 - wobble + 2 * wobble * wob)) & (d_l < d_w)
    m = ndi.gaussian_filter(m.astype(float), 0.5 * R8) > 0.5
    return ndi.binary_fill_holes(m), X, Y


def _grow_sea(w, box, island, seed, rep, key):
    """sea round the island (only inside box), joined with the old sea it touches into one body; the island is a hole in it"""
    bw, bh, X, Y = _grid(box)
    land0 = AA._raster(w['geo']['land'], box[0], box[1], bw, bh)
    assert not (land0 & ndi.binary_dilation(island, iterations=R8)).any(), key + ': the island would touch the old land'
    d_i = ndi.distance_transform_edt(~island) / R8
    wob = _field((bh, bw), 1.8, seed)
    sea = (d_i <= SEA_R * (0.8 + 0.4 * wob)) & ~island & ~land0
    sea = ndi.gaussian_filter(sea.astype(float), 0.6 * R8) > 0.5
    sea &= ~(island | land0)
    water = w['geo']['water']
    grown = ndi.binary_dilation(sea | island, iterations=2)
    hit = [i for i, p in enumerate(water) if (AA._raster([p], box[0], box[1], bw, bh) & grown).any()]
    keep = [q for i, q in enumerate(water) if i not in hit]
    pts = [q for i in hit for q in water[i]] + [[box[0], box[1]], [box[2], box[3]]]
    gx0, gy0 = math.floor(min(q[0] for q in pts)) - 2, math.floor(min(q[1] for q in pts)) - 2
    gx1, gy1 = math.ceil(max(q[0] for q in pts)) + 2, math.ceil(max(q[1] for q in pts)) + 2
    G = np.zeros((int((gy1 - gy0) * R8), int((gx1 - gx0) * R8)), bool)
    for i in hit: G ^= AA._raster([water[i]], gx0, gy0, G.shape[1], G.shape[0])
    c0, r0 = int(round((box[0] - gx0) * R8)), int(round((box[1] - gy0) * R8))
    old = G[r0:r0 + bh, c0:c0 + bw].copy()
    G[r0:r0 + bh, c0:c0 + bw] = (old | sea) & ~island
    w['geo']['water'] = keep + AA._contours(G, gx0, gy0, sigma=1.5)              # (as west_sea and az_merge drew it: the old coast elsewhere moves least)
    after = AA._raster(w['geo']['water'], box[0], box[1], bw, bh)
    rep[key + '_sea'] = dict(added_sq=round(float((sea & ~old).sum()) / R8 / R8, 1), old_pieces_joined=len(hit), island_in_old_water_sq=round(float((old & island).sum()) / R8 / R8, 1))
    return after


def _clear_sprites(w, box, mask, clear_mask=None):
    """nothing stands in the new sea (gotcha 2); trees and the like give way on the islands where clear_mask says"""
    bw, bh = mask.shape[1], mask.shape[0]
    def bad(q):
        c, r = int((q[0] - box[0]) * R8), int((q[1] - box[1]) * R8)
        return 0 <= r < bh and 0 <= c < bw and (bool(mask[r, c]) or (clear_mask is not None and bool(clear_mask[r, c])))
    n = {}
    for k in ('trees', 'tufts', 'peaks', 'hills', 'crags', 'boulders', 'brush', 'reeds', 'wheattufts', 'ripples', 'thorns'):
        if k in w: n0 = len(w[k]); w[k] = [q for q in w[k] if not bad(q)]; n[k] = n0 - len(w[k])
    return {k: v for k, v in n.items() if v}


def _clip_tints(w, box, sea):
    bw, bh = sea.shape[1], sea.shape[0]; clipped = {}
    for k in [k for k in w['geo'] if k not in ('land', 'water')]:
        polys = w['geo'].get(k) or []
        near = [p for p in polys if any(box[0] <= q[0] < box[2] and box[1] <= q[1] < box[3] for q in p)]
        if not near: continue
        inter = sea & AA._raster(near, box[0], box[1], bw, bh)
        if inter.sum() > 4:
            w['geo'][k] = list(polys) + AA._contours(inter, box[0], box[1], sigma=1.0, minarea=0.05); clipped[k] = round(float(inter.sum()) / R8 / R8, 1)
    return clipped


def _place(mask, X, Y, spacing, salt):
    ys, xs = np.nonzero(mask); placed = []; grid = {}
    for i in np.argsort(_hash(X[ys, xs], Y[ys, xs], salt), kind='stable'):
        x, y = X[ys[i], xs[i]], Y[ys[i], xs[i]]; gk = (int(x // spacing), int(y // spacing))
        if any(math.dist(q, (x, y)) < spacing for dx in (-1, 0, 1) for dy in (-1, 0, 1) for q in grid.get((gk[0] + dx, gk[1] + dy), ())): continue
        grid.setdefault(gk, []).append((x, y)); placed.append((round(float(x), 3), round(float(y), 3)))
    return placed


def _shore(island, sea_after, W_):
    """a thin sand rim on the island's edge"""
    d = ndi.distance_transform_edt(island) / R8
    return island & (d <= W_)


def merge_na(w, layout, edges, seed=SEED):
    pos, info, hidden, grp = _setup(layout, edges)
    terr = lambda v: info[v].get('terrain') or ''
    rep = {}
    shown = lambda v: v in pos and v not in hidden
    E = [(a, b, k) for a, b, k in edges['edges']]

    # ================= Angel's Landing: an island, a very faint dashed trail =================
    AL = {v for v, g in grp.items() if g == 'al'}
    al_wet = {v for v in AL if terr(v) in ('Swimming', 'Water')}
    for v in AL:                                                                  # (a spacer between water rooms or the mainland is in the water)
        if info[v].get('void') and all((u in al_wet or u not in AL) for a, b, k in E for u in (a, b) if v in (a, b) and u != v): al_wet.add(v)
    al_dry = AL - al_wet - PARKED
    ed_d = [(a, b) for a, b, k in E if a in al_dry and b in al_dry and (k != 'ud' or math.dist(pos[a], pos[b]) < 3)]
    ed_m = [(a, b) for a, b, k in E if {a, b} <= AL and ((a in al_wet) != (b in al_wet)) and k != 'ud' and not {a, b} & PARKED]
    xs = [pos[v][0] for v in al_dry | al_wet]; ys = [pos[v][1] for v in al_dry | al_wet]
    ABOX = (math.floor(min(xs)) - 10, math.floor(min(ys)) - 10, math.ceil(max(xs)) + 4, math.ceil(max(ys)) + 6)
    isl_a, AX, AY = _island(ABOX, pos, al_dry, al_wet, ed_d, ed_m, AL_R, seed)
    sea_a = _grow_sea(w, ABOX, isl_a, seed + 1, rep, 'angels')
    rep['angels_tints_clipped'] = _clip_tints(w, ABOX, sea_a & ~isl_a)
    rep['angels_sprites_cleared'] = _clear_sprites(w, ABOX, sea_a & ~isl_a, isl_a)
    w['geo']['land'] = list(w['geo']['land']) + AA._contours(isl_a, ABOX[0], ABOX[1], sigma=1.0)
    G = defaultdict(set)                                                          # the trail: every shown exit of the area, the swim from the beach included
    for a, b, k in E:
        if not ({a, b} & AL) or not (shown(a) and shown(b)) or k == 'ud': continue
        G[a].add(b); G[b].add(a)
    pinned = {v for v in G if v not in AL}
    faint = _chains(G, pos, pinned, 0.4)
    w['pffaint'] = list(w.get('pffaint') or []) + faint
    sand_a = _shore(isl_a, sea_a, 0.28)
    mtn = [pos[v] for v in AL if terr(v) == 'Mountains' and v not in PARKED]
    P = np.c_[AX.ravel(), AY.ravel()]
    d_mtn = cKDTree(np.array(mtn)).query(P)[0].reshape(AX.shape)
    pts = _samples([_drawn(l) for l in faint], 0.1); d_path = cKDTree(pts).query(P)[0].reshape(AX.shape)
    barren = isl_a & ~sand_a & (d_mtn <= 1.3 * (0.75 + 0.5 * _field(AX.shape, 0.5, seed + 2)))
    barren = ndi.gaussian_filter(barren.astype(float), 0.4 * R8) > 0.5
    w['geo']['sand'] = list(w['geo'].get('sand') or []) + AA._contours(sand_a, ABOX[0], ABOX[1], sigma=1.0, minarea=0.1)
    w['geo']['clifftop'] = list(w['geo'].get('clifftop') or []) + AA._contours(barren, ABOX[0], ABOX[1], sigma=1.5, minarea=0.1)   # (grey rocky ground round the ledge and the overlook)
    rocks = _place(barren & (d_path > 0.45), AX, AY, 0.9, 61)
    tufts = _place(isl_a & ~sand_a & ~barren & (d_path > 0.4), AX, AY, 0.85, 62)
    w['boulders'] = list(w.get('boulders') or []) + [[x, y, round(0.4 + 0.3 * float(_hash(x, y, 63)), 2)] for x, y in rocks]
    w['tufts'] = list(w.get('tufts') or []) + [[x, y, round(0.75 + 0.3 * float(_hash(x, y, 64)), 2), 'g', int(float(_hash(x, y, 65)) * 3)] for x, y in tufts]
    on = lambda m, box, v: bool(m[int((pos[v][1] - box[1]) * R8), int((pos[v][0] - box[0]) * R8)])
    rep['angels'] = dict(rooms_on_island=len(al_dry), hidden_on_island=len(al_dry & hidden), island_sq=round(float(isl_a.sum()) / R8 / R8, 1),
                         water_to_mainland=round(float(min(math.dist(pos[v], pos[5667]) for v in al_dry)), 1), faint_lines=len(faint),
                         sand_sq=round(float(sand_a.sum()) / R8 / R8, 1), rocky_sq=round(float(barren.sum()) / R8 / R8, 1), boulders=len(rocks), tufts=len(tufts),
                         dry_rooms_off_island=sorted(v for v in al_dry if not on(isl_a, ABOX, v)), wet_rooms_on_land=sorted(v for v in al_wet if v in pos and on(isl_a, ABOX, v)),
                         box=ABOX)

    # ================= the Village of Edo: an island with paths, huts, a temple and a rice field =================
    ED = {v for v, g in grp.items() if g == 'edo' and shown(v)}
    ed_wet = {v for v in ED if terr(v) == 'Swimming'} | {7746}
    ed_dry = ED - ed_wet
    for v in list(ed_dry):                                                        # (a spacer joining only water rooms is water)
        if info[v].get('void') and all(u in ed_wet for a, b, k in E for u in (a, b) if v in (a, b) and u != v and shown(u)): ed_dry.discard(v); ed_wet.add(v)
    eE = [(a, b, k) for a, b, k in E if {a, b} & ED and shown(a) and shown(b)]
    ed_d = [(a, b) for a, b, k in eE if a in ed_dry and b in ed_dry and k != 'ud']
    ed_m = [(a, b) for a, b, k in eE if ((a in ed_wet) != (b in ed_wet)) and k != 'ud']
    xs = [pos[v][0] for v in ED]; ys = [pos[v][1] for v in ED]
    EBOX = (math.floor(min(xs)) - 9, math.floor(min(ys)) - 9, math.ceil(max(xs)) + 9, math.ceil(max(ys)) + 3)
    isl_e, EX, EY = _island(EBOX, pos, ed_dry, ed_wet, ed_d, ed_m, EDO_R, seed + 10, wobble=0.06)
    sea_e = _grow_sea(w, EBOX, isl_e, seed + 11, rep, 'edo')
    rep['edo_tints_clipped'] = _clip_tints(w, EBOX, sea_e & ~isl_e)
    rep['edo_sprites_cleared'] = _clear_sprites(w, EBOX, sea_e & ~isl_e, isl_e)
    w['geo']['land'] = list(w['geo']['land']) + AA._contours(isl_e, EBOX[0], EBOX[1], sigma=1.0)
    # paths: dirt on the island, the water route over the swimming rooms; none inside the temple or across the rice field (the dikes are its paths)
    inner = set(TEMPLE) | {TEMPLE_SPACER}
    GD = defaultdict(set); GW = defaultdict(set)
    for a, b, k in eE:
        if k == 'ud' or {a, b} <= inner or {a, b} <= set(RICE): continue
        if {a, b} & inner and not ({a, b} - inner) <= {7776}: continue
        Gx = GW if (a in ed_wet or b in ed_wet) else GD
        Gx[a].add(b); Gx[b].add(a)
    pinned = {7746} | (set(GW) & set(GD))
    dirt = _chains(GD, pos, pinned, 0.4); seaw = _chains(GW, pos, pinned, 0.6)
    w['fwtracks'] = list(w['fwtracks']) + dirt
    w['seaways'] = list(w.get('seaways') or []) + seaw
    P = np.c_[EX.ravel(), EY.ravel()]
    pts = _samples([_drawn(l) for l in dirt + seaw], 0.1); d_path = cKDTree(pts).query(P)[0].reshape(EX.shape)
    # the rice field: the cells of mutually joined rice rooms, widened half a room, with dikes and rows of rice
    rset = set(RICE); radj = defaultdict(set)
    for a, b, k in eE:
        if {a, b} <= rset: radj[a].add(b); radj[b].add(a)
    assert all(len(radj[v]) >= 2 for v in RICE) and all(sum(1 for a, b, k in eE if v in (a, b)) >= 3 for v in RICE)
    tris = [[pos[a], pos[b], pos[c]] for a in RICE for b in RICE for c in RICE if a < b < c and b in radj[a] and c in radj[a] and c in radj[b]]
    cell = AA._raster(tris, EBOX[0], EBOX[1], EX.shape[1], EY.shape[0])
    rice = ndi.distance_transform_edt(~cell) / R8 <= 0.5
    rice = (ndi.gaussian_filter(rice.astype(float), 0.4 * R8) > 0.5) & isl_e
    patch = AA._contours(rice, EBOX[0], EBOX[1], sigma=1.2, minarea=0.2)
    ri = ndi.binary_erosion(rice, iterations=1); dikes = []
    def runs(line, fixed, along, horiz):
        out = []; on_ = False
        for i, b in enumerate(list(line) + [False]):
            if b and not on_: s = i; on_ = True
            elif not b and on_:
                on_ = False
                if i - s >= 3:
                    a0, a1 = along[s], along[i - 1]
                    out.append([round(float(a0), 2), round(float(fixed), 2), round(float(a1), 2), round(float(fixed), 2)] if horiz else
                               [round(float(fixed), 2), round(float(a0), 2), round(float(fixed), 2), round(float(a1), 2)])
        return out
    rx0, ry0 = float(EX[0, 0]), float(EY[0, 0])
    for yy in np.arange(math.ceil(ry0 / 0.5) * 0.5, EY[-1, 0], 0.5):
        r = int(round((yy - ry0) * R8))
        if 0 <= r < ri.shape[0] and ri[r].any(): dikes += runs(ri[r], yy, EX[0], True)
    for xx in np.arange(math.ceil(rx0 / 0.5) * 0.5, EX[0, -1], 0.5):
        c = int(round((xx - rx0) * R8))
        if 0 <= c < ri.shape[1] and ri[:, c].any(): dikes += runs(ri[:, c], xx, EY[:, 0], False)
    tuft = []
    for yy in np.arange(math.ceil(ry0 / 0.5) * 0.5 + 0.25, EY[-1, 0], 0.25):
        for xx in np.arange(math.ceil(rx0 / 0.5) * 0.5 + 0.125, EX[0, -1], 0.25):
            r, c = int((yy - ry0) * R8), int((xx - rx0) * R8)
            if 0 <= r < ri.shape[0] and 0 <= c < ri.shape[1] and ri[r, c] and abs((xx * 2) % 1 - 0.5) > 0.1 and abs((yy * 2) % 1 - 0.5) > 0.05:
                tuft.append([round(float(xx), 2), round(float(yy), 2)])
    w['rice'] = dict(patch=patch, dikes=dikes, tufts=tuft)
    # huts: the 'Inside' rooms (the temple's aside)
    huts = sorted(v for v in ed_dry if terr(v) == 'Inside' and v not in TEMPLE)
    w['gfx'] = list(w['gfx']) + [{'k': 'hut', 'at': 'xy', 'x': round(pos[v][0], 2), 'y': round(pos[v][1] - 0.05, 2), 'w': 0.72, 'h': 0.62} for v in huts]
    # the temple: one graphic over 7777, 7779, 7780 and 7781
    tx = [pos[v][0] for v in TEMPLE]; ty = [pos[v][1] for v in TEMPLE]
    cx, cy = (min(tx) + max(tx)) / 2, (min(ty) + max(ty)) / 2
    tw, th = max(tx) - min(tx) + 1.3, max(ty) - min(ty) + 0.75
    w['gfx'] = list(w['gfx']) + [{'k': 'jtemple', 'at': 'xy', 'x': round(cx, 2), 'y': round(cy, 2), 'w': round(tw, 2), 'h': round(th, 2)}]
    # the ground: a thin sand rim, a few trees by the forest path, grass elsewhere; nothing on paths, huts, the temple or the rice
    sand_e = _shore(isl_e, sea_e, 0.28)
    blocked = rice.copy()
    for v in huts: blocked |= (np.abs(EX - pos[v][0]) < 0.5) & (np.abs(EY - pos[v][1]) < 0.45)
    blocked |= (np.abs(EX - cx) < tw / 2 + 0.15) & (np.abs(EY - cy) < th / 2 + 0.15)
    forest = [pos[v] for v in ED if terr(v) == 'Forest']
    d_for = cKDTree(np.array(forest)).query(P)[0].reshape(EX.shape) if forest else np.full(EX.shape, np.inf)
    trees = _place(isl_e & ~sand_e & ~blocked & (d_path > 0.5) & (d_for <= 1.6), EX, EY, 0.8, 71)
    tufts = _place(isl_e & ~sand_e & ~blocked & (d_path > 0.4) & (d_for > 1.6), EX, EY, 0.9, 72)
    w['trees'] = list(w['trees']) + [[x, y, round(0.7 + 0.2 * float(_hash(x, y, 73)), 2), 'd', int(float(_hash(x, y, 74)) * 3)] for x, y in trees]
    w['tufts'] = list(w.get('tufts') or []) + [[x, y, round(0.7 + 0.3 * float(_hash(x, y, 75)), 2), 'g', int(float(_hash(x, y, 76)) * 3)] for x, y in tufts]
    w['geo']['sand'] = list(w['geo'].get('sand') or []) + AA._contours(sand_e, EBOX[0], EBOX[1], sigma=1.0, minarea=0.1)
    rep['edo'] = dict(rooms_on_island=len(ed_dry), swimming_rooms=len(ed_wet - {7746}), island_sq=round(float(isl_e.sum()) / R8 / R8, 1),
                      dirt_lines=len(dirt), water_lines=len(seaw), huts=huts, temple=[round(cx, 2), round(cy, 2), round(tw, 2), round(th, 2)],
                      rice_sq=round(float(rice.sum()) / R8 / R8, 1), dikes=len(dikes), rice_tufts=len(tuft), trees=len(trees), tufts=len(tufts),
                      dry_rooms_off_island=sorted(v for v in ed_dry if not on(isl_e, EBOX, v)), wet_rooms_on_land=sorted(v for v in ed_wet if on(isl_e, EBOX, v)),
                      min_edge_gap=round(float(min(ndi.distance_transform_edt(isl_e)[int((pos[v][1] - EBOX[1]) * R8), int((pos[v][0] - EBOX[0]) * R8)] / R8 for v in ed_dry)), 2),
                      box=EBOX)
    xs_ = [q[0] for k in ('land', 'water') for p in w['geo'][k] for q in p]; ys_ = [q[1] for k in ('land', 'water') for p in w['geo'][k] for q in p]
    b0 = list(w['bounds'])
    w['bounds'] = [min(b0[0], math.floor(min(xs_)) - 2), min(b0[1], math.floor(min(ys_)) - 2), b0[2], b0[3]]
    rep['bounds'] = [b0, w['bounds']]
    return w, rep


def add_na_places(w, layouts):
    """Angel's Landing (owner's directions, Oct 16; they end at 21135, A Break in the Coast Line). Added before route_fix, which joins its line across
    the Ofcol Shortcut"""
    import data as DT
    from route_fix import make_tracer
    from extra_places import segments
    rooms, walk, at = make_tracer(w, layouts)
    lines = (DT.AREAS + '\n' + DT.MORE_DIRECTIONS).split('\n')
    rep = {}
    name = "Angel's Landing"
    assert not any(p['name'] == name for p in w['places'])
    route = next(l.split('|', 1)[1].strip().rstrip(';') for l in lines if l.startswith(name + '|'))
    t = walk(route); last = max(i for i, v in enumerate(t) if at(v))
    upto = t[:last + 1]; segs = segments([at(v) for v in upto])
    w['places'].append(dict(name=name, route=route, room=rooms[upto[-1]]['name'], dir='here' if last == len(t) - 1 else route.split(';')[-1],
                            path=[q for s in segs for q in s], segs=segs, group='af', where='an island off the Forgotten Beach',
                            note=None if len(segs) == 1 else "Part of your directions passes through areas that aren't drawn yet, so the traced line breaks there."))
    rep[name] = dict(end_room=upto[-1], rooms=len(t), pieces=len(segs), marker=segs[-1][-1])
    return w, rep


def grimdog_route(w, layouts):
    """The Grimdog Port Authority's route traced on through the hidden rooms to 21076, where its directions end (the marker moves there with it)"""
    from route_fix import make_tracer
    from extra_places import segments
    rooms, walk, at = make_tracer(w, layouts)
    rep = {}
    p = next(p for p in w['places'] if p['name'] == 'The Grimdog Port Authority')
    t = walk(p['route'].rstrip(';')); last = max(i for i, v in enumerate(t) if at(v))
    if t[last] == 21076:
        old = list(p['path'][-1]); segs = segments([at(v) for v in t[:last + 1]])
        p['path'] = [q for s in segs for q in s]; p['segs'] = segs; p['room'] = rooms[21076]['name']
        rep['Grimdog'] = dict(marker_from=old, marker_to=segs[-1][-1], pieces=len(segs))
    return w, rep
