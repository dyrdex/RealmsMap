"""Puts the Southern Mountain Range, its Southern Mountain Trade Route and the moved Sparse Woodlands trail on the map
(smr_layout_final.json, smr_editor_edges.json: the owner's layout from tools/southern_mountain_range_editor).
Owner's rules (Oct 14):
1. Paths are drawn with respect to their neighbouring rooms: wherever rooms are directly adjacent, the path widens into one pathway that takes in
   several rooms.
2. A clump of rooms that all touch one another is not a path but a clearing: one open dirt patch made of those rooms (4 rooms in a square = a
   square patch). Both rules come from one shape: every cell of mutually exit-joined rooms (3 rooms all joined to each other, or the 4 corners of a
   square) is filled, cells that share rooms run together, and the patch is widened by half a room. A string of rooms with no such cells is a plain
   trail. It follows the exits, not the distance between rooms (the owner spread some blocks out to ~2.7 rooms apart).
Decided here (not in the owner's rules): the Trade Route is a formal road like the other trade routes (same widening, road colours, off-ramp pads
where the route meets other rooms); everything else is dirt. Terrain comes from the rooms' TinTin terrain. The land grows round the rooms (the map
now reaches south). Spacer rooms are drawn only between two real rooms (dead-end stubs left off); rooms and links of hidden rooms are not drawn.
The Sparse Woodlands trail (the Forest of Tears rooms the owner moved in this editor) is drawn by ft_merge from the moved positions (build.py
passes them in); this module only draws the links between it and the range.
Runs after ft_merge on a grid that reaches from the map's north edge (y -215) to the new south edge; the land is traced again from it."""
import math, random
import numpy as np
from collections import defaultdict
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from scipy.spatial import cKDTree, ConvexHull
from skimage.morphology import disk
import arrange_apply as AA
import gap_fill as GF
from ntr_merge import _chains, _samples, _nearest_on

R8 = GF.R8
X0, X1 = GF.X0, GF.X1
YN = -215.0
W = int((X1 - X0) * R8)
SQ = 1.1             # a room's square (rooms are 1 x 1; a little more so that neighbours merge)
CELL_MAX = 6.0       # exits longer than this do not make a cell (they are links, not neighbours)
PAD = 0.55           # a clearing reaches half a room beyond the outer rooms
MIN_PATCH = 3.0      # smallest clearing / wide pathway kept (sq rooms)
LAND_R = 4.2         # land reaches this far from a path
TERR_R = 3.8         # a room's terrain tint reaches this far
CLEAR = 1.0          # sprites keep this far from a path or patch
BAND = 2.4           # standard forest reaches this far (wobbled) from the connection to the Ashen Forest
SPRITE = {'m': 2.0, 'h': 1.7, 'd': 0.95}   # minimum spacing: peaks, hills, trees


def _drawn(p, n=14):
    """the line the template draws for a polyline p (its curve(): quadratic pieces with the points as controls, joined at the mid-points)"""
    if len(p) < 3: return [list(q) for q in p]
    out = [list(p[0])]; start = list(p[0])
    for i in range(1, len(p) - 1):
        m = [(p[i][0] + p[i + 1][0]) / 2, (p[i][1] + p[i + 1][1]) / 2]
        for k in range(1, n + 1):
            t = k / n; out.append([(1 - t) ** 2 * start[0] + 2 * (1 - t) * t * p[i][0] + t * t * m[0], (1 - t) ** 2 * start[1] + 2 * (1 - t) * t * p[i][1] + t * t * m[1]])
        start = m
    out.append(list(p[-1])); return out


def _paint(img, a, b, win, wpx):
    ImageDraw.Draw(img).line([a, b], fill=255, width=wpx)


def merge_smr(w, layout, edges, seed=71):
    rng = random.Random(seed); nrng = np.random.default_rng(seed)
    pos = dict(zip(layout['ids'], zip(layout['xs'], layout['ys'])))
    hidden = set(layout.get('hidden', []))
    info = {r['id']: r for r in edges['rooms']}
    mov = {v for v, r in info.items() if not r.get('fixed') and v in pos}
    shown = lambda v: v in mov and v not in hidden
    void = lambda v: bool(info[v].get('void'))
    grp = lambda v: info[v].get('grp')
    DOM = {v for v in mov if shown(v) and grp(v) in ('sm', 'ug', 'tr')}        # what this module draws (the trail is ft_merge's)
    TRT = {v for v in DOM if grp(v) == 'tr'}
    report = {}

    # ---------------------------------------------------------------- the graphs
    GS = defaultdict(set); GT = defaultdict(set); links = []; uds = []
    NO_UD = {frozenset((291, 292))}                                    # the one up/down exit that is not drawn (owner, Oct 14)
    for a, b, k in edges['edges']:
        if a not in pos or b not in pos: continue
        if grp(a) == 'af' or grp(b) == 'af': continue                    # the visual-only link to the Ashen Forest (room 670): not drawn yet (owner, Oct 14)
        ina, inb = a in DOM, b in DOM
        if not (ina or inb): continue
        if (a in mov and a in hidden) or (b in mov and b in hidden): continue
        if k == 'ud':                                                  # up/down exits (owner, Oct 14): small dirt lines; they join different levels, so they make no wide path or clearing
            if frozenset((a, b)) not in NO_UD: uds.append((a, b))
            continue
        if ina and inb:
            if (a in TRT) and (b in TRT): GT[a].add(b); GT[b].add(a)
            elif (a not in TRT) and (b not in TRT): GS[a].add(b); GS[b].add(a)
            else: links.append((a, b))
        else: links.append((a, b))                                      # to the Sparse Woodlands trail or to a fixed room on the map
    import json as _js, os as _os
    CL = _js.load(open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'smr_clearings.json')))      # clearings the owner marks by hand (Oct 14)
    in_box = lambda v, bx: bx[0] <= pos[v][0] <= bx[2] and bx[1] <= pos[v][1] <= bx[3]
    boxed = {}; faintG = defaultdict(set)                                       # box index -> the shown rooms inside it
    for i, c in enumerate(CL.get('boxes', [])):
        boxed[i] = {v for v in DOM if in_box(v, c['box'])}
        for G in (GS,):
            for a in list(G):
                for b in list(G[a]):
                    if a in boxed[i] and b in boxed[i]:
                        G[a].discard(b); G[b].discard(a)                      # a connection inside the clearing is not drawn ...
                        if c.get('faint_paths'): faintG[a].add(b); faintG[b].add(a)      # ... or only very lightly
        uds[:] = [(a, b) for a, b in uds if not (a in boxed[i] and b in boxed[i])]
        links[:] = [(a, b) for a, b in links if not (a in boxed[i] and b in boxed[i])]     # (also the range's links to the Trade Route junction inside it)
    climb_rooms = [set(c['rooms']) for c in CL.get('climbs', [])]
    for cr in climb_rooms:                                                      # the thin lines between the rooms of a climb are replaced by its wide rocky path
        uds[:] = [(a, b) for a, b in uds if not (a in cr and b in cr)]
        links[:] = [(a, b) for a, b in links if not (a in cr and b in cr)]
        for a in list(GS):
            for b in list(GS[a]):
                if a in cr and b in cr: GS[a].discard(b); GS[b].discard(a)
    report['clearing_boxes'] = [{'name': c['name'], 'rooms': len(boxed[i])} for i, c in enumerate(CL.get('boxes', []))]
    def prune(G, extra):
        pr = set()
        while True:                                                    # dead-end spacer stubs are left off
            sp = [v for v in G if void(v) and len(G[v]) + extra.get(v, 0) <= 1]
            if not sp: break
            for v in sp:
                for u in list(G[v]): G[u].discard(v)
                del G[v]; pr.add(v)
        for v in [v for v in G if not G[v]]: del G[v]
        return pr
    lcount = defaultdict(int)
    for a, b in links: lcount[a] += 1; lcount[b] += 1
    pruned = prune(GS, lcount) | prune(GT, lcount)
    report['rooms_shown'] = {'range': len([v for v in DOM if v not in TRT]), 'route': len(TRT)}
    report['spacer_stubs_dropped'] = len(pruned)
    onmap = {v for G in (GS, GT) for v in G} | {v for a, b in links for v in (a, b) if v in DOM}
    onmap |= {v for a, b in uds for v in (a, b) if v in DOM and not void(v)}                 # (a real room whose only exits are up/down ones is still on the map)
    LINKS = [(a, b) for a, b in links if (a in DOM) != (b in DOM) or (a in DOM and b in DOM)]
    LINKS = [(a, b) for a, b in LINKS if all((v not in DOM) or v in onmap for v in (a, b))]
    UDL = [(a, b) for a, b in uds if all((v not in DOM) or v in onmap for v in (a, b))]       # (a spacer dropped as a stub takes its up/down exit with it)
    UDL = [e for e in UDL if e not in LINKS and (e[1], e[0]) not in LINKS]
    report['up_down_exits'] = {'with_a_range_end': len(uds), 'not_drawn_pruned': len(uds) - len(UDL), 'left_out': [291, 292]}

    # the visual-only connection (owner, Oct 14; not in TinTin's map): room 559 -> spacer room 990001 -> Ashen Forest room 670, a standard dirt trail through standard forest
    VIS = (559, 990001, 670)
    vis = [[round(pos[v][0], 2), round(pos[v][1], 2)] for v in VIS] if all(v in pos and v not in hidden for v in VIS) else None
    moved_ends = 0
    if vis:
        import json, os
        _al = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ashen_layout_final.json')))
        old670 = dict(zip(_al['ids'], zip(_al['xs'], _al['ys'])))[670]                  # where the Ashen Forest drew room 670 (its trail north to 2864 starts there)
        for ln in w['fwtracks']:
            for i in (0, -1):
                if math.dist(ln[i], old670) < 0.06: ln[i] = list(vis[-1]); moved_ends += 1   # (not moved inside the Ashen merge: that re-rolls its random trees)
    report['ashen_connection'] = {'trail_ends_moved': moved_ends, 'drawn': bool(vis), 'length': round(sum(math.dist(p, q) for p, q in zip(vis, vis[1:])), 1) if vis else None}

    # ---------------------------------------------------------------- the window (everything this module paints lies in it)
    allp = np.array([pos[v] for v in onmap] + ([pos[v] for v in VIS] if vis else [])); pad = 12.0
    wx0 = math.floor(allp[:, 0].min() - pad); wx1 = math.ceil(allp[:, 0].max() + pad)
    wy0 = math.floor(allp[:, 1].min() - pad); wy1 = math.ceil(allp[:, 1].max() + pad)
    ww, hw = int((wx1 - wx0) * R8), int((wy1 - wy0) * R8)
    px = lambda p: ((p[0] - wx0) * R8, (p[1] - wy0) * R8)
    gy, gx = np.mgrid[0:hw, 0:ww]; WXg = (gx + .5) / R8 + wx0; WYg = (gy + .5) / R8 + wy0

    # ---------------------------------------------------------------- wide pathways and clearings (one shape, from the adjacent rooms)
    def fabric(G):
        """clearings and wide pathways: every cell of mutually exit-joined real rooms (a triangle, or a 4-cycle = the corners of a square) is filled,
        the cells that share rooms run together, and the result is widened by half a room (the rooms' own squares). Spacing does not matter: a block
        of rooms the owner spread out is still a clump."""
        real = {v for v in G if not void(v)}
        nb = {v: {u for u in G[v] if u in real and math.dist(pos[u], pos[v]) <= CELL_MAX} for v in real}
        cells = set()
        for a in real:
            for b in nb[a]:
                for c in nb[a] & nb[b]:
                    if len({a, b, c}) == 3: cells.add(frozenset((a, b, c)))
            for b in nb[a]:
                for c in nb[a]:
                    if b < c:
                        for d in (nb[b] & nb[c]) - {a}:
                            if len({a, b, c, d}) == 4: cells.add(frozenset((a, b, d, c)))
        im = Image.new('L', (ww, hw), 0); dr = ImageDraw.Draw(im); used = 0
        for cell in cells:
            pts = np.array([pos[v] for v in cell])
            hull = pts[ConvexHull(pts).vertices] if len(pts) >= 3 else pts
            if ConvexHull(pts).volume < 0.45: continue                                   # (three in a line: no area)
            dr.polygon([px(p) for p in hull], fill=255, outline=255); used += 1
        m0 = np.array(im, bool)
        m0 = ndi.binary_dilation(m0, structure=disk(int(PAD * R8)))                     # (the rooms' own squares)
        lab, n = ndi.label(m0); keep = np.zeros_like(m0)
        rp = [(v, px(pos[v])) for v in real]
        for i in range(1, n + 1):
            comp = lab == i
            nrooms = sum(1 for v, p in rp if 0 <= int(p[1]) < hw and 0 <= int(p[0]) < ww and comp[int(p[1]), int(p[0])])
            if nrooms >= 4 and comp.sum() / R8 / R8 >= MIN_PATCH: keep |= comp
        op = ndi.gaussian_filter(keep.astype(float), 0.45 * R8) > 0.5                  # (rounds the corners a little)
        return op, list(cells)
    def trails(G, wide):
        """the lines of what is NOT inside a wide pathway or clearing"""
        T = defaultdict(set)
        for a in G:
            for b in G[a]:
                if a >= b: continue
                n = max(2, int(math.dist(pos[a], pos[b]) * 3)); inside = True
                for i in range(n + 1):
                    x = pos[a][0] + (pos[b][0] - pos[a][0]) * i / n; y = pos[a][1] + (pos[b][1] - pos[a][1]) * i / n
                    c, r = int((x - wx0) * R8), int((y - wy0) * R8)
                    if not (0 <= r < hw and 0 <= c < ww and wide[r, c]): inside = False; break
                if not inside: T[a].add(b); T[b].add(a)
        return T
    dwide, dadj = fabric(GS); rwide, radj = fabric(GT)
    forced = Image.new('L', (ww, hw), 0); fd = ImageDraw.Draw(forced)
    for c in CL.get('boxes', []):                                              # the owner's rectangles: one dirt clearing each
        x0_, y0_, x1_, y1_ = c['box']; fd.rectangle([px((x0_, y0_)), px((x1_, y1_))], fill=255)
    dwide = ndi.gaussian_filter((dwide | np.array(forced, bool)).astype(float), 0.45 * R8) > 0.5
    added = {}; done_to = {}
    def disk_px(): return int(PAD * R8)
    sq_ = int(SQ * R8)
    def put_square(dr_, p_): dr_.rectangle([p_[0] - sq_ / 2, p_[1] - sq_ / 2, p_[0] + sq_ / 2, p_[1] + sq_ / 2], fill=255)
    todo = []
    for e_ in CL.get('add_rooms', []):
        e_ = {'room': e_} if isinstance(e_, int) else dict(e_); e_['to'] = [e_['to']] if isinstance(e_.get('to'), int) else list(e_.get('to') or [])
        if e_['room'] not in pos or any(t not in pos for t in e_['to']): added[e_['room']] = 'missing'; continue
        todo.append(e_)
    while todo:                                                               # hulls first, then stems nearest-first (a chain of rooms grows the clearing room by room)
        hulls = [e_ for e_ in todo if e_.get('mode') == 'hull']
        if hulls: e_ = hulls[0]
        else:
            best = None
            for e_c in todo:
                lab_, n_ = ndi.label(dwide); ids_ = {lab_[min(max(int(px(pos[t])[1]), 0), hw - 1), min(max(int(px(pos[t])[0]), 0), ww - 1)] for t in e_c['to']} - {0}
                comp_ = np.isin(lab_, list(ids_)) if ids_ else dwide
                d_, (iy_, ix_) = ndi.distance_transform_edt(~comp_, return_indices=True)
                p_ = px(pos[e_c['room']]); r_, c_ = min(max(int(p_[1]), 0), hw - 1), min(max(int(p_[0]), 0), ww - 1)
                if best is None or d_[r_, c_] < best[0]: best = (d_[r_, c_], e_c, (int(ix_[r_, c_]), int(iy_[r_, c_])))
            e_ = best[1]
        todo.remove(e_)
        im_ = Image.new('L', (ww, hw), 0); dr_ = ImageDraw.Draw(im_); p_ = px(pos[e_['room']])
        if e_.get('mode') == 'hull':
            pts = [pos[e_['room']]] + [pos[t] for t in e_['to']]
            cor = np.array([(x + dx, y + dy) for x, y in pts for dx in (-SQ / 2, SQ / 2) for dy in (-SQ / 2, SQ / 2)])
            hl = cor[ConvexHull(cor).vertices]; dr_.polygon([px(q) for q in hl], fill=255, outline=255); added[e_['room']] = 'hull of %d rooms' % len(pts)
        else:
            tx, ty = best[2] if not hulls else (int(p_[0]), int(p_[1]))
            dr_.line([p_, (tx, ty)], fill=255, width=sq_); put_square(dr_, p_); added[e_['room']] = round(float(best[0]) / R8, 1) if not hulls else 0
            key_ = tuple(e_['to'])
            for q_ in done_to.get(key_, []) + e_['to']:                          # ... and to the other rooms of its group within 4 rooms: rooms side by side fill the ground between them
                if math.dist(pos[q_], pos[e_['room']]) <= 4.0: dr_.line([p_, px(pos[q_])], fill=255, width=sq_)
            done_to.setdefault(key_, []).append(e_['room'])
        dwide = dwide | np.array(im_, bool)                                       # (smoothed once, below: smoothing after every room eroded the small clearings)
    if CL.get('add_rooms'): dwide = ndi.gaussian_filter(dwide.astype(float), 0.45 * R8) > 0.5
    report['clearing_rooms_added'] = added
    dwide &= ~rwide                                                                 # (a road patch lies on top of any dirt patch)
    dT = trails(GS, dwide | rwide); rT = trails(GT, rwide)
    dirt_lines = _chains(dT, pos, set(), 0.8) if dT else []
    road_lines = _chains(rT, pos, set(), 0.8) if rT else []
    # the links between the range, the route, the moved Sparse Woodlands trail and fixed rooms: small dirt lines
    link_lines = []; far = []
    snap = {}; offs = []                                                       # off-ramps lie ON the drawn road: a Trade Route room's pad (and the end of the line that joins it) goes to the nearest point of the road
    for a, b in LINKS:
        for v, o in ((a, b), (b, a)):
            if v in TRT and o not in TRT and road_lines and v not in snap:
                q_ = _nearest_on([_drawn(l) for l in road_lines], pos[v]); snap[v] = [round(q_[0], 2), round(q_[1], 2)]; offs.append(round(math.dist(q_, pos[v]), 2))
    end_ = lambda v: snap.get(v) or [round(pos[v][0], 2), round(pos[v][1], 2)]
    for a, b in LINKS + UDL:
        d = math.dist(pos[a], pos[b])
        if d > 30: far.append((a, b, round(d, 1)))
        else: link_lines.append([end_(a), end_(b)])
    dpatch = AA._contours(dwide, wx0, wy0, sigma=1.0, tol=0.35, minarea=MIN_PATCH * 0.5)
    rpatch = AA._contours(rwide, wx0, wy0, sigma=1.0, tol=0.35, minarea=MIN_PATCH * 0.5)
    # ---- thin paths never run over a clearing (owner, Oct 14): each stops where it enters one (it only shows that the path leads into it)
    dmask = AA._raster(dpatch, wx0, wy0, ww, hw)
    def clip(lines, step=0.08, keep_every=4):
        out = []; cut = 0
        for ln in lines:
            pts = []                                                              # the line, sampled; remember which samples are inside a clearing
            for p, q in zip(ln[:-1], ln[1:]):
                n_ = max(1, int(math.dist(p, q) / step))
                pts += [(p[0] + (q[0] - p[0]) * k / n_, p[1] + (q[1] - p[1]) * k / n_) for k in range(n_)]
            pts.append(tuple(ln[-1]))
            ins = []
            for x, y in pts:
                c_, r_ = int((x - wx0) * R8), int((y - wy0) * R8)
                ins.append(0 <= r_ < hw and 0 <= c_ < ww and bool(dmask[r_, c_]))
            if not any(ins): out.append(ln); continue
            cut += 1; run = []
            for pt, i_ in zip(pts, ins):
                if i_:
                    if len(run) >= 2: out.append(run)
                    run = []
                else: run.append(pt)
            if len(run) >= 2: out.append(run)
        res = []
        for ln in out:
            if isinstance(ln[0], tuple):                                           # a clipped run: thin it (a point every ~0.3), keep both ends
                th = ln[::keep_every]
                if th[-1] != ln[-1]: th.append(ln[-1])
                ln = [[round(x, 2), round(y, 2)] for x, y in th]
                if math.dist(ln[0], ln[-1]) < 0.12: continue                        # (a stub shorter than that shows nothing)
            res.append(ln)
        return res, cut
    dirt_lines, cut1 = clip(dirt_lines); link_lines, cut2 = clip(link_lines); vis_c, cut3 = clip([vis]) if vis else ([], 0)
    report['lines_stopped_at_a_clearing'] = {'trails': cut1, 'links': cut2, 'connection_to_670': cut3}
    # ---- the hand-made clearings' extras: their inner paths very lightly, rough-terrain marks between them
    faint_lines = _chains(faintG, pos, set(), 0.6) if faintG else []
    w['smrfaint'] = faint_lines
    road_s = _samples([_drawn(l) for l in w['etrtracks'] + road_lines if any(wx0 <= q[0] <= wx1 and wy0 <= q[1] <= wy1 for q in l)], 0.1)
    rtree = cKDTree(road_s) if len(road_s) else None
    ftree = cKDTree(_samples(faint_lines, 0.1)) if faint_lines else None
    marks = []
    for c in CL.get('boxes', []):
        if not c.get('rough_marks'): continue
        x0_, y0_, x1_, y1_ = c['box']; cand = []
        for gx_ in np.arange(x0_ + 0.45, x1_ - 0.4, 0.2):
            for gy_ in np.arange(y0_ + 0.45, y1_ - 0.4, 0.2):
                if ftree is not None and ftree.query([gx_, gy_])[0] < 0.42: continue
                if rtree is not None and rtree.query([gx_, gy_])[0] < 1.0: continue
                cand.append((gx_ + nrng.uniform(-0.08, 0.08), gy_ + nrng.uniform(-0.08, 0.08)))
        placed_ = []
        for i in nrng.permutation(len(cand)):
            x, y = cand[i]
            if all(math.dist((x, y), q) >= 0.8 for q in placed_): placed_.append((x, y))
        for x, y in placed_:
            marks.append([round(x, 2), round(y, 2), round(rng.uniform(0.55, 0.85), 2), 'b' if rng.random() < 0.4 else rng.choice([0, 1, 2])])
        report.setdefault('rough_marks', {})[c['name']] = len(placed_)
    # ---- a climb: one wide rocky path through the four rooms (it stops at clearings too)
    climbs = []
    for c in CL.get('climbs', []):
        pts = [pos[v] for v in c['rooms']]
        im = Image.new('L', (ww, hw), 0); ImageDraw.Draw(im).polygon([px(p) for p in pts], fill=255, outline=255)
        m = ndi.binary_dilation(np.array(im, bool), structure=disk(int(0.55 * R8))) & ~ndi.binary_dilation(dmask, structure=disk(1))
        m = ndi.gaussian_filter(m.astype(float), 0.5 * R8) > 0.5
        polys = AA._contours(m, wx0, wy0, sigma=1.0, tol=0.3, minarea=0.5)
        hach = []
        ys_, xs_ = np.nonzero(m); y_lo, y_hi, x_lo, x_hi = (ys_.min() / R8 + wy0, ys_.max() / R8 + wy0, xs_.min() / R8 + wx0, xs_.max() / R8 + wx0)
        k_ = 0
        for gy_ in np.arange(y_lo + 0.3, y_hi - 0.2, 0.5):
            for gx_ in np.arange(x_lo + 0.3, x_hi - 0.2, 0.55):
                x, y = gx_ + (0.27 if k_ % 2 else 0) + rng.uniform(-0.07, 0.07), gy_ + rng.uniform(-0.07, 0.07)
                c_, r_ = int((x - wx0) * R8), int((y - wy0) * R8)
                if 0 <= r_ < hw and 0 <= c_ < ww and m[r_, c_] and m[min(r_ + 3, hw - 1), c_]: hach.append([round(x - 0.13, 2), round(y + 0.09, 2), round(x + 0.13, 2), round(y - 0.09, 2)] if (int(gx_ * 7) % 2) else [round(x - 0.13, 2), round(y - 0.09, 2), round(x + 0.13, 2), round(y + 0.09, 2)])
            k_ += 1
        cand = [(wx0 + xx / R8, wy0 + yy / R8) for yy, xx in zip(ys_[::6], xs_[::6]) if ndi.distance_transform_edt(m)[yy, xx] > 0.3 * R8] if m.sum() else []
        placed_ = []
        for i in nrng.permutation(len(cand)):
            x, y = cand[i]
            if all(math.dist((x, y), q) >= 1.0 for q in placed_): placed_.append((x, y))
        for x, y in placed_: marks.append([round(x, 2), round(y, 2), round(rng.uniform(0.55, 0.8), 2), 'b' if rng.random() < 0.45 else rng.choice([0, 1, 2])])
        climbs.append({'name': c['name'], 'polys': polys, 'hach': hach})
        report.setdefault('climbs', {})[c['name']] = {'sq': round(float(m.sum()) / R8 / R8, 1), 'hatching': len(hach), 'marks': len(placed_)}
    w['smrclimb'] = climbs; w['smrmarks'] = marks
    pads = []
    for a, b in LINKS:                                                              # off-ramp pads: where the route meets anything that is not the route
        for v, o in ((a, b), (b, a)):
            if v in TRT and o not in TRT: pads.append(end_(v))
    pads = [list(p) for p in sorted({tuple(p) for p in pads})]
    w['smrpatch'] = dpatch; w['roadpatch'] = rpatch
    w['fwtracks'] = list(w['fwtracks']) + dirt_lines + link_lines + vis_c
    w['etrtracks'] = list(w['etrtracks']) + road_lines
    w['ntrjoins'] = list(w['ntrjoins']) + pads
    report['dirt'] = {'cells': len(dadj), 'patches': len(dpatch), 'patch_sq': round(float(dwide.sum()) / R8 / R8, 1), 'trail_lines': len(dirt_lines)}
    report['road'] = {'cells': len(radj), 'patches': len(rpatch), 'patch_sq': round(float(rwide.sum()) / R8 / R8, 1), 'road_lines': len(road_lines), 'pads': len(pads), 'pad_was_off_the_road_by': offs}
    report['links_drawn'] = len(link_lines) - len([1 for a, b in UDL if math.dist(pos[a], pos[b]) <= 30]); report['links_over_30'] = far
    report['up_down_exits']['drawn'] = len([1 for a, b in UDL if math.dist(pos[a], pos[b]) <= 30])

    # ---------------------------------------------------------------- the paths as a raster (land margin, sprite clearance)
    pim = Image.new('L', (ww, hw), 0); pd = ImageDraw.Draw(pim)
    for G in (GS, GT):
        for a in G:
            for b in G[a]:
                if a < b: pd.line([px(pos[a]), px(pos[b])], fill=255, width=2)
    for a, b in LINKS + UDL: pd.line([px(pos[a]), px(pos[b])], fill=255, width=2)
    if vis:
        for p, q in zip(vis, vis[1:]): pd.line([px(p), px(q)], fill=255, width=2)
    for v in onmap:
        p = px(pos[v]); pd.ellipse([p[0] - 2, p[1] - 2, p[0] + 2, p[1] + 2], fill=255)
    skel = np.array(pim, bool)
    d_path = ndi.distance_transform_edt(~(skel | dwide | rwide)) / R8

    # ---------------------------------------------------------------- the land
    land0 = AA._raster(w['geo']['land'], X0, YN, W, int((wy1 + 40 - YN) * R8))           # (the grid reaches 40 rooms below the window)
    water0 = AA._raster(w['geo']['water'], X0, YN, W, int((wy1 + 40 - YN) * R8))
    c0, r0 = int((wx0 - X0) * R8), int((wy0 - YN) * R8)
    sub = (slice(r0, r0 + hw), slice(c0, c0 + ww))
    wob = ndi.gaussian_filter(nrng.normal(size=(hw, ww)), 1.8 * R8); wob = (wob - wob.min()) / (wob.max() - wob.min())
    near = d_path <= LAND_R * (0.7 + 0.6 * wob)
    near = ndi.binary_closing(near, structure=np.ones((3, 3), bool), iterations=int(1.5 * R8))
    near = ndi.binary_fill_holes(near)
    near = ndi.gaussian_filter(near.astype(float), 0.8 * R8) > 0.5
    new_land = near & ~water0[sub]
    before = float(land0.sum()) / R8 / R8
    land_n = land0.copy(); land_n[sub] |= new_land
    added = land_n & ~land0
    lab, n = ndi.label(added)
    report['land_new_sq'] = round(float(added.sum()) / R8 / R8, 1); report['land_new_pieces'] = int(n)
    nland = AA._contours(land_n, X0, YN)
    # (land beyond the traced rows is kept as it was)
    keep = []
    cut_y = YN + land_n.shape[0] / R8
    for p in w['geo']['land']:
        if min(q[1] for q in p) >= cut_y - 1e-6: keep.append(p)
    w['geo']['land'] = nland + keep
    report['land_sq_before_after'] = (round(before), round(float(land_n.sum()) / R8 / R8))

    # ---------------------------------------------------------------- terrain: tints and sprites, from the rooms' own terrain
    real = [v for v in onmap if not void(v) and v in DOM]
    cls = {'Mountains': 'm', 'Hills': 'h', 'Forest': 'd'}
    tree = cKDTree(np.array([pos[v] for v in real])); lab_t = [info[v].get('terrain') or '' for v in real]
    P = np.c_[WXg.ravel(), WYg.ravel()]
    dist, idx = tree.query(P)
    tcls = np.array([cls.get(t, '') for t in lab_t], dtype='U1')[idx].reshape(hw, ww)
    dist = dist.reshape(hw, ww)
    landw = land_n[sub]
    band = np.zeros((hw, ww), bool)
    if vis:                                                                    # standard forest round the connection and the trail on to 2864: ground, trees; no other tint
        bl = [vis, [vis[-1], [round(pos[2864][0], 2), round(pos[2864][1], 2)]]]
        dv = cKDTree(_samples(bl, 0.1)).query(np.c_[WXg.ravel(), WYg.ravel()])[0].reshape(hw, ww)
        band = (dv <= BAND * (0.7 + 0.6 * wob)) & landw & ~water0[sub]
        band = ndi.gaussian_filter(band.astype(float), 0.6 * R8) > 0.5
    on = landw & (dist <= TERR_R)
    mount = on & (tcls == 'm') & ~band
    bar = ndi.gaussian_filter(mount.astype(float), 0.6 * R8) > 0.5
    nz = ndi.gaussian_filter(nrng.normal(size=(hw, ww)), 1.4 * R8); nz = (nz - nz.min()) / (nz.max() - nz.min())
    bar2 = bar & (nz > 0.58)
    w['geo']['barren'] = list(w['geo'].get('barren') or []) + AA._contours(bar, wx0, wy0, sigma=2.0)
    w['geo']['barren2'] = list(w['geo'].get('barren2') or []) + AA._contours(bar2, wx0, wy0, sigma=2.0)
    free = landw & (d_path > CLEAR) & ~water0[sub]
    forest = {'trees': 0, 'fill_sq': 0.0, 'old_trees_cleared': 0, 'old_tufts_cleared': 0, 'tints_clipped': {}}
    if vis:
        for k, ks in (('trees', 'old_trees_cleared'), ('tufts', 'old_tufts_cleared')):         # what was growing there is cleared (gotcha 2); the standard forest replaces it
            keep_, n_ = [], 0
            for t in w[k]:
                c_, r_ = int((t[0] - wx0) * R8), int((t[1] - wy0) * R8)
                if 0 <= r_ < hw and 0 <= c_ < ww and band[r_, c_]: n_ += 1
                else: keep_.append(t)
            w[k] = keep_; forest[ks] = n_
        for k in ('ash', 'dread', 'dread2', 'sparse', 'deep', 'bog', 'sand', 'shallows', 'blight', 'black', 'blackheart', 'bramble', 'doom'):    # other ground tints are taken out of the band (a polygon on top of the tint, drawn even-odd, is a hole)
            polys = w['geo'].get(k) or []
            if not polys: continue
            inter = band & AA._raster([p for p in polys if any(wx0 <= q[0] < wx1 and wy0 <= q[1] < wy1 for q in p)], wx0, wy0, ww, hw)
            if inter.sum() > 0:
                w['geo'][k] = list(polys) + AA._contours(inter, wx0, wy0, sigma=1.0, minarea=0.1); forest['tints_clipped'][k] = round(float(inter.sum()) / R8 / R8, 1)
        w['geo']['fill'] = list(w['geo'].get('fill') or []) + AA._contours(band, wx0, wy0, sigma=2.0)
        forest['fill_sq'] = round(float(band.sum()) / R8 / R8, 1)
        ys, xs = np.nonzero(band & free); placed = []; gridc = {}
        for i in nrng.permutation(len(ys)):
            x, y = WXg[ys[i], xs[i]], WYg[ys[i], xs[i]]; gk = (int(x // 1.0), int(y // 1.0)); ok = True
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if any(math.dist(q, (x, y)) < 1.0 for q in gridc.get((gk[0] + dx, gk[1] + dy), ())): ok = False
            if ok: gridc.setdefault(gk, []).append((x, y)); placed.append((round(float(x), 3), round(float(y), 3)))
        w['trees'] = list(w['trees']) + [[x, y, round(rng.uniform(0.85, 1.15), 2), rng.choice(['w', 'w', 'd']), rng.choice([0, 1, 2])] for x, y in placed]
        forest['trees'] = len(placed)
        free &= ~band                                                          # (no hills / peaks sprites inside the forest band)
    report['ashen_connection']['forest'] = forest
    out = {'m': [], 'h': [], 'd': []}
    for c in ('m', 'h', 'd'):
        ys, xs = np.nonzero(on & (tcls == c) & free)
        order = nrng.permutation(len(ys)); placed = []; gridc = {}
        cs = SPRITE[c]
        for i in order:
            x, y = WXg[ys[i], xs[i]], WYg[ys[i], xs[i]]; gk = (int(x // cs), int(y // cs)); ok = True
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for q in gridc.get((gk[0] + dx, gk[1] + dy), ()):
                        if math.dist(q, (x, y)) < cs: ok = False; break
                    if not ok: break
                if not ok: break
            if ok: gridc.setdefault(gk, []).append((x, y)); placed.append((round(float(x), 3), round(float(y), 3)))
        out[c] = placed
    w['peaks'] = list(w['peaks']) + [[x, y, round(rng.uniform(0.9, 1.25), 2), 'm', rng.choice([0, 0, 1, 1, 2])] for x, y in out['m']]
    w['hills'] = list(w['hills']) + [[x, y, round(rng.uniform(0.85, 1.2), 2), 'h', rng.choice([0, 1, 2])] for x, y in out['h']]
    w['trees'] = list(w['trees']) + [[x, y, round(rng.uniform(0.85, 1.15), 2), 'd', rng.choice([0, 1, 2])] for x, y in out['d']]
    report['terrain'] = {'barren_sq': round(float(bar.sum()) / R8 / R8, 1), 'peaks': len(out['m']), 'hills': len(out['h']), 'trees': len(out['d'])}

    ymax = max(allp[:, 1].max() + 14, 0)                                          # (room below the range for the west sea to taper off)
    w['bounds'] = [w['bounds'][0], w['bounds'][1], w['bounds'][2], max(w['bounds'][3], int(math.ceil(ymax)))]
    report['bounds'] = w['bounds']
    return w, report
